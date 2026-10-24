# Reliable and Efficient AI for Scientific Simulation

## Research question

Can a lightweight machine-learning surrogate provide useful computational efficiency for scientific simulation while retaining acceptable accuracy and automatically deferring to a deterministic model when predictions become unreliable?

The Solar System and atmospheric-light model provide a controlled scientific environment for testing three connected properties: efficiency, reliability, and automatic fallback. The deterministic model remains the synthetic teacher and final safety reference.

## Hybrid architecture

```text
Astronomical and atmospheric input
                ↓
Deterministic feature preparation
                ↓
Five-model surrogate ensemble
                ↓
Ensemble spread + OOD distance + raw physical checks
                ↓
Central reliability decision
          ↙ reliable   unreliable ↘
   ML surrogate result      deterministic physics result
```

Every eligible real-body or Scenario Mode request passes through `reliability_service.py`. Missing features or model files, severe OOD, high ensemble spread, and serious raw physical violations all produce an explicit deterministic fallback. The API returns the AI result when valid, the deterministic result, their absolute deltas, the reliability signals, the final method, and any fallback reason.

## Uncertainty

Uncertainty is the mean target-wise sample standard deviation across five independently generated-and-trained HistGradientBoosting surrogates using seeds 741–745. It is an empirical disagreement score, not a calibrated probability or confidence interval.

The runtime threshold is the q99 uncertainty observed on the untouched validation split: `0.008112074`. The q95 value, `0.005107275`, is retained for the threshold experiment.

Across the 4,000-case benchmark, uncertainty had Pearson correlation `0.259` and Spearman rank correlation `0.462` with mean absolute prediction error. It is useful as a ranking signal but substantially weaker than the OOD score. High-error/low-uncertainty failures are preserved in `failure_cases.csv`.

## OOD detection

Distance, irradiance, pressure, and density are transformed with `log1p`; the remaining features stay linear. Each feature is standardized using the 9,000-row training-plus-validation reference set. The scalar OOD score is the root mean square standardized distance across all 11 inputs.

- In distribution: score ≤ q95 (`1.472961457`)
- Near boundary: q95 < score ≤ q99 (`1.765183470`)
- Severe: score > q99

The thresholds are empirical training-distribution quantiles, not manually selected constants. Across in-distribution and shifted cases, OOD score had Pearson correlation `0.566` and Spearman correlation `0.723` with error.

## Physical validation

Raw ML predictions are recorded before correction. Negative fractions, values outside `[0, 1]`, and energy-sum deviation are reported. A serious violation—more than `0.1` outside the allowed range or energy error above `0.1`—forces deterministic fallback. Smaller deviations are retained as raw violations, then clamped and energy-normalized for safe display.

The benchmark found minor raw consistency deviations in 3,998 of 4,000 ensemble predictions and no serious violations. This means postprocessing is part of the surrogate system and raw model outputs must not be described as physically exact.

## Decision policy

The deployed q99 policy returns AI only when all conditions hold:

1. required inputs and model artifacts are available;
2. OOD score ≤ `1.765183470`;
3. uncertainty score ≤ `0.008112074`;
4. no serious raw physical violation occurs.

Otherwise the deterministic result is returned with a visible reason. Near-boundary cases are labeled `caution` but are not rejected unless another threshold is exceeded.

The q99 policy was selected as the least conservative tested reliability policy: it retained AI for 67.7% of the mixed-regime benchmark while reducing mean absolute error from `0.012930` to `0.005421` and the frequency of errors above `0.02` from 28.30% to 9.95%. The q95 policy reduced error further but used AI for only 31.0% of cases.

## Efficiency result

The efficiency hypothesis was not supported on the measured machine. Median batch cost was `0.08684 ms/sample` for deterministic physics, `0.09822 ms/sample` for the ensemble, and `0.12806 ms/sample` for the q99 hybrid. Single-input medians were `0.0339 ms` for physics and `151.8572 ms` for ensemble inference. The hybrid improves reliability but is slower than the already-lightweight deterministic implementation.

This negative result is central: the current surrogate is useful for studying reliability decisions, not for claiming computational acceleration. A future efficiency study would need a heavier deterministic teacher, vectorized/compiled inference, a smaller uncertainty model, or larger scientific batches.

## Scenario Mode

Scenario Mode now uses the same hybrid path as real-body predictions. User inputs remain request-local. The interface displays the final result source and exposes a collapsible research panel containing uncertainty, OOD class, reliability decision, physical checks, physics–AI delta, and fallback reason.

## Limitations

- The deterministic teacher is a simplified aggregate model, not full radiative transfer.
- Physics-only error is zero by construction because synthetic labels come from that model.
- Ensemble spread is not calibrated coverage.
- OOD distance can miss high-error points and can reject safe points.
- Feature correlations, especially distance and irradiance, complicate attribution.
- The ensemble increases model size and single-request latency.
- The experiment does not establish observational atmospheric accuracy.

Detailed measurements and reproduction commands are in [AI_PHYSICS_BENCHMARK.md](AI_PHYSICS_BENCHMARK.md).
