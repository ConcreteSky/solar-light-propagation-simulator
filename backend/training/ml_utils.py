from __future__ import annotations

import io
import time
from collections.abc import Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from app.ml.model_contract import (
    FEATURE_COLUMNS,
    LINEAR_FEATURES,
    LOG_FEATURES,
    TARGET_COLUMNS,
    TRAINING_SEED,
)
from app.services.ml_prediction_service import ModelPredictionError, validate_prediction


def make_preprocessor() -> ColumnTransformer:
    log_pipeline = Pipeline(
        [
            ("missing", SimpleImputer(strategy="median")),
            ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
            ("scale", StandardScaler()),
        ]
    )
    linear_pipeline = Pipeline(
        [
            ("missing", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        [("log", log_pipeline, LOG_FEATURES), ("linear", linear_pipeline, LINEAR_FEATURES)],
        verbose_feature_names_out=False,
    )


def candidate_factories() -> dict[str, Callable[[], Pipeline]]:
    return {
        "linear_regression": lambda: Pipeline(
            [("preprocess", make_preprocessor()), ("regressor", LinearRegression())]
        ),
        "random_forest": lambda: Pipeline(
            [
                ("preprocess", make_preprocessor()),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=160,
                        max_depth=18,
                        min_samples_leaf=2,
                        random_state=TRAINING_SEED,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "hist_gradient_boosting": lambda: Pipeline(
            [
                ("preprocess", make_preprocessor()),
                (
                    "regressor",
                    MultiOutputRegressor(
                        HistGradientBoostingRegressor(
                            learning_rate=0.08,
                            max_iter=180,
                            max_leaf_nodes=31,
                            l2_regularization=0.05,
                            random_state=TRAINING_SEED,
                        )
                    ),
                ),
            ]
        ),
    }


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, object]:
    per_target: dict[str, dict[str, float]] = {}
    for index, target in enumerate(TARGET_COLUMNS):
        mae = float(mean_absolute_error(y_true[:, index], y_pred[:, index]))
        rmse = float(np.sqrt(mean_squared_error(y_true[:, index], y_pred[:, index])))
        variance = float(np.var(y_true[:, index]))
        per_target[target] = {
            "mae": mae,
            "mae_percentage_points": mae * 100,
            "rmse": rmse,
            "r2": (
                float(r2_score(y_true[:, index], y_pred[:, index]))
                if variance > 1e-15
                else None
            ),
        }
    return {
        "per_target": per_target,
        "mean_mae": float(np.mean([value["mae"] for value in per_target.values()])),
        "mean_rmse": float(np.mean([value["rmse"] for value in per_target.values()])),
    }


def physical_consistency(predictions: np.ndarray) -> dict[str, float | int]:
    corrected = 0
    serious = 0
    negative_rows = int((predictions[:, :3] < 0).any(axis=1).sum())
    over_one_rows = int((predictions > 1).any(axis=1).sum())
    energy_errors = np.abs(predictions[:, :3].sum(axis=1) - 1.0)
    for row in predictions:
        try:
            corrected += int(validate_prediction(row).corrected)
        except ModelPredictionError:
            serious += 1
    return {
        "rows": len(predictions),
        "minor_correction_count": corrected,
        "minor_correction_rate": corrected / len(predictions),
        "serious_violation_count": serious,
        "serious_violation_rate": serious / len(predictions),
        "negative_fraction_rows": negative_rows,
        "over_one_rows": over_one_rows,
        "maximum_energy_sum_error": float(energy_errors.max()),
        "mean_energy_sum_error": float(energy_errors.mean()),
    }


def artifact_size_bytes(model: Pipeline) -> int:
    buffer = io.BytesIO()
    joblib.dump(model, buffer)
    return buffer.tell()


def timed_prediction_ms(model: Pipeline, frame: pd.DataFrame, repeats: int = 5) -> float:
    model.predict(frame.iloc[: min(16, len(frame))])
    durations = []
    for _ in range(repeats):
        start = time.perf_counter()
        model.predict(frame)
        durations.append(time.perf_counter() - start)
    return float(np.median(durations) * 1000 / len(frame))


def timed_single_prediction_ms(model: Pipeline, row: pd.DataFrame, repeats: int = 100) -> float:
    model.predict(row)
    durations = []
    for _ in range(repeats):
        start = time.perf_counter()
        model.predict(row)
        durations.append(time.perf_counter() - start)
    return float(np.median(durations) * 1000)


def split_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    return tuple(
        frame.loc[frame["split"] == split].reset_index(drop=True)
        for split in ("train", "validation", "test")
    )  # type: ignore[return-value]


def xy(frame: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    return frame[FEATURE_COLUMNS], frame[TARGET_COLUMNS].to_numpy(dtype=float)


def grouped_test_metrics(
    frame: pd.DataFrame, predictions: np.ndarray
) -> dict[str, dict[str, object]]:
    groups = {
        "inner_system_le_0_75_au": frame["distance_from_sun_km"] <= 0.75 * 149_597_870.7,
        "outer_system_gt_8_au": frame["distance_from_sun_km"] > 8 * 149_597_870.7,
        "dense_atmosphere_gt_200k_pa": (frame["has_atmosphere"])
        & (frame["surface_pressure_pa"] > 200_000),
        "airless": ~frame["has_atmosphere"].astype(bool),
    }
    result: dict[str, dict[str, object]] = {}
    for name, mask in groups.items():
        indices = np.flatnonzero(mask.to_numpy())
        if len(indices):
            result[name] = {
                "samples": len(indices),
                **regression_metrics(
                    frame.loc[mask, TARGET_COLUMNS].to_numpy(dtype=float),
                    predictions[indices],
                ),
                "physical_consistency": physical_consistency(predictions[indices]),
            }
    return result
