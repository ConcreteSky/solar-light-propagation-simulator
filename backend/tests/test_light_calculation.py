import math
import unittest

from fastapi import HTTPException

from app.main import analyze
from app.services.catalog import load_catalog
from app.services.light_calculation_service import (
    PhysicsInput,
    analyze_destination,
    calculate_light_behavior,
)


class LightCalculationTests(unittest.TestCase):
    def test_atmospheric_examples_are_valid(self) -> None:
        for destination in ("mars", "venus", "titan"):
            with self.subTest(destination=destination):
                analysis = analyze_destination(destination)
                self.assertTrue(analysis.hasAtmosphere)
                self.assertTrue(analysis.validation.valid)

        self.assertEqual(analyze_destination("venus").results.dominantColor, "pale yellow")
        self.assertEqual(analyze_destination("titan").results.dominantColor, "orange")

    def test_airless_moon_uses_surface_model(self) -> None:
        analysis = analyze_destination("moon")
        self.assertFalse(analysis.hasAtmosphere)
        self.assertEqual(analysis.results.transmitted, 0.85)
        self.assertIn("surface", " ".join(analysis.validation.warnings).lower())

    def test_invalid_destination_is_a_clean_404(self) -> None:
        with self.assertRaises(HTTPException) as context:
            analyze("not-a-body")
        self.assertEqual(context.exception.status_code, 404)

    def test_missing_optional_atmosphere_data_is_partial(self) -> None:
        analysis = analyze_destination("jupiter")
        self.assertEqual(analysis.calculationStatus, "partial")
        self.assertTrue(
            any("pressure" in warning.lower() for warning in analysis.validation.warnings)
        )
        self.assertTrue(
            any("density" in warning.lower() for warning in analysis.validation.warnings)
        )

    def test_missing_optional_values_never_produce_nonfinite_outputs(self) -> None:
        output = calculate_light_behavior(
            PhysicsInput(
                distance_from_sun_km=149_597_870.7,
                solar_irradiance_w_m2=1366.1,
                has_atmosphere=True,
                surface_pressure_pa=None,
                atmospheric_density_kg_m3=None,
                composition={
                    gas: None for gas in ("CO2", "N2", "O2", "CH4", "H2", "He")
                },
            )
        )
        self.assertTrue(output.partial)
        for value in (
            output.transmitted,
            output.scattered,
            output.absorbed,
            output.relative_brightness,
        ):
            self.assertTrue(math.isfinite(value))

    def test_every_catalog_body_conserves_energy_and_stays_in_range(self) -> None:
        for body in load_catalog():
            with self.subTest(destination=body.id):
                analysis = analyze_destination(body.id)
                fractions = (
                    analysis.results.transmitted,
                    analysis.results.scattered,
                    analysis.results.absorbed,
                )
                self.assertAlmostEqual(sum(fractions), 1.0, places=6)
                for value in (*fractions, analysis.results.relativeBrightness):
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLessEqual(value, 1.0)
                    self.assertTrue(math.isfinite(value))
                self.assertTrue(analysis.validation.valid)


if __name__ == "__main__":
    unittest.main()
