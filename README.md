# Solar Radiation Simulator

Interactive scientific-computing project for visible light, magnetic interaction, charged particles, radiation context, and shielding across the Solar System.

**Live Application:** https://solar-radiation-simulator.vercel.app

## Project overview

The Solar Radiation Simulator expands the original Solar Light Propagation Simulator without replacing it. Here, “radiation” is used broadly for energy and particles arriving from the Sun while the interface keeps visible photons and charged particles scientifically separate. Selecting a destination freezes one shared simulation time and resolves three layers: visible light, charged-particle/radiation context, and magnetic interaction. The light subsystem retains its measured reliability architecture: **Efficiency**, **Reliability**, and automatic deterministic **Fallback**.

The Sun is the only light source. The application requires no manual scientific input and makes no live astronomical-data requests during normal operation.

## Features

- Interactive React Three Fiber Solar System with shared-clock Keplerian motion and clickable destinations.
- Eight planets, five dwarf planets, and nineteen selected moons, with no more than four moons per planet.
- Coplanar simplified elliptical orbits, thin orbit rings, compressed distances, exaggerated body sizes, Saturn rings, and an efficient asteroid belt.
- Mouse/touch camera rotation, cursor-centered zoom, selection focus, labels, and highlighting.
- Locally cached scientific catalog with units, source IDs, deliberate nulls, and ASTM E-490 spectrum data.
- Explainable atmospheric and airless deterministic physics baseline with energy conservation.
- Five-model HistGradientBoosting ensemble with uncertainty, OOD scoring, physical validation, and centralized deterministic fallback.
- Versioned 32-body magnetic, particle, radiation-context, and shielding catalog with explicit evidence quality and unknowns.
- Selected-body field-family overlays for intrinsic, aligned, tilted/offset, induced, crustal, mini-magnetosphere, and parent-plasma interactions.
- Four-panel Solar Interaction Profile with distinct photon and charged-particle encodings.
- Timestamped physical distance, light-travel time, irradiance, apparent solar diameter, interaction percentages, and one short deterministic appearance sentence.
- Reproducible synthetic dataset, real-body benchmarks, candidate-model comparison, and preserved evaluation output.
- Hybrid Scenario Mode for request-local atmosphere pressure, density, and composition changes.
- Versioned mixed-regime benchmarks, failure cases, threshold experiments, feature importance, and local sensitivity artifacts.
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
        ├─ five saved surrogate pipelines ──► mean prediction + uncertainty
        ├─ training-distribution statistics ─► OOD score
        ├─ physical range/energy validation
        └─ one reliability decision ─────────► AI result or physics fallback
        │
        ▼
