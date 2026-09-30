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
  const distance = getAverageSolarDistanceKm(body, bodies)
  const values = [
    ['Average Sun distance', formatDistance(distance)],
    ['Reference light-travel time', formatTravelTime(body.light_reference?.light_travel_time_seconds)],
    ['Reference solar irradiance', formatIrradiance(body.light_reference?.solar_irradiance_w_m2)],
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

export default function ResultPanel({ body, bodies }) {
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
    getLightResult(body.id, { signal: controller.signal })
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
  }, [body])

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
                <p className="appearance-summary">{createAppearanceSummary(body, state.analysis)}</p>
              </div>
              <span className={`method-badge ${state.analysis.validation.fallbackUsed ? 'method-fallback' : ''}`}>
                {state.analysis.validation.fallbackUsed ? 'Deterministic fallback' : 'Validated ML prediction'}
              </span>
            </header>
            <div className="analysis-grid">
              <LightDiagram analysis={state.analysis} />
              <ScientificValues body={body} bodies={bodies} analysis={state.analysis} />
            </div>
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
