# Solar Light Propagation Simulator

Interactive scientific-computing and machine-learning Solar System simulation focused on solar-light propagation and atmospheric interaction.

**Live Application:** https://solar-light-propagation-simulator.vercel.app

## Project overview

The Solar Light Propagation Simulator combines scientific modeling, applied machine learning, reproducible experimentation, and an interactive three-dimensional destination map. Selecting a planet, dwarf planet, or supported moon freezes the shared simulation time, derives the body's approximate orbital state, runs a transparent deterministic light model, obtains a validated machine-learning surrogate result where inputs permit, and renders a destination-specific SVG interaction diagram.

The Sun is the only light source. The application requires no manual scientific input and makes no live astronomical-data requests during normal operation.

## Features

- Interactive React Three Fiber Solar System with shared-clock Keplerian motion and clickable destinations.
- Eight planets, five dwarf planets, and nineteen selected moons, with no more than four moons per planet.
- Coplanar simplified elliptical orbits, thin orbit rings, compressed distances, exaggerated body sizes, Saturn rings, and an efficient asteroid belt.
- Mouse/touch camera rotation, cursor-centered zoom, selection focus, labels, and highlighting.
- Locally cached scientific catalog with units, source IDs, deliberate nulls, and ASTM E-490 spectrum data.
- Explainable atmospheric and airless deterministic physics baseline with energy conservation.
- Saved HistGradientBoosting surrogate with preprocessing, output validation, and explicit deterministic fallback.
- Dynamic atmospheric/airless SVG light-interaction diagram controlled by validated numerical results.
- Timestamped physical distance, light-travel time, irradiance, apparent solar diameter, interaction percentages, and one short deterministic appearance sentence.
- Reproducible synthetic dataset, real-body benchmarks, candidate-model comparison, and preserved evaluation output.
- Hypothetical Scenario Mode for request-local atmosphere pressure, density, and composition changes.
- Bounded, version-aware result caches and frame-level orbital transforms for stable interactive performance.

## Technology stack

- Frontend: React, Vite, React Three Fiber, Drei, Three.js, SVG, Vitest, Testing Library.
- Backend: Python 3.14, FastAPI, Pydantic, NumPy, pandas, SciPy.
- Machine learning: scikit-learn and joblib.
- Deployment: Vercel static frontend plus Python/FastAPI Function in one same-origin project.

## System architecture

```text
3D destination selection
        │ selectedBodyId
        ▼
GET /api/predict/{destinationId}?at={simulatedUtcTimestamp}
        │
        ├─ physical orbital state + stored catalog + ASTM spectrum
        ├─ saved preprocessing/model pipeline
        ├─ range and energy validation
        └─ deterministic fallback when required
        │
        ▼
Result panel + one schematic SVG diagram
```

`GET /api/analyze/{destinationId}` remains the deterministic scientific baseline. `GET /api/predict/{destinationId}` clearly identifies either `machine_learning` or `deterministic_fallback` and reports its comparison with the baseline. Both endpoints accept an optional ISO-8601 `at` query parameter; omitting it preserves the reference-value response path for compatibility.

## Supported celestial objects

- Planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune.
- Dwarf planets: Ceres, Pluto, Eris, Haumea, Makemake.
- Moons: Moon, Phobos, Deimos, Io, Europa, Ganymede, Callisto, Titan, Rhea, Iapetus, Dione, Titania, Oberon, Umbriel, Ariel, Triton, Proteus, Nereid, Larissa.

## Scientific methodology

Timestamped analysis derives heliocentric distance from the shared-clock Keplerian state and applies the inverse-square irradiance relation. Untimestamped analysis preserves the stored reference path. The atmosphere model uses pressure, density, and normalized supported gas fractions to form simplified aggregate scattering and absorption optical depths. Airless bodies use a disclosed generic surface partition because sourced wavelength-dependent albedo is not present in the catalog. Fractions are clamped, normalized, and required to conserve incident energy.

Scientific distances and derived values are separate from compressed visual coordinates. Light-travel time uses the speed of light, solar irradiance follows the inverse-square relation, and apparent solar diameter is derived from the modeled Sun distance. The displayed scattered-light color maps broad spectral classes from the stored solar spectrum and aggregate atmosphere behavior; it is not a full colorimetric or line-by-line radiative-transfer solution.

This is an educational model, not full radiative transfer, ray tracing, Mie scattering, spectroscopy, or an observationally validated atmosphere simulator. Detailed equations and assumptions are documented in [PHYSICS_MODEL.md](docs/PHYSICS_MODEL.md).

## AI methodology

The ML model approximates labels generated by the deterministic physics code. It predicts transmitted, scattered, absorbed, and relative-brightness fractions from eleven supported scientific features. Linear Regression, Random Forest, and HistGradientBoosting were evaluated with fixed seed 741. HistGradientBoosting was selected using validation error and serialized size, then tested on an untouched 1,000-row split.

Synthetic-label agreement demonstrates approximation fidelity only. It does not prove real-world atmospheric accuracy. Actual metrics and physical-correction rates are preserved in [AI_EVALUATION.md](docs/AI_EVALUATION.md) and `data/evaluation/ai_model_evaluation.json`.

The runtime validates model outputs, compares them with the deterministic baseline, and falls back explicitly when required inputs are absent or outputs fail physical checks. Statistical uncertainty estimation, OOD classification, global feature-importance display, and local sensitivity analysis are not implemented in the current runtime and are therefore not claimed as application features.

## Scenario Mode

Scenario Mode is a hypothetical deterministic recalculation. It temporarily substitutes user-supplied atmosphere presence, pressure, density, and supported gas fractions while preserving the selected destination and frozen orbital timestamp. The stored real-body catalog is never mutated. Results are labeled `deterministic_scenario`, validated by the same physical constraints, and cached only under the complete scenario payload.

