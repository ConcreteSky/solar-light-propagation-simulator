"""Re-evaluate the saved model on the untouched synthetic test split."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ml.model_contract import MODEL_PATH  # noqa: E402
from training.ml_utils import (  # noqa: E402
    grouped_test_metrics,
    physical_consistency,
    regression_metrics,
    split_frame,
    timed_prediction_ms,
    xy,
)


def main() -> None:
    frame = pd.read_csv(PROJECT_ROOT / "data" / "training" / "light_training_data.csv")
    _, _, test = split_frame(frame)
    x_test, y_test = xy(test)
    bundle = joblib.load(MODEL_PATH)
    predictions = bundle["pipeline"].predict(x_test)
    result = {
        "model_name": bundle["model_name"],
        "model_version": bundle["model_version"],
        "samples": len(test),
        "metrics": regression_metrics(y_test, predictions),
        "physical_consistency": physical_consistency(predictions),
        "grouped_generalization": grouped_test_metrics(test, predictions),
        "inference_ms_per_sample": timed_prediction_ms(bundle["pipeline"], x_test),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
