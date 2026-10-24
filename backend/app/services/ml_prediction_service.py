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
    RELIABILITY_VERSION,
    MissingModelFeatureError,
    scientific_feature_frame,
)
from ..schemas.light_analysis import (
    AnalysisResults,
    AtmosphereScenario,
    LightAnalysis,
    ModeledLightColor,
)
from ..schemas.light_prediction import (
    BaselineComparison,
    LightPrediction,
    OodAssessment,
    PredictionValidation,
    ReliabilityAssessment,
    UncertaintyEstimate,
)
from .atmospheric_model import calculate_atmosphere
from .body_data_service import get_body
from .light_calculation_service import (
    PHYSICS_MODEL_VERSION,
    analyze_destination,
    classify_dominant_color,
)
from .reliability_service import (
    ReliabilityDecision,
    ReliabilityModelError,
    assess_reliability,
    preload_reliability_model,
    uncertainty_by_output,
)
from .spectral_color_service import derive_transmitted_light_color
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
    """Retain the original single-model artifact for reproducibility checks."""
    bundle = joblib.load(MODEL_PATH)
    required = {"pipeline", "feature_columns", "target_columns", "model_name", "model_version"}
    if not isinstance(bundle, dict) or not required.issubset(bundle):
        raise ModelPredictionError("Model artifact is missing required metadata.")
    if bundle["feature_columns"] != FEATURE_COLUMNS:
        raise ModelPredictionError("Model artifact feature contract is incompatible.")
    return bundle


def preload_model() -> None:
    load_model_bundle()
    preload_reliability_model()


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


def _missing_reliability(reason: str) -> ReliabilityAssessment:
    return ReliabilityAssessment(
        classification="unreliable",
        decision="defer_to_physics",
        fallbackReason=reason,
        physicalViolations=[],
        uncertainty=None,
        ood=None,
        rawAiPrediction=None,
    )


def _reliability_schema(decision: ReliabilityDecision) -> ReliabilityAssessment:
    return ReliabilityAssessment(
        classification=decision.classification,
        decision=decision.decision,
        fallbackReason=decision.fallback_reason,
        physicalViolations=list(decision.physical_violations),
        uncertainty=UncertaintyEstimate(
            score=round(decision.uncertainty_score, 9),
            threshold=round(decision.uncertainty_threshold, 9),
            perOutput=uncertainty_by_output(decision),
            method="five-model ensemble spread (mean target standard deviation)",
        ),
        ood=OodAssessment(
            score=round(decision.ood_score, 9),
            q95=round(decision.ood_q95, 9),
            q99=round(decision.ood_q99, 9),
            classification=decision.ood_classification,
            method="RMS standardized transformed-feature distance",
        ),
        rawAiPrediction=[round(float(value), 9) for value in decision.mean_prediction],
    )


def _feature_frame(baseline: LightAnalysis) -> pd.DataFrame:
    return scientific_feature_frame(
        distance_from_sun_km=baseline.inputs.distanceFromSunKm,
        solar_irradiance_w_m2=baseline.inputs.solarIrradianceWm2,
        has_atmosphere=baseline.hasAtmosphere,
        surface_pressure_pa=baseline.inputs.surfacePressurePa,
        atmospheric_density_kg_m3=baseline.inputs.atmosphericDensityKgM3,
        composition=baseline.inputs.composition.model_dump(),
    )


def _analysis_results(
    baseline: LightAnalysis, prediction: ValidatedPrediction
) -> AnalysisResults:
    composition = baseline.inputs.composition.model_dump()
    if baseline.hasAtmosphere:
        optical = calculate_atmosphere(
            baseline.inputs.surfacePressurePa,
            baseline.inputs.atmosphericDensityKgM3,
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
        bool(baseline.hasAtmosphere),
        normalized_composition,
        column_factor,
        prediction.scattered,
        prediction.absorbed,
        prediction.relative_brightness,
    )
    transmitted_color = derive_transmitted_light_color(color)
    return AnalysisResults(
        transmitted=prediction.transmitted,
        scattered=prediction.scattered,
        absorbed=prediction.absorbed,
        relativeBrightness=prediction.relative_brightness,
        dominantColor=color,
        scatteredLightColor=baseline.results.scatteredLightColor,
        transmittedLightColor=ModeledLightColor(
            label=transmitted_color.label,
            rgb=transmitted_color.rgb,
            spectralBand=transmitted_color.spectral_band,
            confidence=transmitted_color.confidence,
            basis=transmitted_color.basis,
        ),
        apparentSizeCategory=baseline.results.apparentSizeCategory,
    )


def _comparison(
    ai_results: AnalysisResults | None, baseline: LightAnalysis
) -> BaselineComparison:
    values = (0.0, 0.0, 0.0, 0.0) if ai_results is None else (
        abs(ai_results.transmitted - baseline.results.transmitted),
        abs(ai_results.scattered - baseline.results.scattered),
        abs(ai_results.absorbed - baseline.results.absorbed),
        abs(ai_results.relativeBrightness - baseline.results.relativeBrightness),
    )
    return BaselineComparison(
        transmittedAbsoluteError=round(values[0], 6),
        scatteredAbsoluteError=round(values[1], 6),
        absorbedAbsoluteError=round(values[2], 6),
        relativeBrightnessAbsoluteError=round(values[3], 6),
    )


