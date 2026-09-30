const RESULT_COLORS = {
  white: '#f4f4ee', yellow: '#ffd66b', orange: '#f59a4a', red: '#ef6b5c', blue: '#74a7ff',
  'pale blue': '#a9dce8', 'pale yellow': '#f4e6a3', 'dim white': '#aeb8c5', 'gray-white': '#c4c8ca',
}

const DESTINATION_PALETTES = {
  mercury: { surface: '#8c8a84', shadow: '#24272d', atmosphere: '#aeb8c5' },
  venus: { surface: '#dfc47e', shadow: '#4a3921', atmosphere: '#f4e6a3' },
  earth: { surface: '#2f78c4', shadow: '#071c3c', atmosphere: '#78cfff' },
  mars: { surface: '#b94e2c', shadow: '#39150f', atmosphere: '#e58a62' },
  jupiter: { surface: '#caa77b', shadow: '#443225', atmosphere: '#e7cfaa' },
  saturn: { surface: '#d8c28e', shadow: '#453b27', atmosphere: '#efe0b4' },
  uranus: { surface: '#8bd5dc', shadow: '#17414c', atmosphere: '#b9f1f2' },
  neptune: { surface: '#3155b7', shadow: '#0a1745', atmosphere: '#7199ff' },
  titan: { surface: '#c67b32', shadow: '#40200e', atmosphere: '#f2a64e' },
  moon: { surface: '#85817b', shadow: '#242426', atmosphere: '#b7b4b0' },
  pluto: { surface: '#a7927c', shadow: '#302923', atmosphere: '#c9b9aa' },
}

const DEFAULT_PALETTE = { surface: '#9a8c78', shadow: '#24232a', atmosphere: '#a9dce8' }
const NEUTRAL_LIGHT_COLOR = 'rgb(244 232 190)'

export function getValidatedRgbColor(color) {
  const rgb = color?.rgb
  if (!Array.isArray(rgb) || rgb.length !== 3) return NEUTRAL_LIGHT_COLOR
  if (!rgb.every((channel) => Number.isInteger(channel) && channel >= 0 && channel <= 255)) {
    return NEUTRAL_LIGHT_COLOR
  }
  return `rgb(${rgb.join(' ')})`
}

function clamp01(value) {
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0
}

function prominence(value, minimum = 2, range = 11) {
  return minimum + Math.sqrt(clamp01(value)) * range
}

function visibility(value, floor = 0.16) {
  const safeValue = clamp01(value)
  return safeValue <= 0 ? 0 : floor + Math.sqrt(safeValue) * (1 - floor)
}

function incomingStrength(irradiance) {
  if (!Number.isFinite(irradiance)) return 0.55
  return clamp01(Math.log10(1 + irradiance) / Math.log10(1367.1))
}

function IncomingBeam({ irradiance }) {
  const strength = incomingStrength(irradiance)
  const opacity = 0.38 + strength * 0.58
  const width = 10 + strength * 9
  return (
    <g data-testid="incoming-beam" data-strength={strength.toFixed(3)}>
      <path className="diagram-beam-glow" d="M 64 250 L 536 250" strokeWidth={width + 22} opacity={0.08 + strength * 0.13} />
      <path className="diagram-ray diagram-ray-incoming" d="M 64 250 L 536 250" markerEnd="url(#arrow-incoming)" strokeWidth={width} opacity={opacity} />
    </g>
  )
}

function ScatteredFan({ fraction, color }) {
  const width = prominence(fraction, 1.3, 8.5)
  const opacity = visibility(fraction, 0.1)
  const rays = [
    'M 550 240 Q 492 145 382 102',
    'M 544 247 Q 468 201 366 184',
    'M 544 253 Q 468 299 366 316',
    'M 550 260 Q 492 355 382 398',
  ]
  return (
    <g data-testid="scattered-fan" data-fraction={clamp01(fraction).toFixed(3)}>
      {rays.map((path) => (
        <path key={path} className="diagram-ray diagram-ray-scattered" d={path} markerEnd="url(#arrow-scatter)" stroke={color} strokeWidth={width} opacity={opacity} />
      ))}
    </g>
  )
}

