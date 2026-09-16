from __future__ import annotations

import ctypes
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from architecture import architecture_label, host_architecture, normalize_architecture


@dataclass
class MachineInfo:
    operating_system: str
    architecture: str
    cpu_name: str
    cpu_cores: int | None
    cpu_ghz: float | None
    ram_gb: float | None
    storage_total_gb: float | None
    storage_free_gb: float | None
    uefi: bool | None = None
    secure_boot: bool | None = None
    tpm_version: float | None = None
    display_width: int | None = None
    display_height: int | None = None
    cpu_vendor: str | None = None
    gpu_name: str | None = None
    gpu_vram_mb: int | None = None
    system_disk: str | None = None
    storage_partition_style: str | None = None
    storage_filesystem: str | None = None
    virtualization: str | None = None

    def __post_init__(self) -> None:
        # Keep imported and locally detected snapshots on the same stable vocabulary.
        self.architecture = normalize_architecture(self.architecture)


@dataclass
class CheckResult:
    name: str
    status: str
    detected: str
    required: str
    detail: str = ""


def _powershell(script: str) -> str | None:
    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=12, creationflags=flags
        )
        return completed.stdout.strip() if completed.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _windows_details() -> dict[str, Any]:
    script = r"""
$ErrorActionPreference='SilentlyContinue'
$cpu=Get-CimInstance Win32_Processor | Select-Object -First 1
$cs=Get-CimInstance Win32_ComputerSystem
$os=Get-CimInstance Win32_OperatingSystem
$fw=(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control' -Name PEFirmwareType).PEFirmwareType
$sb=$null; try {$sb=Confirm-SecureBootUEFI} catch {}
$t=Get-Tpm
$gpu=Get-CimInstance Win32_VideoController | Select-Object -First 1
$bootDisk=Get-Disk | Where-Object IsBoot -eq $true | Select-Object -First 1
$systemVolume=Get-Volume -DriveLetter ($env:SystemDrive).TrimEnd(':') | Select-Object -First 1
[pscustomobject]@{
 CpuName=$cpu.Name; Cores=$cpu.NumberOfCores; MaxMHz=$cpu.MaxClockSpeed
 RamBytes=[double]$cs.TotalPhysicalMemory
 Uefi=($fw -eq 2); SecureBoot=$sb
 TpmPresent=$t.TpmPresent; TpmSpec=$t.SpecVersion
 CpuVendor=$cpu.Manufacturer
 GpuName=$gpu.Name; GpuVramBytes=[double]$gpu.AdapterRAM
 PartitionStyle=$bootDisk.PartitionStyle; FileSystem=$systemVolume.FileSystem
 Virtualization=if ($cpu.VirtualizationFirmwareEnabled -or $cpu.VMMonitorModeExtensions) {'available'} else {'unknown'}
} | ConvertTo-Json -Compress
"""
    raw = _powershell(script)
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def _windows_native_fallback() -> dict[str, Any]:
    """Read common values without WMI, which may be disabled by policy."""
    values: dict[str, Any] = {}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
            values["CpuName"] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            values["MaxMHz"] = winreg.QueryValueEx(key, "~MHz")[0]
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SecureBoot\State") as key:
                values["SecureBoot"] = bool(winreg.QueryValueEx(key, "UEFISecureBootEnabled")[0])
        except OSError:
            pass
    except (OSError, ImportError):
        pass
    try:
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            values["RamBytes"] = status.ullTotalPhys
    except (AttributeError, OSError):
        pass
    if not values.get("RamBytes"):
        try:
            installed_kb = ctypes.c_ulonglong(0)
            if ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(installed_kb)):
                values["RamBytes"] = installed_kb.value * 1024
        except (AttributeError, OSError):
            pass
    try:
        firmware_type = ctypes.c_uint(0)
        if ctypes.windll.kernel32.GetFirmwareType(ctypes.byref(firmware_type)):
            values["Uefi"] = firmware_type.value == 2
    except (AttributeError, OSError):
        pass
    return values


