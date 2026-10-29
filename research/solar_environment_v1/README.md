# Solar environment research extension v1

This additive research layer documents the transition from the Solar Light Propagation Simulator to the Solar Radiation Simulator. It does not overwrite the light-model datasets, trained artifacts, evaluation results, paper files, or reliability study.

## Research decision

No magnetic-field or radiation ML model was trained. The reviewed evidence is sparse, heterogeneous, and often qualitative; a learned model would imply unsupported precision. Version 1 therefore uses a transparent 32-record reference catalog plus deterministic scenario classification. The existing light surrogate remains scoped to its synthetic light labels with its established uncertainty, OOD, physical validation, and fallback policy.

## Reproducible artifact

`data/solarEnvironment.v1.json` is the canonical machine-readable artifact. It records field family, origin, geometry, supported numeric ranges, particle context, shielding, limitations, data quality, and source IDs. `backend/tests/test_solar_environment.py` verifies complete coverage, important special cases, explicit unknowns, and Scenario Mode behavior.

Derived, reviewable outputs in this directory include the 32-row body summary, field-family and evidence-quality counts, an SVG distribution figure, and the manual verification record. These are a new versioned extraction and do not revise prior light-model experiments.

## Limitations

The classification is not dosimetry, a time-dependent heliophysics model, or a space-weather forecast. Visual extents are illustrative. Parent-magnetosphere exposure varies with location and time beyond the current educational model.
