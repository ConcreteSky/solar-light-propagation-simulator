# Deterministic physics model

## Purpose and scope

Version 1.0.0 is an explainable educational baseline for the simulator. It converts the stored catalog measurements into stable light-behavior labels. It is not a radiative-transfer solver, atmospheric weather model, spectral-line calculation, or claim of research-grade accuracy.

The same rules are used for real-body benchmarks and synthetic labels. There are no per-body final-answer tables. Real catalog rows are kept separate from synthetic training rows.

## Inputs and source priority

`GET /api/analyze/{destinationId}` resolves the stable body ID in `data/celestialBodies.json`. The calculation uses:

- heliocentric semimajor-axis distance; a moon inherits its parent planet's heliocentric distance;
- stored reference solar irradiance when available;
- atmosphere state, pressure, density, and the stored CO2, N2, O2, CH4, H2, and He fractions;
- the local ASTM E-490 spectrum in `data/solarSpectrum.csv`.

Rendered scene coordinates, display colors, textures, and materials are never scientific inputs. The E-490 table is integrated with the trapezoid rule over its stored 300.5–1000 nm range and over the broad 380–780 nm visible interval. Its calculated visible share is returned for traceability. The current aggregate model uses that common spectral shape as the reference; it does not fabricate missing wavelengths or resolve absorption lines.

## Solar input

The inverse-square validation value is:

```text
Iderived = 1366.1 × (149,597,870.7 km / distanceKm)^2
```

The stored irradiance is preferred. When it is absent, the derived value is used and a warning is returned. When both exist and differ by more than 10%, the stored value remains authoritative and the response reports a validation warning.

## Atmospheric model

Pressure and density are expressed relative to 101,325 Pa and 1.225 kg/m³. Available ratios are averaged and compressed into a dimensionless optical-column proxy:

```text
column = log(1 + mean(pressureRatio, densityRatio)) / log(2)
```

Known gas fractions are normalized only inside the optical calculation. Missing individual trace gases contribute zero. The broad visible-light weights are:

| Gas | Scattering weight | Absorption weight |
| --- | ---: | ---: |
| CO2 | 0.45 | 0.25 |
| N2 | 1.00 | 0.02 |
| O2 | 1.05 | 0.12 |
| CH4 | 0.35 | 1.50 |
| H2 | 1.70 | 0.00 |
| He | 0.25 | 0.00 |

These are aggregate teaching coefficients, not laboratory cross-sections. Optical depths are:

```text
tauScatter = 0.16 × column × (0.35 + 0.65 × weightedScatterMix)
tauAbsorb  = 0.07 × column × (0.25 + 0.75 × weightedAbsorptionMix)
transmitted = exp(-(tauScatter + tauAbsorb))
```

Removed energy is divided between scattering and absorption according to their optical-depth shares. A small escape factor, `1 / (1 + 0.05 × column)`, moves multiply interacted scattered energy into the absorbed bucket for dense columns.

In this linear approximation, irradiance scales brightness but does not change normalized atmospheric fractions. Full nonlinear photochemistry is outside scope.

If pressure and density are both missing, the service applies a clearly warned `0.15` composition-only optical-column fallback. If composition is also missing, neutral coefficients are used. Such results have `calculationStatus: "partial"`; missing values remain null in the response.

## Airless-body model

When `hasAtmosphere` is false, atmospheric calculations are skipped. Because the current catalog has no sourced albedo or wavelength-dependent surface reflectance, all airless bodies use one transparent educational partition:

- 0.85 direct/reaching-surface;
- 0.10 reflected/scattered;
- 0.05 absorbed in the simplified surface channel.

The API warns that the generic partition was used. It is not a measured albedo. When atmosphere state is null, the same airless/tenuous fallback is used with `calculationStatus: "partial"` and an additional warning.

## Conservation and validation

Raw fractions are clamped to `[0, 1]`, normalized, and serialized to six decimal places. The rounding remainder is assigned to absorption, so:

```text
transmitted + scattered + absorbed = 1.0
```

All calculated numbers must be finite. Invalid distances, negative irradiance, NaN, and infinity cause calculation failure rather than an invalid API payload. `validation.valid` confirms fraction conservation and the brightness range.

## Relative brightness and apparent size

`relativeBrightness` is a 0–1 educational display value, not an absolute model of human vision:

```text
illumination = min(1, log(1 + 9 × irradiance / 1366.1) / log(10))
availableLight = transmitted + 0.5 × scattered
relativeBrightness = clamp(illumination × availableLight, 0, 1)
```

The logarithm keeps outer-System differences visible without allowing inner planets to exceed one.

Apparent Sun size uses heliocentric distance only:

- large: at most 0.75 AU;
- medium: over 0.75 through 1.25 AU;
- small: over 1.25 through 8 AU;
- very small: over 8 AU.

## Broad color classification

The classifier returns only `white`, `yellow`, `orange`, `red`, `blue`, `pale blue`, `pale yellow`, `dim white`, or `gray-white`. Reusable rules consider methane in H2/He or N2 atmospheres, dense CO2 columns, brightness, and the calculated scattering/absorption fractions. Strong composition-driven hues are classified before the low-brightness fallback, so distance does not erase a characteristic broad hue. The logic does not inspect destination IDs. The categories describe a broad educational appearance, not a rendered RGB color or full spectrum.

## Synthetic generation

`backend/training/generate_training_data.py` uses NumPy's seeded generator. Version 1.0.0 defaults to seed 741 and 10,000 rows:

- distance is log-uniform from 0.3 to 70 AU;
- irradiance follows the same inverse-square relation;
- 72% of samples have an atmosphere;
- atmospheric pressure is sampled across near-vacuum (0.01–100 Pa), thin (100–20,000 Pa), moderate (20,000–200,000 Pa), and dense (200,000–10,000,000 Pa) regimes;
- temperature is a hidden generation variable from 70–800 K;
- density is derived with the ideal-gas relation and the sampled mixture's mean molar mass, capped at 100 kg/m³;
- gas mixtures come from Dirichlet distributions around broad terrestrial, CO2-rich, N2/CH4-rich, H2/He-rich, and mixed archetypes and sum to one;
- airless rows have zero pressure, density, and gas fractions;
- rows are assigned deterministically to 80% train, 10% validation, and 10% test splits.

The categorical label and its stable integer code are both stored. This session does not train or evaluate an ML model.

## Known limitations

- Aggregate coefficients omit clouds, aerosols, dust, surface albedo, viewing geometry, altitude, seasons, weather, and detailed wavelength dependence.
- Dense gas planets lack a defined solid surface; missing catalog pressure/density makes their results partial.
- Several dwarf planets and moons have unknown atmosphere state and therefore use the explicitly warned fallback.
- The airless surface partition is shared and illustrative until sourced albedo data is added in a future, versioned catalog change.
- Color categories are coarse qualitative labels.
- The model assumes mean orbital distance, not instantaneous orbital position.

Any coefficient or formula change must increment the physics/generator version and regenerate both the synthetic dataset and all real-body benchmarks before Session 4 comparisons.
