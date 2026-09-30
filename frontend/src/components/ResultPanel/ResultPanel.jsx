import { useEffect, useRef, useState } from 'react'
import LightDiagram from '../LightDiagram/LightDiagram.jsx'
import { getLightResult } from '../../services/api.js'
import {
  createAppearanceSummary,
  formatDistance,
  formatIrradiance,
  formatPercent,
  formatTravelTime,
  getAverageSolarDistanceKm,
} from '../../utils/lightAnalysis.js'

function ScientificValues({ body, bodies, analysis }) {
  const atmospheric = analysis.hasAtmosphere === true
  const results = analysis.results
  const astronomy = analysis.astronomy
  const distance = astronomy?.distanceFromSunKm ?? getAverageSolarDistanceKm(body, bodies)
  const astronomicalValues = astronomy ? [
    ['Approx. current Sun distance', formatDistance(distance)],
    ['Approx. orbital position', `${astronomy.orbitalAngleDeg.toFixed(2)}° from periapsis`],
    ['Current light-travel time', formatTravelTime(astronomy.lightTravelTimeSeconds)],
    ['Current solar irradiance', formatIrradiance(astronomy.solarIrradianceWm2)],
    ['Apparent solar diameter', `${astronomy.apparentSolarAngularDiameterDeg.toFixed(4)}°`],
  ] : [
    ['Average Sun distance', formatDistance(distance)],
    ['Reference light-travel time', formatTravelTime(body.light_reference?.light_travel_time_seconds)],
    ['Reference solar irradiance', formatIrradiance(body.light_reference?.solar_irradiance_w_m2)],
  ]
  const values = [
    ...astronomicalValues,
    [atmospheric ? 'Transmitted' : 'Reaches surface', formatPercent(results.transmitted)],
    [atmospheric ? 'Scattered' : 'Reflected / scattered', formatPercent(results.scattered)],
    ['Absorbed', formatPercent(results.absorbed)],
  ]

  return (
    <dl className="science-values">
      {values.map(([label, value]) => (
        <div key={label} className="science-value">
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  )
}

export default function ResultPanel({ body, bodies, simulationTimestampMs }) {
  const [state, setState] = useState({ status: 'idle', analysis: null, error: null })
  const requestSequence = useRef(0)

  useEffect(() => {
    const sequence = ++requestSequence.current
    if (!body || body.id === 'sun') {
      setState({ status: 'idle', analysis: null, error: null })
      return undefined
    }

    const controller = new AbortController()
    setState({ status: 'loading', analysis: null, error: null })
    getLightResult(body.id, {
      signal: controller.signal,
      simulatedTime: Number.isFinite(simulationTimestampMs)
        ? new Date(simulationTimestampMs).toISOString()
        : undefined,
    })
      .then((analysis) => {
        if (sequence === requestSequence.current) {
          setState({ status: 'success', analysis, error: null })
        }
      })
      .catch((error) => {
        if (error.name !== 'AbortError' && sequence === requestSequence.current) {
          setState({ status: 'error', analysis: null, error })
        }
      })

    return () => controller.abort()
  }, [body, simulationTimestampMs])

  return (
    <section id="light-analysis" className="analysis-section" aria-labelledby="analysis-title">
      <div className="analysis-inner">
        <p className="panel-kicker">Light analysis</p>
        {!body && (
          <div className="analysis-empty">
            <h2 id="analysis-title">Choose a destination</h2>
            <p>Select a planet, moon, or dwarf planet in the map above.</p>
          </div>
        )}
        {body?.id === 'sun' && (
          <div className="analysis-empty">
            <h2 id="analysis-title">The Sun is the light source</h2>
            <p>Select a destination to examine how its light interacts locally.</p>
          </div>
        )}
        {body && body.id !== 'sun' && state.status === 'loading' && (
          <div className="analysis-loading" role="status">
            <h2 id="analysis-title">Analyzing {body.name}</h2>
            <p>Retrieving validated light results…</p>
          </div>
        )}
        {body && body.id !== 'sun' && state.status === 'error' && (
          <div className="analysis-error" role="alert">
            <h2 id="analysis-title">Analysis unavailable</h2>
            <p>{state.error.status === 404 ? 'The selected destination was not found.' : 'No validated result could be retrieved.'}</p>
          </div>
        )}
        {body && body.id !== 'sun' && state.status === 'success' && (
          <article className="analysis-result">
            <header className="analysis-result-header">
              <div>
                <h2 id="analysis-title">{body.name}</h2>
              </div>
              <span className={`method-badge ${state.analysis.validation.fallbackUsed ? 'method-fallback' : ''}`}>
                {state.analysis.validation.fallbackUsed ? 'Deterministic fallback' : 'Validated ML prediction'}
              </span>
            </header>
            <div className="analysis-grid">
              <LightDiagram analysis={state.analysis} />
              <ScientificValues body={body} bodies={bodies} analysis={state.analysis} />
            </div>
            <p className="appearance-summary">{createAppearanceSummary(body, state.analysis)}</p>
            {state.analysis.astronomy && (
              <p className="analysis-timestamp">
                Frozen analysis time: {new Date(state.analysis.astronomy.simulatedTime).toLocaleString()}
                {' · '}Approximate two-body solution
              </p>
            )}
            {state.analysis.validation.warnings?.length > 0 && (
              <p className="analysis-note" data-testid="analysis-warning">
                Data note: {state.analysis.validation.warnings[0]}
              </p>
            )}
          </article>
        )}
      </div>
    </section>
  )
}
