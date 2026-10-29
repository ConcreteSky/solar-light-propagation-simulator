import { formatDistance, formatIrradiance, formatPercent, formatTravelTime, getAverageSolarDistanceKm } from '../../utils/lightAnalysis.js'

const titleCase = (value) => value == null ? 'Unknown' : String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

export function fieldSchematic(family) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 2 }
  if (['intrinsic_dipole', 'intrinsic_aligned', 'intrinsic_mini'].includes(family)) return <g {...common} className="field-lines">
    <path d="M140 88 C78 22 58 195 140 142"/><path d="M140 88 C215 18 300 55 344 108"/><path d="M140 98 C205 53 265 70 315 109"/><path d="M140 132 C205 177 265 151 315 111"/><path d="M140 142 C215 202 300 165 344 112"/>
    <path d="M83 42 C60 66 55 158 84 181" className="magnetopause-line"/>
  </g>
  if (family === 'intrinsic_tilted_offset') return <g {...common} className="field-lines" transform="translate(12 -6) rotate(-34 145 115)"><path d="M140 88 C72 25 62 194 140 142"/><path d="M140 88 C218 18 306 55 346 108"/><path d="M140 98 C211 54 275 72 322 109"/><path d="M140 132 C211 176 275 149 322 111"/><path d="M140 142 C218 202 306 165 346 112"/><path d="M82 43 C57 72 57 157 84 182" className="magnetopause-line"/></g>
  if (family === 'induced') return <g {...common} className="field-lines induced-lines"><path d="M8 62 C83 60 90 75 118 88 C170 111 245 72 350 76"/><path d="M8 158 C83 160 90 145 118 132 C170 109 245 148 350 144"/><path d="M12 86 C80 87 91 92 116 101 C180 124 248 98 347 99"/><path d="M12 134 C80 133 91 128 116 119 C180 96 248 122 347 121"/><path d="M101 64 C78 89 78 133 101 157" className="magnetopause-line"/></g>
  if (family === 'crustal_remnant') return <g {...common} className="crustal-lines"><path d="M118 101 Q128 70 140 99"/><path d="M137 94 Q151 59 165 97"/><path d="M157 101 Q169 75 181 104"/><path d="M112 116 Q125 139 137 118"/><path d="M153 128 Q166 155 179 126"/><path d="M92 74 C66 97 66 132 91 153" strokeDasharray="5 7"/></g>
  if (family === 'parent_plasma') return <g {...common} className="field-lines parent-plasma-lines">{[58,84,112,140,166].map((y) => <path key={y} d={`M5 ${y} C88 ${y - 20} 230 ${y + 22} 355 ${y - 3}`}/>)}</g>
  return <g {...common} className="unknown-field"><circle cx="145" cy="110" r="54" strokeDasharray="5 7"/><text x="214" y="114" fill="currentColor" stroke="none">Field not established</text></g>
}