def _linux_cpu() -> tuple[str, float | None]:
    name = platform.processor() or "Unknown CPU"
    ghz = None
    try:
        text = Path("/proc/cpuinfo").read_text(errors="ignore")
        model = re.search(r"model name\s*:\s*(.+)", text)
        mhz = re.findall(r"cpu MHz\s*:\s*([0-9.]+)", text)
        if model:
            name = model.group(1).strip()
        if mhz:
            ghz = max(float(value) for value in mhz) / 1000
    except OSError:
        pass
    return name, ghz


def _linux_details() -> dict[str, Any]:
    details: dict[str, Any] = {}
    # Flatpak cannot reliably see the host's block devices or PCI inventory.
    # Keep CPU information, but leave host-only fields unknown rather than reading sandbox paths.
    if os.environ.get("FLATPAK_ID"):
        return details
    try:
        text = Path("/proc/cpuinfo").read_text(errors="ignore")
        vendor = re.search(r"vendor_id\s*:\s*(.+)", text)
        flags = re.search(r"(?:flags|Features)\s*:\s*(.+)", text)
        if vendor:
            details["CpuVendor"] = vendor.group(1).strip()
        if flags:
            values = set(flags.group(1).split())
            details["Virtualization"] = "available" if {"vmx", "svm"} & values else "unknown"
    except OSError:
        pass
    try:
        gpu = subprocess.run(["lspci", "-mm"], capture_output=True, text=True, timeout=4)
        if gpu.returncode == 0:
            for line in gpu.stdout.splitlines():
                if any(kind in line for kind in ('"VGA compatible controller"', '"3D controller"', '"Display controller"')):
                    parts = re.findall(r'"([^"]*)"', line)
                    if parts:
                        details["GpuName"] = parts[-1]
                        break
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        mount = subprocess.run(["findmnt", "-no", "SOURCE,FSTYPE", "/"], capture_output=True, text=True, timeout=4)
        if mount.returncode == 0:
            values = mount.stdout.strip().split()
            if values:
                details["SystemDisk"] = values[0]
            if len(values) > 1:
                details["FileSystem"] = values[1]
            if values and values[0].startswith("/"):
                parent = subprocess.run(["lsblk", "-no", "PKNAME", values[0]], capture_output=True, text=True, timeout=4)
                device = "/dev/" + (parent.stdout.strip() or values[0].split("/")[-1])
                style = subprocess.run(["lsblk", "-no", "PTTYPE", device], capture_output=True, text=True, timeout=4)
                if style.returncode == 0 and style.stdout.strip():
                    details["PartitionStyle"] = style.stdout.strip().upper()
    except (OSError, subprocess.SubprocessError):
        pass
    return details


def collect_machine_info(screen: tuple[int, int] | None = None) -> MachineInfo:
    disk = None
    if not os.environ.get("FLATPAK_ID"):
        root = Path(os.environ.get("SystemDrive", "C:") + "\\") if sys.platform == "win32" else Path("/")
        try:
            disk = shutil.disk_usage(root)
        except OSError:
            disk = None
    details: dict[str, Any] = {}
    tpm_version = None
    if sys.platform == "win32":
        details.update(_windows_native_fallback())
        details.update({key: value for key, value in _windows_details().items() if value is not None})
    else:
        details.update(_linux_details())

    if sys.platform == "win32":
        cpu_name = details.get("CpuName") or platform.processor() or "Unknown CPU"
        cpu_ghz = (float(details["MaxMHz"]) / 1000) if details.get("MaxMHz") else None
        ram_gb = (float(details["RamBytes"]) / 1024**3) if details.get("RamBytes") else None
        tpm_spec = details.get("TpmSpec") or ""
        versions = re.findall(r"\d+(?:\.\d+)?", str(tpm_spec))
        tpm_version = max((float(v) for v in versions), default=None) if details.get("TpmPresent") else None
    else:
        cpu_name, cpu_ghz = _linux_cpu()
        ram_gb = None
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            ram_gb = pages * page_size / 1024**3
        except (ValueError, OSError, AttributeError):
            pass

    return MachineInfo(
        operating_system=f"{platform.system()} {platform.release()}",
        architecture=host_architecture(),
        cpu_name=str(cpu_name).strip(),
        cpu_cores=int(details.get("Cores") or os.cpu_count() or 0) or None,
        cpu_ghz=cpu_ghz,
        ram_gb=ram_gb,
        storage_total_gb=disk.total / 1024**3 if disk else None,
        storage_free_gb=disk.free / 1024**3 if disk else None,
        uefi=details.get("Uefi") if "Uefi" in details else None,
        secure_boot=details.get("SecureBoot") if isinstance(details.get("SecureBoot"), bool) else None,
        tpm_version=tpm_version,
        display_width=screen[0] if screen else None,
        display_height=screen[1] if screen else None,
        cpu_vendor=details.get("CpuVendor"),
        gpu_name=details.get("GpuName"),
        gpu_vram_mb=round(float(details["GpuVramBytes"]) / 1024**2) if details.get("GpuVramBytes") else None,
        system_disk=details.get("SystemDisk"),
        storage_partition_style=details.get("PartitionStyle"),
        storage_filesystem=details.get("FileSystem"),
        virtualization=details.get("Virtualization"),
    )


