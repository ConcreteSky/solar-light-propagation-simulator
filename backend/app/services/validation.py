from __future__ import annotations

import math


def clamp01(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Calculated output must be finite.")
    return min(1.0, max(0.0, value))


def conserve_fractions(
    transmitted: float, scattered: float, absorbed: float
) -> tuple[float, float, float]:
    values = [clamp01(transmitted), clamp01(scattered), clamp01(absorbed)]
    total = sum(values)
    if total <= 0:
        raise ValueError("At least one energy fraction must be positive.")
    normalized = [value / total for value in values]
    # Assign the rounding remainder to absorption so the serialized sum is exactly 1.
    first = round(normalized[0], 6)
    second = round(normalized[1], 6)
    third = round(1.0 - first - second, 6)
    return first, second, third


def fractions_are_valid(values: tuple[float, float, float]) -> bool:
    return all(math.isfinite(value) and 0 <= value <= 1 for value in values) and math.isclose(
        sum(values), 1.0, rel_tol=0, abs_tol=1e-6
    )
