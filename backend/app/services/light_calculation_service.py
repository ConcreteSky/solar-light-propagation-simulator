from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from ..schemas.celestial_body import AtmosphericComposition
from ..schemas.light_analysis import (
    AnalysisInputs,
    AnalysisResults,
    AnalysisValidation,
    AstronomicalState,
    LightAnalysis,
)
from .atmospheric_model import AtmosphericResult, calculate_atmosphere
from .body_data_service import get_body, get_body_index
from .solar_input_service import (
    ASTRONOMICAL_UNIT_KM,
    REFERENCE_IRRADIANCE_W_M2,
    resolve_solar_input,
)
from .surface_model import calculate_airless_surface
from .validation import clamp01, conserve_fractions, fractions_are_valid
from .orbital_service import calculate_orbital_state


@dataclass(frozen=True)
class PhysicsInput:
    distance_from_sun_km: float
    solar_irradiance_w_m2: float
    has_atmosphere: bool | None
    surface_pressure_pa: float | None
    atmospheric_density_kg_m3: float | None
    composition: dict[str, float | None]


@dataclass(frozen=True)
class PhysicsOutput:
    transmitted: float
    scattered: float
    absorbed: float
    relative_brightness: float
    dominant_color: str
    apparent_size_category: str
    warnings: tuple[str, ...]
    partial: bool


def _apparent_size(distance_km: float) -> str:
    distance_au = distance_km / ASTRONOMICAL_UNIT_KM
    if distance_au <= 0.75:
        return "large"
    if distance_au <= 1.25:
        return "medium"
    if distance_au <= 8:
        return "small"
    return "very small"


def _relative_brightness(
    irradiance_w_m2: float, transmitted: float, scattered: float
) -> float:
    irradiance_ratio = max(0.0, irradiance_w_m2) / REFERENCE_IRRADIANCE_W_M2
    compressed_illumination = min(1.0, math.log1p(9 * irradiance_ratio) / math.log(10))
    available_light = transmitted + 0.5 * scattered
    return clamp01(compressed_illumination * available_light)


def classify_dominant_color(
    has_atmosphere: bool,
    composition: dict[str, float],
    column_factor: float,
    scattered: float,
    absorbed: float,
    brightness: float,
) -> str:
    if not has_atmosphere:
        if brightness < 0.08:
            return "dim white"
        return "gray-white" if brightness < 0.25 else "white"

    methane = composition.get("CH4", 0.0)
    hydrogen_helium = composition.get("H2", 0.0) + composition.get("He", 0.0)
    nitrogen = composition.get("N2", 0.0)
    carbon_dioxide = composition.get("CO2", 0.0)

    if methane >= 0.005 and nitrogen >= 0.5:
        return "orange"
    if methane >= 0.01 and hydrogen_helium >= 0.5:
        return "pale blue" if brightness < 0.35 else "blue"
    if carbon_dioxide >= 0.8 and column_factor >= 2:
        return "pale yellow"
    if brightness < 0.08:
        return "dim white"
    if absorbed >= 0.35:
        return "red"
    if scattered >= 0.22:
        return "pale blue"
    if scattered >= 0.08:
        return "yellow"
    return "white"


def calculate_light_behavior(inputs: PhysicsInput) -> PhysicsOutput:
    if inputs.distance_from_sun_km <= 0 or not math.isfinite(inputs.distance_from_sun_km):
        raise ValueError("Distance from the Sun must be finite and positive.")
    if inputs.solar_irradiance_w_m2 < 0 or not math.isfinite(inputs.solar_irradiance_w_m2):
        raise ValueError("Solar irradiance must be finite and nonnegative.")

    warnings: list[str] = []
    partial = False
    column_factor = 0.0
    normalized_composition = {gas: 0.0 for gas in ("CO2", "N2", "O2", "CH4", "H2", "He")}

    if inputs.has_atmosphere is True:
        optical: AtmosphericResult = calculate_atmosphere(
            inputs.surface_pressure_pa,
            inputs.atmospheric_density_kg_m3,
            inputs.composition,
        )
        raw_fractions = (optical.transmitted, optical.scattered, optical.absorbed)
        column_factor = optical.column_factor
        normalized_composition = optical.normalized_composition
        warnings.extend(optical.warnings)
        partial = optical.partial
        modeled_has_atmosphere = True
    else:
        surface = calculate_airless_surface()
        raw_fractions = (surface.transmitted, surface.scattered, surface.absorbed)
        warnings.extend(surface.warnings)
        modeled_has_atmosphere = False
        if inputs.has_atmosphere is None:
            warnings.insert(
                0,
                "Atmosphere state is unknown; the airless/tenuous fallback was used.",
            )
            partial = True

    transmitted, scattered, absorbed = conserve_fractions(*raw_fractions)
    brightness = round(
        _relative_brightness(inputs.solar_irradiance_w_m2, transmitted, scattered),
        6,
    )
    color = classify_dominant_color(
        modeled_has_atmosphere,
        normalized_composition,
        column_factor,
        scattered,
        absorbed,
        brightness,
    )
    return PhysicsOutput(
        transmitted=transmitted,
        scattered=scattered,
        absorbed=absorbed,
        relative_brightness=brightness,
        dominant_color=color,
        apparent_size_category=_apparent_size(inputs.distance_from_sun_km),
        warnings=tuple(warnings),
        partial=partial,
    )