function IncomingPanel({ environment, analysis, body }) {
  const dynamic = environment.dynamic
  return <section className="interaction-panel incoming-panel" aria-labelledby="incoming-title">
    <h3 id="incoming-title"><span>A</span> Incoming solar environment</h3>
    <p className="panel-intro">Two different things arrive from the Sun. Light carries radiant energy; the solar wind is a flow of electrically charged matter.</p>
    <svg viewBox="0 0 520 230" role="img" aria-label={`Sunlight and charged particles approaching ${body.name} as separate streams`}>
      <defs><marker id="particle-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z"/></marker><linearGradient id="light-beam" x1="0" x2="1"><stop offset="0" stopColor="#ffe590" stopOpacity=".9"/><stop offset="1" stopColor="#ffd05a" stopOpacity=".18"/></linearGradient></defs>
      <circle cx="58" cy="112" r="42" className="sun-corona"/><circle cx="58" cy="112" r="29" className="profile-sun"/><text x="40" y="176">SUN</text>
      <path d="M94 76 L432 91 L432 126 L94 146 Z" className="photon-beam"/>
      {[88,103,118,133].map((y) => <path key={y} d={`M96 ${y} L421 ${y + (y - 110) * 0.18}`} className="photon-ray"/>)}
      <text x="175" y="68" className="stream-title photon-title">VISIBLE LIGHT / PHOTONS</text><text x="198" y="84" className="stream-note">radiant energy · travels directly</text>
      {[164,184,204].map((y, index) => <path key={y} d={`M92 ${y} C180 ${y - 22} 280 ${y + 20} 414 ${y - index * 3}`} className="particle-flow" markerEnd="url(#particle-arrow)"/>)}
      {[135,190,250,318,375].map((x, index) => <circle key={x} cx={x} cy={180 + Math.sin(index * 1.8) * 17} r="3" className="particle-dot"/>)}
      <text x="172" y="224" className="stream-title particle-title">SOLAR WIND / CHARGED PARTICLES</text>
      {analysis.hasAtmosphere && <circle cx="454" cy="111" r="39" className="atmosphere-shell"/>}<circle cx="454" cy="111" r="27" className="profile-body"/><text x="438" y="116" className="body-monogram">{body.name.slice(0, 3).toUpperCase()}</text>
      <path d="M416 42 L446 78" className="callout-line"/><text x="335" y="31" className="callout-label">{analysis.hasAtmosphere ? 'ATMOSPHERE' : 'LOCAL ENVIRONMENT'}</text>
    </svg>
    <div className="diagram-key" aria-label="Incoming environment explanation"><div><i className="key-photon"/><span><strong>Light input</strong> sets irradiance and drives the visible-light calculation.</span></div><div><i className="key-particle"/><span><strong>Particle input</strong> is redirected, trapped, or admitted according to the local magnetic and atmospheric environment.</span></div></div>
    <div className="profile-readouts"><strong>{formatIrradiance(dynamic.solarIrradianceWm2)}</strong><span>{dynamic.steadyStateSolarWindFluxProxy.toFixed(3)}× Earth steady-flux proxy</span><span>{dynamic.uvContext}</span></div>
  </section>
}

function MagneticPanel({ environment, body }) {
  const magnetic = environment.magnetic
  return <section className="interaction-panel magnetic-panel" aria-labelledby="magnetic-title">
    <h3 id="magnetic-title"><span>B</span> Magnetic interaction</h3>
    <p className="panel-intro">Field lines show how charged particles are guided around or toward the body. They do not bend the yellow sunlight shown above.</p>
    <svg viewBox="0 0 360 220" data-field-family={magnetic.family} role="img" aria-label={`${titleCase(magnetic.family)} magnetic-field schematic for ${body.name}`}>
      <defs><marker id="wind-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0 L10 5 L0 10 z"/></marker><radialGradient id="body-shade"><stop offset="0" stopColor="#294d70"/><stop offset="1" stopColor="#102236"/></radialGradient></defs>
      <g className="upstream-wind">{[72,105,138].map((y) => <path key={y} d={`M6 ${y} C34 ${y - 5} 52 ${y + 4} 75 ${y}`} markerEnd="url(#wind-arrow)"/>)}</g>
      {fieldSchematic(magnetic.family)}
      <circle cx="145" cy="110" r="26" className="profile-body detailed-body"/><text x="128" y="115" className="body-monogram">{body.name.slice(0, 3).toUpperCase()}</text>
      <path d="M63 31 L82 61" className="callout-line"/><text x="9" y="22" className="callout-label">SUNWARD SIDE</text>
      <path d="M279 29 L296 71" className="callout-line"/><text x="249" y="20" className="callout-label">DOWNSTREAM</text>
      <text x="7" y="194" className="wind-label">CHARGED SOLAR PARTICLES</text><text x="237" y="194" className="tail-label">{magnetic.family === 'crustal_remnant' ? 'LOCAL ANOMALIES' : magnetic.family === 'induced' ? 'DRAPED TAIL' : magnetic.family === 'parent_plasma' ? 'PARENT PLASMA FLOW' : 'MAGNETIC TAIL / WAKE'}</text>
    </svg>
    <div className="field-explainer"><div><span>Origin</span><strong>{magnetic.origin}</strong></div><div><span>Topology</span><strong>{magnetic.geometry}</strong></div><div><span>Interpretation</span><strong>{magnetic.notes}</strong></div></div>
  </section>
}

