"""Read-only, deterministic planning derived from existing assessment results."""
from __future__ import annotations

from typing import Any

from checker import MachineInfo, CheckResult


def _item(category: str, check: str, current: str, target: str, severity: str, explanation: str, action: str = "review", gap: str | None = None, optional: bool = False) -> dict[str, Any]:
    return {"category": category, "check": check, "current": current, "target": target, "gap": gap, "action_type": action, "severity": severity, "explanation": explanation, "optional": optional}


def build_upgrade_plan(machine: MachineInfo, requirements: dict[str, Any], checks: list[CheckResult], suitability: dict[str, Any], readiness: dict[str, Any], lifecycle: dict[str, Any] | None = None) -> dict[str, Any]:
    plan = {"required_hardware_changes": [], "required_configuration_changes": [], "storage_actions": [], "unresolved_items": [], "optional_improvements": [], "already_satisfied": [], "lifecycle_warning": "", "overall_summary": ""}
    numeric = {"CPU cores": ("cpu_cores", "cores"), "CPU speed": ("cpu_ghz", "GHz"), "Memory": ("ram_gb", "GB"), "Free storage": ("storage_free_gb", "GB")}
    for check in checks:
        if check.status == "pass":
            plan["already_satisfied"].append({"check": check.name, "current": check.detected, "target": check.required})
            continue
        if check.status == "unknown":
            plan["unresolved_items"].append(_item("unknown", check.name, check.detected, check.required, "review", f"{check.name} could not be verified; confirm it before deciding on an upgrade."))
            continue
        if check.name in numeric:
            key, unit = numeric[check.name]
            required = requirements.get(key)
            actual = getattr(machine, key, None)
            if isinstance(required, (int, float)) and not isinstance(required, bool) and required > 0 and isinstance(actual, (int, float)) and not isinstance(actual, bool):
                gap = max(0.0, float(required) - float(actual))
                gap_text = f"{gap:.1f} {unit}" if isinstance(required, float) or isinstance(actual, float) else f"{int(gap)} {unit}"
            else:
                gap_text = None
            explanation = f"The detected {check.name.lower()} is below the published minimum."
            if check.name == "Free storage":
                plan["storage_actions"].append(_item("storage", check.name, check.detected, check.required, "required", explanation, action="free_or_expand", gap=gap_text))
            else:
                plan["required_hardware_changes"].append(_item("hardware", check.name, check.detected, check.required, "required", explanation, action="upgrade_or_replace", gap=gap_text))
            continue
        name = check.name.lower()
        if "architecture" in name or "cpu" in name:
            plan["required_hardware_changes"].append(_item("hardware", check.name, check.detected, check.required, "required", "The processor does not meet the published compatibility condition; software settings cannot make it officially compatible.", action="replace_hardware"))
        elif any(value in name for value in ("tpm", "secure boot", "uefi")) or "partition" in name:
            plan["required_configuration_changes" if "partition" not in name else "storage_actions"].append(_item("configuration", check.name, check.detected, check.required, "required", "The current configuration does not meet the installation condition.", action="firmware_or_boot"))
        else:
            plan["unresolved_items"].append(_item("unknown", check.name, check.detected, check.required, "review", "This requirement failed but no safe automatic change can be identified."))
    for item in readiness.get("checks", []):
        if item["status"] in {"not_ready", "review", "unknown"}:
            bucket = plan["storage_actions"] if "storage" in item["name"].lower() or "partition" in item["name"].lower() else plan["required_configuration_changes"]
            if item["status"] == "unknown":
                bucket = plan["unresolved_items"]
            bucket.append(_item("configuration", item["name"], item["detected"], item["required"], "required", item["explanation"], action="review_configuration"))
    if suitability.get("category") in {"Marginal", "Meets minimum"}:
        plan["optional_improvements"].append(_item("headroom", "Suitability", "Published minimums met", "More headroom", "optional", suitability.get("explanation", "Additional capacity may improve headroom."), action="optional_capacity", optional=True))
    if lifecycle and lifecycle.get("support_status") in {"eol", "nearing_eol"}:
        plan["lifecycle_warning"] = f"{lifecycle.get('release', 'This release')} is {lifecycle['support_status'].replace('_', ' ')}; hardware changes cannot restore vendor support."
    required_count = sum(len(plan[key]) for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions"))
    unresolved_count = len(plan["unresolved_items"])
    if required_count:
        plan["overall_summary"] = f"{required_count} required change(s) or configuration item(s) remain."
    elif unresolved_count:
        plan["overall_summary"] = f"No confirmed upgrade is required, but {unresolved_count} item(s) need review."
    else:
        plan["overall_summary"] = "No mandatory hardware or configuration changes are required."
    return plan


def localized_plan(plan: dict[str, Any], language: str = "en") -> dict[str, Any]:
    """Return a presentation copy with planner prose translated; identifiers stay stable."""
    from localization import t
    result = {key: (list(value) if isinstance(value, list) else value) for key, value in plan.items()}
    if plan["required_hardware_changes"] or plan["required_configuration_changes"] or plan["storage_actions"]:
        result["overall_summary"] = t("planner.summary.required", language, count=sum(len(plan[key]) for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions")))
    elif plan["unresolved_items"]:
        result["overall_summary"] = t("planner.summary.review", language, count=len(plan["unresolved_items"]))
    else:
        result["overall_summary"] = t("planner.summary.none", language)
    if plan.get("lifecycle_warning"):
        result["lifecycle_warning"] = t("planner.lifecycle_warning", language, warning=plan["lifecycle_warning"])
    for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions", "unresolved_items", "optional_improvements"):
        localized = []
        for item in plan[key]:
            copy = dict(item)
            if item.get("optional"):
                copy["explanation"] = t("planner.explanation.optional", language, current=item["current"], target=item["target"])
            elif item.get("category") == "unknown":
                copy["explanation"] = t("planner.explanation.unknown", language, check=item["check"], current=item["current"], target=item["target"])
            elif item.get("category") in {"configuration", "storage"}:
                copy["explanation"] = t("planner.explanation.configuration", language, check=item["check"])
            else:
                copy["explanation"] = t("planner.explanation.hardware", language, check=item["check"])
            localized.append(copy)
        result[key] = localized
    return result
