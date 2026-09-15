"""Read-only assessment of whether the current machine configuration is install-ready."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from checker import MachineInfo


@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    status: str  # pass, review, not_ready, unknown
    detected: str
    required: str
    explanation: str
    remediation: str = ""


def _result(name: str, actual: Any, required: str, ok: bool | None, explanation: str, remediation: str = "") -> ReadinessCheck:
    if ok is None:
        return ReadinessCheck(name, "unknown", "Unknown", required, explanation, remediation)
    return ReadinessCheck(name, "pass" if ok else "not_ready", str(actual), required, explanation, remediation if not ok else "")


def evaluate_installation_readiness(machine: MachineInfo, requirements: dict[str, Any], compatibility_results=None) -> dict[str, Any]:
    """Evaluate current configuration without scanning hardware or changing compatibility."""
    checks: list[ReadinessCheck] = []
    allowed = [item.upper() for item in requirements.get("architecture", [])]
    checks.append(_result("Architecture", machine.architecture, " or ".join(allowed), machine.architecture.upper() in allowed,
                          "The installer must support the detected processor architecture.",
                          "This processor architecture cannot be changed by a software setting."))
    required = requirements.get("storage_gb")
    if not isinstance(required, (int, float)) or isinstance(required, bool) or required <= 0:
        required = None
    if required is None:
        pass
    elif machine.storage_free_gb is None:
        checks.append(_result("Free storage", "Unknown", f"At least {requirements.get('storage_gb', 0):g} GB", None,
                              "Available installation space could not be verified.", "Check free space on the system disk manually."))
    else:
        checks.append(_result("Free storage", f"{machine.storage_free_gb:.1f} GB available", f"At least {required:g} GB",
                              machine.storage_free_gb >= required, "The installer needs enough free space for this profile.",
                              f"Free at least {max(0, required - machine.storage_free_gb):.1f} GB on the system disk."))

    install = requirements.get("installation", {})
    if install.get("uefi") == "required":
        checks.append(_result("UEFI", "Enabled" if machine.uefi else "Disabled", "Required", machine.uefi,
                              "This installation profile requires UEFI boot mode.", "Boot in UEFI mode instead of Legacy/CSM if supported." if machine.uefi is not True else ""))
    if install.get("secure_boot") in {"required", "optional", "disabled"}:
        mode = install["secure_boot"]
        if machine.secure_boot is None:
            checks.append(_result("Secure Boot", "Could not verify", mode.title(), None, "Secure Boot state could not be verified.", "Check UEFI firmware settings manually."))
        elif mode == "required":
            checks.append(_result("Secure Boot", "Enabled" if machine.secure_boot else "Disabled", "Required", machine.secure_boot,
                                  "Secure Boot is required by this installation profile.", "Enable Secure Boot in UEFI firmware if supported."))
        elif mode == "disabled":
            checks.append(_result("Secure Boot", "Disabled" if not machine.secure_boot else "Enabled", "Disabled", not machine.secure_boot,
                                  "This installer documents Secure Boot as disabled for the selected profile.", "Disable Secure Boot in UEFI firmware for installation."))
    if "partition_style" in install:
        expected = str(install["partition_style"]).upper()
        actual = machine.storage_partition_style.upper() if machine.storage_partition_style else None
        checks.append(_result("Partition style", actual or "Unknown", expected, actual == expected if actual else None,
                              "The installation profile specifies a partition-table format.", "Use the installer’s supported partition layout; no disk changes are made automatically."))
    if "tpm_version" in install:
        required = float(install["tpm_version"])
        actual = machine.tpm_version
        checks.append(_result("TPM", f"Version {actual:g}" if actual is not None else "Unknown", f"Version {required:g}",
                              actual >= required if actual is not None else None, "TPM is required for this installation profile.",
                              "Check firmware settings for TPM, Intel PTT, or AMD fTPM."))

    if any(check.status == "not_ready" for check in checks):
        status = "not_ready"
    elif any(check.status == "unknown" for check in checks):
        status = "unknown"
    elif any(check.status == "review" for check in checks):
        status = "review"
    else:
        status = "ready"
    return {"status": status, "checks": [asdict(check) for check in checks],
            "explanation": {"ready": "The current configuration is ready for the checked installation conditions.",
                            "review": "Some installation conditions need review.",
                            "unknown": "Some installation conditions could not be verified.",
                            "not_ready": "One or more mandatory installation conditions are not met."}[status]}
