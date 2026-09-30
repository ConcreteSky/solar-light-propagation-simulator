import math
import unittest
from datetime import datetime, timedelta, timezone

from app.services.body_data_service import get_body, get_body_index
from app.services.light_calculation_service import analyze_destination
from app.services.orbital_service import (
    SPEED_OF_LIGHT_KM_S,
    SUN_RADIUS_KM,
    calculate_orbital_state,
    load_orbital_elements,
)


J2000 = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)


class OrbitalDynamicsTests(unittest.TestCase):
    def test_planet_periods_have_the_correct_relative_order(self) -> None:
        elements = load_orbital_elements()
        ordered = [elements[name]["period_days"] for name in (
            "mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune"
        )]
        self.assertEqual(ordered, sorted(ordered))

    def test_one_orbital_period_returns_to_the_same_position(self) -> None:
        body = get_body("mars")
        index = get_body_index()
        period = float(load_orbital_elements()["mars"]["period_days"])
        first = calculate_orbital_state(body, index, J2000)
        second = calculate_orbital_state(body, index, J2000 + timedelta(days=period))
        self.assertAlmostEqual(first.x_km, second.x_km, places=3)
        self.assertAlmostEqual(first.z_km, second.z_km, places=3)

    def test_keplerian_distance_reaches_periapsis_and_apoapsis(self) -> None:
        body = get_body("earth")
        element = load_orbital_elements()["earth"]
        period = float(element["period_days"])
        days_to_periapsis = ((360 - float(element["mean_anomaly_deg"])) % 360) / 360 * period
        periapsis = calculate_orbital_state(body, get_body_index(), J2000 + timedelta(days=days_to_periapsis))
        apoapsis = calculate_orbital_state(body, get_body_index(), J2000 + timedelta(days=days_to_periapsis + period / 2))
        semimajor = body.orbit.semimajor_axis_km
        eccentricity = body.orbit.eccentricity
        self.assertAlmostEqual(periapsis.distance_from_sun_km, semimajor * (1 - eccentricity), delta=2)
        self.assertAlmostEqual(apoapsis.distance_from_sun_km, semimajor * (1 + eccentricity), delta=2)

    def test_moon_position_is_parent_position_plus_parent_relative_orbit(self) -> None:
        index = get_body_index()
        moon = calculate_orbital_state(get_body("moon"), index, J2000)
        earth = calculate_orbital_state(get_body("earth"), index, J2000)
        parent_relative_distance = math.hypot(moon.x_km - earth.x_km, moon.z_km - earth.z_km)
        expected = get_body("moon").orbit.semimajor_axis_km * (
            1 - get_body("moon").orbit.eccentricity * math.cos(
                math.radians(load_orbital_elements()["moon"]["mean_anomaly_deg"])
            )
        )
        self.assertAlmostEqual(parent_relative_distance, expected, delta=25_000)

    def test_dynamic_measurements_use_physical_distance(self) -> None:
        analysis = analyze_destination("earth", J2000)
        astronomy = analysis.astronomy
        self.assertIsNotNone(astronomy)
        self.assertAlmostEqual(
            astronomy.lightTravelTimeSeconds,
            astronomy.distanceFromSunKm / SPEED_OF_LIGHT_KM_S,
            places=5,
        )
        expected_diameter = math.degrees(2 * math.atan(SUN_RADIUS_KM / astronomy.distanceFromSunKm))
        self.assertAlmostEqual(astronomy.apparentSolarAngularDiameterDeg, expected_diameter, places=8)

    def test_irradiance_obeys_inverse_square_law(self) -> None:
        near = analyze_destination("earth", datetime(2026, 1, 3, tzinfo=timezone.utc)).astronomy
        far = analyze_destination("earth", datetime(2026, 7, 5, tzinfo=timezone.utc)).astronomy
        expected_ratio = (far.distanceFromSunKm / near.distanceFromSunKm) ** 2
        self.assertAlmostEqual(near.solarIrradianceWm2 / far.solarIrradianceWm2, expected_ratio, places=7)

    def test_atmospheric_interaction_fractions_do_not_change_with_orbit(self) -> None:
        first = analyze_destination("earth", datetime(2026, 1, 3, tzinfo=timezone.utc))
        second = analyze_destination("earth", datetime(2026, 7, 5, tzinfo=timezone.utc))
        self.assertEqual(first.results.transmitted, second.results.transmitted)
        self.assertEqual(first.results.scattered, second.results.scattered)
        self.assertEqual(first.results.absorbed, second.results.absorbed)

    def test_missing_orbital_data_fails_explicitly(self) -> None:
        body = get_body("earth").model_copy(update={"id": "missing-orbit"})
        with self.assertRaisesRegex(ValueError, "No orbital elements"):
            calculate_orbital_state(body, get_body_index(), J2000)


if __name__ == "__main__":
    unittest.main()
