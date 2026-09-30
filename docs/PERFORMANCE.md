# Performance

This document records the final performance pass for the Solar Light Propagation Simulator. Measurements were taken on the local Windows development machine on 2026-10-01. They are comparative engineering measurements, not universal hardware guarantees.

## Method

- Frontend: Vite production build served locally, three page loads per version, followed by 180 `requestAnimationFrame` samples while orbital animation ran. Medians are reported. Browser heap values were sampled when Chromium exposed `performance.memory`.
- Backend: Python 3.14 virtual environment, 300 calls per case after one warm-up. Latencies are wall-clock measurements from the service layer and exclude HTTP/network overhead.
- Startup: five fresh Python processes imported the FastAPI application and preloaded the saved model. This figure is strongly affected by operating-system file cache and concurrent machine load.
- Regression: representative deterministic, ML/fallback, and scenario outputs for Earth, Mars, Venus, Moon, Jupiter, Titan, and Pluto were serialized consistently and hashed before and after the changes.

The temporary browser profiler used for these measurements was removed from production source after the benchmark.

## Results

### Frontend

| Metric | Baseline | Optimized | Observation |
| --- | ---: | ---: | --- |
| Median load event | 161.4 ms | 156.8 ms | 2.8% lower |
| Median first contentful paint | 180.0 ms | 176.0 ms | 2.2% lower |
| Mean sampled animation callback rate | 94.2/s | 140.6/s | 49.2% higher in this browser environment |
| Median p95 frame interval | 36.3 ms | 7.9 ms | 78.2% lower |
| Sampled JS heap range | 27.4–38.6 MiB | 18.2–37.1 MiB | Too noisy to claim an improvement |

The callback rate can exceed monitor refresh rate in the test environment, so it must not be interpreted as display FPS. The p95 frame interval is the more useful stability signal. Time to a fully drawn WebGL scene was not isolated by the temporary probe; first contentful paint is retained as the repeatable page-interactivity proxy. A manual cold navigation showed the scene within the approximately 1.5-second observation interval, including shader and asset startup.

Visual meshes, materials, texture handling, lighting, orbit paths, atmosphere shells, asteroid density, and SVG detail were not reduced.

The final minified production output is 1,236.94 kB of JavaScript (338.43 kB gzip) and 11.55 kB of CSS (3.27 kB gzip). The baseline JavaScript was 1,234.16 kB (337.69 kB gzip); the small cache/control-code increase is documented rather than presented as a bundle-size improvement. Vite continues to warn that the single core scene chunk exceeds 500 kB. Splitting the core Three.js scene would add an awkward visible loading stage, while the optional Scenario UI is too small to materially change the payload, so no low-value code split was introduced.

### Backend service latency

| Case (median, 300 calls) | Baseline | Optimized | Change |
| --- | ---: | ---: | ---: |
| Deterministic Earth analysis | 0.0306 ms | 0.0002 ms | cached repeat |
| Earth ML prediction | 27.6793 ms | 0.0003 ms | cached repeat |
| Earth deterministic scenario | 0.0736 ms | 0.0029 ms | cached repeat |
| Pluto fallback prediction | 0.0696 ms | 0.0003 ms | cached repeat |

The optimized values are repeat-key cache hits. A new destination, timestamp, model version, physics version, or scenario payload still executes the original calculation path. No equations, trained-model parameters, preprocessing order, or validation rules were changed.

Five-process startup-and-model-preload median changed from approximately 1,977.9 ms to 2,448.2 ms. The optimization did not change the model loader, and the later sample was slower, so no startup improvement is claimed. The saved model and metadata continue to load once per process through the existing single-entry cache.

OOD processing and statistical uncertainty processing are not benchmarked because the current runtime does not implement those features. Global feature importance and local sensitivity are also not runtime features in this repository. The README deliberately does not claim them.

## Bottlenecks found

- The simulation clock published React state every 100 ms, rerendering the application and rebuilding scene element trees even though only object transforms needed continuous updates.
- Planet and moon positions, orbit ellipse point arrays, and some stable diagram geometry were recreated during unrelated renders.
- Repeated identical frontend analyses crossed the network again.
- Deterministic analyses, ML predictions, and scenarios repeated reusable work for identical inputs.
- The body lookup dictionary was rebuilt on every lookup.

The API already cancelled stale frontend requests and protected results with a request sequence. Scenario controls already submitted only from the explicit recalculation button, so no slider debounce was needed. Catalog, orbital-element, solar-spectrum, and model loading were already process-cached.

## Changes

- Continuous visual motion now updates Three.js group transforms in `useFrame`; React receives lower-frequency clock text updates.
- The exact simulated timestamp remains available through a stable clock accessor, and selection freezes analysis at that exact time.
- Static orbital constants, orbit geometry, asteroid radii, and reusable SVG path data are cached or memoized.
- Stable components and callbacks avoid unrelated scene and control rerenders.
- Frontend analysis results use a bounded 64-entry, version-keyed cache while retaining abort and stale-response protection.
- Backend deterministic, scenario, and prediction results use bounded, version-keyed LRU caches (256, 128, and 256 entries respectively).
- The static body index is constructed once per process.

All shared cached objects are treated as read-only. Scenario inputs remain request-local, and cache keys include the complete normalized scenario payload. Model and physics version strings invalidate incompatible results.

Serialized Earth service responses measured 1,105 bytes for deterministic analysis, 1,049 bytes for prediction, and 1,139 bytes for the scenario case. Training rows, benchmark datasets, and evaluation artifacts are not included in runtime responses.

## Regression evidence

- Scientific/AI/scenario output hash before and after: `8bfb9a1bca491e38d1bc43d5bbd18921c50e2163dddca499d70dfc26b329f977`.
- Visual QA covered the animated scene, Sun-facing illumination, outer-planet visibility, orbit paths, destination selection, the atmospheric SVG diagram, scattered-light color, and Scenario Mode.
- The browser produced no runtime errors. Three.js emits an upstream `THREE.Clock` deprecation warning from the rendering dependency; dependency migration was kept out of this low-risk pass.

Run the repeatable backend benchmark from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m training.benchmark_runtime --iterations 300
```

The benchmark is diagnostic and intentionally avoids brittle pass/fail timing thresholds.
