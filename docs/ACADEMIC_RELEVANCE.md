# Academic Relevance

This document describes honest thematic connections for the same single project. It is not part of the scientific methodology and does not claim programme affiliation, supervision, laboratory involvement, or collaboration.

## Gdańsk — efficient computation and scientific computing

The project provides a measured comparison between deterministic scientific computation and an ML surrogate, including load cost, steady-state latency, throughput, memory, and hybrid fallback overhead. The present result is scientifically useful because the surrogate did not accelerate the lightweight deterministic implementation. This motivates future work on vectorized inference, compiled models, larger batches, or computationally heavier scientific teachers. The current implementation does not use parallel runtime inference and should not be described as a parallel-computing project.

## Łódź — applied machine learning and robustness

The project trains and evaluates a surrogate across repeated seeds, distribution shifts, physical constraints, and explicit failure cases. Ensemble disagreement and OOD distance are evaluated against actual errors, including false negatives and unnecessary fallbacks. This supports discussion of robust applied ML without claiming calibrated uncertainty or universal reliability.

## SGH — statistical evaluation and quantitative decisions

The work uses MAE, RMSE, R², correlations, quantile-derived thresholds, error distributions, timing dispersion, and accuracy–runtime trade-offs. The fallback policy is a quantitative decision rule whose costs and benefits are measured rather than assumed. The deterministic teacher and synthetic-label limitation remain explicit.

## Silesian — trustworthy automated decision-making

The hybrid architecture exposes when automation is accepted and when it defers to a more dependable method. Users can inspect uncertainty, OOD class, physical checks, result source, and fallback reason. This provides a transparent case study in reliability-aware automation while acknowledging that the chosen detectors still miss some errors and sometimes reject safe predictions.
