from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# Application-defined headroom guidance, intentionally separate from official requirements.
HEADROOM_TARGETS = {"cpu_cores": 1.5, "cpu_ghz": 1.5, "ram_gb": 1.5, "storage_gb": 1.5}


@dataclass(frozen=True)
class SuitabilityResult:
    category: str
    score: int
    explanation: str


def assess_suitability(machine, requirements: dict[str, Any], checks: list[Any]) -> SuitabilityResult:
    statuses = {item.name: item.status for item in checks}
    if any(item.status == "fail" for item in checks):
        return SuitabilityResult("Not compatible", 0, "Official compatibility checks include a failure, so suitability cannot be positive.")
    values = {
        "cpu_cores": machine.cpu_cores,
        "cpu_ghz": machine.cpu_ghz,
        "ram_gb": machine.ram_gb,
        "storage_gb": machine.storage_free_gb,
    }
    ratios = []
    unknown = []
    for key, target in HEADROOM_TARGETS.items():
        required = requirements.get(key)
        actual = values[key]
        if not required or required <= 0:
            continue
        if actual is None or statuses.get({"cpu_cores": "CPU cores", "cpu_ghz": "CPU speed", "ram_gb": "Memory", "storage_gb": "Free storage"}[key]) == "unknown":
            unknown.append(key)
        else:
            ratios.append(float(actual) / float(required))
    if unknown or any(item.status == "unknown" for item in checks):
        return SuitabilityResult("Marginal", 50, "Suitability could not be fully assessed because some detected hardware values are unknown.")
    minimum = min(ratios, default=1.0)
    score = max(50, min(100, round(50 + (minimum - 1) * 50)))
    if minimum >= 2.0:
        category = "Excellent fit"
        explanation = "CPU, memory, and storage provide substantial headroom above the published minimums."
    elif minimum >= 1.5:
        category = "Good fit"
        explanation = "This system exceeds the published minimums with comfortable headroom."
    elif minimum >= 1.15:
        category = "Meets minimum"
        explanation = "The system clears the published minimums, with limited additional headroom."
    else:
        category = "Marginal"
        limiting = min((key for key in HEADROOM_TARGETS if key in requirements), key=lambda key: values[key] / requirements[key], default="hardware")
        labels = {"cpu_cores": "CPU cores", "cpu_ghz": "CPU speed", "ram_gb": "memory", "storage_gb": "free storage"}
        explanation = f"The system meets the minimums, but has little {labels.get(limiting, limiting)} headroom."
    return SuitabilityResult(category, score, explanation)


def suitability_dict(result: SuitabilityResult) -> dict[str, Any]:
    return asdict(result)