function AbsorptionRegion({ fraction, atmospheric }) {
  const safeFraction = clamp01(fraction)
  return (
    <g data-testid="absorption-indicator" data-fraction={safeFraction.toFixed(3)}>
      <ellipse
        className="diagram-absorption-glow"
        cx={atmospheric ? 590 : 575}
        cy="250"
        rx={18 + 48 * Math.sqrt(safeFraction)}
        ry={38 + 72 * Math.sqrt(safeFraction)}
        opacity={visibility(safeFraction, 0.08)}
      />
      <path
        className="diagram-absorption-mark"
        d={atmospheric ? 'M 566 250 L 626 250' : 'M 554 250 L 608 250'}
        strokeWidth={3 + safeFraction * 12}
        opacity={visibility(safeFraction, 0.12)}
      />
    </g>
  )
}

function PlanetSurface({ palette, atmospheric }) {
  return (
    <>
      {atmospheric && (
        <>
          <circle data-testid="atmosphere-boundary" className="diagram-atmosphere-glow" cx="800" cy="250" r="247" stroke={palette.atmosphere} />
          <circle className="diagram-atmosphere-shell" cx="800" cy="250" r="238" stroke={palette.atmosphere} />
        </>
      )}
      <circle data-testid="surface-boundary" className="diagram-planet-surface" cx="800" cy="250" r="224" fill="url(#planet-surface-gradient)" stroke={palette.surface} />
      <path className="diagram-horizon-highlight" d="M 612 128 Q 555 250 612 372" />
    </>
  )
}

function AtmosphericDiagram({ results, palette, scatteredColor }) {
  return (
    <>
      <PlanetSurface palette={palette} atmospheric />
      <ScatteredFan fraction={results.scattered} color={scatteredColor} />
      <path
        data-testid="transmitted-beam"
        data-fraction={clamp01(results.transmitted).toFixed(3)}
        className="diagram-ray diagram-ray-transmitted"
        d="M 544 250 L 742 250"
        markerEnd="url(#arrow-result)"
        strokeWidth={prominence(results.transmitted, 3, 15)}
        opacity={visibility(results.transmitted)}
      />
      <AbsorptionRegion fraction={results.absorbed} atmospheric />
      <text x="68" y="212" className="diagram-label diagram-label-strong">Incoming sunlight</text>
      <text x="594" y="62" className="diagram-label">Atmosphere</text>
      <text x="650" y="228" className="diagram-label diagram-label-result">Transmitted</text>
      <text x="393" y="82" className="diagram-label">Scattered</text>
      <text x="566" y="432" className="diagram-label">Absorbed</text>
    </>
  )
}

function AirlessDiagram({ results, palette, scatteredColor }) {
  return (
    <>
      <PlanetSurface palette={palette} atmospheric={false} />
      <path
        data-testid="transmitted-beam"
        data-fraction={clamp01(results.transmitted).toFixed(3)}
        className="diagram-ray diagram-ray-surface"
        d="M 544 250 L 627 250"
        strokeWidth={prominence(results.transmitted, 3, 15)}
        opacity={visibility(results.transmitted)}
      />
      <g data-testid="reflected-ray"><ScatteredFan fraction={results.scattered} color={scatteredColor} /></g>
      <AbsorptionRegion fraction={results.absorbed} atmospheric={false} />
      <text x="68" y="212" className="diagram-label diagram-label-strong">Incoming sunlight</text>
      <text x="594" y="62" className="diagram-label">Surface</text>
      <text x="514" y="228" className="diagram-label diagram-label-result">Reaches surface</text>
      <text x="386" y="82" className="diagram-label">Reflected / scattered</text>
      <text x="554" y="432" className="diagram-label">Absorbed</text>
    </>
  )
}

function getPrimaryResult(results, atmospheric) {
  const candidates = [
    { label: atmospheric ? 'transmitted' : 'reaches surface', value: results.transmitted },
    { label: atmospheric ? 'scattered' : 'reflected / scattered', value: results.scattered },
    { label: 'absorbed', value: results.absorbed },
  ]
  return candidates.reduce((strongest, candidate) => (
    clamp01(candidate.value) > clamp01(strongest.value) ? candidate : strongest
  ))
}

