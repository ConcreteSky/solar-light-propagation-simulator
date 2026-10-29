# Magnetic fields and visual families

The simulator distinguishes physical interaction families instead of drawing one generic ring around every selected body.

| Family | Examples | Selected-body visual |
| --- | --- | --- |
| `intrinsic_dipole` | Mercury, Earth, Jupiter | compressed dayside loops and an extended tail |
| `intrinsic_aligned` | Saturn | symmetric, nearly aligned intrinsic loops |
| `intrinsic_tilted_offset` | Uranus, Neptune | visibly tilted and offset loops |
| `induced` | Venus, Europa, Callisto, Titan | open draped lines; no closed intrinsic dipole |
| `crustal_remnant` | Mars, Moon | localized surface arcs |
| `intrinsic_mini` | Ganymede | compact intrinsic mini-magnetosphere |
| `parent_plasma` | Io and several outer-planet moons | sweeping parent-magnetosphere plasma lines |
| `negligible` / `unknown` | small bodies with insufficient evidence | no invented field overlay |

The Three.js overlay is rendered only for the selected body and uses a few low-segment lines. Its size is illustrative and is not a measurement. Numeric field ranges are shown only when the source catalog supports them.

Primary references and exact URLs are mapped in `data/sources.json`, including NASA/NSSDCA planet fact sheets, NASA magnetosphere pages, Mars Global Surveyor results, and mission pages for Europa, Ganymede, and Titan.
