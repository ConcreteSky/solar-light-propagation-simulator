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
from app.schemas.celestial_body import AtmosphericComposition
from app.schemas.light_analysis import AtmosphereScenario, ModeledLightColor
from pydantic import ValidationError


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
        self.assertEqual(analysis.results.scatteredLightColor.label, "neutral")
        self.assertEqual(analysis.results.scatteredLightColor.confidence, "fallback")

    def test_scattered_color_is_independent_of_surface_color(self) -> None:
        earth = analyze_destination("earth")
        mars = analyze_destination("mars")
        self.assertEqual(earth.results.scatteredLightColor.label, "blue")
        self.assertEqual(mars.results.scatteredLightColor.label, "blue")
        self.assertNotEqual(earth.destination, mars.destination)

    def test_supported_atmospheres_produce_distinct_scattered_colors(self) -> None:
        earth = analyze_destination("earth")
        uranus = analyze_destination("uranus")
        titan = analyze_destination("titan")
        self.assertEqual(earth.results.scatteredLightColor.label, "blue")
        self.assertEqual(uranus.results.scatteredLightColor.label, "cyan")
        self.assertEqual(titan.results.scatteredLightColor.label, "orange")

    def test_unknown_composition_uses_neutral_scattered_color(self) -> None:
        pluto = analyze_destination("pluto")
        self.assertEqual(pluto.results.scatteredLightColor.label, "neutral")
        self.assertEqual(pluto.results.scatteredLightColor.confidence, "fallback")

    def test_scenario_composition_recalculates_scattered_color(self) -> None:
        baseline = analyze_destination("earth")
        scenario = AtmosphereScenario(
            hasAtmosphere=True,
            surfacePressurePa=101_325,
            atmosphericDensityKgM3=1.2,
            composition=AtmosphericComposition(
                CO2=0,
                N2=0,
                O2=0,
                CH4=0.02,
                H2=0.85,
                He=0.13,
            ),
        )
        changed = analyze_destination("earth", scenario=scenario)
        self.assertEqual(baseline.results.scatteredLightColor.label, "blue")
        self.assertEqual(changed.results.scatteredLightColor.label, "cyan")

    def test_invalid_rgb_channels_are_rejected_by_response_schema(self) -> None:
        with self.assertRaises(ValidationError):
            ModeledLightColor(
                label="neutral",
                rgb=(999, 0, 0),
                spectralBand=None,
                confidence="fallback",
                basis="neutral-fallback",
            )

    def test_existing_spectrum_and_fraction_regression_is_unchanged(self) -> None:
        earth = analyze_destination("earth")
        self.assertEqual(earth.inputs.solarSpectrumVisibleFraction, 0.700153)
        self.assertEqual(
            (earth.results.transmitted, earth.results.scattered, earth.results.absorbed),
            (0.834967, 0.140087, 0.024946),
        )

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
