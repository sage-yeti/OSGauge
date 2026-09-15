"""Deterministic comparison of two canonical machine snapshots."""
from __future__ import annotations

from dataclasses import asdict
from html import escape
from typing import Any

from checker import MachineInfo, compatibility_score, evaluate, overall_status
from installation_readiness import evaluate_installation_readiness
from lifecycle import lifecycle_status, profile_metadata
from suitability import assess_suitability, suitability_dict


_FIELDS = (
    ("CPU", "cpu_name"), ("CPU cores", "cpu_cores"), ("CPU speed", "cpu_ghz"),
    ("Memory (GB)", "ram_gb"), ("GPU", "gpu_name"), ("VRAM (MB)", "gpu_vram_mb"),
    ("Total storage (GB)", "storage_total_gb"), ("Free storage (GB)", "storage_free_gb"),
    ("Architecture", "architecture"), ("UEFI", "uefi"), ("Secure Boot", "secure_boot"),
    ("TPM", "tpm_version"), ("Partition style", "storage_partition_style"),
    ("Filesystem", "storage_filesystem"), ("Virtualization", "virtualization"),
)


def _display(value: Any) -> str:
    if value is None or value == "":
        return "Unknown"
    if isinstance(value, bool):
        return "Enabled" if value else "Disabled"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def _difference(a: Any, b: Any) -> str:
    if a is None or b is None or a == "" or b == "":
        return "unknown"
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if a > b:
            return "A higher"
        if b > a:
            return "B higher"
    return "different" if a != b else "same"


def _candidate(a: dict[str, Any], b: dict[str, Any]) -> tuple[str, str]:
    status_order = {"pass": 0, "review": 1, "fail": 2}
    readiness_order = {"ready": 0, "review": 1, "unknown": 2, "not_ready": 3}
    suitability_order = {"Excellent fit": 0, "Good fit": 1, "Meets minimum": 2, "Marginal": 3, "Not compatible": 4}
    key_a = (status_order.get(a["compatibility"], 9), readiness_order.get(a["readiness"], 9), suitability_order.get(a["suitability"]["category"], 9), -a["suitability"]["score"], -a["compatibility_score"])
    key_b = (status_order.get(b["compatibility"], 9), readiness_order.get(b["readiness"], 9), suitability_order.get(b["suitability"]["category"], 9), -b["suitability"]["score"], -b["compatibility_score"])
    if key_a < key_b:
        return "A", "Machine A is the stronger candidate for this OS."
    if key_b < key_a:
        return "B", "Machine B is the stronger candidate for this OS."
    return "tie", "Both machines are similarly suitable for this OS."


def compare_machines(machine_a: MachineInfo, machine_b: MachineInfo, requirements: dict[str, Any], target_os: str | None = None, labels: tuple[str, str] = ("Machine A", "Machine B"), metadata: tuple[dict[str, Any], dict[str, Any]] = ({}, {})) -> dict[str, Any]:
    rows = []
    values_a, values_b = asdict(machine_a), asdict(machine_b)
    for name, key in _FIELDS:
        a, b = values_a.get(key), values_b.get(key)
        rows.append({"name": name, "field": key, "a": _display(a), "b": _display(b), "difference": _difference(a, b)})
    result: dict[str, Any] = {"machines": {"a": {"label": labels[0], "metadata": metadata[0], "machine": values_a}, "b": {"label": labels[1], "metadata": metadata[1], "machine": values_b}}, "hardware": rows}
    if target_os and target_os in requirements:
        profile = requirements[target_os]
        checks_a, checks_b = evaluate(machine_a, profile), evaluate(machine_b, profile)
        suit_a = suitability_dict(assess_suitability(machine_a, profile, checks_a))
        suit_b = suitability_dict(assess_suitability(machine_b, profile, checks_b))
        ready_a = evaluate_installation_readiness(machine_a, profile, checks_a)
        ready_b = evaluate_installation_readiness(machine_b, profile, checks_b)
        assessment_a = {"compatibility": overall_status(checks_a), "compatibility_score": compatibility_score(checks_a), "suitability": suit_a, "readiness": ready_a["status"], "checks": [asdict(x) for x in checks_a]}
        assessment_b = {"compatibility": overall_status(checks_b), "compatibility_score": compatibility_score(checks_b), "suitability": suit_b, "readiness": ready_b["status"], "checks": [asdict(x) for x in checks_b]}
        winner, summary = _candidate(assessment_a, assessment_b)
        result["target"] = {"name": target_os, "lifecycle": {**profile_metadata(target_os, profile), "support_status": lifecycle_status(profile)}, "a": assessment_a, "b": assessment_b, "candidate": winner, "summary": summary}
    return result