def _numeric(name: str, actual: float | int | None, required: float | int | None, unit: str) -> CheckResult:
    if isinstance(required, bool) or not isinstance(required, (int, float)):
        return CheckResult(name, "unknown", "Not specified", "Not specified")
    if actual is None:
        return CheckResult(name, "unknown", "Could not detect", f"{required:g} {unit}")
    passed = actual >= required
    return CheckResult(name, "pass" if passed else "fail", f"{actual:.1f} {unit}", f"{required:g} {unit}")


def evaluate(machine: MachineInfo, requirements: dict[str, Any]) -> list[CheckResult]:
    results = [
        _numeric("CPU cores", machine.cpu_cores, requirements.get("cpu_cores"), "cores"),
        _numeric("CPU speed", machine.cpu_ghz, requirements.get("cpu_ghz"), "GHz"),
        _numeric("Memory", machine.ram_gb, requirements.get("ram_gb"), "GB"),
        _numeric("Free storage", machine.storage_free_gb, requirements.get("storage_gb"), "GB"),
    ]
    allowed = [normalize_architecture(a) for a in requirements.get("architecture", [])]
    allowed = [a for a in allowed if a != "unknown"]
    architecture = normalize_architecture(machine.architecture)
    if architecture == "unknown":
        arch_status = "unknown"
        detected_architecture = "Could not detect"
    else:
        arch_status = "pass" if architecture in allowed else "fail"
        detected_architecture = architecture
    results.append(CheckResult("Architecture", arch_status, detected_architecture, " or ".join(allowed) or "Not specified"))

    for key, label in (("uefi", "UEFI firmware"), ("secure_boot", "Secure Boot")):
        if key in requirements:
            actual = getattr(machine, key)
            status = "unknown" if actual is None else ("pass" if actual else "fail")
            results.append(CheckResult(label, status, "Could not verify" if actual is None else ("Available" if actual else "Not available"), "Required"))
    if "tpm_version" in requirements:
        actual = machine.tpm_version
        status = "unknown" if actual is None else ("pass" if actual >= requirements["tpm_version"] else "fail")
        results.append(CheckResult("TPM", status, "Could not verify" if actual is None else f"Version {actual:g}", f"Version {requirements['tpm_version']:g}"))
    if "display_width" in requirements:
        actual = None if machine.display_width is None else min(machine.display_width, machine.display_height or 0)
        required = min(requirements["display_width"], requirements["display_height"])
        status = "unknown" if actual is None else ("pass" if actual >= required else "fail")
        detected = "Could not detect" if actual is None else f"{machine.display_width} × {machine.display_height}"
        results.append(CheckResult("Display resolution", status, detected, f"At least {requirements['display_width']} × {requirements['display_height']}"))
    return results


def overall_status(results: list[CheckResult]) -> str:
    if any(item.status == "fail" for item in results):
        return "fail"
    if any(item.status == "unknown" for item in results):
        return "review"
    return "pass"


def compatibility_score(results: list[CheckResult]) -> int:
    """Return a simple supplementary score from the existing check results."""
    if not results:
        return 0
    weights = {"pass": 1.0, "unknown": 0.5, "fail": 0.0}
    return round(100 * sum(weights.get(item.status, 0.0) for item in results) / len(results))


