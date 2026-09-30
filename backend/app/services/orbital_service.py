from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from ..schemas.celestial_body import CelestialBody

ORBITAL_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "orbitalElements.v1.json"
SPEED_OF_LIGHT_KM_S = 299_792.458
SUN_RADIUS_KM = 695_700.0


@dataclass(frozen=True)
class OrbitalState:
    simulated_time: datetime
    x_km: float
    z_km: float
    distance_from_sun_km: float
    orbital_angle_deg: float
    light_travel_time_seconds: float
    apparent_solar_angular_diameter_deg: float
    period_days: float
    reference_epoch_jd: float
    phase_status: str
    source: str


@lru_cache(maxsize=1)
def load_orbital_elements() -> dict[str, dict[str, float | str]]:
    with ORBITAL_DATA_PATH.open(encoding="utf-8") as data_file:
        payload = json.load(data_file)
    return payload["bodies"]


def datetime_to_julian_day(value: datetime) -> float:
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).timestamp() / 86_400.0 + 2_440_587.5


def solve_kepler(mean_anomaly_rad: float, eccentricity: float) -> float:
    mean_anomaly = mean_anomaly_rad % math.tau
    eccentric_anomaly = math.pi if eccentricity >= 0.8 else mean_anomaly
    for _ in range(20):
        delta = (eccentric_anomaly - eccentricity * math.sin(eccentric_anomaly) - mean_anomaly) / (
            1 - eccentricity * math.cos(eccentric_anomaly)
        )
        eccentric_anomaly -= delta
        if abs(delta) < 1e-12:
            break
    return eccentric_anomaly


def _relative_position(body: CelestialBody, simulated_time: datetime) -> tuple[float, float, float, dict]:
    element = load_orbital_elements().get(body.id)
    if element is None:
        raise ValueError(f"No orbital elements are available for {body.id}.")
    semimajor_axis = body.orbit.semimajor_axis_km
    if not semimajor_axis or semimajor_axis <= 0:
        raise ValueError(f"No positive semimajor axis is available for {body.id}.")
    period_days = float(element["period_days"])
    epoch_jd = float(element["epoch_jd"])
    direction = float(element.get("direction", 1))
    elapsed_days = datetime_to_julian_day(simulated_time) - epoch_jd
    mean_anomaly = math.radians(float(element["mean_anomaly_deg"])) + direction * math.tau * elapsed_days / period_days
    eccentricity = min(max(float(body.orbit.eccentricity or 0), 0.0), 0.95)
    eccentric_anomaly = solve_kepler(mean_anomaly, eccentricity)
    x_km = semimajor_axis * (math.cos(eccentric_anomaly) - eccentricity)
    z_km = semimajor_axis * math.sqrt(1 - eccentricity**2) * math.sin(eccentric_anomaly)
    true_anomaly = math.degrees(math.atan2(z_km, x_km)) % 360
    return x_km, z_km, true_anomaly, element


def calculate_orbital_state(
    body: CelestialBody,
    body_index: dict[str, CelestialBody],
    simulated_time: datetime,
) -> OrbitalState:
    utc_time = (
        simulated_time.replace(tzinfo=timezone.utc)
        if simulated_time.tzinfo is None
        else simulated_time.astimezone(timezone.utc)
    )
    relative_x, relative_z, angle, element = _relative_position(body, utc_time)
    if body.orbit.reference == "parent":
        parent = body_index.get(body.parent)
        if parent is None:
            raise ValueError(f"No parent body is available for {body.id}.")
        parent_x, parent_z, _, _ = _relative_position(parent, utc_time)
        x_km = parent_x + relative_x
        z_km = parent_z + relative_z
    else:
        x_km, z_km = relative_x, relative_z

    distance = math.hypot(x_km, z_km)
    angular_diameter = math.degrees(2 * math.atan(SUN_RADIUS_KM / distance))
    return OrbitalState(
        simulated_time=utc_time,
        x_km=x_km,
        z_km=z_km,
        distance_from_sun_km=distance,
        orbital_angle_deg=angle,
        light_travel_time_seconds=distance / SPEED_OF_LIGHT_KM_S,
        apparent_solar_angular_diameter_deg=angular_diameter,
        period_days=float(element["period_days"]),
        reference_epoch_jd=float(element["epoch_jd"]),
        phase_status=str(element["phase_status"]),
        source=str(element["source"]),
    )
