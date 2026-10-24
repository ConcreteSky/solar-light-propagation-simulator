import math
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.main import predict, predict_hypothetical_scenario
from app.ml.model_contract import FEATURE_COLUMNS, scientific_feature_frame
from app.schemas.celestial_body import AtmosphericComposition
from app.schemas.light_analysis import AtmosphereScenario
from app.services.catalog import load_catalog
from app.services.ml_prediction_service import (
    ModelPredictionError,
    clear_prediction_cache,
    load_model_bundle,
    prediction_cache_info,
    predict_destination,
    predict_scenario,
    predict_numeric,
    validate_prediction,
)
from app.services.reliability_service import ReliabilityDecision, assess_reliability


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
        self.assertEqual(result.resultSource, "ML surrogate")
        self.assertEqual(result.reliability.decision, "use_ai")
        self.assertEqual(result.reliability.classification, "reliable")
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
        decision = ReliabilityDecision(
            mean_prediction=np.array([2.0, -1.0, 0.0, float("nan")]),
            uncertainty_per_output=np.zeros(4),
            uncertainty_score=0.0,
            uncertainty_threshold=0.01,
            ood_score=0.5,
            ood_q95=1.4,
            ood_q99=1.7,
            ood_classification="in_distribution",
            classification="unreliable",
            decision="defer_to_physics",
            fallback_reason="serious_physical_violation",
            physical_violations=("non_finite_or_invalid_shape",),
        )
        with patch(
            "app.services.ml_prediction_service.assess_reliability",
            return_value=decision,
        ):
            result = predict_destination("earth")
        self.assertEqual(result.method, "deterministic_fallback")
        self.assertIn("non_finite_or_invalid_shape", result.reliability.physicalViolations)

    def test_severe_ood_scenario_defers_to_physics(self) -> None:
        scenario = AtmosphereScenario(
            hasAtmosphere=True,
            surfacePressurePa=1_000_000_000,
            atmosphericDensityKgM3=1_000_000,
            composition=AtmosphericComposition(
                CO2=0.05, N2=0.05, O2=0, CH4=0.1, H2=0.65, He=0.15
            ),
        )
        result = predict_scenario("earth", scenario)
        self.assertEqual(result.method, "deterministic_fallback")
        self.assertEqual(result.resultSource, "Deterministic fallback")
        self.assertEqual(result.reliability.decision, "defer_to_physics")
        self.assertEqual(result.reliability.ood.classification, "severe")

    def test_scenario_endpoint_uses_hybrid_pipeline(self) -> None:
        scenario = AtmosphereScenario(
            hasAtmosphere=True,
            surfacePressurePa=101_325,
            atmosphericDensityKgM3=1.225,
            composition=AtmosphericComposition(
                CO2=0.0004, N2=0.7808, O2=0.2095, CH4=0.000002, H2=0, He=0
            ),
        )
        result = predict_hypothetical_scenario("earth", scenario)
        self.assertIsNotNone(result.reliability.uncertainty)
        self.assertIsNotNone(result.reliability.ood)
        self.assertIsNotNone(result.aiResults)
        self.assertIsNotNone(result.deterministicResults)

    def test_scenario_cache_keys_include_reliability_inputs(self) -> None:
        base = dict(
            hasAtmosphere=True,
            atmosphericDensityKgM3=1.225,
            composition=AtmosphericComposition(
                CO2=0.0004, N2=0.7808, O2=0.2095, CH4=0.000002, H2=0, He=0
            ),
        )
        ordinary = AtmosphereScenario(surfacePressurePa=101_325, **base)
        changed = AtmosphereScenario(surfacePressurePa=120_000, **base)
        with patch(
            "app.services.ml_prediction_service.assess_reliability",
            wraps=assess_reliability,
        ) as reliability_check:
            first = predict_scenario("earth", ordinary)
            repeated = predict_scenario("earth", ordinary)
            different = predict_scenario("earth", changed)

        self.assertIs(first, repeated)
        self.assertIsNot(first, different)
        self.assertEqual(reliability_check.call_count, 2)
        self.assertEqual(prediction_cache_info()["scenario"].hits, 1)

    def test_scenario_feature_preparation_normalizes_gas_fractions(self) -> None:
        frame = scientific_feature_frame(
            distance_from_sun_km=149_597_870.7,
            solar_irradiance_w_m2=1361,
            has_atmosphere=True,
            surface_pressure_pa=101_325,
            atmospheric_density_kg_m3=1.225,
            composition={"CO2": 2.0, "N2": 6.0, "O2": 2.0, "CH4": 0, "H2": 0, "He": 0},
        )
        self.assertAlmostEqual(
            frame[["co2_fraction", "n2_fraction", "o2_fraction", "ch4_fraction", "h2_fraction", "he_fraction"]]
            .iloc[0]
            .sum(),
            1.0,
        )

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
        self.assertEqual(prediction_cache_info()["real"].hits, 1)


if __name__ == "__main__":
    unittest.main()
