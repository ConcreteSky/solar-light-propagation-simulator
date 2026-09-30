"""Write deterministic analysis results for every real catalog destination."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.catalog import load_catalog  # noqa: E402
from app.services.light_calculation_service import analyze_destination  # noqa: E402


def build_benchmarks() -> dict[str, object]:
    bodies = load_catalog()
    return {
        "schemaVersion": "1.0.0",
        "physicsModelVersion": "1.0.0",
        "description": "Deterministic educational baseline; real bodies are validation cases, not synthetic training rows.",
        "benchmarkCount": len(bodies),
        "benchmarks": [
            analyze_destination(body.id).model_dump(mode="json") for body in bodies
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate real-body light benchmarks.")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2]
        / "data"
        / "benchmark"
        / "real_body_benchmarks.json",
    )
    args = parser.parse_args()
    payload = build_benchmarks()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=2, ensure_ascii=False)
        output_file.write("\n")
    print(f"Wrote {payload['benchmarkCount']} real-body benchmarks to {args.output}")


if __name__ == "__main__":
    main()