def evaluate_all(machine: MachineInfo, requirements: dict[str, Any]) -> dict[str, list[CheckResult]]:
    """Evaluate every profile against one already-collected machine snapshot."""
    return {name: evaluate(machine, profile) for name, profile in requirements.items()}


def rank_compatibility(results_by_os: dict[str, list[CheckResult]], suitability_by_os: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Summarize and deterministically rank hardware compatibility results."""
    status_order = {"pass": 0, "review": 1, "fail": 2}
    ranked = [
        {
            "name": name,
            "checks": checks,
            "status": overall_status(checks),
            "score": compatibility_score(checks),
            "suitability": suitability_by_os[name] if suitability_by_os and name in suitability_by_os else None,
        }
        for name, checks in results_by_os.items()
    ]
    suitability_order = {"Excellent fit": 0, "Good fit": 1, "Meets minimum": 2, "Marginal": 3, "Not compatible": 4}
    return sorted(ranked, key=lambda item: (status_order[item["status"]], suitability_order.get((item["suitability"] or {}).get("category"), 5), -item["score"], item["name"]))


def load_requirements(path: Path | None = None) -> dict[str, Any]:
    from requirements_update import load_requirements_info
    return load_requirements_info(path).profiles


def as_report(machine: MachineInfo, requirements: dict[str, Any]) -> dict[str, Any]:
    from suitability import assess_suitability, suitability_dict
    from lifecycle import profile_metadata, lifecycle_status
    from installation_readiness import evaluate_installation_readiness
    checks = evaluate(machine, requirements)
    enriched = []
    for check in checks:
        item = asdict(check)
        item.update(explain_check(machine, requirements, check))
        enriched.append(item)
    suitability = suitability_dict(assess_suitability(machine, requirements, checks))
    metadata = profile_metadata(requirements.get("os_family", requirements.get("version", "")), requirements)
    metadata["support_status"] = lifecycle_status(requirements)
    readiness = evaluate_installation_readiness(machine, requirements, checks)
    from upgrade_planner import build_upgrade_plan
    plan = build_upgrade_plan(machine, requirements, checks, suitability, readiness, metadata)
    return {"machine": asdict(machine), "overall": overall_status(checks), "checks": enriched, "suitability": suitability, "lifecycle": metadata, "installation_readiness": readiness, "upgrade_plan": plan}


def explain_check(machine: MachineInfo, requirements: dict[str, Any], check: CheckResult, language: str = "en") -> dict[str, str]:
    """Return concise, deterministic explanation and remediation text for a check."""
    from localization import t
    name = check.name.lower()
    if check.status == "pass":
        explanation = t("explanation.pass", language, detected=check.detected, required=check.required)
        remediation = ""
    elif check.status == "unknown":
        explanation = t("explanation.unknown", language, required=check.required)
        remediation = t("remediation.unknown", language)
    else:
        explanation = t("explanation.fail", language, detected=check.detected, required=check.required)
        remediation = t("remediation.fail", language)

    if "tpm" in name:
        explanation = ("TPM 2.0 provides hardware-backed security required by this profile. "
                       + (f"Detected {check.detected}; required {check.required}." if check.status != "unknown" else "It could not be verified.") )
        remediation = "Check UEFI/BIOS for TPM, Intel PTT, or AMD fTPM and enable it if supported." if check.status != "pass" else ""
    elif "secure boot" in name:
        remediation = "Check UEFI firmware settings for Secure Boot; do not change it automatically." if check.status != "pass" else ""
    elif "uefi" in name:
        remediation = "Check whether the system is booted in UEFI mode rather than legacy/CSM mode." if check.status != "pass" else ""
    elif "virtualization" in name:
        remediation = "Check UEFI/BIOS for Intel VT-x, AMD-V, or SVM if this capability is needed." if check.status != "pass" else ""
    elif "memory" in name and check.status == "fail":
        remediation = "More physical memory is needed to meet this requirement."
    elif "storage" in name and check.status == "fail":
        remediation = "Free additional space on the system disk; no files are changed automatically."
    elif "architecture" in name and check.status == "fail":
        remediation = "The processor architecture is not supported by this profile; a software setting cannot change it."
    elif "cpu" in name and check.status == "fail":
        remediation = "The detected processor does not meet this measurable requirement; replacing hardware may be necessary."
    return {"explanation": explanation, "remediation": remediation}


def plain_text_report(machine: MachineInfo, target_os: str, requirements: dict[str, Any], language: str = "en") -> str:
    from localization import check_label, readiness_explanation, status_label, suitability_explanation, suitability_label, t
    report = as_report(machine, requirements)
    score = compatibility_score([CheckResult(**{key: item[key] for key in ("name", "status", "detected", "required", "detail")}) for item in report["checks"]])
    lifecycle = report["lifecycle"]
    lines = [f"{t('app.title', language)} - {target_os}", f"{t('label.compatibility', language)}: {status_label(report['overall'], language).upper()} (score {score}/100)", f"{t('label.suitability', language)}: {suitability_label(report['suitability']['category'], language)} — {suitability_explanation(report['suitability']['category'], report['suitability']['explanation'], language)}", f"{t('label.lifecycle', language)}: {lifecycle['release']} ({status_label(lifecycle['support_status'], language)})", f"{t('label.installation_readiness', language)}: {status_label(report['installation_readiness']['status'], language).upper()} — {readiness_explanation(report['installation_readiness']['status'], language)}", "",
             f"OS: {machine.operating_system}", f"Architecture: {architecture_label(machine.architecture)}", f"{t('machine.processor', language)}: {machine.cpu_name}",
             f"{t('machine.graphics', language)}: {machine.gpu_name or 'Unknown'}", f"RAM: {machine.ram_gb or 'Unknown'} GB",
             f"{t('check.free_storage', language)}: {machine.storage_free_gb or 'Unknown'} GB", "", f"{t('label.check', language)}:"]
    lines.append(f"{t('label.installation_readiness', language)}:")
    for item in report["installation_readiness"]["checks"]:
        lines.append(f"- {check_label(item['name'], language)}: {status_label(item['status'], language).upper()} ({item['detected']} / {item['required']})")
    from upgrade_planner import localized_plan
    plan = localized_plan(report["upgrade_plan"], language)
    lines += ["", "Upgrade plan:", plan["overall_summary"]]
    for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions", "unresolved_items", "optional_improvements"):
        for item in plan[key]:
            lines.append(f"- {item['check']}: {item['current']} / {item['target']} — {item['explanation']}")
    lines.append("")
    for item in report["checks"]:
        localized = explain_check(machine, requirements, CheckResult(**{key: item[key] for key in ("name", "status", "detected", "required", "detail")}), language)
        lines.append(f"- {check_label(item['name'], language)}: {status_label(item['status'], language).upper()} ({item['detected']} / {item['required']})")
        if item["status"] != "pass":
            lines.append(f"  {localized['explanation']}")
            if localized["remediation"]:
                lines.append(f"  {t('label.next_step', language)}: {localized['remediation']}")
    return "\n".join(lines)


def html_report(machine: MachineInfo, target_os: str, requirements: dict[str, Any], language: str = "en") -> str:
    """Create a self-contained, offline-readable HTML report."""
    from html import escape
    from localization import check_label, readiness_explanation, status_label, suitability_explanation, suitability_label, t
    report = as_report(machine, requirements)
    score = compatibility_score([CheckResult(**{key: item[key] for key in ("name", "status", "detected", "required", "detail")}) for item in report["checks"]])
    rows = []
    for item in report["checks"]:
        localized = explain_check(machine, requirements, CheckResult(**{key: item[key] for key in ("name", "status", "detected", "required", "detail")}), language)
        extra = f"<p>{escape(localized['explanation'])}</p>"
        if localized["remediation"]:
            extra += f"<p><strong>{escape(t('label.next_step', language))}:</strong> {escape(localized['remediation'])}</p>"
        rows.append(f"<tr class='{escape(item['status'])}'><th>{escape(check_label(item['name'], language))}</th><td>{escape(status_label(item['status'], language))}</td><td>{escape(item['detected'])}</td><td>{escape(item['required'])}</td><td>{extra}</td></tr>")
    machine_rows = "".join(f"<tr><th>{escape(label)}</th><td>{escape(str(value or 'Unknown'))}</td></tr>" for label, value in (("Operating system", machine.operating_system), ("Architecture", architecture_label(machine.architecture)), ("CPU", machine.cpu_name), ("GPU", machine.gpu_name), ("RAM (GB)", machine.ram_gb), ("Free storage (GB)", machine.storage_free_gb), ("System disk", machine.system_disk), ("Partition style", machine.storage_partition_style), ("Filesystem", machine.storage_filesystem), ("Virtualization", machine.virtualization)))
    lifecycle = report["lifecycle"]
    readiness_rows = "".join(f"<tr class='{escape(item['status'])}'><th>{escape(check_label(item['name'], language))}</th><td>{escape(status_label(item['status'], language))}</td><td>{escape(item['detected'])}</td><td>{escape(item['required'])}</td></tr>" for item in report["installation_readiness"]["checks"])
    lifecycle_rows = "".join(f"<tr><th>{escape(label)}</th><td>{escape(str(value or 'Unknown'))}</td></tr>" for label, value in (("Release", lifecycle["release"]), (t("label.lifecycle", language), lifecycle["lifecycle_type"]), ("Support status", status_label(lifecycle["support_status"], language)), ("Release date", lifecycle["release_date"]), ("EOL date", lifecycle["eol_date"])))
    from upgrade_planner import localized_plan
    localized_upgrade = localized_plan(report["upgrade_plan"], language)
    plan_rows = "".join(f"<tr><th>{escape(item['check'])}</th><td>{escape(item['current'])}</td><td>{escape(item['target'])}</td><td>{escape(item['explanation'])}</td></tr>" for key in ("required_hardware_changes", "required_configuration_changes", "storage_actions", "unresolved_items", "optional_improvements") for item in localized_upgrade[key])
    plan_section = f"<section><h2>{escape(t('action.upgrade_plan', language))}</h2><p>{escape(localized_upgrade['overall_summary'])}</p><table><tr><th>{escape(t('label.check', language))}</th><th>{escape(t('label.detected', language))}</th><th>{escape(t('label.required', language))}</th><th>{escape(t('label.explanation', language))}</th></tr>{plan_rows}</table></section>"
    return f"""<!doctype html><html lang='{escape(language)}'><head><meta charset='utf-8'><title>{escape(t('report.title', language))}</title><style>body{{font:15px Segoe UI,Arial,sans-serif;color:#1f2937;background:#f5f7fb;max-width:1100px;margin:32px auto;padding:0 20px}}section{{background:#fff;border:1px solid #dfe5ef;border-radius:10px;padding:18px;margin:16px 0}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #e5e7eb;vertical-align:top}}.pass td:nth-child(2){{color:#15803d}}.fail td:nth-child(2),.not_ready td:nth-child(2){{color:#b91c1c}}.unknown td:nth-child(2){{color:#a16207}}h1{{margin-bottom:4px}}</style></head><body><h1>{escape(t('report.title', language))}</h1><p><strong>{escape(target_os)}</strong> — {escape(t('label.compatibility', language).lower())} <strong>{escape(status_label(report['overall'], language))}</strong> — score <strong>{score}/100</strong></p><section><h2>{escape(t('report.release', language))}</h2><table>{lifecycle_rows}</table></section><section><h2>{escape(t('label.suitability', language))}</h2><p><strong>{escape(suitability_label(report['suitability']['category'], language))}</strong> — {escape(suitability_explanation(report['suitability']['category'], report['suitability']['explanation'], language))}</p></section><section><h2>{escape(t('report.readiness', language))}</h2><p><strong>{escape(status_label(report['installation_readiness']['status'], language))}</strong> — {escape(readiness_explanation(report['installation_readiness']['status'], language))}</p><table><tr><th>{escape(t('label.check', language))}</th><th>{escape(t('label.result', language))}</th><th>{escape(t('label.detected', language))}</th><th>{escape(t('label.required', language))}</th></tr>{readiness_rows}</table></section>{plan_section}<section><h2>{escape(t('report.machine', language))}</h2><table>{machine_rows}</table></section><section><h2>{escape(t('report.checks', language))}</h2><table><tr><th>{escape(t('label.check', language))}</th><th>{escape(t('label.result', language))}</th><th>{escape(t('label.detected', language))}</th><th>{escape(t('label.required', language))}</th><th>{escape(t('label.explanation', language))}</th></tr>{''.join(rows)}</table></section></body></html>"""