export default function LightDiagram({ analysis }) {
  const atmospheric = analysis.hasAtmosphere === true
  const results = analysis.results
  const resultColor = RESULT_COLORS[results.dominantColor] ?? RESULT_COLORS.white
  const scatteredColor = getValidatedRgbColor(results.scatteredLightColor)
  const transmittedColor = getValidatedRgbColor(results.transmittedLightColor)
  const palette = DESTINATION_PALETTES[analysis.destination] ?? DEFAULT_PALETTE
  const primaryResult = getPrimaryResult(results, atmospheric)
  const primaryPercent = (clamp01(primaryResult.value) * 100).toFixed(1)
  const irradiance = analysis.astronomy?.solarIrradianceWm2 ?? analysis.inputs?.solarIrradianceWm2

  return (
    <figure
      className="light-diagram-wrap"
      data-destination={analysis.destination}
      style={{
        '--diagram-result-color': resultColor,
        '--diagram-scatter-color': scatteredColor,
        '--diagram-transmitted-color': transmittedColor,
        '--diagram-atmosphere-color': palette.atmosphere,
      }}
    >
      <svg
        className="light-diagram"
        data-mode={atmospheric ? 'atmospheric' : 'airless'}
        viewBox="0 0 900 500"
        role="img"
        aria-label={atmospheric ? `Schematic atmospheric light interaction at ${analysis.name}` : `Schematic airless surface light interaction at ${analysis.name}`}
      >
        <defs>
          <linearGradient id="diagram-background-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#0d172a" /><stop offset="0.58" stopColor="#080f1e" /><stop offset="1" stopColor="#050913" />
          </linearGradient>
          <radialGradient id="planet-surface-gradient" cx="22%" cy="42%" r="78%">
            <stop offset="0" stopColor={palette.surface} /><stop offset="0.42" stopColor={palette.surface} /><stop offset="1" stopColor={palette.shadow} />
          </radialGradient>
          <linearGradient id="incoming-light-gradient" gradientUnits="userSpaceOnUse" x1="64" y1="250" x2="536" y2="250">
            <stop offset="0" stopColor="#fffdf0" stopOpacity="0.78" /><stop offset="0.55" stopColor="#ffe5a3" /><stop offset="1" stopColor="#ffd06b" />
          </linearGradient>
          <linearGradient id="result-light-gradient" gradientUnits="userSpaceOnUse" x1="544" y1="250" x2="742" y2="250">
            <stop offset="0" stopColor="#fff4c9" /><stop offset="0.48" stopColor={transmittedColor} /><stop offset="1" stopColor={transmittedColor} stopOpacity={0.24 + clamp01(results.transmitted) * 0.6} />
          </linearGradient>
          <linearGradient id="absorption-gradient" gradientUnits="userSpaceOnUse" x1="554" y1="250" x2="626" y2="250">
            <stop offset="0" stopColor="#ff9a64" stopOpacity="0.72" /><stop offset="1" stopColor="#101522" stopOpacity="0" />
          </linearGradient>
          <filter id="soft-beam-glow" x="-30%" y="-100%" width="160%" height="300%"><feGaussianBlur stdDeviation="10" /></filter>
          <filter id="soft-atmosphere-glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="8" /></filter>
          <marker id="arrow-incoming" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="20" markerHeight="20" markerUnits="userSpaceOnUse" orient="auto"><path d="M 0 0 L 12 6 L 0 12 z" fill="#ffd77f" /></marker>
          <marker id="arrow-result" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="18" markerHeight="18" markerUnits="userSpaceOnUse" orient="auto"><path d="M 0 0 L 12 6 L 0 12 z" fill={transmittedColor} /></marker>
          <marker id="arrow-scatter" viewBox="0 0 12 12" refX="9" refY="6" markerWidth="14" markerHeight="14" markerUnits="userSpaceOnUse" orient="auto"><path d="M 0 0 L 12 6 L 0 12 z" fill={scatteredColor} /></marker>
        </defs>
        <rect width="900" height="500" rx="12" fill="url(#diagram-background-gradient)" />
        <path className="diagram-grid-line" d="M 0 250 L 900 250" />
        <IncomingBeam irradiance={irradiance} />
        {atmospheric
          ? <AtmosphericDiagram results={results} palette={palette} scatteredColor={scatteredColor} />
          : <AirlessDiagram results={results} palette={palette} scatteredColor={scatteredColor} />}
      </svg>
      <div className="diagram-primary-result" data-testid="primary-result">
        <span>Primary interaction</span><strong>{primaryPercent}% {primaryResult.label}</strong>
      </div>
      <figcaption>Light-interaction diagram is schematic. RGB colors show broad modeled classes, not exact human perception.</figcaption>
    </figure>
  )
}