def analyze_destination(
    destination_id: str, simulated_time: datetime | None = None
) -> LightAnalysis:
    body = get_body(destination_id)
    body_index = get_body_index()
    orbital = (
        calculate_orbital_state(body, body_index, simulated_time)
        if simulated_time is not None
        else None
    )
    solar = resolve_solar_input(
        body,
        body_index,
        orbital.distance_from_sun_km if orbital else None,
    )
    composition = body.atmosphere.composition.model_dump()
    output = calculate_light_behavior(
        PhysicsInput(
            distance_from_sun_km=solar.distance_from_sun_km,
            solar_irradiance_w_m2=solar.irradiance_w_m2,
            has_atmosphere=body.atmosphere.hasAtmosphere,
            surface_pressure_pa=body.atmosphere.surface_pressure_pa,
            atmospheric_density_kg_m3=body.atmosphere.density_kg_m3,
            composition=composition,
        )
    )
    warnings = [*solar.warnings, *output.warnings]
    fractions = (output.transmitted, output.scattered, output.absorbed)
    valid = fractions_are_valid(fractions) and 0 <= output.relative_brightness <= 1
    source_ids = list(dict.fromkeys([*body.source_ids, "nlr-e490"]))

    astronomy = None
    if orbital:
        astronomy = AstronomicalState(
            simulatedTime=orbital.simulated_time.isoformat().replace("+00:00", "Z"),
            distanceFromSunKm=round(orbital.distance_from_sun_km, 3),
            orbitalAngleDeg=round(orbital.orbital_angle_deg, 6),
            lightTravelTimeSeconds=round(orbital.light_travel_time_seconds, 6),
            solarIrradianceWm2=round(solar.irradiance_w_m2, 9),
            apparentSolarAngularDiameterDeg=round(
                orbital.apparent_solar_angular_diameter_deg, 9
            ),
            orbitalPeriodDays=orbital.period_days,
            referenceEpochJd=orbital.reference_epoch_jd,
            phaseStatus=orbital.phase_status,
            approximate=True,
        )

    return LightAnalysis(
        destination=body.id,
        name=body.name,
        bodyType=body.type,
        hasAtmosphere=body.atmosphere.hasAtmosphere,
        calculationStatus="partial" if output.partial else "complete",
        inputs=AnalysisInputs(
            distanceFromSunKm=solar.distance_from_sun_km,
            solarIrradianceWm2=solar.irradiance_w_m2,
            derivedSolarIrradianceWm2=round(solar.derived_irradiance_w_m2, 6),
            irradianceSource=solar.irradiance_source,
            surfacePressurePa=body.atmosphere.surface_pressure_pa,
            atmosphericDensityKgM3=body.atmosphere.density_kg_m3,
            composition=AtmosphericComposition.model_validate(composition),
            solarSpectrumVisibleFraction=round(solar.spectrum.visible_fraction, 6),
            solarSpectrumRangeNm=[
                solar.spectrum.minimum_wavelength_nm,
                solar.spectrum.maximum_wavelength_nm,
            ],
        ),
        results=AnalysisResults(
            transmitted=output.transmitted,
            scattered=output.scattered,
            absorbed=output.absorbed,
            relativeBrightness=output.relative_brightness,
            dominantColor=output.dominant_color,
            apparentSizeCategory=output.apparent_size_category,
        ),
        validation=AnalysisValidation(
            energySum=round(sum(fractions), 6),
            valid=valid,
            warnings=warnings,
        ),
        sourceIds=source_ids,
        astronomy=astronomy,
    )
