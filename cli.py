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


def _payload(machine, requirements, names, verbose: bool, data_version: int, profile_metadata=None) -> dict:
    results = evaluate_all(machine, requirements)
    suitability = {name: suitability_dict(assess_suitability(machine, requirements[name], results[name])) for name in names}
    ranked = rank_compatibility({name: results[name] for name in names}, suitability)
    output = []
    for item in ranked:
        metadata = profile_metadata(item["name"], requirements[item["name"]])
        metadata["support_status"] = lifecycle_status(requirements[item["name"]])
        readiness = evaluate_installation_readiness(machine, requirements[item["name"]], results[item["name"]])
        entry = {"name": item["name"], "status": item["status"], "score": item["score"], "suitability": item["suitability"], "installation_readiness": readiness, **metadata}
        if verbose:
            entry["checks"] = [{**asdict(check), **explain_check(machine, requirements[item["name"]], check)} for check in results[item["name"]]]
        output.append(entry)
    payload = {"requirements_database_version": data_version, "machine": asdict(machine), "results": output}
    if profile_metadata:
        payload["machine_source"] = "Imported profile"
        payload["profile_metadata"] = profile_metadata
    return payload


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="os-readiness-checker", description="Check this computer against OS requirements.")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--list", action="store_true", help="list available operating systems")
    parser.add_argument("--all", action="store_true", help="check every operating system")
    parser.add_argument("--check", metavar="OS", help="check one operating system")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--verbose", action="store_true", help="include detected and required check details")
    parser.add_argument("--output", type=Path, help="write output to a file")
    parser.add_argument("--profile", type=Path, help="analyze an exported .osrprofile instead of scanning this computer")
    parser.add_argument("--export-profile", type=Path, help="scan this computer once and save a machine profile")
    args = parser.parse_args(argv)
    try:
        info = load_requirements_info()
        requirements = info.profiles
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
        payload = _payload(machine, requirements, names, args.verbose, info.data_version, profile_metadata)
        if args.json:
            text = json.dumps(payload, indent=2)
        else:
            lines = []
            for item in payload["results"]:
                lines.append(f"{item['name']:<24} {item['status'].upper():<7} {item['suitability']['category']}")
                lines.append(f"  Installation readiness: {item['installation_readiness']['status'].replace('_', ' ').title()}")
                if args.verbose:
                    lines.append(f"  Suitability: {item['suitability']['explanation']}")
                    for check in item["checks"]:
                        lines.append(f"  {check['name']}: {check['status']} ({check['detected']} / {check['required']})")
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
    raise SystemExit(main())