def _fallback_response(
    baseline: LightAnalysis,
    reason: str,
    reliability: ReliabilityAssessment | None = None,
    ai_results: AnalysisResults | None = None,
    corrected: bool = False,
    warnings: list[str] | None = None,
) -> LightPrediction:
    return LightPrediction(
        destination=baseline.destination,
        name=baseline.name,
        bodyType=baseline.bodyType,
        method="deterministic_fallback",
        resultSource="Deterministic fallback",
        modelName=None if ai_results is None else "hist_gradient_boosting_ensemble",
        modelVersion=MODEL_VERSION,
        hasAtmosphere=baseline.hasAtmosphere,
        results=baseline.results,
        validation=PredictionValidation(
            valid=baseline.validation.valid,
            fallbackUsed=True,
            corrected=corrected,
            energySum=baseline.validation.energySum,
            warnings=[reason, *(warnings or []), *baseline.validation.warnings],
        ),
        baselineComparison=_comparison(ai_results, baseline),
        aiResults=ai_results,
        deterministicResults=baseline.results,
        reliability=reliability or _missing_reliability(reason),
        sourceIds=baseline.sourceIds,
        astronomy=baseline.astronomy,
    )


def _hybrid_prediction(
    baseline: LightAnalysis, extra_warnings: list[str] | None = None
) -> LightPrediction:
    try:
        load_model_bundle()
        decision = assess_reliability(_feature_frame(baseline))
        reliability = _reliability_schema(decision)
        try:
            validated = validate_prediction(decision.mean_prediction)
            ai_results = _analysis_results(baseline, validated)
        except ModelPredictionError as error:
            return _fallback_response(
                baseline,
                f"Reliability fallback: {error}",
                reliability=reliability,
                warnings=extra_warnings,
            )
    except MissingModelFeatureError as error:
        return _fallback_response(baseline, f"ML fallback: {error}")
    except (FileNotFoundError, OSError, ValueError, ReliabilityModelError, ModelPredictionError) as error:
        return _fallback_response(baseline, f"ML fallback: {error}")

    warnings = [*(extra_warnings or []), *validated.warnings]
    if decision.decision == "defer_to_physics":
        return _fallback_response(
            baseline,
            f"Reliability fallback: {decision.fallback_reason}",
            reliability=reliability,
            ai_results=ai_results,
            corrected=validated.corrected,
            warnings=warnings,
        )

    fractions = (ai_results.transmitted, ai_results.scattered, ai_results.absorbed)
    return LightPrediction(
        destination=baseline.destination,
        name=baseline.name,
        bodyType=baseline.bodyType,
        method="machine_learning",
        resultSource="ML surrogate",
        modelName="hist_gradient_boosting_ensemble",
        modelVersion=MODEL_VERSION,
        hasAtmosphere=baseline.hasAtmosphere,
        results=ai_results,
        validation=PredictionValidation(
            valid=fractions_are_valid(fractions),
            fallbackUsed=False,
            corrected=validated.corrected,
            energySum=round(sum(fractions), 6),
            warnings=warnings,
        ),
        baselineComparison=_comparison(ai_results, baseline),
        aiResults=ai_results,
        deterministicResults=baseline.results,
        reliability=reliability,
        sourceIds=baseline.sourceIds,
        astronomy=baseline.astronomy,
    )


def _predict_destination_uncached(
    destination_id: str, simulated_time: datetime | None = None
) -> LightPrediction:
    body = get_body(destination_id)
    baseline = analyze_destination(body.id, simulated_time)
    missing_gases = [
        gas for gas, value in body.atmosphere.composition.model_dump().items() if value is None
    ]
    warnings = []
    if missing_gases:
        warnings.append(
            "Unreported individual gases use zero optical contribution, matching the deterministic model: "
            + ", ".join(missing_gases)
            + "."
        )
    return _hybrid_prediction(baseline, warnings)


def _predict_scenario_uncached(
    destination_id: str,
    scenario: AtmosphereScenario,
    simulated_time: datetime | None = None,
) -> LightPrediction:
    body = get_body(destination_id)
    baseline = analyze_destination(body.id, simulated_time, scenario)
    return _hybrid_prediction(baseline)


@lru_cache(maxsize=256)
def _cached_prediction(
    destination_id: str,
    simulated_time: datetime | None,
    model_version: str,
    physics_version: str,
    reliability_version: str,
) -> LightPrediction:
    return _predict_destination_uncached(destination_id, simulated_time)


@lru_cache(maxsize=128)
def _cached_scenario_prediction(
    destination_id: str,
    simulated_time: datetime | None,
    scenario_json: str,
    model_version: str,
    physics_version: str,
    reliability_version: str,
) -> LightPrediction:
    scenario = AtmosphereScenario.model_validate_json(scenario_json)
    return _predict_scenario_uncached(destination_id, scenario, simulated_time)


def predict_destination(
    destination_id: str, simulated_time: datetime | None = None
) -> LightPrediction:
    return _cached_prediction(
        destination_id.strip().lower(), simulated_time, MODEL_VERSION,
        PHYSICS_MODEL_VERSION, RELIABILITY_VERSION,
    )


def predict_scenario(
    destination_id: str,
    scenario: AtmosphereScenario,
    simulated_time: datetime | None = None,
) -> LightPrediction:
    return _cached_scenario_prediction(
        destination_id.strip().lower(), simulated_time, scenario.model_dump_json(),
        MODEL_VERSION, PHYSICS_MODEL_VERSION, RELIABILITY_VERSION,
    )


def clear_prediction_cache() -> None:
    _cached_prediction.cache_clear()
    _cached_scenario_prediction.cache_clear()


def prediction_cache_info() -> dict[str, object]:
    return {
        "real": _cached_prediction.cache_info(),
        "scenario": _cached_scenario_prediction.cache_info(),
    }
