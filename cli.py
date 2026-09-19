from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from checker import collect_machine_info, evaluate_all, explain_check, rank_compatibility
from requirements_update import load_requirements_info
from version import APP_VERSION
from suitability import assess_suitability, suitability_dict
from lifecycle import profile_metadata, resolve_profile, lifecycle_status
from installation_readiness import evaluate_installation_readiness
from machine_profile import export_profile, import_profile
from upgrade_planner import build_upgrade_plan, localized_plan
from machine_comparison import compare_machines, plain_text_comparison
from localization import recommendation_match_label, resolve_language, status_label, suitability_explanation, suitability_label, t
from recommendation import recommend, primary_recommendations, PREFERENCES, PREFERENCE_LABELS


def _windows_console_process_count() -> int | None:
    """Return the number of processes attached to this Windows console."""
    if sys.platform != "win32":
        return None
    try:
        import ctypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_processes = kernel32.GetConsoleProcessList
        get_processes.argtypes = [ctypes.POINTER(ctypes.c_uint), ctypes.c_uint]
        get_processes.restype = ctypes.c_uint
        process_ids = (ctypes.c_uint * 64)()
        count = get_processes(process_ids, len(process_ids))
        return int(count) if count else None
    except (AttributeError, ImportError, OSError):
        return None


def _should_pause_on_exit(argv=None, platform=None, console_process_count=None) -> bool:
    """Pause only for a bare Windows CLI launched in its own console."""
    effective_platform = sys.platform if platform is None else platform
    arguments = list(sys.argv[1:] if argv is None else argv)
    if effective_platform != "win32" or arguments:
        return False
    process_count = _windows_console_process_count() if console_process_count is None else console_process_count
    return process_count == 1


def _pause_for_standalone_console() -> None:
    print("Press Enter to close...", flush=True)
    try:
        input()
    except EOFError:
        pass


def _key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _find_target(value: str, requirements: dict) -> str | None:
    resolved = resolve_profile(value, requirements)
    if resolved:
        return resolved
    wanted = _key(value)
    for name in requirements:
        if _key(name) == wanted:
            return name
    return next((name for name in requirements if _key(name).startswith(wanted)), None)


