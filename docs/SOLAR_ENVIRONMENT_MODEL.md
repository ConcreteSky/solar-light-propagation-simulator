# Solar environment model

Version 1.0.0 expands the application from a light-only simulator into a layered Solar Environment Simulator. It preserves the original light engine and adds a reference-based magnetic, charged-particle, radiation-context, and shielding layer for all 32 destinations.

## Layer boundaries

1. **Light:** the existing deterministic atmosphere/surface model and reliability-aware ML surrogate. Its fractions, OOD screening, uncertainty, and fallback behavior are unchanged.
2. **Particles and radiation context:** qualitative local categories from reviewed NASA sources. These are not dose estimates, real-time space weather, or trajectory forecasts.
3. **Magnetic interaction:** a body-specific field family, geometry, origin, approximate strength where a defensible range exists, and a qualitative shielding category.

`data/solarEnvironment.v1.json` is independent of `data/celestialBodies.json` and versioned separately. Unknown values remain `null` or `unknown`; no generic field is invented to fill a gap.

## Dynamic values

Each prediction response includes `solarEnvironment`. Solar irradiance comes from the same frozen orbital state as the light analysis. `steadyStateSolarWindFluxProxy` is the irradiance ratio to 1361 W/m² and is only an inverse-square steady-input proxy. It is explicitly not an event forecast.

Atmospheric shielding is recalculated from Scenario Mode pressure: absent, minimal below 100 Pa, limited below 10 kPa, moderate below 500 kPa, and substantial above that. Magnetic shielding is held to the stored reference record. The combined category and scenario-adjusted surface exposure are conservative ordinal classifications, not dosimetry.

## Honest uncertainty

Every record declares `dataQuality` as `supported`, `limited`, or `unknown`, plus an `approximate` flag and source IDs. Bodies such as Eris, Haumea, Makemake, and Nereid show unknown magnetic state rather than a decorative dipole. Giant-planet “surface exposure” is `not_applicable` because there is no solid reference surface.
