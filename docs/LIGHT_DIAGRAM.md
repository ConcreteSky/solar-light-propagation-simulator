# Dynamic light-interaction diagram

## Component structure

Session 5 adds one lower analysis section without changing the 3D Solar System layout or selection convention.

- `App.jsx` continues to own `selectedBodyId` and passes the selected catalog body to the result section.
- `ResultPanel.jsx` requests and presents one destination result.
- `LightDiagram.jsx` renders one reusable SVG in atmospheric or airless mode.
- `services/api.js` retrieves validated backend output and performs a secondary deterministic request if the prediction endpoint itself is unavailable.
- `utils/lightAnalysis.js` formats stored reference measurements and generates the single short sentence.

No component recalculates atmospheric physics or ML predictions.

## Required diagram input

`LightDiagram` receives the standardized response returned by `/api/predict/{destinationId}` or the frontend's schema-compatible `/api/analyze/{destinationId}` fallback. It uses:

- `hasAtmosphere`;
- transmitted fraction;
- scattered fraction;
- absorbed fraction;
- relative brightness;
- deterministic broad color category.

Fractions must already be validated by the backend. The diagram has a fixed `viewBox`, so it scales with its container without changing the modeled values.

## Atmospheric mode

When `hasAtmosphere` is exactly `true`, the SVG shows incoming neutral sunlight, a schematic atmospheric boundary, the destination surface/body boundary, a transmitted ray, two predefined scattered paths, and an absorption marker.

Calculated fractions control stroke width and opacity. Relative brightness controls only incoming-ray prominence. Scattering directions never change and do not claim a real viewing angle.

## Airless and uncertain-atmosphere mode

When `hasAtmosphere` is `false`, no atmospheric boundary is drawn. The same component shows incoming light reaching a surface, one predefined reflected/scattered path, and absorption.

When atmosphere state is unknown, the backend already returns its explicitly warned airless/tenuous deterministic fallback. The frontend uses the surface mode and displays the first warning as a data note. It does not invent an atmosphere.

The Session 3 airless percentages are a generic educational surface partition because sourced surface albedo is not available. UI labels therefore say “Reaches surface” and “Reflected / scattered,” not atmospheric transmission. They must not be described as measured reflection percentages.

## Color handling

Incoming sunlight is always neutral warm white. It is not recolored to match a sky. The transmitted/result ray may use the backend's limited deterministic category: white, yellow, orange, red, blue, pale blue, pale yellow, dim white, or gray-white. Scattered paths use one subdued neutral-blue diagram color for legibility, not as a claim that the directly viewed Sun or sky has that color.

The appearance sentence uses the backend's deterministic apparent-size and color categories. `dim white` becomes the simpler supported word “dim.” If no supported category exists, the sentence says “neutral in color” instead of inventing a hue.

## Scientific values

The panel displays only:

- average heliocentric semimajor-axis distance in km;
- stored reference light-travel time in seconds;
- stored reference solar irradiance in W/m²;
- the three interaction fractions as percentages.

Moon distance uses the stored parent planet's heliocentric semimajor axis, matching the catalog's `parent_semimajor_axis` convention. Values are labeled as average/reference quantities and are not instantaneous orbital measurements. Missing reference values display `Data unavailable`.

## API integration and request safety

The normal request is:

```text
GET /api/predict/{destinationId}
```

This endpoint already reports whether ML or deterministic fallback produced the result. If the prediction request fails for a reason other than cancellation or an invalid ID, the frontend requests:

```text
GET /api/analyze/{destinationId}
```

The adapted response is explicitly labeled `deterministic_fallback`. A 404 remains an error rather than producing decorative data.

Every selection creates an `AbortController`. A monotonically increasing request sequence also prevents an older response from replacing a newer selection even if a transport ignores cancellation.

## Limitations

- The diagram is schematic and not to spatial, angular, or intensity scale.
- Ray paths do not model observer position, ray tracing, Mie scattering, or spectral lines.
- The AI approximates the deterministic educational model, not independent observations.
- Absorption is shown as a simple marker rather than a physical location or thermal process.
- Missing core scientific inputs use the backend's disclosed fallback; the frontend does not synthesize replacements.
