"""Train and persist the repeated-seed ensemble and OOD reference used at runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.ml.model_contract import FEATURE_COLUMNS, LOG_FEATURES, TARGET_COLUMNS
from training.generate_training_data import generate_training_frame
from training.ml_utils import make_hist_gradient_boosting_pipeline


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = ROOT / "backend" / "models" / "reliability_ensemble.joblib"
DEFAULT_METADATA = ROOT / "backend" / "models" / "reliability_metadata.json"
REFERENCE_DATASET = ROOT / "data" / "training" / "light_training_data.csv"
SEEDS = (741, 742, 743, 744, 745)
RELIABILITY_VERSION = "1.0.0"


def transformed_matrix(frame: pd.DataFrame) -> np.ndarray:
    columns = []
    for feature in FEATURE_COLUMNS:
        values = frame[feature].astype(float).to_numpy()
        columns.append(np.log1p(values) if feature in LOG_FEATURES else values)
    return np.column_stack(columns)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples-per-seed", type=int, default=10_000)
    parser.add_argument("--artifact", type=Path, default=DEFAULT_ARTIFACT)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    args = parser.parse_args()

    models = []
    for seed in SEEDS:
        frame = generate_training_frame(args.samples_per_seed, seed)
        fit = frame[frame["split"].isin(("train", "validation"))]
        model = make_hist_gradient_boosting_pipeline(seed)
        model.fit(fit[FEATURE_COLUMNS], fit[TARGET_COLUMNS].to_numpy(float))
        models.append(model)

    reference = pd.read_csv(REFERENCE_DATASET)
    reference_fit = reference[reference["split"].isin(("train", "validation"))]
    matrix = transformed_matrix(reference_fit)
    feature_mean = matrix.mean(axis=0)
    feature_std = matrix.std(axis=0)
    feature_std[feature_std < 1e-12] = 1.0
    ood_scores = np.sqrt(np.mean(((matrix - feature_mean) / feature_std) ** 2, axis=1))

    validation = reference[reference["split"] == "validation"]
    validation_predictions = np.stack(
        [model.predict(validation[FEATURE_COLUMNS]) for model in models]
    )
    validation_uncertainty = validation_predictions.std(axis=0, ddof=1).mean(axis=1)

    bundle = {
        "models": models,
        "feature_columns": FEATURE_COLUMNS,
        "target_columns": TARGET_COLUMNS,
        "model_name": "hist_gradient_boosting_ensemble",
        "model_version": "1.0.0",
        "reliability_version": RELIABILITY_VERSION,
        "seeds": list(SEEDS),
        "feature_mean": feature_mean,
        "feature_std": feature_std,
        "ood_q95": float(np.quantile(ood_scores, 0.95)),
        "ood_q99": float(np.quantile(ood_scores, 0.99)),
        "uncertainty_q95": float(np.quantile(validation_uncertainty, 0.95)),
        "uncertainty_q99": float(np.quantile(validation_uncertainty, 0.99)),
    }
    args.artifact.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, args.artifact, compress=3)

    metadata = {
        key: value
        for key, value in bundle.items()
        if key not in {"models", "feature_mean", "feature_std"}
    }
    metadata.update(
        {
            "feature_mean": feature_mean.tolist(),
            "feature_std": feature_std.tolist(),
            "samples_per_seed": args.samples_per_seed,
            "training_rows_per_model": int(args.samples_per_seed * 0.9),
            "reference_rows": len(reference_fit),
            "artifact_size_bytes": args.artifact.stat().st_size,
            "uncertainty_method": "mean target standard deviation across five independently generated-and-trained surrogates",
            "ood_method": "RMS standardized feature distance after log1p transformation of distance, irradiance, pressure, and density",
            "decision_policy": "defer when OOD or uncertainty exceeds the training-distribution q99 threshold, or when raw output has a serious physical violation",
        }
    )
    args.metadata.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
