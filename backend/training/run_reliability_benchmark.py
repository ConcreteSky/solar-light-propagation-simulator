"""Reproducible reliability/efficiency benchmark for the hybrid inference policy."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import time
import tracemalloc
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.stats import pearsonr, spearmanr
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.ml.model_contract import FEATURE_COLUMNS, LOG_FEATURES, MODEL_PATH, TARGET_COLUMNS
from app.services.light_calculation_service import PhysicsInput, calculate_light_behavior
from app.services.solar_input_service import ASTRONOMICAL_UNIT_KM, derive_irradiance
from training.generate_training_data import GASES, _density_from_state, _sample_composition


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "training" / "light_training_data.csv"
ARTIFACT = ROOT / "backend" / "models" / "reliability_ensemble.joblib"
DEFAULT_OUTPUT = ROOT / "research" / "results" / "reliability_efficiency"
SEED = 741


def physics_from_row(row: pd.Series) -> np.ndarray:
    output = calculate_light_behavior(PhysicsInput(
        distance_from_sun_km=float(row.distance_from_sun_km),
        solar_irradiance_w_m2=float(row.incoming_solar_irradiance_w_m2),
        has_atmosphere=bool(row.has_atmosphere),
        surface_pressure_pa=float(row.surface_pressure_pa),
        atmospheric_density_kg_m3=float(row.atmospheric_density_kg_m3),
        composition={gas: float(row[f"{gas.lower()}_fraction"]) for gas in GASES},
    ))
    return np.array([output.transmitted, output.scattered, output.absorbed, output.relative_brightness])


def shifted_frame(group: str, count: int, seed: int) -> pd.DataFrame:
    ranges = {
        "near_boundary": ((50, 70), (5e6, 1e7)),
        "moderate_shift": ((70, 100), (1e7, 2e7)),
        "severe_shift": ((100, 150), (2e7, 5e7)),
    }
    rng = np.random.default_rng(seed)
    distance_range, pressure_range = ranges[group]
    rows = []
    for _ in range(count):
        distance_au = float(10 ** rng.uniform(np.log10(distance_range[0]), np.log10(distance_range[1])))
        distance = distance_au * ASTRONOMICAL_UNIT_KM
        pressure = float(10 ** rng.uniform(np.log10(pressure_range[0]), np.log10(pressure_range[1])))
        fractions = _sample_composition(rng)
        density = _density_from_state(pressure, float(rng.uniform(70, 800)), fractions)
        row = {
            "distance_from_sun_km": distance,
            "incoming_solar_irradiance_w_m2": derive_irradiance(distance),
            "has_atmosphere": True,
            "surface_pressure_pa": pressure,
            "atmospheric_density_kg_m3": density,
            **{f"{gas.lower()}_fraction": float(value) for gas, value in zip(GASES, fractions)},
        }
        truth = physics_from_row(pd.Series(row))
        row.update(dict(zip(TARGET_COLUMNS, truth)))
        rows.append(row)
    return pd.DataFrame(rows)


def transformed_matrix(frame: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        np.log1p(frame[name].astype(float).to_numpy())
        if name in LOG_FEATURES else frame[name].astype(float).to_numpy()
        for name in FEATURE_COLUMNS
    ])


def ensemble_outputs(bundle: dict[str, object], frame: pd.DataFrame):
    predictions = np.stack([model.predict(frame[FEATURE_COLUMNS]) for model in bundle["models"]])
    mean = predictions.mean(axis=0)
    uncertainty_outputs = predictions.std(axis=0, ddof=1)
    uncertainty = uncertainty_outputs.mean(axis=1)
    matrix = transformed_matrix(frame)
    scores = np.sqrt(np.mean(((matrix - bundle["feature_mean"]) / bundle["feature_std"]) ** 2, axis=1))
    return mean, uncertainty_outputs, uncertainty, scores


def physical_flags(predictions: np.ndarray) -> tuple[np.ndarray, np.ndarray, list[str]]:
    fractions = predictions[:, :3]
    energy_error = np.abs(fractions.sum(axis=1) - 1)
    minor = (fractions < 0).any(axis=1) | (predictions > 1).any(axis=1) | (energy_error > 1e-6)
    serious = (
        (fractions < -0.1).any(axis=1)
        | (fractions > 1.1).any(axis=1)
        | (predictions[:, 3] < -0.1)
        | (predictions[:, 3] > 1.1)
        | (energy_error > 0.1)
        | ~np.isfinite(predictions).all(axis=1)
    )
    reasons = [
        ";".join(filter(None, (
            "negative_fraction" if (fractions[i] < 0).any() else "",
            "value_outside_unit_interval" if (predictions[i] > 1).any() else "",
            "energy_nonconservation" if energy_error[i] > 1e-6 else "",
        )))
        for i in range(len(predictions))
    ]
    return minor, serious, reasons


def metric_row(system: str, truth: np.ndarray, prediction: np.ndarray, runtime_ms: float, memory_bytes: int, violations: int) -> dict[str, object]:
    error = np.abs(prediction - truth)
    row: dict[str, object] = {
        "system": system,
        "mean_mae": float(error.mean()),
        "mean_rmse": float(np.sqrt(np.mean((prediction - truth) ** 2))),
        "maximum_absolute_error": float(error.max()),
        "runtime_ms_per_sample": runtime_ms,
        "memory_bytes": memory_bytes,
        "physical_violation_rows": violations,
    }
    for index, target in enumerate(TARGET_COLUMNS):
        row[f"{target}_mae"] = float(mean_absolute_error(truth[:, index], prediction[:, index]))
        row[f"{target}_rmse"] = float(np.sqrt(mean_squared_error(truth[:, index], prediction[:, index])))
        row[f"{target}_r2"] = float(r2_score(truth[:, index], prediction[:, index]))
    return row


def timed(operation, repeats: int) -> dict[str, object]:
    operation()
    values = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        operation()
        values.append((time.perf_counter_ns() - started) / 1e6)
    return {
        "samples": repeats,
        "mean_ms": statistics.fmean(values),
        "median_ms": statistics.median(values),
        "std_ms": statistics.stdev(values) if len(values) > 1 else 0.0,
        "minimum_ms": min(values),
        "maximum_ms": max(values),
    }


def timed_interleaved(operations: dict[str, object], repeats: int) -> dict[str, dict[str, object]]:
    """Warm every method equally, then rotate order to reduce thermal/order bias."""
    for operation in operations.values():
        for _ in range(3):
            operation()
    samples: dict[str, list[float]] = {name: [] for name in operations}
    names = list(operations)
    for repeat in range(repeats):
        order = names[repeat % len(names):] + names[:repeat % len(names)]
        for name in order:
            started = time.perf_counter_ns()
            operations[name]()
            samples[name].append((time.perf_counter_ns() - started) / 1e6)
    return {
        name: {
            "samples": repeats,
            "mean_ms": statistics.fmean(values),
            "median_ms": statistics.median(values),
            "std_ms": statistics.stdev(values) if len(values) > 1 else 0.0,
            "minimum_ms": min(values),
            "maximum_ms": max(values),
        }
        for name, values in samples.items()
    }


def peak_memory(operation) -> int:
    tracemalloc.start()
    operation()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def save_figure(fig, output: Path, name: str) -> None:
    fig.tight_layout()
    fig.savefig(output / f"{name}.png", dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shift-samples", type=int, default=1000)
    parser.add_argument("--timing-repeats", type=int, default=12)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    bundle = joblib.load(ARTIFACT)
    persisted = pd.read_csv(DATASET)
    test = persisted[persisted.split == "test"].copy()
    test["source_group"] = "in_distribution"
    frames = [test]
    for index, group in enumerate(("near_boundary", "moderate_shift", "severe_shift")):
        shifted = shifted_frame(group, args.shift_samples, 1741 + index)
        shifted["source_group"] = group
        frames.append(shifted)
    frame = pd.concat(frames, ignore_index=True)
    frame["operating_regime"] = np.select(
        [
            ~frame.has_atmosphere.astype(bool),
            frame.surface_pressure_pa < 100,
            frame.surface_pressure_pa > 200_000,
        ],
        ["airless", "thin_atmosphere", "dense_atmosphere"],
        default="ordinary_atmosphere",
    )
    truth = frame[TARGET_COLUMNS].to_numpy(float)
    prediction, uncertainty_outputs, uncertainty, ood = ensemble_outputs(bundle, frame)
    absolute = np.abs(prediction - truth)
    mean_error = absolute.mean(axis=1)
    minor, serious, violation_reasons = physical_flags(prediction)

    benchmark = frame[FEATURE_COLUMNS + ["source_group", "operating_regime"]].copy()
    for index, target in enumerate(TARGET_COLUMNS):
        benchmark[f"physics_{target}"] = truth[:, index]
        benchmark[f"ai_{target}"] = prediction[:, index]
        benchmark[f"absolute_error_{target}"] = absolute[:, index]
        benchmark[f"uncertainty_{target}"] = uncertainty_outputs[:, index]
    benchmark["mean_absolute_error"] = mean_error
    benchmark["uncertainty"] = uncertainty
    benchmark["ood_score"] = ood
    benchmark["uncertainty_bin"] = pd.qcut(
        uncertainty, 4, labels=["low", "moderate", "high", "very_high"]
    ).astype(str)
    benchmark["ood_bin"] = pd.qcut(
        ood, 4, labels=["low", "moderate", "high", "very_high"]
    ).astype(str)
    benchmark["raw_physical_violation"] = minor
    benchmark["serious_physical_violation"] = serious
    benchmark["physical_violation_reasons"] = violation_reasons
    benchmark.to_csv(args.output / "physics_ai_benchmark.csv", index=False)
    benchmark[["source_group", "operating_regime", "uncertainty", "uncertainty_bin", "mean_absolute_error"]].to_csv(args.output / "uncertainty_error_results.csv", index=False)
    benchmark[["source_group", "operating_regime", "ood_score", "ood_bin", "mean_absolute_error"]].to_csv(args.output / "ood_error_results.csv", index=False)
    pd.concat([
        benchmark.groupby("uncertainty_bin", observed=True).agg(
            samples=("mean_absolute_error", "size"),
            mean_score=("uncertainty", "mean"),
            mean_absolute_error=("mean_absolute_error", "mean"),
            p95_absolute_error=("mean_absolute_error", lambda values: values.quantile(.95)),
        ).reset_index(names="bin").assign(signal="uncertainty"),
        benchmark.groupby("ood_bin", observed=True).agg(
            samples=("mean_absolute_error", "size"),
            mean_score=("ood_score", "mean"),
            mean_absolute_error=("mean_absolute_error", "mean"),
            p95_absolute_error=("mean_absolute_error", lambda values: values.quantile(.95)),
        ).reset_index(names="bin").assign(signal="ood"),
    ], ignore_index=True).to_csv(args.output / "reliability_bins.csv", index=False)

    policies = [
        ("ai_only", float("inf"), float("inf")),
        ("ood_q99_uncertainty_q99", float(bundle["ood_q99"]), float(bundle["uncertainty_q99"])),
        ("ood_q99_uncertainty_q95", float(bundle["ood_q99"]), float(bundle["uncertainty_q95"])),
        ("ood_q95_uncertainty_q95", float(bundle["ood_q95"]), float(bundle["uncertainty_q95"])),
        ("physics_only", float("-inf"), float("-inf")),
    ]
    threshold_rows = []
    policy_masks = {}
    for name, ood_threshold, uncertainty_threshold in policies:
        fallback = serious | (ood > ood_threshold) | (uncertainty > uncertainty_threshold)
        policy_masks[name] = fallback
        hybrid_error = np.where(fallback, 0.0, mean_error)
        threshold_rows.append({
            "policy": name,
            "ood_threshold": ood_threshold,
            "uncertainty_threshold": uncertainty_threshold,
            "ai_usage_rate": float((~fallback).mean()),
            "fallback_rate": float(fallback.mean()),
            "mean_absolute_error": float(hybrid_error.mean()),
            "p95_absolute_error": float(np.quantile(hybrid_error, 0.95)),
            "severe_error_rate_gt_0_02": float((hybrid_error > 0.02).mean()),
        })
    thresholds = pd.DataFrame(threshold_rows)

    rows = [row for _, row in frame.iterrows()]
    physics_operation = lambda: np.stack([physics_from_row(row) for row in rows])
    ai_operation = lambda: ensemble_outputs(bundle, frame)[0]
    preprocessing_operation = lambda: [
        model.named_steps["preprocess"].transform(frame[FEATURE_COLUMNS])
        for model in bundle["models"]
    ]
    batch_operations = {
        "physics_only": physics_operation,
        "ensemble_preprocessing": preprocessing_operation,
        "ensemble_ai": ai_operation,
    }
    hybrid_policy_names = ("ood_q99_uncertainty_q99", "ood_q99_uncertainty_q95", "ood_q95_uncertainty_q95")
    for policy in hybrid_policy_names:
        fallback_rows = [rows[index] for index in np.flatnonzero(policy_masks[policy])]
        def hybrid_operation(items=fallback_rows):
            ensemble_outputs(bundle, frame)
            if items:
                np.stack([physics_from_row(row) for row in items])
        batch_operations[f"hybrid_{policy}"] = hybrid_operation
    batch_timings = timed_interleaved(batch_operations, args.timing_repeats)
    runtime_rows = [
        {
            "mode": "batch", "method": method, **values,
            "ms_per_sample": values["median_ms"] / len(frame),
            "throughput_samples_per_second": 1000 * len(frame) / values["median_ms"],
        }
        for method, values in batch_timings.items()
    ]
    one = frame.iloc[[0]]
    one_row = frame.iloc[0]
    for method, operation in (
        ("physics_only", lambda: physics_from_row(one_row)),
        ("ensemble_ai", lambda: ensemble_outputs(bundle, one)[0]),
    ):
        values = timed(operation, 100)
        runtime_rows.append({
            "mode": "single", "method": method, **values,
            "ms_per_sample": values["median_ms"],
            "throughput_samples_per_second": 1000 / values["median_ms"],
        })

    hybrid_timings = {
        policy: batch_timings[f"hybrid_{policy}"]["median_ms"] / len(frame)
        for policy in hybrid_policy_names
    }
    runtime = pd.DataFrame(runtime_rows)
    runtime.to_csv(args.output / "runtime_results.csv", index=False)

    model_load = timed(lambda: joblib.load(ARTIFACT), 5)
    memory = pd.DataFrame([
        {"operation": "serialized_ensemble_artifact", "bytes": ARTIFACT.stat().st_size, "measurement": "file_size"},
        {"operation": "physics_batch", "bytes": peak_memory(physics_operation), "measurement": "tracemalloc_peak"},
        {"operation": "ensemble_ai_batch", "bytes": peak_memory(ai_operation), "measurement": "tracemalloc_peak"},
        {"operation": "model_load_median", "bytes": None, "measurement": "milliseconds", "value": model_load["median_ms"]},
    ])
    memory.to_csv(args.output / "memory_results.csv", index=False)

    for row in threshold_rows:
        if row["policy"] in hybrid_timings:
            row["runtime_ms_per_sample"] = hybrid_timings[row["policy"]]
        elif row["policy"] == "ai_only":
            row["runtime_ms_per_sample"] = float(runtime[(runtime["mode"] == "batch") & (runtime["method"] == "ensemble_ai")].iloc[0].ms_per_sample)
        else:
            row["runtime_ms_per_sample"] = float(runtime[(runtime["mode"] == "batch") & (runtime["method"] == "physics_only")].iloc[0].ms_per_sample)
    thresholds = pd.DataFrame(threshold_rows)
    thresholds.to_csv(args.output / "fallback_threshold_results.csv", index=False)

    chosen = policy_masks["ood_q99_uncertainty_q99"]
    hybrid_prediction = prediction.copy()
    hybrid_prediction[chosen] = truth[chosen]
    physics_runtime = float(runtime[(runtime["mode"] == "batch") & (runtime["method"] == "physics_only")].iloc[0].ms_per_sample)
    ai_runtime = float(runtime[(runtime["mode"] == "batch") & (runtime["method"] == "ensemble_ai")].iloc[0].ms_per_sample)
    artifact_size = ARTIFACT.stat().st_size
    systems = pd.DataFrame([
        metric_row("Physics only", truth, truth, physics_runtime, 0, 0),
        metric_row("ML only", truth, prediction, ai_runtime, artifact_size, int(minor.sum())),
        metric_row("Hybrid q99", truth, hybrid_prediction, hybrid_timings["ood_q99_uncertainty_q99"], artifact_size, int((minor & ~chosen).sum())),
    ])
    systems["ai_usage_rate"] = [0.0, 1.0, float((~chosen).mean())]
    systems["fallback_rate"] = [1.0, 0.0, float(chosen.mean())]
    systems["throughput_samples_per_second"] = 1000 / systems["runtime_ms_per_sample"]
    systems["speedup_vs_physics"] = physics_runtime / systems["runtime_ms_per_sample"]
    systems.to_csv(args.output / "hybrid_system_results.csv", index=False)

    p95 = float(np.quantile(mean_error, 0.95))
    median_error = float(np.median(mean_error))
    median_uncertainty = float(np.median(uncertainty))
    failure_labels = np.full(len(frame), "", dtype=object)
    failure_labels[(mean_error >= p95) & (uncertainty <= median_uncertainty)] = "high_error_low_uncertainty"
    failure_labels[(mean_error >= p95) & (ood <= bundle["ood_q95"])] = "high_error_ood_miss"
    failure_labels[(ood > bundle["ood_q99"]) & (mean_error <= median_error)] = "unnecessary_ood_fallback"
    failure_labels[(uncertainty > bundle["uncertainty_q99"]) & (mean_error <= median_error)] = "overly_conservative_uncertainty"
    failure_labels[serious] = "serious_physical_violation"
    failures = benchmark.copy()
    failures["failure_type"] = failure_labels
    failures = failures[failures.failure_type != ""].sort_values("mean_absolute_error", ascending=False)
    failures.groupby("failure_type", group_keys=False).head(10).to_csv(args.output / "failure_cases.csv", index=False)

    saved = joblib.load(MODEL_PATH)["pipeline"]
    importance = permutation_importance(saved, test[FEATURE_COLUMNS], test[TARGET_COLUMNS].to_numpy(float), scoring="neg_mean_absolute_error", n_repeats=10, random_state=SEED, n_jobs=-1)
    pd.DataFrame({"feature": FEATURE_COLUMNS, "importance_mean": importance.importances_mean, "importance_std": importance.importances_std}).sort_values("importance_mean", ascending=False).to_csv(args.output / "feature_importance.csv", index=False)

    sensitivity_rows = []
    numeric_features = [name for name in FEATURE_COLUMNS if name != "has_atmosphere"]
    representative_indices = frame.groupby("source_group")["surface_pressure_pa"].apply(lambda values: (values - values.median()).abs().idxmin())
    for source_group, row_index in representative_indices.items():
        baseline = frame.loc[row_index, FEATURE_COLUMNS].copy()
        baseline_frame = pd.DataFrame([baseline], columns=FEATURE_COLUMNS)
        baseline_ai = saved.predict(baseline_frame)[0]
        baseline_physics = physics_from_row(baseline)
        for feature in numeric_features:
            value = float(baseline[feature])
            if value == 0:
                continue
            for direction, factor in (("minus_5_percent", 0.95), ("plus_5_percent", 1.05)):
                perturbed = baseline.copy()
                perturbed[feature] = value * factor
                perturbed_frame = pd.DataFrame([perturbed], columns=FEATURE_COLUMNS)
                ai_delta = saved.predict(perturbed_frame)[0] - baseline_ai
                physics_delta = physics_from_row(perturbed) - baseline_physics
                for target_index, target in enumerate(TARGET_COLUMNS):
                    sensitivity_rows.append({
                        "source_group": source_group,
                        "feature": feature,
                        "direction": direction,
                        "target": target,
                        "baseline_value": value,
                        "ai_output_delta": float(ai_delta[target_index]),
                        "physics_output_delta": float(physics_delta[target_index]),
                    })
    pd.DataFrame(sensitivity_rows).to_csv(args.output / "local_sensitivity.csv", index=False)

    summary = {
        "sample_count": len(frame),
        "group_counts": frame.source_group.value_counts().to_dict(),
        "uncertainty_error_pearson": float(pearsonr(uncertainty, mean_error).statistic),
        "uncertainty_error_spearman": float(spearmanr(uncertainty, mean_error).statistic),
        "ood_error_pearson": float(pearsonr(ood, mean_error).statistic),
        "ood_error_spearman": float(spearmanr(ood, mean_error).statistic),
        "chosen_policy": "ood_q99_uncertainty_q99",
        "thresholds": {"ood": float(bundle["ood_q99"]), "uncertainty": float(bundle["uncertainty_q99"])},
        "model_load_median_ms": model_load["median_ms"],
        "model_artifact_bytes": artifact_size,
        "notes": [
            "physics outputs are the synthetic teacher, so physics-only error is zero by construction",
            "ensemble spread is a ranking signal, not a calibrated confidence interval",
            "tracemalloc does not include every native-library allocation",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    environment = {
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
        "model_version": bundle["model_version"],
        "reliability_version": bundle["reliability_version"],
        "physics_version": "1.0.0",
        "dataset_version": "generator-1.0.0",
        "code_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "seeds": bundle["seeds"],
        "settings": {"shift_samples": args.shift_samples, "timing_repeats": args.timing_repeats},
    }
    (args.output / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    figures = args.output / "figures"
    figures.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.2, 4)); ax.scatter(truth[:, 0], prediction[:, 0], s=5, alpha=.2); ax.plot([0, 1], [0, 1], "k--"); ax.set(xlabel="Physics transmitted fraction", ylabel="AI transmitted fraction", title="Physics vs AI prediction")
    save_figure(fig, figures, "01_physics_vs_ai_prediction")
    fig, ax = plt.subplots(figsize=(6.2, 4)); rt = systems; ax.bar(rt.system, rt.runtime_ms_per_sample); ax.set(ylabel="Median ms per sample", title="Measured batch runtime")
    save_figure(fig, figures, "02_physics_vs_ai_runtime")
    fig, ax = plt.subplots(figsize=(6.2, 4)); ax.scatter(uncertainty, mean_error, s=5, alpha=.2); ax.set(xlabel="Ensemble uncertainty", ylabel="Mean absolute error", title="Uncertainty versus error")
    save_figure(fig, figures, "03_uncertainty_vs_error")
    fig, ax = plt.subplots(figsize=(6.2, 4)); ax.scatter(ood, mean_error, s=5, alpha=.2); ax.axvline(bundle["ood_q99"], color="r", ls="--"); ax.set(xlabel="OOD score", ylabel="Mean absolute error", title="OOD score versus error")
    save_figure(fig, figures, "04_ood_vs_error")
    display = thresholds[~thresholds.policy.isin(["ai_only", "physics_only"])]
    fig, ax = plt.subplots(figsize=(7, 4)); ax.plot(display.policy, display.mean_absolute_error, "o-"); ax.tick_params(axis="x", rotation=20); ax.set(ylabel="Hybrid mean absolute error", title="Fallback threshold versus accuracy")
    save_figure(fig, figures, "05_threshold_vs_accuracy")
    fig, ax = plt.subplots(figsize=(7, 4)); ax.plot(display.policy, display.runtime_ms_per_sample, "o-"); ax.tick_params(axis="x", rotation=20); ax.set(ylabel="Median ms per sample", title="Fallback threshold versus runtime")
    save_figure(fig, figures, "06_threshold_vs_runtime")
    fig, ax = plt.subplots(figsize=(6.2, 4)); ax.plot(thresholds.ai_usage_rate, thresholds.mean_absolute_error, "o"); ax.set(xlabel="AI usage rate", ylabel="System mean absolute error", title="AI usage versus system error")
    save_figure(fig, figures, "07_ai_usage_vs_error")
    fig, ax = plt.subplots(figsize=(6.2, 4)); ax.bar(systems.system, systems.mean_mae); ax.set(ylabel="Mean absolute error", title="Physics, ML, and hybrid comparison")
    save_figure(fig, figures, "08_system_comparison")
    reason_counts = pd.Series({"severe OOD": int((ood > bundle["ood_q99"]).sum()), "high uncertainty": int((uncertainty > bundle["uncertainty_q99"]).sum()), "serious physical": int(serious.sum())})
    fig, ax = plt.subplots(figsize=(6.2, 4)); ax.bar(reason_counts.index, reason_counts.values); ax.set(ylabel="Triggered rows", title="Fallback signal counts")
    save_figure(fig, figures, "09_fallback_reasons")
    failure_plot = failures.groupby("failure_type").mean_absolute_error.mean().sort_values()
    fig, ax = plt.subplots(figsize=(7, 4)); ax.barh(failure_plot.index.str.replace("_", " "), failure_plot.values); ax.set(xlabel="Mean absolute error", title="Representative failure categories")
    save_figure(fig, figures, "10_failure_cases")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
