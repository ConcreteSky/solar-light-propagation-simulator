# Scientific data sources

Accessed **2026-09-30**. The machine-readable mapping is in `data/sources.json`; each body records the source IDs used. Values are cached locally so normal app use does not call NASA, JPL, or NLR.

## Source policy

- Physical and atmospheric values: NASA NSSDCA individual fact sheets and NASA Science body pages.
- Planet heliocentric reference orbits: NASA NSSDCA metric fact table and individual fact sheets.
- Moon parent-centered orbits: NASA/JPL Planetary Satellite Mean Elements, cross-checked against NASA satellite fact sheets.
- Dwarf-planet orbits: NASA/JPL Horizons / Small-Body Database reference values.
- Spectrum and mean planet irradiance: ASTM E-490-00 workbook distributed by the National Laboratory of the Rockies (formerly NREL).
- Fractions are volume fractions. A `null` means the selected authoritative source did not provide a stable, useful numeric value; qualitative claims were not converted into invented numbers.

## Important value groups

| Bodies | Properties cached | Unit | Primary source |
|---|---|---|---|
| Mercury–Neptune | radius, diameter, mass, mean gravity, semimajor axis, eccentricity, perihelion, aphelion | km, kg, m/s² | [NASA Planetary Fact Sheets](https://nssdc.gsfc.nasa.gov/planetary/factsheet/) |
| Venus, Earth, Mars | pressure, near-surface density, major composition | Pa, kg/m³, fraction | NASA individual fact sheets: [Venus](https://nssdc.gsfc.nasa.gov/planetary/factsheet/venusfact.html), [Earth](https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html), [Mars](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) |
| Giant planets | major H₂/He/CH₄ composition | fraction | NASA individual planet fact sheets |
| Ceres, Pluto, Eris, Haumea, Makemake | physical values and heliocentric orbit | km, kg, km, dimensionless | [NASA dwarf planets](https://science.nasa.gov/dwarf-planets/) and [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) |
| Selected moons | physical values and parent-centered orbit | km, kg, m/s², dimensionless | [NASA Planetary Satellites](https://ssd.jpl.nasa.gov/sats/) and [JPL mean elements](https://ssd.jpl.nasa.gov/sats/elem/) |
| Titan | pressure, density, N₂/CH₄ fractions | Pa, kg/m³, fraction | [NASA Titan Facts](https://science.nasa.gov/saturn/moons/titan/facts/) |
| Triton | pressure and qualitative atmosphere | Pa | [NASA Triton](https://science.nasa.gov/neptune/moons/triton/) |
| Planet irradiance | mean reference solar irradiance | W/m² | [ASTM E-490 reference page](https://www.nlr.gov/grid/solar-resource/spectra-astm-e490) |

## ASTM E-490 local subset

`data/solarSpectrum.csv` is converted from the official E-490-00 workbook linked on the NLR reference page. It retains 516 rows from 300.5 through 1000.0 nm (the source grid has no 300.0 nm row). Source irradiance in W·m⁻²·µm⁻¹ was divided by 1000 to produce W·m⁻²·nm⁻¹. No interpolation or smoothing was applied.

## Derived reference fields

The E-490 page publishes mean irradiance for the eight planets and Pluto. For Ceres, Eris, Haumea, and Makemake, the cached reference uses the inverse-square relation from 1366.1 W/m² at 1 AU and the cited JPL semimajor axis. Light travel time uses the same cached distance and the exact conventional speed of light, 299,792.458 km/s. Moon reference light values use the parent planet because parent–moon separation is negligible at this app's educational scale.

## Deliberate nulls

- Giant planets: surface pressure and surface density are `null` because they have no solid reference surface; a one-bar level is not labeled as a surface.
- Pluto: its atmosphere is seasonal and variable, so stable surface pressure, density, and numeric gas fractions are not asserted here.
- Eris, Haumea, Makemake: atmosphere fields are `null` rather than treating uncertain or transient volatiles as a measured atmosphere.
- Haumea: radius is `null` because the body is strongly elongated; a single radius would hide the shape assumption.
- Makemake: mass and gravity are `null` because the reviewed NASA overview does not provide a suitably stable single reference value.
- Io, Europa, Ganymede, Callisto: the atmosphere flag and numeric atmosphere fields are `null` because their extremely tenuous exospheres are not equivalent to a modeled surface atmosphere.
- Most moon periapsis/apoapsis fields are `null`; the authoritative mean-element eccentricity is retained and future code can use it without presenting derived distances as separately published facts.

