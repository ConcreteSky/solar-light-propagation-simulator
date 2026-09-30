const RESULT_COLORS = {
  white: '#f4f4ee',
  yellow: '#ffd66b',
  orange: '#f59a4a',
  red: '#ef6b5c',
  blue: '#74a7ff',
  'pale blue': '#a9dce8',
  'pale yellow': '#f4e6a3',
  'dim white': '#aeb8c5',
  'gray-white': '#c4c8ca',
}

function prominence(value, minimum = 1.5, range = 8) {
  return minimum + Math.sqrt(Math.max(0, value ?? 0)) * range
}

function visibility(value) {
  if (!Number.isFinite(value) || value <= 0) return 0
  return 0.18 + Math.sqrt(value) * 0.82
}

function IncomingRays({ irradiance }) {
  const normalized = Number.isFinite(irradiance)
    ? Math.max(0, Math.min(1, Math.log10(1 + irradiance) / Math.log10(1367.1)))
    : 0.55
  const opacity = 0.3 + normalized * 0.65
  return [126, 174, 222].map((y) => (
    <line
      key={y}
      className="diagram-ray diagram-ray-incoming"
      x1="52"
      y1={y}
      x2="382"
      y2={y}
      markerEnd="url(#arrow-incoming)"
      opacity={opacity}
      strokeWidth={1.5 + normalized * 3.5}
    />
  ))
}

function AtmosphericDiagram({ results, resultColor }) {
  return (
    <>
      <path
        data-testid="atmosphere-boundary"
        className="diagram-atmosphere"
        d="M 448 62 Q 352 174 448 286"
      />
      <path className="diagram-surface" d="M 520 55 Q 415 174 520 293" />
      <path
        className="diagram-ray diagram-ray-transmitted"
        d="M 397 174 L 660 174"
        markerEnd="url(#arrow-result)"
        stroke={resultColor}
        strokeWidth={prominence(results.transmitted)}
        opacity={visibility(results.transmitted)}
      />
      <path
        className="diagram-ray diagram-ray-scattered"
        d="M 414 168 Q 480 95 566 73"
        markerEnd="url(#arrow-scatter)"
        strokeWidth={prominence(results.scattered, 1, 6)}
        opacity={visibility(results.scattered)}
      />
      <path
        className="diagram-ray diagram-ray-scattered"
        d="M 414 180 Q 470 252 555 272"
        markerEnd="url(#arrow-scatter)"
        strokeWidth={prominence(results.scattered, 1, 6)}
        opacity={visibility(results.scattered)}
      />
      <circle
        data-testid="absorption-indicator"
        className="diagram-absorption"
        cx="446"
        cy="174"
        r={8 + 25 * Math.sqrt(Math.max(0, results.absorbed ?? 0))}
        opacity={visibility(results.absorbed)}
      />
      <text x="425" y="38" className="diagram-label">Atmosphere</text>
      <text x="574" y="158" className="diagram-label">Transmitted</text>
      <text x="512" y="91" className="diagram-label">Scattered</text>
      <text x="426" y="325" className="diagram-label">Absorbed</text>
    </>
  )
}

function AirlessDiagram({ results }) {
  return (
    <>
      <path data-testid="surface-boundary" className="diagram-surface" d="M 492 45 Q 382 174 492 303" />
      <path
        className="diagram-ray diagram-ray-surface"
        d="M 397 174 L 478 174"
        strokeWidth={prominence(results.transmitted)}
        opacity={visibility(results.transmitted)}
      />
      <path
        data-testid="reflected-ray"
        className="diagram-ray diagram-ray-reflected"
        d="M 463 166 Q 390 88 300 76"
        markerEnd="url(#arrow-scatter)"
        strokeWidth={prominence(results.scattered, 1, 6)}
        opacity={visibility(results.scattered)}
      />
      <circle
        data-testid="absorption-indicator"
        className="diagram-absorption"
        cx="468"
        cy="183"
        r={8 + 25 * Math.sqrt(Math.max(0, results.absorbed ?? 0))}
        opacity={visibility(results.absorbed)}
      />
      <text x="438" y="31" className="diagram-label">Surface</text>
      <text x="355" y="154" className="diagram-label">Reaches surface</text>
      <text x="268" y="61" className="diagram-label">Reflected / scattered</text>
      <text x="424" y="326" className="diagram-label">Absorbed</text>
    </>
  )
}

export default function LightDiagram({ analysis }) {
  const atmospheric = analysis.hasAtmosphere === true
  const results = analysis.results
  const resultColor = RESULT_COLORS[results.dominantColor] ?? RESULT_COLORS.white

  return (
    <figure className="light-diagram-wrap">
      <svg
        className="light-diagram"
        data-mode={atmospheric ? 'atmospheric' : 'airless'}
        viewBox="0 0 720 350"
        role="img"
        aria-label={
          atmospheric
            ? 'Schematic atmospheric light interaction'
            : 'Schematic airless surface light interaction'
        }
      >
        <defs>
          <marker id="arrow-incoming" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#ffe1a0" />
          </marker>
          <marker id="arrow-result" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill={resultColor} />
          </marker>
          <marker id="arrow-scatter" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#b8d8ee" />
          </marker>
          <linearGradient id="body-shade" x1="0" x2="1">
            <stop offset="0" stopColor="#263650" />
            <stop offset="1" stopColor="#0a1020" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="720" height="350" rx="8" className="diagram-background" />
        <text x="52" y="99" className="diagram-label diagram-label-strong">Incoming sunlight</text>
        <IncomingRays irradiance={analysis.astronomy?.solarIrradianceWm2 ?? analysis.inputs?.solarIrradianceWm2} />
        {atmospheric ? (
          <AtmosphericDiagram results={results} resultColor={resultColor} />
        ) : (
          <AirlessDiagram results={results} />
        )}
      </svg>
      <figcaption>Light-interaction diagram is schematic.</figcaption>
    </figure>
  )
}
