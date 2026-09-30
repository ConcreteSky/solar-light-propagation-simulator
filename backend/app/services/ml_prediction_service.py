from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from ..ml.model_contract import (
    FEATURE_COLUMNS,
    MODEL_PATH,
    MODEL_VERSION,
    MissingModelFeatureError,
    destination_feature_frame,
)
from ..schemas.light_analysis import AnalysisResults
from ..schemas.light_prediction import (
    BaselineComparison,
    LightPrediction,
    PredictionValidation,
)
from .atmospheric_model import calculate_atmosphere
from .body_data_service import get_body, get_body_index
from .light_calculation_service import analyze_destination, classify_dominant_color
from .solar_input_service import resolve_solar_input
from .validation import clamp01, conserve_fractions, fractions_are_valid


class ModelPredictionError(RuntimeError):
    pass


@dataclass(frozen=True)
class ValidatedPrediction:
    transmitted: float
    scattered: float
    absorbed: float
    relative_brightness: float
    corrected: bool
    warnings: tuple[str, ...]


@lru_cache(maxsize=1)
def load_model_bundle() -> dict[str, object]:
    bundle = joblib.load(MODEL_PATH)
    required = {"pipeline", "feature_columns", "target_columns", "model_name", "model_version"}
    if not isinstance(bundle, dict) or not required.issubset(bundle):
        raise ModelPredictionError("Model artifact is missing required metadata.")
    if bundle["feature_columns"] != FEATURE_COLUMNS:
        raise ModelPredictionError("Model artifact feature contract is incompatible.")
    return bundle


def preload_model() -> None:
    load_model_bundle()


def predict_numeric(bundle: dict[str, object], frame: pd.DataFrame) -> np.ndarray:
    if list(frame.columns) != FEATURE_COLUMNS:
        raise ValueError(
            f"Expected {len(FEATURE_COLUMNS)} ordered features; received {len(frame.columns)}."
        )
    raw = np.asarray(bundle["pipeline"].predict(frame), dtype=float)
    if raw.shape != (len(frame), 4):
        raise ModelPredictionError(f"Unexpected model output shape: {raw.shape}")
    return raw


def validate_prediction(raw: np.ndarray) -> ValidatedPrediction:
    values = np.asarray(raw, dtype=float).reshape(-1)
    if values.shape != (4,) or not np.isfinite(values).all():
        raise ModelPredictionError("Model returned non-finite or incorrectly shaped output.")

    fractions = values[:3]
    brightness = float(values[3])
    energy_error = abs(float(fractions.sum()) - 1.0)
    if (
        (fractions < -0.1).any()
        or (fractions > 1.1).any()
        or brightness < -0.1
        or brightness > 1.1
        or energy_error > 0.1
    ):
        raise ModelPredictionError("Model prediction has a serious physical-consistency violation.")

    corrected = bool(
        (fractions < 0).any()
        or (fractions > 1).any()
        or not math.isclose(float(fractions.sum()), 1.0, abs_tol=1e-6)
        or not 0 <= brightness <= 1
    )
    warnings: list[str] = []
    if corrected:
        warnings.append("Minor model inconsistencies were clamped and energy-normalized.")
    transmitted, scattered, absorbed = conserve_fractions(*fractions.tolist())
    return ValidatedPrediction(
        transmitted=transmitted,
        scattered=scattered,
        absorbed=absorbed,
        relative_brightness=round(clamp01(brightness), 6),
        corrected=corrected,
        warnings=tuple(warnings),
    )


def _fallback_response(
    destination_id: str, reason: str, simulated_time: datetime | None = None
) -> LightPrediction:
    baseline = analyze_destination(destination_id, simulated_time)
    return LightPrediction(
        destination=baseline.destination,
        name=baseline.name,
        bodyType=baseline.bodyType,
        method="deterministic_fallback",
        modelName=None,
        modelVersion=MODEL_VERSION,
        hasAtmosphere=baseline.hasAtmosphere,
        results=baseline.results,
        validation=PredictionValidation(
            valid=baseline.validation.valid,
            fallbackUsed=True,
            corrected=False,
            energySum=baseline.validation.energySum,
            warnings=[reason, *baseline.validation.warnings],
        ),
        baselineComparison=BaselineComparison(
            transmittedAbsoluteError=0.0,
            scatteredAbsoluteError=0.0,
            absorbedAbsoluteError=0.0,
            relativeBrightnessAbsoluteError=0.0,
        ),
        sourceIds=baseline.sourceIds,
        astronomy=baseline.astronomy,
    )


