"""Centralized uncertainty, OOD, physical-validation, and fallback decisions."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from ..ml.model_contract import (
    FEATURE_COLUMNS,
    LOG_FEATURES,
    RELIABILITY_MODEL_PATH,
    RELIABILITY_VERSION,
    RESULT_KEYS,
)


class ReliabilityModelError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReliabilityDecision:
    mean_prediction: np.ndarray
    uncertainty_per_output: np.ndarray
    uncertainty_score: float
    uncertainty_threshold: float
    ood_score: float
    ood_q95: float
    ood_q99: float
    ood_classification: str
    classification: str
    decision: str
    fallback_reason: str | None
    physical_violations: tuple[str, ...]


@lru_cache(maxsize=1)
def load_reliability_bundle() -> dict[str, object]:
    bundle = joblib.load(RELIABILITY_MODEL_PATH)
    required = {
        "models",
        "feature_columns",
        "target_columns",
        "reliability_version",
        "feature_mean",
        "feature_std",
        "ood_q95",
        "ood_q99",
        "uncertainty_q99",
    }
    if not isinstance(bundle, dict) or not required.issubset(bundle):
        raise ReliabilityModelError("Reliability artifact is incomplete.")
    if bundle["feature_columns"] != FEATURE_COLUMNS:
        raise ReliabilityModelError("Reliability feature contract is incompatible.")
    if bundle["reliability_version"] != RELIABILITY_VERSION:
        raise ReliabilityModelError("Reliability artifact version is incompatible.")
    if len(bundle["models"]) < 2:
        raise ReliabilityModelError("Uncertainty estimation requires an ensemble.")
    return bundle


def preload_reliability_model() -> None:
    load_reliability_bundle()


def _transformed_matrix(frame: pd.DataFrame) -> np.ndarray:
    columns = []
    for feature in FEATURE_COLUMNS:
        values = frame[feature].astype(float).to_numpy()
        columns.append(np.log1p(values) if feature in LOG_FEATURES else values)
    return np.column_stack(columns)


def _physical_violations(raw: np.ndarray) -> tuple[tuple[str, ...], bool]:
    if raw.shape != (4,) or not np.isfinite(raw).all():
        return ("non_finite_or_invalid_shape",), True
    fractions = raw[:3]
    energy_error = abs(float(fractions.sum()) - 1.0)
    violations = []
    if (fractions < 0).any():
        violations.append("negative_fraction")
    if (fractions > 1).any() or raw[3] < 0 or raw[3] > 1:
        violations.append("value_outside_unit_interval")
    if energy_error > 1e-6:
        violations.append("energy_nonconservation")
    serious = bool(
        (fractions < -0.1).any()
        or (fractions > 1.1).any()
        or raw[3] < -0.1
        or raw[3] > 1.1
        or energy_error > 0.1
    )
    return tuple(violations), serious


def assess_reliability(frame: pd.DataFrame) -> ReliabilityDecision:
    if list(frame.columns) != FEATURE_COLUMNS or len(frame) != 1:
        raise ValueError("Reliability assessment expects one ordered feature row.")
    bundle = load_reliability_bundle()
    predictions = np.stack(
        [np.asarray(model.predict(frame)[0], dtype=float) for model in bundle["models"]]
    )
    mean_prediction = predictions.mean(axis=0)
    uncertainty_per_output = predictions.std(axis=0, ddof=1)
    uncertainty_score = float(uncertainty_per_output.mean())

    matrix = _transformed_matrix(frame)
    feature_mean = np.asarray(bundle["feature_mean"], dtype=float)
    feature_std = np.asarray(bundle["feature_std"], dtype=float)
    ood_score = float(
        np.sqrt(np.mean(((matrix[0] - feature_mean) / feature_std) ** 2))
    )
    ood_q95 = float(bundle["ood_q95"])
    ood_q99 = float(bundle["ood_q99"])
    uncertainty_threshold = float(bundle["uncertainty_q99"])
    ood_classification = (
        "in_distribution"
        if ood_score <= ood_q95
        else "near_boundary" if ood_score <= ood_q99 else "severe"
    )
    physical_violations, serious_violation = _physical_violations(mean_prediction)

    reasons = []
    if ood_score > ood_q99:
        reasons.append("severe_ood")
    if uncertainty_score > uncertainty_threshold:
        reasons.append("high_uncertainty")
    if serious_violation:
        reasons.append("serious_physical_violation")
    fallback_reason = ", ".join(reasons) or None
    decision = "defer_to_physics" if reasons else "use_ai"
    classification = (
        "unreliable"
        if reasons
        else "caution"
        if ood_classification == "near_boundary"
        else "reliable"
    )
    return ReliabilityDecision(
        mean_prediction=mean_prediction,
        uncertainty_per_output=uncertainty_per_output,
        uncertainty_score=uncertainty_score,
        uncertainty_threshold=uncertainty_threshold,
        ood_score=ood_score,
        ood_q95=ood_q95,
        ood_q99=ood_q99,
        ood_classification=ood_classification,
        classification=classification,
        decision=decision,
        fallback_reason=fallback_reason,
        physical_violations=physical_violations,
    )


def uncertainty_by_output(decision: ReliabilityDecision) -> dict[str, float]:
    return {
        key: round(float(value), 9)
        for key, value in zip(RESULT_KEYS, decision.uncertainty_per_output)
    }