def plain_text_comparison(result: dict[str, Any]) -> str:
    lines = [f"Machine comparison: {result['machines']['a']['label']} vs {result['machines']['b']['label']}"]
    if result.get("target"):
        target = result["target"]
        lines += [f"OS: {target['name']}", f"Machine A: {target['a']['compatibility'].upper()} ({target['a']['compatibility_score']}/100), {target['a']['suitability']['category']}, readiness {target['a']['readiness']}", f"Machine B: {target['b']['compatibility'].upper()} ({target['b']['compatibility_score']}/100), {target['b']['suitability']['category']}, readiness {target['b']['readiness']}", f"Assessment: {target['summary']}"]
        for side in ("a", "b"):
            for check in target[side]["checks"]:
                if check["status"] != "pass":
                    lines.append(f"{result['machines'][side]['label']}: {check['name']} — {check['status']} ({check['detected']} / {check['required']})")
    lines.append("Hardware differences:")
    for row in result["hardware"]:
        if row["difference"] not in {"same", "unknown"}:
            lines.append(f"- {row['name']}: {row['a']} vs {row['b']} ({row['difference']})")
    return "\n".join(lines)


def html_comparison_report(result: dict[str, Any]) -> str:
    a, b = result["machines"]["a"], result["machines"]["b"]
    hardware = "".join(f"<tr><th>{escape(row['name'])}</th><td>{escape(row['a'])}</td><td>{escape(row['b'])}</td><td>{escape(row['difference'])}</td></tr>" for row in result["hardware"])
    target = result.get("target")
    section = ""
    if target:
        rows = "".join(f"<tr><th>{escape(check['name'])}</th><td>{escape(check['status'])}</td><td>{escape(check['detected'])}</td><td>{escape(check['required'])}</td></tr>" for check in target["a"]["checks"])
        rows_b = "".join(f"<tr><th>{escape(check['name'])}</th><td>{escape(check['status'])}</td><td>{escape(check['detected'])}</td><td>{escape(check['required'])}</td></tr>" for check in target["b"]["checks"])
        section = f"<section><h2>{escape(target['name'])}</h2><p>Candidate assessment: {escape(target['summary'])}</p><table><tr><th></th><th>{escape(a['label'])}</th><th>{escape(b['label'])}</th></tr><tr><th>Compatibility</th><td>{escape(target['a']['compatibility'])} ({target['a']['compatibility_score']}/100)</td><td>{escape(target['b']['compatibility'])} ({target['b']['compatibility_score']}/100)</td></tr><tr><th>Suitability</th><td>{escape(target['a']['suitability']['category'])} ({target['a']['suitability']['score']}/100)</td><td>{escape(target['b']['suitability']['category'])} ({target['b']['suitability']['score']}/100)</td></tr><tr><th>Installation readiness</th><td>{escape(target['a']['readiness'])}</td><td>{escape(target['b']['readiness'])}</td></tr></table><h3>Machine A checks</h3><table>{rows}</table><h3>Machine B checks</h3><table>{rows_b}</table></section>"
    meta = "".join(f"<p>{escape(item['label'])} capture time: {escape(str(item['metadata'].get('created_at', 'unknown')))}</p>" for item in (a, b) if item["metadata"])
    return f"<!doctype html><html><head><meta charset='utf-8'><title>Machine comparison</title><style>body{{font:15px Segoe UI,Arial,sans-serif;color:#1f2937;background:#f5f7fb;max-width:1100px;margin:32px auto;padding:0 20px}}section{{background:#fff;border:1px solid #dfe5ef;border-radius:10px;padding:18px;margin:16px 0}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #e5e7eb;vertical-align:top}}th{{font-weight:600}}</style></head><body><h1>Machine comparison</h1><p>{escape(a['label'])} vs {escape(b['label'])}</p>{meta}{section}<section><h2>Hardware comparison</h2><table><tr><th>Attribute</th><th>{escape(a['label'])}</th><th>{escape(b['label'])}</th><th>Difference</th></tr>{hardware}</table></section></body></html>"