The current interface replaces the visible result with the scenario result; it does not present a side-by-side baseline comparison or run the ML surrogate for hypothetical inputs.

## Performance

High-frequency orbital motion is isolated from low-frequency React UI state: Three.js transforms update per frame, while scientific analysis runs only when a destination is selected or a scenario is submitted. Static orbital constants and geometry are reused, callbacks and stable components are memoized, stale requests remain cancellable, and repeated identical results use bounded version-keyed caches on both client and server.

On the measured local production build, median p95 animation-frame interval fell from 36.3 ms to 7.9 ms. Repeat-key backend medians fell from 27.6793 ms to 0.0003 ms for ML prediction and from 0.0736 ms to 0.0029 ms for a scenario analysis. Hardware, browser, process startup, and cold serverless behavior vary; full methodology, caveats, and all measured values are in [PERFORMANCE.md](docs/PERFORMANCE.md).

## Installation

Requirements:

- Python 3.14
- Node.js 24 or a compatible current LTS release
- npm

Backend setup from the repository root:

```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Frontend setup:

```powershell
cd frontend
npm ci
```

## Local development

Start the API from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Start Vite from `frontend/` in a second terminal:

```powershell
npm run dev
```

Open <http://127.0.0.1:5173>. Vite proxies local `/api` requests to <http://127.0.0.1:8000>.

The saved runtime model must remain at `backend/models/light_model.joblib` with `backend/models/light_model_metadata.json`. No environment variable is required for the standard same-origin setup. For a separately hosted API, set `VITE_API_ROOT` to its origin before building the frontend.

Run all automated gates:

```powershell
cd frontend
npm run validate:data
npm test
npm run build

cd ..\backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Run the non-gating runtime benchmark from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m training.benchmark_runtime --iterations 300
```

## API documentation

Local interactive OpenAPI documentation is available at <http://127.0.0.1:8000/docs>.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/health` | Service and catalog health |
| `GET /api/bodies` | Complete stored destination catalog |
| `GET /api/analyze/{destinationId}[?at=ISO-8601]` | Deterministic baseline, optionally timestamped |
| `POST /api/analyze/{destinationId}/scenario[?at=ISO-8601]` | Deterministic recalculation with user-supplied atmospheric pressure, density, and composition |
| `GET /api/predict/{destinationId}[?at=ISO-8601]` | Validated ML result or disclosed deterministic fallback, optionally timestamped |

Invalid destination IDs return HTTP 404. Missing model files, incomplete core inputs, non-finite output, and serious conservation failures use the deterministic fallback when safe.

## Research structure and reproducibility

The repository contains the 10,000-row versioned synthetic dataset, 32 real-body benchmarks, saved model, preprocessing contract, candidate evaluation, physics/ML comparison data, source documentation, and fixed split/seed information. Complete commands and checksums are provided in [RESEARCH_REPRODUCIBILITY.md](docs/RESEARCH_REPRODUCIBILITY.md). Historical datasets, experiment outputs, metrics, scripts, and model artifacts remain separate from normal runtime API payloads.

The private `research_backup/` snapshot is excluded from publication. Public research artifacts remain at their canonical project paths.

## Scientific data sources

Scientific and asset provenance is documented in:

- [DATA_SOURCES.md](docs/DATA_SOURCES.md)
- [ASSET_SOURCES.md](docs/ASSET_SOURCES.md)
- `data/sources.json`

Catalog values are based primarily on NASA, JPL, and the ASTM E-490 reference distributed by the National Laboratory of the Rockies. Display colors and stylized textures are illustrative and never scientific inputs.

## Known limitations

- The coplanar two-body orbital model is approximate and is not a precision ephemeris.
- Render distances are compressed and celestial sizes are exaggerated for navigation; neither is used as a scientific input.
- Aggregate atmosphere coefficients omit clouds, aerosols, dust, weather, seasons, and spectral absorption lines.
- Real-body atmospheric properties are fixed catalog values unless Scenario Mode is used.
- Airless interaction percentages use a documented generic surface assumption, not measured body-specific albedo.
- Several giant planets, dwarf planets, and moons lack complete pressure, density, composition, or atmosphere-state inputs and therefore use disclosed fallback.
- Diagram ray directions are illustrative and do not represent observer geometry.
- The model was trained on synthetic physics labels; independent observational validation was not available for the project's energy-partition convention.
- The runtime does not currently provide statistical uncertainty, OOD detection, global feature importance, local sensitivity, or side-by-side scenario comparison.
- Serverless cold starts and client GPU capability can affect initial load time.

## Deployment

`vercel.json` builds `frontend/` and packages `api/index.py` as a Python 3.14 FastAPI Function. Runtime dependencies are pinned in the root `requirements.txt`. Static frontend and API routes share one origin, while local two-process development remains unchanged.

The deployment excludes the private research backup, virtual environment, dependency directories, caches, and generated build output.

## Documentation

- [Physics model](docs/PHYSICS_MODEL.md)
- [Orbital model and simulation clock](docs/ORBITAL_MODEL.md)
- [AI model](docs/AI_MODEL.md)
- [AI evaluation](docs/AI_EVALUATION.md)
- [Light diagram](docs/LIGHT_DIAGRAM.md)
- [Research reproducibility](docs/RESEARCH_REPRODUCIBILITY.md)
- [Performance](docs/PERFORMANCE.md)

## License and attribution

Application source code is released under the [MIT License](LICENSE). Scientific data and third-party source material remain subject to their original providers' terms and attribution requirements. No downloaded imagery is redistributed beyond the documented locally created schematic assets.
