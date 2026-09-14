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
    root = Path(os.environ.get("SystemDrive", "C:") + "\\") if sys.platform == "win32" else Path("/")
    disk = shutil.disk_usage(root)
    details: dict[str, Any] = {}
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
        architecture=platform.machine().upper(),
        cpu_name=str(cpu_name).strip(),
        cpu_cores=int(details.get("Cores") or os.cpu_count() or 0) or None,
        cpu_ghz=cpu_ghz,
        ram_gb=ram_gb,
        storage_total_gb=disk.total / 1024**3,
        storage_free_gb=disk.free / 1024**3,
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


def _numeric(name: str, actual: float | int | None, required: float | int, unit: str) -> CheckResult:
    if actual is None:
        return CheckResult(name, "unknown", "Could not detect", f"{required:g} {unit}")
    passed = actual >= required
    return CheckResult(name, "pass" if passed else "fail", f"{actual:.1f} {unit}", f"{required:g} {unit}")


def evaluate(machine: MachineInfo, requirements: dict[str, Any]) -> list[CheckResult]:
    results = [
        _numeric("CPU cores", machine.cpu_cores, requirements["cpu_cores"], "cores"),
        _numeric("CPU speed", machine.cpu_ghz, requirements["cpu_ghz"], "GHz"),
        _numeric("Memory", machine.ram_gb, requirements["ram_gb"], "GB"),
        _numeric("Free storage", machine.storage_free_gb, requirements["storage_gb"], "GB"),
    ]
    allowed = [a.upper() for a in requirements.get("architecture", [])]
    arch_pass = machine.architecture in allowed
    results.append(CheckResult("Architecture", "pass" if arch_pass else "fail", machine.architecture, " or ".join(allowed)))

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


def rank_compatibility(results_by_os: dict[str, list[CheckResult]]) -> list[dict[str, Any]]:
    """Summarize and deterministically rank hardware compatibility results."""
    status_order = {"pass": 0, "review": 1, "fail": 2}
    ranked = [
        {
            "name": name,
            "checks": checks,
            "status": overall_status(checks),
            "score": compatibility_score(checks),
        }
        for name, checks in results_by_os.items()
    ]
    return sorted(ranked, key=lambda item: (-item["score"], status_order[item["status"]], item["name"]))


def load_requirements(path: Path | None = None) -> dict[str, Any]:
    path = path or Path(__file__).with_name("requirements.json")
    return json.loads(path.read_text(encoding="utf-8"))


def as_report(machine: MachineInfo, requirements: dict[str, Any]) -> dict[str, Any]:
    checks = evaluate(machine, requirements)
    return {"machine": asdict(machine), "overall": overall_status(checks), "checks": [asdict(c) for c in checks]}