Solar Interaction Profile + preserved light diagnostics
```

`GET /api/analyze/{destinationId}` remains the deterministic scientific baseline. Prediction responses disclose the selected source, both AI and deterministic values when inference is available, their deltas, uncertainty, OOD classification, physical checks, and any fallback reason. Both destination endpoints accept an optional ISO-8601 `at` query parameter.

## Supported celestial objects

- Planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune.
- Dwarf planets: Ceres, Pluto, Eris, Haumea, Makemake.
- Moons: Moon, Phobos, Deimos, Io, Europa, Ganymede, Callisto, Titan, Rhea, Iapetus, Dione, Titania, Oberon, Umbriel, Ariel, Triton, Proteus, Nereid, Larissa.

## Scientific methodology

Timestamped analysis derives heliocentric distance from the shared-clock Keplerian state and applies the inverse-square irradiance relation. Untimestamped analysis preserves the stored reference path. The atmosphere model uses pressure, density, and normalized supported gas fractions to form simplified aggregate scattering and absorption optical depths. Airless bodies use a disclosed generic surface partition because sourced wavelength-dependent albedo is not present in the catalog. Fractions are clamped, normalized, and required to conserve incident energy.

Scientific distances and derived values are separate from compressed visual coordinates. Light-travel time uses the speed of light, solar irradiance follows the inverse-square relation, and apparent solar diameter is derived from the modeled Sun distance. The displayed scattered-light color maps broad spectral classes from the stored solar spectrum and aggregate atmosphere behavior; it is not a full colorimetric or line-by-line radiative-transfer solution.

This is an educational model, not full radiative transfer, ray tracing, Mie scattering, spectroscopy, or an observationally validated atmosphere simulator. Detailed equations and assumptions are documented in [PHYSICS_MODEL.md](docs/PHYSICS_MODEL.md).

The environment layer is also educational: radiation and shielding levels are qualitative, magnetic extents are schematic, and the steady solar-wind value is an inverse-square proxy rather than real-time space weather or dosimetry. See [SOLAR_ENVIRONMENT_MODEL.md](docs/SOLAR_ENVIRONMENT_MODEL.md).

## AI methodology

The ML system approximates labels generated by the deterministic physics code. Five independently seeded HistGradientBoosting pipelines predict transmitted, scattered, absorbed, and relative-brightness fractions from eleven supported scientific features. Their mean is the candidate prediction and their spread is an empirical uncertainty signal. A standardized feature-distance score detects inputs outside the training distribution.

Synthetic-label agreement demonstrates approximation fidelity only. It does not prove real-world atmospheric accuracy. Actual metrics and physical-correction rates are preserved in [AI_EVALUATION.md](docs/AI_EVALUATION.md) and `data/evaluation/ai_model_evaluation.json`.

The central reliability policy falls back when required inputs are missing, uncertainty exceeds its validation q99 threshold, OOD score exceeds its training q99 threshold, or raw outputs seriously violate physical constraints. Near-boundary cases are marked with caution. Global permutation importance and local perturbation sensitivity are reproducible research artifacts rather than per-request explanations. See [RELIABLE_AI.md](docs/RELIABLE_AI.md) and [AI_PHYSICS_BENCHMARK.md](docs/AI_PHYSICS_BENCHMARK.md).

## Scenario Mode

Scenario Mode runs the same hybrid reliability path as destination prediction. It temporarily substitutes user-supplied atmosphere presence, pressure, density, and normalized supported gas fractions while preserving the selected destination and frozen orbital timestamp. The stored catalog is never mutated. The result panel shows the final source and provides expandable reliability details; unsafe or incomplete scenarios fall back automatically to deterministic physics.

## Performance

High-frequency orbital motion is isolated from low-frequency React UI state: Three.js transforms update per frame, while scientific analysis runs only when a destination is selected or a scenario is submitted. Static orbital constants and geometry are reused, callbacks and stable components are memoized, stale requests remain cancellable, and repeated identical results use bounded version-keyed caches on both client and server.

On the measured local production build, median p95 animation-frame interval fell from 36.3 ms to 7.9 ms. The new controlled 4,000-case benchmark found deterministic physics faster than both the five-model ensemble and the q99 hybrid; therefore no AI speedup is claimed. The hybrid instead reduced mixed-regime mean absolute error from `0.012930` to `0.005421` while using AI for 67.7% of cases. Hardware, browser, process startup, and cold serverless behavior vary; see [PERFORMANCE.md](docs/PERFORMANCE.md).

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

The runtime artifacts in `backend/models/` must remain beside the application, including the original model and the reliability ensemble with their metadata. No environment variable is required for the standard same-origin setup. For a separately hosted API, set `VITE_API_ROOT` to its origin before building the frontend.

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
| `GET /api/environment/{destinationId}[?at=ISO-8601]` | Reference magnetic/particle environment plus dynamic steady-input and shielding context |
| `POST /api/analyze/{destinationId}/scenario[?at=ISO-8601]` | Deterministic recalculation with user-supplied atmospheric pressure, density, and composition |
| `GET /api/predict/{destinationId}[?at=ISO-8601]` | Validated ML result or disclosed deterministic fallback, optionally timestamped |
| `POST /api/predict/{destinationId}/scenario[?at=ISO-8601]` | Hybrid scenario prediction with reliability diagnostics and automatic fallback |

Invalid destination IDs return HTTP 404. Missing model files, incomplete core inputs, non-finite output, and serious conservation failures use the deterministic fallback when safe.

## Research structure and reproducibility

The repository contains the 10,000-row versioned synthetic dataset, 32 real-body benchmarks, saved models, preprocessing contract, candidate evaluation, and a 4,000-case reliability/efficiency study spanning in-distribution, boundary, shifted, dense, thin, and airless regimes. Versioned CSV/JSON results and ten figures are in `research/results/reliability_efficiency/`; commands and assumptions are documented in [AI_PHYSICS_BENCHMARK.md](docs/AI_PHYSICS_BENCHMARK.md) and [RESEARCH_REPRODUCIBILITY.md](docs/RESEARCH_REPRODUCIBILITY.md).

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
- Ensemble spread is an empirical ranking signal, not a calibrated confidence interval; OOD distance is also a screening heuristic, not proof that a prediction is wrong.
- Feature importance and local sensitivity are offline research diagnostics, not causal explanations or per-request UI features.
- The interface exposes AI/deterministic deltas in expandable details, but does not render two full result diagrams side by side.
- Serverless cold starts and client GPU capability can affect initial load time.
- Magnetic and radiation categories are qualitative; no event forecast, dose calculation, or trajectory integration is performed.
- Unknown small-body fields remain unknown, and selected-body magnetic geometry is illustrative rather than to scale.

## Deployment

`vercel.json` builds `frontend/` and packages `api/index.py` as a Python 3.14 FastAPI Function. Runtime dependencies are pinned in the root `requirements.txt`. Static frontend and API routes share one origin, while local two-process development remains unchanged.

The deployment excludes the private research backup, virtual environment, dependency directories, caches, and generated build output.

## Documentation

- [Physics model](docs/PHYSICS_MODEL.md)
- [Orbital model and simulation clock](docs/ORBITAL_MODEL.md)
- [AI model](docs/AI_MODEL.md)
- [AI evaluation](docs/AI_EVALUATION.md)
- [Reliable AI architecture](docs/RELIABLE_AI.md)
- [AI/physics reliability and efficiency benchmark](docs/AI_PHYSICS_BENCHMARK.md)
- [Academic relevance](docs/ACADEMIC_RELEVANCE.md)
- [Light diagram](docs/LIGHT_DIAGRAM.md)
- [Solar environment model](docs/SOLAR_ENVIRONMENT_MODEL.md)
- [Magnetic fields](docs/MAGNETIC_FIELDS.md)
- [Radiation environment](docs/RADIATION_ENVIRONMENT.md)
- [Scenario Mode](docs/SCENARIO_MODE.md)
- [Visualization model](docs/VISUALIZATION_MODEL.md)
- [Research reproducibility](docs/RESEARCH_REPRODUCIBILITY.md)
- [Performance](docs/PERFORMANCE.md)

## License and attribution

Application source code is released under the [MIT License](LICENSE). Scientific data and third-party source material remain subject to their original providers' terms and attribution requirements. No downloaded imagery is redistributed beyond the documented locally created schematic assets.
