# Paper 1 reliability–efficiency update

The paper's central narrative should now evaluate four properties together: accuracy, efficiency, reliability, and deterministic fallback.

The current evidence supports the following limited result:

> On controlled synthetic distribution shifts, the q99 hybrid policy reduced ensemble mean absolute error from 0.012930 to 0.005421 and reduced errors above 0.02 from 28.30% to 9.95%, while using AI for 67.7% of cases. The hybrid was slower than both deterministic physics and ML-only inference on the measured machine.

Therefore the proposed claim that the hybrid provides a useful accuracy–efficiency trade-off is only partly supported. Reliability improved, but computational acceleration did not. Paper 1 should present this as a negative efficiency result and avoid claiming general speedup.

Required evidence is versioned in `research/results/reliability_efficiency/`, with methodology in `docs/AI_PHYSICS_BENCHMARK.md` and decision rules in `docs/RELIABLE_AI.md`.

The discussion should retain these failure cases:

- high error despite low ensemble spread;
- high error not flagged as OOD;
- safe predictions rejected by OOD;
- overly conservative uncertainty flags;
- nearly universal small raw energy-sum deviations requiring postprocessing.

Synthetic deterministic labels remain the reference. None of these experiments establish observational atmospheric accuracy.
