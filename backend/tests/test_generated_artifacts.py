import csv
import json
import math
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = PROJECT_ROOT / "data" / "training" / "light_training_data.csv"
BENCHMARK_PATH = PROJECT_ROOT / "data" / "benchmark" / "real_body_benchmarks.json"


class GeneratedArtifactTests(unittest.TestCase):
    def test_training_dataset_invariants(self) -> None:
        with DATASET_PATH.open(encoding="utf-8", newline="") as dataset_file:
            rows = list(csv.DictReader(dataset_file))

        self.assertEqual(len(rows), 10_000)
        self.assertEqual(
            {split: sum(row["split"] == split for row in rows) for split in ("train", "validation", "test")},
            {"train": 8_000, "validation": 1_000, "test": 1_000},
        )
        gas_columns = (
            "co2_fraction",
            "n2_fraction",
            "o2_fraction",
            "ch4_fraction",
            "h2_fraction",
            "he_fraction",
        )
        for row in rows:
            energy_sum = sum(
                float(row[column])
                for column in (
                    "transmitted_light_fraction",
                    "scattered_light_fraction",
                    "absorbed_light_fraction",
                )
            )
            self.assertTrue(math.isclose(energy_sum, 1.0, abs_tol=1e-6))
            self.assertGreaterEqual(float(row["relative_brightness"]), 0.0)
            self.assertLessEqual(float(row["relative_brightness"]), 1.0)
            if row["has_atmosphere"] == "True":
                self.assertTrue(
                    math.isclose(
                        sum(float(row[column]) for column in gas_columns),
                        1.0,
                        abs_tol=1e-8,
                    )
                )
            else:
                self.assertEqual(float(row["surface_pressure_pa"]), 0.0)
                self.assertEqual(float(row["atmospheric_density_kg_m3"]), 0.0)
                self.assertEqual(sum(float(row[column]) for column in gas_columns), 0.0)

    def test_real_body_benchmarks_cover_the_catalog(self) -> None:
        with BENCHMARK_PATH.open(encoding="utf-8") as benchmark_file:
            payload = json.load(benchmark_file)
        with (PROJECT_ROOT / "data" / "celestialBodies.json").open(
            encoding="utf-8"
        ) as catalog_file:
            catalog = json.load(catalog_file)

        expected_ids = {body["id"] for body in catalog["bodies"]}
        benchmark_ids = {row["destination"] for row in payload["benchmarks"]}
        self.assertEqual(payload["benchmarkCount"], len(expected_ids))
        self.assertEqual(benchmark_ids, expected_ids)
        self.assertTrue(all(row["validation"]["valid"] for row in payload["benchmarks"]))


if __name__ == "__main__":
    unittest.main()