def _payload(machine, requirements, names, verbose: bool, data_version: int, profile_info=None, upgrade_plan: bool = False) -> dict:
    results = evaluate_all(machine, requirements)
    suitability = {name: suitability_dict(assess_suitability(machine, requirements[name], results[name])) for name in names}
    ranked = rank_compatibility({name: results[name] for name in names}, suitability)
    output = []
    for item in ranked:
        metadata = profile_metadata(item["name"], requirements[item["name"]])
        metadata["support_status"] = lifecycle_status(requirements[item["name"]])
        readiness = evaluate_installation_readiness(machine, requirements[item["name"]], results[item["name"]])
        entry = {"name": item["name"], "status": item["status"], "score": item["score"], "suitability": item["suitability"], "installation_readiness": readiness, **metadata}
        if upgrade_plan:
            entry["upgrade_plan"] = build_upgrade_plan(machine, requirements[item["name"]], results[item["name"]], item["suitability"], readiness, metadata)
        if verbose:
            entry["checks"] = [{**asdict(check), **explain_check(machine, requirements[item["name"]], check)} for check in results[item["name"]]]
        output.append(entry)
    payload = {"requirements_database_version": data_version, "machine": asdict(machine), "results": output}
    if profile_info:
        payload["machine_source"] = "Imported profile"
        payload["profile_metadata"] = profile_info
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="os-readiness-checker", description="Check this computer against OS requirements.")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--list", action="store_true", help="list available operating systems")
    parser.add_argument("--all", action="store_true", help="check every operating system")
    parser.add_argument("--check", metavar="OS", help="check one operating system")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--verbose", action="store_true", help="include detected and required check details")
    parser.add_argument("--upgrade-plan", action="store_true", help="include a read-only upgrade plan for the selected OS")
    parser.add_argument("--output", type=Path, help="write output to a file")
    parser.add_argument("--profile", type=Path, help="analyze an exported .osrprofile instead of scanning this computer")
    parser.add_argument("--compare", nargs=2, metavar=("MACHINE_A", "MACHINE_B"), help="compare two profiles, or use 'local' for this computer")
    parser.add_argument("--export-profile", type=Path, help="scan this computer once and save a machine profile")
    parser.add_argument("--lang", choices=("en", "it", "es", "de", "fr"), default="en", help="language for human-readable output")
    parser.add_argument("--recommend", action="store_true", help="rank operating systems for selected priorities")
    parser.add_argument("--prefer", action="append", default=[], metavar="KEY=0|1|2", help="recommendation priority (repeatable)")
    raw_args = list(sys.argv[1:] if argv is None else argv)
    args = parser.parse_args(raw_args)
    if not raw_args:
        parser.print_help()
        return 0
    try:
        info = load_requirements_info()
        requirements = info.profiles
        language = resolve_language(args.lang)
        if args.recommend:
            preferences = {}
            for value in args.prefer:
                key, _, weight = value.partition("=")
                if key in PREFERENCES:
                    try:
                        preferences[key] = max(0, min(2, int(weight)))
                    except ValueError:
                        pass
            machine = import_profile(args.profile)[0] if args.profile else collect_machine_info()
            all_checks = evaluate_all(machine, requirements)
            suits = {name: suitability_dict(assess_suitability(machine, requirements[name], all_checks[name])) for name in requirements}
            readiness = {name: evaluate_installation_readiness(machine, requirements[name], all_checks[name]) for name in requirements}
            recommendations = recommend(requirements, all_checks, suits, readiness, preferences)
            payload = {"machine": asdict(machine), "preferences": preferences, "recommendations": recommendations}
            if args.json:
                text = json.dumps(payload, indent=2)
            else:
                lines = ["Best matches for your selected priorities:"]
                for item in primary_recommendations(recommendations)[:5]:
                    lines.append(f"{item['name']} — {recommendation_match_label(item['preference_match_category'], language)} ({item['preference_score']}/100), {item['compatibility_status'].upper()}")
                if not primary_recommendations(recommendations):
                    lines.append("No fully compatible recommendation is currently available.")
                text = "\n".join(lines)
            if args.output:
                args.output.write_text(text + "\n", encoding="utf-8")
            else:
                print(text)
            return 0
        if args.compare:
            machines = []
            metadata = []
            for source in args.compare:
                if source.lower() == "local":
                    machines.append(collect_machine_info())
                    metadata.append({})
                else:
                    machine, meta = import_profile(Path(source))
                    machines.append(machine)
                    metadata.append(meta)
            target = _find_target(args.check, requirements) if args.check else None
            if args.check and not target:
                print(f"Unknown operating system: {args.check}", file=sys.stderr)
                return 2
            comparison = compare_machines(machines[0], machines[1], requirements, target, metadata=tuple(metadata))
            payload = {"comparison": comparison, "requirements_database_version": info.data_version}
            text = json.dumps(payload, indent=2) if args.json else plain_text_comparison(comparison)
            if args.output:
                args.output.write_text(text + "\n", encoding="utf-8")
            else:
                print(text)
            return 1 if comparison.get("target") and comparison["target"]["candidate"] in {"A", "B"} and comparison["target"]["a"]["compatibility"] == "fail" and comparison["target"]["b"]["compatibility"] == "fail" else 0
        if args.list:
            value = json.dumps(list(requirements)) if args.json else "\n".join(requirements)
            if args.output:
                args.output.write_text(value + ("\n" if not value.endswith("\n") else ""), encoding="utf-8")
            else:
                print(value)
            return 0
        if not args.export_profile and bool(args.all) == bool(args.check):
            parser.error("choose exactly one of --all or --check (or use --list)")
        names = list(requirements) if args.all else ([_find_target(args.check, requirements)] if args.check else [])
        if args.export_profile and not names:
            machine = collect_machine_info()
            export_profile(machine, args.export_profile, data_version=info.data_version)
            return 0
        if not names or not names[0]:
            print(f"Unknown operating system: {args.check}", file=sys.stderr)
            return 2
        profile_metadata = None
        if args.profile:
            if args.export_profile:
                parser.error("--profile and --export-profile cannot be used together")
            machine, profile_metadata = import_profile(args.profile)
        else:
            machine = collect_machine_info()
            if args.export_profile:
                export_profile(machine, args.export_profile, data_version=info.data_version)
        payload = _payload(machine, requirements, names, args.verbose, info.data_version, profile_metadata, args.upgrade_plan)
        if args.json:
            text = json.dumps(payload, indent=2)
        else:
            lines = []
            for item in payload["results"]:
                lines.append(f"{item['name']:<24} {status_label(item['status'], language).upper():<12} {suitability_label(item['suitability']['category'], language)}")
                lines.append(f"  {t('label.installation_readiness', language)}: {status_label(item['installation_readiness']['status'], language)}")
                if args.verbose:
                    lines.append(f"  {t('label.suitability', language)}: {suitability_explanation(item['suitability']['category'], item['suitability']['explanation'], language)}")
                    for check in item["checks"]:
                        lines.append(f"  {check['name']}: {check['status']} ({check['detected']} / {check['required']})")
                if args.upgrade_plan:
                    display_plan = localized_plan(item["upgrade_plan"], language)
                    lines.append(f"  {t('action.upgrade_plan', language)}: {display_plan['overall_summary']}")
                    for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions", "unresolved_items", "optional_improvements"):
                        for plan_item in display_plan[key]:
                            lines.append(f"    - {plan_item['check']}: {plan_item['current']} / {plan_item['target']} — {plan_item['explanation']}")
            text = "\n".join(lines)
            if profile_metadata:
                text = f"Machine source: Imported profile (captured {profile_metadata.get('created_at', 'unknown')})\n" + text
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        return 1 if any(item["status"] == "fail" for item in payload["results"]) else 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    exit_code = main()
    if exit_code == 0 and _should_pause_on_exit():
        _pause_for_standalone_console()
    raise SystemExit(exit_code)
