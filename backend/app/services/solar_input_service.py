from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ..schemas.celestial_body import CelestialBody

ASTRONOMICAL_UNIT_KM = 149_597_870.7
REFERENCE_IRRADIANCE_W_M2 = 1366.1
SPECTRUM_PATH = Path(__file__).resolve().parents[3] / "data" / "solarSpectrum.csv"


@dataclass(frozen=True)
class SpectrumSummary:
    minimum_wavelength_nm: float
    maximum_wavelength_nm: float
    integrated_w_m2: float
    visible_integrated_w_m2: float
    visible_fraction: float


@dataclass(frozen=True)
class SolarInput:
    distance_from_sun_km: float
    irradiance_w_m2: float
    derived_irradiance_w_m2: float
    irradiance_source: str
    spectrum: SpectrumSummary
    warnings: tuple[str, ...]


def _trapezoid(points: list[tuple[float, float]]) -> float:
    return sum(
        (x1 - x0) * (y0 + y1) / 2
        for (x0, y0), (x1, y1) in zip(points, points[1:])
    )


@lru_cache(maxsize=1)
def load_spectrum_summary() -> SpectrumSummary:
    with SPECTRUM_PATH.open(encoding="utf-8", newline="") as spectrum_file:
        rows = [
            (float(row["wavelength_nm"]), float(row["irradiance_w_m2_nm"]))
            for row in csv.DictReader(spectrum_file)
        ]

    if len(rows) < 2 or any(not math.isfinite(value) for row in rows for value in row):
        raise ValueError("The local ASTM E-490 spectrum is empty or invalid.")

    visible_rows = [row for row in rows if 380 <= row[0] <= 780]
    integrated = _trapezoid(rows)
    visible_integrated = _trapezoid(visible_rows)
    return SpectrumSummary(
        minimum_wavelength_nm=rows[0][0],
        maximum_wavelength_nm=rows[-1][0],
        integrated_w_m2=integrated,
        visible_integrated_w_m2=visible_integrated,
        visible_fraction=visible_integrated / integrated,
    )


def heliocentric_distance_km(
    body: CelestialBody, body_index: dict[str, CelestialBody]
) -> float:
    if body.orbit.reference == "sun" and body.orbit.semimajor_axis_km:
        return body.orbit.semimajor_axis_km
    parent = body_index.get(body.parent)
    if parent and parent.orbit.semimajor_axis_km:
        return parent.orbit.semimajor_axis_km
    raise ValueError(f"No heliocentric distance is available for {body.id}.")


def derive_irradiance(distance_from_sun_km: float) -> float:
    if not math.isfinite(distance_from_sun_km) or distance_from_sun_km <= 0:
        raise ValueError("Distance from the Sun must be finite and positive.")
    return REFERENCE_IRRADIANCE_W_M2 * (
        ASTRONOMICAL_UNIT_KM / distance_from_sun_km
    ) ** 2


def resolve_solar_input(
    body: CelestialBody,
    body_index: dict[str, CelestialBody],
    distance_override_km: float | None = None,
) -> SolarInput:
    distance = (
        distance_override_km
        if distance_override_km is not None
        else heliocentric_distance_km(body, body_index)
    )
    derived = derive_irradiance(distance)
    stored = body.light_reference.solar_irradiance_w_m2
    warnings: list[str] = []

    if distance_override_km is not None:
        irradiance = derived
        source = "inverse_square"
    elif stored is not None and math.isfinite(stored) and stored >= 0:
        irradiance = stored
        source = "stored_reference"
        if stored > 0 and abs(stored - derived) / stored > 0.1:
            warnings.append(
                "Stored irradiance differs from the inverse-square check by more than 10%."
            )
    else:
        irradiance = derived
        source = "inverse_square"
        warnings.append(
            "Stored irradiance is unavailable; inverse-square irradiance was used."
        )

    return SolarInput(
        distance_from_sun_km=distance,
        irradiance_w_m2=irradiance,
        derived_irradiance_w_m2=derived,
        irradiance_source=source,
        spectrum=load_spectrum_summary(),
        warnings=tuple(warnings),
    )
