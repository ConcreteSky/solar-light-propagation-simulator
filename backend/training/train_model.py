"""Train, select, evaluate, and save the Session 4 regression model."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.model_contract import (  # noqa: E402
    FEATURE_COLUMNS,
    MODEL_METADATA_PATH,
    MODEL_PATH,
    MODEL_VERSION,
    TARGET_COLUMNS,
    TRAINING_SEED,
    MissingModelFeatureError,
    destination_feature_frame,
)
from app.services.body_data_service import get_body_index  # noqa: E402
from app.services.catalog import load_catalog  # noqa: E402
from app.services.light_calculation_service import analyze_destination  # noqa: E402
from app.services.ml_prediction_service import (  # noqa: E402
    ModelPredictionError,
    predict_numeric,
    validate_prediction,
)
from app.services.solar_input_service import resolve_solar_input  # noqa: E402
from training.ml_utils import (  # noqa: E402
    artifact_size_bytes,
    candidate_factories,
    grouped_test_metrics,
    physical_consistency,
    regression_metrics,
    split_frame,
    timed_prediction_ms,
    timed_single_prediction_ms,
    xy,
)

DATASET_PATH = PROJECT_ROOT / "data" / "training" / "light_training_data.csv"
EVALUATION_PATH = PROJECT_ROOT / "data" / "evaluation" / "ai_model_evaluation.json"


def audit_dataset(frame: pd.DataFrame) -> dict[str, object]:
    numeric = frame.select_dtypes(include=np.number)
    fractions = frame[TARGET_COLUMNS[:3]].sum(axis=1)
    atmospheric = frame[frame["has_atmosphere"].astype(bool)]
    gas_columns = FEATURE_COLUMNS[5:]
    return {
        "samples": len(frame),
        "columns": len(frame.columns),
        "split_counts": frame["split"].value_counts().to_dict(),
        "missing_values": int(frame.isna().sum().sum()),
        "nonfinite_values": int((~np.isfinite(numeric)).sum().sum()),
        "duplicate_records": int(frame.duplicated().sum()),
        "duplicate_feature_records": int(frame.duplicated(FEATURE_COLUMNS).sum()),
        "maximum_energy_conservation_error": float((fractions - 1).abs().max()),
        "maximum_atmospheric_composition_error": float(
            (atmospheric[gas_columns].sum(axis=1) - 1).abs().max()
        ),
        "feature_distributions": frame[FEATURE_COLUMNS].describe().loc[
            ["min", "mean", "std", "max"]
        ].to_dict(),
        "target_distributions": frame[TARGET_COLUMNS].describe().loc[
            ["min", "mean", "std", "max"]
        ].to_dict(),
    }


def real_body_evaluation(bundle: dict[str, object]) -> dict[str, object]:
    body_index = get_body_index()
    compared: list[dict[str, object]] = []
    excluded: list[dict[str, str]] = []
    raw_predictions: list[np.ndarray] = []
    expected: list[list[float]] = []

    for body in load_catalog():
        baseline = analyze_destination(body.id)
        try:
            frame = destination_feature_frame(body, resolve_solar_input(body, body_index))
            raw = predict_numeric(bundle, frame)[0]
            validated = validate_prediction(raw)
        except (MissingModelFeatureError, ModelPredictionError, ValueError) as error:
            excluded.append({"destination": body.id, "reason": str(error)})
            continue

        truth = [
            baseline.results.transmitted,
            baseline.results.scattered,
            baseline.results.absorbed,
            baseline.results.relativeBrightness,
        ]
        corrected = [
            validated.transmitted,
            validated.scattered,
            validated.absorbed,
            validated.relative_brightness,
        ]
        raw_predictions.append(raw)
        expected.append(truth)
        compared.append(
            {
                "destination": body.id,
                "prediction": dict(zip(TARGET_COLUMNS, corrected)),
                "deterministic": dict(zip(TARGET_COLUMNS, truth)),
                "absolute_errors": dict(
                    zip(TARGET_COLUMNS, np.abs(np.asarray(corrected) - np.asarray(truth)).tolist())
                ),
                "minor_correction_applied": validated.corrected,
            }
        )

    raw_array = np.asarray(raw_predictions)
    expected_array = np.asarray(expected)
    return {
        "comparison": "machine learning versus deterministic educational physics",
        "evaluated_bodies": len(compared),
        "excluded_bodies": excluded,
        "metrics_on_raw_predictions": regression_metrics(expected_array, raw_array),
        "physical_consistency": physical_consistency(raw_array),
        "per_body": compared,
        "independent_observation_comparison": {
            "status": "not_performed",
            "reason": "The local source catalog has no independent measurements matching the model's aggregate transmitted/scattered/absorbed convention. No observational accuracy claim is made.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the deterministic-physics surrogate model.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--model-output", type=Path, default=MODEL_PATH)
    parser.add_argument("--evaluation-output", type=Path, default=EVALUATION_PATH)
    args = parser.parse_args()

    frame = pd.read_csv(args.dataset)
    audit = audit_dataset(frame)
    if any(
        audit[key]
        for key in (
            "missing_values",
            "nonfinite_values",
            "duplicate_records",
            "duplicate_feature_records",
        )
    ) or audit["maximum_energy_conservation_error"] > 1e-6:
        raise ValueError(f"Dataset audit failed: {audit}")

    train, validation, test = split_frame(frame)
    x_train, y_train = xy(train)
    x_validation, y_validation = xy(validation)
    candidate_results: dict[str, dict[str, object]] = {}
    fitted_candidates = {}

    for name, factory in candidate_factories().items():
        model = factory()
        start = time.perf_counter()
        model.fit(x_train, y_train)
        fit_seconds = time.perf_counter() - start
        predictions = model.predict(x_validation)
        candidate_results[name] = {
            "validation_metrics": regression_metrics(y_validation, predictions),
            "physical_consistency": physical_consistency(predictions),
            "fit_seconds": fit_seconds,
            "inference_ms_per_sample": timed_prediction_ms(model, x_validation),
            "serialized_size_bytes": artifact_size_bytes(model),
        }
        fitted_candidates[name] = model

    best_mae = min(
        result["validation_metrics"]["mean_mae"] for result in candidate_results.values()
    )
    near_best = [
        name
        for name, result in candidate_results.items()
        if result["validation_metrics"]["mean_mae"] <= best_mae * 1.02
    ]
    selected_name = min(
        near_best, key=lambda name: candidate_results[name]["serialized_size_bytes"]
    )

    final_model = candidate_factories()[selected_name]()
    combined = pd.concat([train, validation], ignore_index=True)
    x_combined, y_combined = xy(combined)
    final_model.fit(x_combined, y_combined)
    x_test, y_test = xy(test)
    test_predictions = final_model.predict(x_test)

    bundle: dict[str, object] = {
        "pipeline": final_model,
        "feature_columns": FEATURE_COLUMNS,
        "target_columns": TARGET_COLUMNS,
        "model_name": selected_name,
        "model_version": MODEL_VERSION,
        "training_seed": TRAINING_SEED,
        "generator_version": str(frame["generator_version"].iloc[0]),
    }
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.model_output)

    model_size = args.model_output.stat().st_size
    metadata = {
        key: value for key, value in bundle.items() if key != "pipeline"
    } | {"model_size_bytes": model_size}
    MODEL_METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_METADATA_PATH.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)
        metadata_file.write("\n")

    evaluation = {
        "model_version": MODEL_VERSION,
        "random_seed": TRAINING_SEED,
        "dataset_path": str(args.dataset.relative_to(PROJECT_ROOT)),
        "dataset_audit": audit,
        "split_policy": "Predefined deterministic 80/10/10 train/validation/test split from generator version 1.0.0; the test split was not used for model selection.",
        "candidate_validation_results": candidate_results,
        "selection": {
            "selected_model": selected_name,
            "rule": "Lowest validation mean MAE; if candidates are within 2%, choose the smaller serialized model.",
            "validation_rows_used_for_selection": len(validation),
            "final_refit_rows": len(combined),
        },
        "selected_model_test_results": {
            "samples": len(test),
            "metrics_on_raw_predictions": regression_metrics(y_test, test_predictions),
            "physical_consistency": physical_consistency(test_predictions),
            "grouped_generalization": grouped_test_metrics(test, test_predictions),
            "batch_inference_ms_per_sample": timed_prediction_ms(final_model, x_test),
            "single_inference_median_ms": timed_single_prediction_ms(
                final_model, x_test.iloc[[0]]
            ),
            "model_size_bytes": model_size,
        },
        "real_body_evaluation": real_body_evaluation(bundle),
        "scientific_scope": "The model approximates synthetic labels from the deterministic educational physics engine; these results do not establish observational accuracy.",
    }
    args.evaluation_output.parent.mkdir(parents=True, exist_ok=True)
    with args.evaluation_output.open("w", encoding="utf-8") as evaluation_file:
        json.dump(evaluation, evaluation_file, indent=2, allow_nan=False)
        evaluation_file.write("\n")

    print(json.dumps({
        "selected_model": selected_name,
        "test_metrics": evaluation["selected_model_test_results"]["metrics_on_raw_predictions"],
        "single_inference_median_ms": evaluation["selected_model_test_results"]["single_inference_median_ms"],
        "model_size_bytes": model_size,
        "real_bodies_evaluated": evaluation["real_body_evaluation"]["evaluated_bodies"],
    }, indent=2))


if __name__ == "__main__":
    main()
