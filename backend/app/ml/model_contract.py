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


def destination_feature_frame(body: CelestialBody, solar: SolarInput) -> pd.DataFrame:
    if body.atmosphere.hasAtmosphere is None:
        raise MissingModelFeatureError("Atmosphere state is unknown.")

    composition = body.atmosphere.composition.model_dump()
    if body.atmosphere.hasAtmosphere and all(value is None for value in composition.values()):
        raise MissingModelFeatureError("Atmospheric composition is unavailable.")
    values: dict[str, float | bool | None] = {
        "distance_from_sun_km": solar.distance_from_sun_km,
        "incoming_solar_irradiance_w_m2": solar.irradiance_w_m2,
        "has_atmosphere": body.atmosphere.hasAtmosphere,
        "surface_pressure_pa": body.atmosphere.surface_pressure_pa,
        "atmospheric_density_kg_m3": body.atmosphere.density_kg_m3,
        # This matches the deterministic model's documented zero optical
        # contribution for an unreported individual gas; it is not a measured zero.
        "co2_fraction": composition["CO2"] or 0.0,
        "n2_fraction": composition["N2"] or 0.0,
        "o2_fraction": composition["O2"] or 0.0,
        "ch4_fraction": composition["CH4"] or 0.0,
        "h2_fraction": composition["H2"] or 0.0,
        "he_fraction": composition["He"] or 0.0,
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