function ShieldingPanel({ environment }) {
  const dynamic = environment.dynamic
  return <section className="interaction-panel shielding-panel" aria-labelledby="shielding-title">
    <h3 id="shielding-title"><span>C</span> Shielding &amp; exposure</h3>
    <div className="shielding-stack" aria-label="Shielding layers">
      <div><span>Magnetic</span><strong data-level={dynamic.magneticShielding}>{titleCase(dynamic.magneticShielding)}</strong></div>
      <div><span>Atmospheric</span><strong data-level={dynamic.atmosphericShielding}>{titleCase(dynamic.atmosphericShielding)}</strong></div>
      <div><span>Combined</span><strong data-level={dynamic.combinedShielding}>{titleCase(dynamic.combinedShielding)}</strong></div>
      <div className="exposure-row"><span>Surface exposure</span><strong data-level={dynamic.scenarioAdjustedSurfaceExposure}>{titleCase(dynamic.scenarioAdjustedSurfaceExposure)}</strong></div>
    </div>
    <p>{dynamic.consequence}</p>
  </section>
}

function Metric({ label, children }) { return <div><dt>{label}</dt><dd>{children ?? 'Unknown'}</dd></div> }

function MetricsPanel({ body, bodies, analysis, environment }) {
  const astronomy = analysis.astronomy
  const magnetic = environment.magnetic
  const strength = magnetic.surfaceStrengthMicrotesla
  const distance = astronomy?.distanceFromSunKm ?? getAverageSolarDistanceKm(body, bodies)
  return <section className="interaction-panel metrics-panel" aria-labelledby="metrics-title">
    <h3 id="metrics-title"><span>D</span> Environment metrics</h3>
    <dl>
      <Metric label="Sun distance">{formatDistance(distance)}</Metric><Metric label="Light travel">{formatTravelTime(astronomy?.lightTravelTimeSeconds ?? body.light_reference?.light_travel_time_seconds)}</Metric>
      <Metric label="Field family">{titleCase(magnetic.family)}</Metric><Metric label="Surface field">{strength ? `${strength.min ?? '?'}–${strength.max ?? '?'} μT` : 'Not established'}</Metric>
      <Metric label="Magnetosphere">{titleCase(magnetic.magnetospherePresence)}</Metric><Metric label="Solar-wind exposure">{titleCase(environment.particleEnvironment.solarWindExposure)}</Metric>
      <Metric label="Radiation context">{titleCase(environment.particleEnvironment.radiationLevel)}</Metric><Metric label="Trapped particles">{titleCase(environment.particleEnvironment.trappedRadiation)}</Metric>
    </dl>
  </section>
}

function LightInteraction({ analysis }) {
  const result = analysis.results
  return <section className="light-interaction" aria-labelledby="light-interaction-title"><div><p className="subsystem-label">Preserved light subsystem</p><h3 id="light-interaction-title">Visible-light interaction</h3></div><div className="light-bars">
    {['transmitted','scattered','absorbed'].map((key) => <div key={key}><span>{titleCase(key)}</span><meter min="0" max="1" value={result[key]} /><strong>{formatPercent(result[key])}</strong></div>)}
  </div><dl><Metric label="Apparent size">{titleCase(result.apparentSizeCategory)}</Metric><Metric label="Transmitted color">{result.transmittedLightColor?.label ?? result.dominantColor}</Metric><Metric label="Scattered color">{result.scatteredLightColor?.label}</Metric></dl></section>
}

export default function SolarInteractionProfile({ body, bodies, analysis }) {
  const environment = analysis.solarEnvironment
  if (!environment) return <p className="analysis-note">Solar-environment data is unavailable for this response.</p>
  return <div className="solar-interaction-profile">
    <div className="profile-heading"><p className="panel-kicker">Solar interaction profile</p><span className={`quality-badge quality-${environment.dataQuality}`}>{titleCase(environment.dataQuality)} evidence</span></div>
    <p className="environment-summary">{environment.summary}</p>
    <div className="interaction-grid"><IncomingPanel environment={environment} analysis={analysis} body={body}/><MagneticPanel environment={environment} body={body}/><ShieldingPanel environment={environment}/><MetricsPanel body={body} bodies={bodies} analysis={analysis} environment={environment}/></div>
    <LightInteraction analysis={analysis}/>
    <p className="classification-notice">{environment.classificationNotice}</p>
  </div>
}
