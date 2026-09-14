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


def _key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum())


def _find_target(value: str, requirements: dict) -> str | None:
    wanted = _key(value)
    for name in requirements:
        if _key(name) == wanted:
            return name
    return next((name for name in requirements if _key(name).startswith(wanted)), None)


def _payload(machine, requirements, names, verbose: bool, data_version: int) -> dict:
    results = evaluate_all(machine, requirements)
    suitability = {name: suitability_dict(assess_suitability(machine, requirements[name], results[name])) for name in names}
    ranked = rank_compatibility({name: results[name] for name in names}, suitability)
    output = []
    for item in ranked:
        entry = {"name": item["name"], "status": item["status"], "score": item["score"], "suitability": item["suitability"]}
        if verbose:
            entry["checks"] = [{**asdict(check), **explain_check(machine, requirements[item["name"]], check)} for check in results[item["name"]]]
        output.append(entry)
    return {"requirements_database_version": data_version, "machine": asdict(machine), "results": output}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="os-readiness-checker", description="Check this computer against OS requirements.")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    parser.add_argument("--list", action="store_true", help="list available operating systems")
    parser.add_argument("--all", action="store_true", help="check every operating system")
    parser.add_argument("--check", metavar="OS", help="check one operating system")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--verbose", action="store_true", help="include detected and required check details")
    parser.add_argument("--output", type=Path, help="write output to a file")
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
        if bool(args.all) == bool(args.check):
            parser.error("choose exactly one of --all or --check (or use --list)")
        names = list(requirements) if args.all else [_find_target(args.check, requirements)]
        if not names[0]:
            print(f"Unknown operating system: {args.check}", file=sys.stderr)
            return 2
        machine = collect_machine_info()
        payload = _payload(machine, requirements, names, args.verbose, info.data_version)
        if args.json:
            text = json.dumps(payload, indent=2)
        else:
            lines = []
            for item in payload["results"]:
                lines.append(f"{item['name']:<24} {item['status'].upper():<7} {item['suitability']['category']}")
                if args.verbose:
                    lines.append(f"  Suitability: {item['suitability']['explanation']}")
                    for check in item["checks"]:
                        lines.append(f"  {check['name']}: {check['status']} ({check['detected']} / {check['required']})")
            text = "\n".join(lines)
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
