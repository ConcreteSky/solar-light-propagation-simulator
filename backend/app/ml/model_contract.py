from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from ..schemas.celestial_body import CelestialBody
from ..services.solar_input_service import SolarInput

MODEL_VERSION = "1.0.0"
TRAINING_SEED = 741
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "light_model.joblib"
MODEL_METADATA_PATH = Path(__file__).resolve().parents[2] / "models" / "light_model_metadata.json"
RELIABILITY_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "reliability_ensemble.joblib"
RELIABILITY_METADATA_PATH = Path(__file__).resolve().parents[2] / "models" / "reliability_metadata.json"
RELIABILITY_VERSION = "1.0.0"

FEATURE_COLUMNS = [
    "distance_from_sun_km",
    "incoming_solar_irradiance_w_m2",
    "has_atmosphere",
    "surface_pressure_pa",
    "atmospheric_density_kg_m3",
    "co2_fraction",
    "n2_fraction",
    "o2_fraction",
    "ch4_fraction",
    "h2_fraction",
    "he_fraction",
]
LOG_FEATURES = [
    "distance_from_sun_km",
    "incoming_solar_irradiance_w_m2",
    "surface_pressure_pa",
    "atmospheric_density_kg_m3",
]
LINEAR_FEATURES = [
    "has_atmosphere",
    "co2_fraction",
    "n2_fraction",
    "o2_fraction",
    "ch4_fraction",
    "h2_fraction",
    "he_fraction",
]
TARGET_COLUMNS = [
    "transmitted_light_fraction",
    "scattered_light_fraction",
    "absorbed_light_fraction",
    "relative_brightness",
]
RESULT_KEYS = ["transmitted", "scattered", "absorbed", "relativeBrightness"]


class MissingModelFeatureError(ValueError):
    pass


def scientific_feature_frame(
    *,
    distance_from_sun_km: float,
    solar_irradiance_w_m2: float,
    has_atmosphere: bool | None,
    surface_pressure_pa: float | None,
    atmospheric_density_kg_m3: float | None,
    composition: dict[str, float | None],
) -> pd.DataFrame:
    if has_atmosphere is None:
        raise MissingModelFeatureError("Atmosphere state is unknown.")
    if has_atmosphere and all(value is None for value in composition.values()):
        raise MissingModelFeatureError("Atmospheric composition is unavailable.")
    gases = {
        "CO2": max(float(composition["CO2"] or 0.0), 0.0),
        "N2": max(float(composition["N2"] or 0.0), 0.0),
        "O2": max(float(composition["O2"] or 0.0), 0.0),
        "CH4": max(float(composition["CH4"] or 0.0), 0.0),
        "H2": max(float(composition["H2"] or 0.0), 0.0),
        "He": max(float(composition["He"] or 0.0), 0.0),
    }
    gas_total = sum(gases.values())
    if has_atmosphere and gas_total <= 0:
        raise MissingModelFeatureError("Atmospheric composition has no positive fractions.")
    if has_atmosphere:
        gases = {name: value / gas_total for name, value in gases.items()}
    else:
        gases = {name: 0.0 for name in gases}

    values: dict[str, float | bool | None] = {
        "distance_from_sun_km": distance_from_sun_km,
        "incoming_solar_irradiance_w_m2": solar_irradiance_w_m2,
        "has_atmosphere": has_atmosphere,
        "surface_pressure_pa": surface_pressure_pa,
        "atmospheric_density_kg_m3": atmospheric_density_kg_m3,
        # The deterministic model normalizes the supported gas mixture before
        # applying coefficients. Use that same scientific representation here.
        "co2_fraction": gases["CO2"],
        "n2_fraction": gases["N2"],
        "o2_fraction": gases["O2"],
        "ch4_fraction": gases["CH4"],
        "h2_fraction": gases["H2"],
        "he_fraction": gases["He"],
    }

    missing = [name for name in FEATURE_COLUMNS if values[name] is None]
    if missing:
        raise MissingModelFeatureError(
            "Missing required model features: " + ", ".join(missing)
        )
    for name in FEATURE_COLUMNS:
        value = values[name]
        if isinstance(value, bool):
            continue
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise MissingModelFeatureError(f"Invalid model feature: {name}")

    return pd.DataFrame([values], columns=FEATURE_COLUMNS)


def destination_feature_frame(body: CelestialBody, solar: SolarInput) -> pd.DataFrame:
    return scientific_feature_frame(
        distance_from_sun_km=solar.distance_from_sun_km,
        solar_irradiance_w_m2=solar.irradiance_w_m2,
        has_atmosphere=body.atmosphere.hasAtmosphere,
        surface_pressure_pa=body.atmosphere.surface_pressure_pa,
        atmospheric_density_kg_m3=body.atmosphere.density_kg_m3,
        composition=body.atmosphere.composition.model_dump(),
    )
