from __future__ import annotations

import math
from dataclasses import dataclass

GASES = ("CO2", "N2", "O2", "CH4", "H2", "He")
SCATTER_WEIGHTS = {
    "CO2": 0.45,
    "N2": 1.0,
    "O2": 1.05,
    "CH4": 0.35,
    "H2": 1.7,
    "He": 0.25,
}
ABSORPTION_WEIGHTS = {
    "CO2": 0.25,
    "N2": 0.02,
    "O2": 0.12,
    "CH4": 1.5,
    "H2": 0.0,
    "He": 0.0,
}


@dataclass(frozen=True)
class AtmosphericResult:
    transmitted: float
    scattered: float
    absorbed: float
    column_factor: float
    normalized_composition: dict[str, float]
    warnings: tuple[str, ...]
    partial: bool


def calculate_atmosphere(
    pressure_pa: float | None,
    density_kg_m3: float | None,
    composition: dict[str, float | None],
) -> AtmosphericResult:
    warnings: list[str] = []
    partial = False
    ratios: list[float] = []

    if pressure_pa is None:
        warnings.append("Surface pressure is missing from the scientific catalog.")
        partial = True
    else:
        ratios.append(max(0.0, pressure_pa) / 101_325.0)
    if density_kg_m3 is None:
        warnings.append("Atmospheric density is missing from the scientific catalog.")
        partial = True
    else:
        ratios.append(max(0.0, density_kg_m3) / 1.225)

    known = {gas: max(0.0, composition.get(gas) or 0.0) for gas in GASES}
    composition_total = sum(known.values())
    if composition_total <= 0:
        normalized = {gas: 0.0 for gas in GASES}
        warnings.append("Atmospheric composition is unavailable; neutral coefficients were used.")
        partial = True
    else:
        normalized = {gas: value / composition_total for gas, value in known.items()}
        if composition_total > 1.05:
            warnings.append("Gas fractions exceeded one and were normalized for the optical model.")

    if ratios:
        mean_ratio = sum(ratios) / len(ratios)
        column_factor = math.log1p(mean_ratio) / math.log(2)
    else:
        # A small, explicit composition-only fallback; it is never presented as measured data.
        column_factor = 0.15
        warnings.append("A minimal composition-only optical column fallback was applied.")

    scatter_mix = sum(normalized[gas] * SCATTER_WEIGHTS[gas] for gas in GASES)
    absorption_mix = sum(
        normalized[gas] * ABSORPTION_WEIGHTS[gas] for gas in GASES
    )
    tau_scatter = 0.16 * column_factor * (0.35 + 0.65 * scatter_mix)
    tau_absorb = 0.07 * column_factor * (0.25 + 0.75 * absorption_mix)
    total_tau = min(12.0, tau_scatter + tau_absorb)
    transmitted = math.exp(-total_tau)

    removed = 1.0 - transmitted
    scatter_share = tau_scatter / (tau_scatter + tau_absorb) if total_tau > 0 else 0
    escape_factor = 1.0 / (1.0 + 0.05 * column_factor)
    scattered = removed * scatter_share * escape_factor
    absorbed = 1.0 - transmitted - scattered

    return AtmosphericResult(
        transmitted=transmitted,
        scattered=scattered,
        absorbed=absorbed,
        column_factor=column_factor,
        normalized_composition=normalized,
        warnings=tuple(warnings),
        partial=partial,
    )
