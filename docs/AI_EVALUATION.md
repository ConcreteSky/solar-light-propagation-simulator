# AI evaluation results

These are actual results from model version 1.0.0, trained locally with scikit-learn and seed 741. The complete machine-readable record is `data/evaluation/ai_model_evaluation.json`.

## Dataset audit

The 10,000-row dataset contained no missing values, non-finite values, duplicate rows, or duplicate feature records. Maximum energy-conservation error was `2.22e-16`. Gas mixtures and airless-row constraints passed the Session 3 artifact tests, so regeneration was not necessary.

## Validation-set candidate comparison

| Candidate | Mean MAE | Mean RMSE | Corrections | Serious violations | Approx. size |
| --- | ---: | ---: | ---: | ---: | ---: |
| Linear Regression | 0.033794 | 0.049613 | 42.8% | 2.8% | 4.8 KB |
| Random Forest | 0.004273 | 0.010465 | 0% | 0% | 59.3 MB |
| HistGradientBoosting | 0.001644 | 0.003632 | 99.9% | 0% | 2.68 MB |

HistGradientBoosting was selected because its validation MAE was substantially lower than Random Forest while its artifact was much smaller. Linear Regression was fastest and smallest but materially less accurate and produced serious invalid outputs. HistGradientBoosting's frequent corrections are small energy normalizations caused by independent target regressors; the maximum validation energy-sum error was 0.03688 and no prediction crossed the serious-fallback threshold.

## Untouched test results

Errors below are fractions. Percentage-point MAE is fraction MAE multiplied by 100.

| Target | MAE | MAE, percentage points | RMSE | R² |
| --- | ---: | ---: | ---: | ---: |
| Transmitted | 0.001876 | 0.1876 | 0.004789 | 0.998970 |
| Scattered | 0.001450 | 0.1450 | 0.003343 | 0.998980 |
| Absorbed | 0.000601 | 0.0601 | 0.001569 | 0.998887 |
| Relative brightness | 0.001855 | 0.1855 | 0.003996 | 0.999893 |

Mean target MAE was 0.001445. Raw test predictions had no serious physical violations. Of 1,000 rows, 999 required minor normalization; 35 contained a slightly negative raw fraction and 21 contained a raw value slightly above one. Maximum raw energy-sum error was 0.02802 and mean error was 0.001412. Returned API values are clamped and normalized.

The saved model is 2,679,028 bytes. Measured median one-row inference was approximately 9.03 ms on the development machine. Batched test inference was approximately 0.014–0.018 ms per row; timing varies by machine and process load.

## Condition-based generalization checks

| Test group | Rows | Mean MAE | Mean RMSE | Serious violations |
| --- | ---: | ---: | ---: | ---: |
| Inner system, ≤0.75 AU | 181 | 0.001228 | 0.002846 | 0 |
| Outer system, >8 AU | 398 | 0.001147 | 0.002594 | 0 |
| Dense atmosphere, >200 kPa | 129 | 0.005334 | 0.008079 | 0 |
| Airless | 285 | 0.000237 | 0.000457 | 0 |

Dense atmospheres are the hardest tested regime. R² is intentionally reported as undefined for the three constant airless fraction targets; MAE and RMSE remain meaningful there.

## Real-body comparison

Nineteen of 32 catalog bodies had sufficient inputs for direct ML-versus-deterministic comparison. Mean absolute errors across those bodies were:

| Target | MAE | MAE, percentage points |
| --- | ---: | ---: |
| Transmitted | 0.000311 | 0.0311 |
| Scattered | 0.000491 | 0.0491 |
| Absorbed | 0.000164 | 0.0164 |
| Relative brightness | 0.001742 | 0.1742 |

No serious physical violation occurred. The 13 excluded/fallback bodies were Jupiter, Saturn, Uranus, Neptune, Pluto, Eris, Haumea, Makemake, Io, Europa, Ganymede, Callisto, and Triton. Reasons were missing pressure/density, wholly missing composition, or unknown atmosphere state.

## Independent observations

Comparison B was not performed. The local sources contain established astronomical inputs, but no independent measurements using this project's aggregate energy-partition convention. Consequently, these results support approximation fidelity only—not real-world atmospheric accuracy.
