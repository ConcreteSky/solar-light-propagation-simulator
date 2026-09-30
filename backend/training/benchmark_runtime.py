"""Repeatable, non-mutating runtime benchmark for the deployed service paths."""

from __future__ import annotations

import argparse
import json
import statistics
import time

from app.schemas.celestial_body import AtmosphericComposition
from app.schemas.light_analysis import AtmosphereScenario
from app.services.light_calculation_service import analyze_destination
from app.services.ml_prediction_service import load_model_bundle, predict_destination


SCENARIO = AtmosphereScenario(
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


def measure(operation, iterations: int) -> dict[str, float]:
    operation()
    samples = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        operation()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    return {
        "median_ms": round(statistics.median(samples), 4),
        "p95_ms": round(sorted(samples)[max(0, int(iterations * 0.95) - 1)], 4),
        "mean_ms": round(statistics.fmean(samples), 4),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=200)
    args = parser.parse_args()

    load_model_bundle.cache_clear()
    model_started = time.perf_counter_ns()
    load_model_bundle()
    model_load_ms = (time.perf_counter_ns() - model_started) / 1_000_000

    results = {
        "iterations": args.iterations,
        "model_cold_load_ms": round(model_load_ms, 4),
        "deterministic_earth": measure(
            lambda: analyze_destination("earth"), args.iterations
        ),
        "prediction_earth": measure(
            lambda: predict_destination("earth"), args.iterations
        ),
        "scenario_earth": measure(
            lambda: analyze_destination("earth", scenario=SCENARIO), args.iterations
        ),
        "deterministic_pluto_fallback": measure(
            lambda: analyze_destination("pluto"), args.iterations
        ),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
