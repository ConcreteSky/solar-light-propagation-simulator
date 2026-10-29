import { formatDistance, formatIrradiance, formatPercent, formatTravelTime, getAverageSolarDistanceKm } from '../../utils/lightAnalysis.js'

const titleCase = (value) => value == null ? 'Unknown' : String(value).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

export function fieldSchematic(family) {
  const common = { fill: 'none', stroke: 'currentColor', strokeWidth: 2 }
  if (['intrinsic_dipole', 'intrinsic_aligned', 'intrinsic_mini'].includes(family)) return <g {...common}><path d="M88 68 C35 15 35 125 88 72"/><path d="M92 68 C170 2 190 125 92 72"/><path d="M92 58 C150 20 172 45 190 70"/></g>
  if (family === 'intrinsic_tilted_offset') return <g {...common} transform="translate(12 -5) rotate(-32 90 70)"><path d="M88 68 C35 15 35 125 88 72"/><path d="M92 68 C175 2 195 125 92 72"/></g>
  if (family === 'induced') return <g {...common}><path d="M5 35 C65 35 55 55 90 58 C135 64 155 45 200 42"/><path d="M5 105 C65 105 55 85 90 82 C135 76 155 95 200 98"/></g>
  if (family === 'crustal_remnant') return <g {...common}><path d="M62 58 Q72 35 82 58"/><path d="M83 50 Q96 25 108 52"/><path d="M105 56 Q116 36 126 58"/></g>
  if (family === 'parent_plasma') return <g {...common}>{[35,55,85,105].map((y) => <path key={y} d={`M5 ${y} Q90 ${y - 12} 200 ${y + 4}`}/>)}</g>
  return <g {...common} strokeDasharray="4 5"><path d="M55 70 H125"/><text x="135" y="75" fill="currentColor" stroke="none" fontSize="12">field unknown / negligible</text></g>
}

function IncomingPanel({ environment }) {
  const dynamic = environment.dynamic
  return <section className="interaction-panel incoming-panel" aria-labelledby="incoming-title">
    <h3 id="incoming-title"><span>A</span> Incoming solar environment</h3>
    <svg viewBox="0 0 420 125" role="img" aria-label="Sunlight and charged particles shown as separate incoming streams">
      <circle cx="42" cy="62" r="25" className="profile-sun"/><text x="22" y="108">SUN</text>
      <path d="M75 45 H345" className="photon-stream"/><text x="130" y="35">VISIBLE LIGHT · PHOTONS</text>
      <path d="M75 84 H345" className="particle-stream"/><text x="125" y="108">SOLAR WIND · CHARGED PARTICLES</text>
      <circle cx="370" cy="63" r="25" className="profile-body"/>
    </svg>
    <div className="profile-readouts"><strong>{formatIrradiance(dynamic.solarIrradianceWm2)}</strong><span>{dynamic.steadyStateSolarWindFluxProxy.toFixed(3)}× Earth steady-flux proxy</span><span>{dynamic.uvContext}</span></div>
  </section>
}

function MagneticPanel({ environment }) {
  const magnetic = environment.magnetic
  return <section className="interaction-panel magnetic-panel" aria-labelledby="magnetic-title">
    <h3 id="magnetic-title"><span>B</span> Magnetic interaction</h3>
    <svg viewBox="0 0 210 140" data-field-family={magnetic.family} role="img" aria-label={`${titleCase(magnetic.family)} magnetic-field schematic`}>
      {fieldSchematic(magnetic.family)}<circle cx="90" cy="70" r="17" className="profile-body"/>
    </svg>
    <p><strong>{magnetic.type}</strong> · {magnetic.shape}</p>
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
    <div className="interaction-grid"><IncomingPanel environment={environment}/><MagneticPanel environment={environment}/><ShieldingPanel environment={environment}/><MetricsPanel body={body} bodies={bodies} analysis={analysis} environment={environment}/></div>
    <LightInteraction analysis={analysis}/>
    <p className="classification-notice">{environment.classificationNotice}</p>
  </div>
}