def predict_destination(
    destination_id: str, simulated_time: datetime | None = None
) -> LightPrediction:
    # Resolve the ID first so an unsupported destination remains a clean 404.
    body = get_body(destination_id)
    baseline = analyze_destination(body.id, simulated_time)
    solar = resolve_solar_input(
        body,
        get_body_index(),
        baseline.astronomy.distanceFromSunKm if baseline.astronomy else None,
    )
    warnings: list[str] = []

    try:
        frame = destination_feature_frame(body, solar)
        missing_gases = [
            gas
            for gas, value in body.atmosphere.composition.model_dump().items()
            if value is None
        ]
        if missing_gases:
            warnings.append(
                "Unreported individual gases use zero optical contribution, matching the deterministic model: "
                + ", ".join(missing_gases)
                + "."
            )
        bundle = load_model_bundle()
        raw = predict_numeric(bundle, frame)[0]
        prediction = validate_prediction(raw)
    except MissingModelFeatureError as error:
        return _fallback_response(body.id, f"ML fallback: {error}", simulated_time)
    except (FileNotFoundError, OSError, ValueError, ModelPredictionError) as error:
        return _fallback_response(body.id, f"ML fallback: {error}", simulated_time)

    composition = body.atmosphere.composition.model_dump()
    if body.atmosphere.hasAtmosphere:
        optical = calculate_atmosphere(
            body.atmosphere.surface_pressure_pa,
            body.atmosphere.density_kg_m3,
            composition,
        )
        normalized_composition = optical.normalized_composition
        column_factor = optical.column_factor
    else:
        normalized_composition = {
            gas: 0.0 for gas in ("CO2", "N2", "O2", "CH4", "H2", "He")
        }
        column_factor = 0.0

    color = classify_dominant_color(
        bool(body.atmosphere.hasAtmosphere),
        normalized_composition,
        column_factor,
        prediction.scattered,
        prediction.absorbed,
        prediction.relative_brightness,
    )
    results = AnalysisResults(
        transmitted=prediction.transmitted,
        scattered=prediction.scattered,
        absorbed=prediction.absorbed,
        relativeBrightness=prediction.relative_brightness,
        dominantColor=color,
        apparentSizeCategory=baseline.results.apparentSizeCategory,
    )
    fractions = (results.transmitted, results.scattered, results.absorbed)
    warnings.extend(prediction.warnings)
    return LightPrediction(
        destination=body.id,
        name=body.name,
        bodyType=body.type,
        method="machine_learning",
        modelName=str(bundle["model_name"]),
        modelVersion=str(bundle["model_version"]),
        hasAtmosphere=body.atmosphere.hasAtmosphere,
        results=results,
        validation=PredictionValidation(
            valid=fractions_are_valid(fractions),
            fallbackUsed=False,
            corrected=prediction.corrected,
            energySum=round(sum(fractions), 6),
            warnings=warnings,
        ),
        baselineComparison=BaselineComparison(
            transmittedAbsoluteError=round(
                abs(results.transmitted - baseline.results.transmitted), 6
            ),
            scatteredAbsoluteError=round(
                abs(results.scattered - baseline.results.scattered), 6
            ),
            absorbedAbsoluteError=round(
                abs(results.absorbed - baseline.results.absorbed), 6
            ),
            relativeBrightnessAbsoluteError=round(
                abs(results.relativeBrightness - baseline.results.relativeBrightness), 6
            ),
        ),
        sourceIds=baseline.sourceIds,
        astronomy=baseline.astronomy,
    )
