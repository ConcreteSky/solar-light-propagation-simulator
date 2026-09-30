"""Generate deterministic synthetic inputs and labels from the physics service."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.light_calculation_service import (  # noqa: E402
    PhysicsInput,
    calculate_light_behavior,
)
from app.services.solar_input_service import (  # noqa: E402
    ASTRONOMICAL_UNIT_KM,
    derive_irradiance,
)

GENERATOR_VERSION = "1.0.0"
DEFAULT_SEED = 741
DEFAULT_SAMPLES = 10_000
GASES = ("CO2", "N2", "O2", "CH4", "H2", "He")
COLOR_CODES = {
    "white": 0,
    "yellow": 1,
    "orange": 2,
    "red": 3,
    "blue": 4,
    "pale blue": 5,
    "pale yellow": 6,
    "dim white": 7,
    "gray-white": 8,
}

INPUT_COLUMNS = [
    "distance_from_sun_km",
    "incoming_solar_irradiance_w_m2",
    "has_atmosphere",
    "surface_pressure_pa",
    "atmospheric_density_kg_m3",
    "co2_fraction",
    "n2_fraction",
    "o2_fraction",
    "ch4_fraction",
    "h2_fraction",
    "he_fraction",
]
OUTPUT_COLUMNS = [
    "transmitted_light_fraction",
    "scattered_light_fraction",
    "absorbed_light_fraction",
    "relative_brightness",
    "dominant_color",
    "dominant_color_code",
]
METADATA_COLUMNS = ["generator_version", "random_seed", "split"]
TRAINING_COLUMNS = METADATA_COLUMNS + INPUT_COLUMNS + OUTPUT_COLUMNS

COMPOSITION_ARCHETYPES = np.array(
    [
        [3.0, 5.0, 2.0, 0.2, 0.1, 0.1],
        [12.0, 1.0, 0.1, 0.1, 0.1, 0.1],
        [0.1, 12.0, 0.1, 1.0, 0.1, 0.1],
        [0.1, 0.1, 0.1, 0.4, 12.0, 3.0],
        [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
    ]
)


def _sample_pressure(rng: np.random.Generator) -> float:
    regime = rng.choice(4, p=[0.20, 0.25, 0.35, 0.20])
    bounds = (
        (0.01, 100.0),
        (100.0, 20_000.0),
        (20_000.0, 200_000.0),
        (200_000.0, 10_000_000.0),
    )
    low, high = bounds[int(regime)]
    return float(10 ** rng.uniform(np.log10(low), np.log10(high)))


def _sample_composition(rng: np.random.Generator) -> np.ndarray:
    alpha = COMPOSITION_ARCHETYPES[int(rng.integers(len(COMPOSITION_ARCHETYPES)))]
    return rng.dirichlet(alpha)


def _density_from_state(
    pressure_pa: float, temperature_k: float, fractions: np.ndarray
) -> float:
    molar_masses_kg_mol = np.array(
        [0.04401, 0.028014, 0.031998, 0.016043, 0.002016, 0.004003]
    )
    mean_molar_mass = float(np.dot(fractions, molar_masses_kg_mol))
    specific_gas_constant = 8.314462618 / mean_molar_mass
    return min(100.0, pressure_pa / (specific_gas_constant * temperature_k))


def generate_training_frame(sample_count: int, seed: int) -> pd.DataFrame:
    if not 5_000 <= sample_count <= 20_000:
        raise ValueError("sample_count must be between 5,000 and 20,000.")

    rng = np.random.default_rng(seed)
    rows: list[dict[str, object]] = []
    for index in range(sample_count):
        distance_au = float(10 ** rng.uniform(np.log10(0.3), np.log10(70.0)))
        distance_km = distance_au * ASTRONOMICAL_UNIT_KM
        irradiance = derive_irradiance(distance_km)
        has_atmosphere = bool(rng.random() < 0.72)

        if has_atmosphere:
            fractions = _sample_composition(rng)
            pressure = _sample_pressure(rng)
            temperature = float(rng.uniform(70.0, 800.0))
            density = _density_from_state(pressure, temperature, fractions)
        else:
            fractions = np.zeros(len(GASES))
            pressure = 0.0
            density = 0.0

        composition = {gas: float(value) for gas, value in zip(GASES, fractions)}
        result = calculate_light_behavior(
            PhysicsInput(
                distance_from_sun_km=distance_km,
                solar_irradiance_w_m2=irradiance,
                has_atmosphere=has_atmosphere,
                surface_pressure_pa=pressure,
                atmospheric_density_kg_m3=density,
                composition=composition,
            )
        )
        split_roll = index % 10
        split = "train" if split_roll < 8 else "validation" if split_roll == 8 else "test"
        rows.append(
            {
                "generator_version": GENERATOR_VERSION,
                "random_seed": seed,
                "split": split,
                "distance_from_sun_km": distance_km,
                "incoming_solar_irradiance_w_m2": irradiance,
                "has_atmosphere": has_atmosphere,
                "surface_pressure_pa": pressure,
                "atmospheric_density_kg_m3": density,
                "co2_fraction": composition["CO2"],
                "n2_fraction": composition["N2"],
                "o2_fraction": composition["O2"],
                "ch4_fraction": composition["CH4"],
                "h2_fraction": composition["H2"],
                "he_fraction": composition["He"],
                "transmitted_light_fraction": result.transmitted,
                "scattered_light_fraction": result.scattered,
                "absorbed_light_fraction": result.absorbed,
                "relative_brightness": result.relative_brightness,
                "dominant_color": result.dominant_color,
                "dominant_color_code": COLOR_CODES[result.dominant_color],
            }
        )
    return pd.DataFrame(rows, columns=TRAINING_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic light-model samples.")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "data"
        / "training"
        / "light_training_data.csv",
    )
    args = parser.parse_args()
    frame = generate_training_frame(args.samples, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False, float_format="%.10g")
    print(f"Wrote {len(frame):,} deterministic samples to {args.output}")


if __name__ == "__main__":
    main()
