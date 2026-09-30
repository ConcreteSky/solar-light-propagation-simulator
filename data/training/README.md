# Training data

`light_training_data.csv` contains 10,000 deterministic synthetic rows from physics generator version 1.0.0 and random seed 741. The rows cover airless, near-vacuum, thin, moderate, and dense atmospheric cases over 0.3–70 AU. They are not copies of real Solar System bodies.

Regenerate from `backend/` with:

```powershell
.\.venv\Scripts\python.exe training\generate_training_data.py
```

The exact column contract, ranges, and invariants are in `backend/training/training_schema.json`; the formulas and assumptions are in `docs/PHYSICS_MODEL.md`. `training_template.csv` is retained as the original Session 1 schema-only artifact.
