# Orbital model and simulation clock

## Scope

The simulator uses a deliberately simplified, coplanar two-body model. Every displayed planet,
dwarf planet, and existing supported moon advances from one shared simulated UTC timestamp. It
does not implement N-body perturbations, inclination, precession, or a precision ephemeris.

The versioned orbital inputs live in `data/orbitalElements.v1.json`. The pre-existing
`data/celestialBodies.json`, solar spectrum, training data, trained model, and evaluation report
remain unchanged.

## Reference data

- The eight planets use NASA/JPL's J2000 approximate Keplerian elements. Their J2000 mean anomaly
  is `mean longitude - longitude of perihelion`, and their published sidereal periods control the
  common-clock motion.
- Ceres, Pluto, Eris, Haumea, and Makemake use period, epoch, and mean anomaly values retrieved
  from the NASA/JPL Small-Body Database API. Their semimajor axes and eccentricities remain the
  preserved project catalog values.
- Moons use NASA/JPL Planetary Satellite Mean Elements. JPL states that these mean elements
  describe general orbit shape and are not precision ephemerides, so all moon positions are
  explicitly approximate. Triton's documented retrograde direction is retained.

Primary references:

- https://ssd.jpl.nasa.gov/planets/approx_pos.html
- https://ssd.jpl.nasa.gov/sats/elem/
- https://ssd-api.jpl.nasa.gov/doc/sbdb.html

## Equations

For elapsed simulated days `Δt`, period `P`, reference mean anomaly `M0`, and direction `d`:

```text
M = M0 + d 2π Δt / P
M = E - e sin(E)
x = a (cos(E) - e)
z = a sqrt(1 - e²) sin(E)
r = sqrt(x² + z²)
```

Kepler's equation is solved with Newton iteration. All orbits are placed in the `x-z` plane, with
`+x` pointing toward periapsis. A moon's parent-relative vector is added to its moving parent's
heliocentric vector. This is sufficient for the educational distance variation represented here;
it is not a replacement for JPL Horizons.

## Shared time and playback

The React clock stores one timestamp in milliseconds. Slow, normal, and fast playback advance it
by 1, 7, and 30 simulated days per real second. Playback rate changes only how quickly the clock
reaches a timestamp. Orbital state is a pure function of body data and that timestamp, so all
speeds produce the same solution at the same simulated time.

Selecting any body pauses the clock. The analysis request records that frozen timestamp. The user
may resume orbital movement; the panel retains its labeled frozen result until selection, date
entry, or a later pause supplies another analysis timestamp. This avoids API calls on animation
frames.

## Physical and rendered coordinates

Physical calculations use catalog semimajor axes in kilometres and parent-relative moon vectors.
Rendered coordinates use the existing logarithmic orbit compression and exaggerated body/moon
sizes. No physical distance, light time, irradiance, or angular diameter is ever derived from a
Three.js coordinate.

The displayed orbital angle is the approximate true anomaly measured from periapsis in the
simplified orbital plane.

## Dynamic light measurements

At a selected timestamp, the backend calculates:

```text
light time = r / 299792.458 km s⁻¹
irradiance = 1366.1 W m⁻² (1 AU / r)²
solar angular diameter = 2 atan(695700 km / r)
```

Stored reference distances and irradiances remain in the original catalog. Timestamped requests
use the dynamic inverse-square value. Atmospheric composition, pressure, density, and the
transmitted/scattered/absorbed physics remain fixed; orbital distance changes incoming intensity,
not the atmospheric assumptions.

The existing ML model v1.0 is reused without retraining. Its preserved feature contract already
accepts distance and incoming irradiance. The saved model, training dataset, random seed, and
evaluation report were not overwritten.

## API compatibility

Existing calls remain valid:

```text
GET /api/analyze/earth
GET /api/predict/earth
```

Dynamic calls add an optional ISO-8601 UTC query parameter:

```text
GET /api/predict/earth?at=2026-09-30T12:00:00.000Z
```

Timestamped responses include an `astronomy` object. Untimestamped responses retain the previous
reference behavior and return `astronomy: null`, allowing old clients and the updated client to
operate against the expanded API during deployment.

## Visual lighting

Three.js uses a non-attenuating point light at the Sun, moderate ambient light, hemisphere fill,
low material emissive fill, and slightly raised tone-mapping exposure. This keeps outer planets
readable while preserving a brighter Sun-facing hemisphere and a distinguishable dark side.

This scene lighting is presentation only. It does not feed the API, orbital model, solar spectrum,
physics engine, or ML features. Physical irradiance remains the inverse-square calculation above.

## Limitations

- Orbits are coplanar and omit perturbations and secular element rates.
- Planet formulae are approximate; JPL Horizons is required for precision ephemerides.
- Satellite mean elements are descriptive rather than precision ephemerides.
- Dwarf-planet phases are osculating values at their recorded epochs while the preserved catalog
  supplies their simplified `a` and `e`; long-range positions are approximate.
- Moon motion has a small but real effect on heliocentric distance in this model, though the scene
  exaggerates moon spacing for selection.
