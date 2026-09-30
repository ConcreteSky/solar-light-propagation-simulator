import math
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.main import predict
from app.ml.model_contract import FEATURE_COLUMNS
from app.services.catalog import load_catalog
from app.services.ml_prediction_service import (
    ModelPredictionError,
    clear_prediction_cache,
    load_model_bundle,
    prediction_cache_info,
    predict_destination,
    predict_numeric,
    validate_prediction,
)


class MachineLearningPredictionTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_prediction_cache()

    def test_saved_model_loads_with_expected_contract(self) -> None:
        bundle = load_model_bundle()
        self.assertEqual(bundle["feature_columns"], FEATURE_COLUMNS)
        self.assertEqual(bundle["model_name"], "hist_gradient_boosting")

    def test_atmospheric_destination_uses_machine_learning(self) -> None:
        result = predict_destination("earth")
        self.assertEqual(result.method, "machine_learning")
        self.assertFalse(result.validation.fallbackUsed)
        self.assertTrue(result.validation.valid)

    def test_airless_destination_uses_machine_learning(self) -> None:
        result = predict_destination("moon")
        self.assertEqual(result.method, "machine_learning")
        self.assertFalse(result.hasAtmosphere)
        self.assertAlmostEqual(
            result.results.transmitted
            + result.results.scattered
            + result.results.absorbed,
            1.0,
            places=6,
        )

    def test_missing_scientific_data_uses_deterministic_fallback(self) -> None:
        result = predict_destination("jupiter")
        self.assertEqual(result.method, "deterministic_fallback")
        self.assertTrue(result.validation.fallbackUsed)
        self.assertIn("missing required model features", " ".join(result.validation.warnings).lower())

    def test_missing_model_uses_deterministic_fallback(self) -> None:
        with patch(
            "app.services.ml_prediction_service.load_model_bundle",
            side_effect=FileNotFoundError("test model missing"),
        ):
            result = predict_destination("earth")
        self.assertEqual(result.method, "deterministic_fallback")
        self.assertIn("test model missing", " ".join(result.validation.warnings))

    def test_seriously_invalid_prediction_uses_fallback(self) -> None:
        with patch(
            "app.services.ml_prediction_service.predict_numeric",
            return_value=np.array([[2.0, -1.0, 0.0, float("nan")]]),
        ):
            result = predict_destination("earth")
        self.assertEqual(result.method, "deterministic_fallback")

    def test_incorrect_feature_dimensions_are_rejected(self) -> None:
        bundle = load_model_bundle()
        bad_frame = pd.DataFrame([[0.0] * 10], columns=FEATURE_COLUMNS[:10])
        with self.assertRaises(ValueError):
            predict_numeric(bundle, bad_frame)

    def test_validator_rejects_serious_conservation_violation(self) -> None:
        with self.assertRaises(ModelPredictionError):
            validate_prediction(np.array([0.8, 0.8, 0.2, 0.5]))

    def test_every_destination_returns_safe_compatible_output(self) -> None:
        for body in load_catalog():
            with self.subTest(destination=body.id):
                result = predict_destination(body.id)
                values = (
                    result.results.transmitted,
                    result.results.scattered,
                    result.results.absorbed,
                    result.results.relativeBrightness,
                )
                self.assertTrue(all(math.isfinite(value) for value in values))
                self.assertTrue(all(0 <= value <= 1 for value in values))
                self.assertAlmostEqual(sum(values[:3]), 1.0, places=6)
                self.assertTrue(result.validation.valid)
                payload = result.model_dump(mode="json")
                self.assertIn(payload["method"], ("machine_learning", "deterministic_fallback"))
                self.assertIn("baselineComparison", payload)

    def test_invalid_destination_is_a_clean_404(self) -> None:
        with self.assertRaises(HTTPException) as context:
            predict("not-a-body")
        self.assertEqual(context.exception.status_code, 404)

    def test_identical_prediction_is_cached(self) -> None:
        first = predict_destination("earth")
        second = predict_destination("earth")
        self.assertIs(first, second)
        self.assertEqual(prediction_cache_info().hits, 1)


if __name__ == "__main__":
    unittest.main()
