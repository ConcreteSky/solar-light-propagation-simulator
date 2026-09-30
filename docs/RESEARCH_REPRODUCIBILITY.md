# Research reproducibility

## Research question and evidence boundary

The project investigates how accurately lightweight regression models can approximate a transparent educational light-interaction model across plausible Solar System-like conditions. Agreement with synthetic deterministic labels measures software approximation fidelity. It is not independent evidence of real atmospheric accuracy.

The protected pre-Session-6 snapshot is stored locally under `research_backup/` and cataloged by `research_backup/RESEARCH_MANIFEST.md`. It is intentionally excluded from GitHub and deployment. Public research files remain in their original repository paths.

## Scientific inputs

- `data/celestialBodies.json`: 32 planets, dwarf planets, and selected moons with source IDs, units, and deliberate nulls.
- `data/solarSpectrum.csv`: 516-row ASTM E-490 subset covering 300.5–1000 nm in W/m²/nm.
- `data/sources.json`: machine-readable source registry.
- `docs/DATA_SOURCES.md`: source methodology, conversions, and null policy.

Normal operation is fully local and makes no live NASA, JPL, or spectrum requests.

## Deterministic baseline

`backend/app/services/light_calculation_service.py` coordinates stored-input resolution, inverse-square irradiance validation, the simplified atmosphere/surface models, finite-range checks, and energy normalization. Its assumptions and coefficients are documented in `docs/PHYSICS_MODEL.md`.

The baseline produces transmitted, scattered, and absorbed fractions whose sum is one, normalized relative brightness, a broad deterministic color category, and an apparent-size category. It is educational aggregate physics—not full radiative transfer, spectroscopy, cloud, aerosol, or observer-geometry modeling.

## Synthetic dataset

Generator version 1.0.0 uses NumPy seed 741 and produces 10,000 rows over 0.3–70 AU. The predefined split is 8,000 training, 1,000 validation, and 1,000 test rows. Atmospheric mixtures are sampled from documented Dirichlet archetypes; density is derived from sampled pressure, temperature, and mean molar mass. Airless rows use zero pressure, density, and gas fractions.

From `backend/`:

```powershell
.\.venv\Scripts\python.exe training\generate_training_data.py
.\.venv\Scripts\python.exe training\generate_benchmarks.py
```

Expected SHA-256 values for the preserved artifacts are:

- `data/training/light_training_data.csv`: `879360785bd11681116099002ca9046bf65d225b92df1c2615ed938a8a2bb8f6`
- `data/benchmark/real_body_benchmarks.json`: `c4a648df04668b8934f0f1a4d40a1ba9d7ebd74c6cfe497cd6a28f69f8243fd2`

Regeneration intentionally overwrites generated working artifacts. Preserve or compare the originals before running those commands.

## Model training and selection

The feature order, target order, preprocessing, and candidate configurations are defined in `backend/app/ml/model_contract.py` and `backend/training/ml_utils.py`. Inputs are distance, irradiance, atmosphere flag, pressure, density, and six supported gas fractions. Targets are transmitted, scattered, absorbed, and relative-brightness fractions.

The candidates are Linear Regression, Random Forest, and multi-output HistGradientBoosting. Candidate selection uses validation mean MAE; models within 2% are resolved by serialized size. The selected HistGradientBoosting pipeline is refit on 9,000 train-plus-validation rows and evaluated once on the untouched 1,000-row test set.

```powershell
.\.venv\Scripts\python.exe training\train_model.py
.\.venv\Scripts\python.exe training\evaluate_model.py
```

The preserved model SHA-256 is `9ff8c72f9a0f0eb102b9d73e0a71e0645690c9d1ecbecb830169c13d13eff233`. Actual candidate metrics, group tests, physical-correction rates, inference timing, and 19-body comparison are stored in `data/evaluation/ai_model_evaluation.json` and explained in `docs/AI_EVALUATION.md`.

No compatible independent observational measurements exist in the local sources for the project's aggregate energy-partition convention. The observational comparison is therefore explicitly recorded as not performed.

## Reproduction environment

The original run used Python 3.14.0, FastAPI 0.142.0, NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1, joblib 1.6.0, and Pydantic 2.13.5. Exact deployment runtime packages are pinned in the root `requirements.txt`; development-compatible ranges remain in `backend/requirements.txt`.

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend reproduction uses the committed npm lockfile:

```powershell
cd frontend
npm ci
npm run validate:data
npm test
npm run build
```

## Integrity verification

The private research snapshot contains 43 files. Each checksum in `research_backup/RESEARCH_MANIFEST.md` was verified against both the copied file and its original immediately after snapshot creation. To repeat the comparison locally, calculate SHA-256 for each relative path in `research_backup/original/` and compare it with the manifest and the matching workspace path.

## Known limitations

- Synthetic-label accuracy does not establish observational validity.
- Atmospheric coefficients are aggregate educational assumptions.
- Surface albedo, clouds, aerosols, dust, seasons, viewing geometry, and spectral lines are omitted.
- Missing pressure, density, composition, or atmosphere state causes disclosed fallback rather than fabricated inputs.
- Independent multi-output regressors require the documented output-normalization layer.
- Inference timing varies with hardware and hosting cold starts.
