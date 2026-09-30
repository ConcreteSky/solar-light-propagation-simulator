import { useMemo, useState } from 'react'
import SolarSystemScene from './components/SolarSystem/SolarSystemScene.jsx'
import ResultPanel from './components/ResultPanel/ResultPanel.jsx'
import SimulationControls from './components/SimulationControls/SimulationControls.jsx'
import { celestialBodies, sun } from './data/catalog.js'
import useSimulationClock from './hooks/useSimulationClock.js'

const SESSION_START_MS = Date.now()

export default function App() {
  const [selectedBodyId, setSelectedBodyId] = useState(null)
  const [analysisTimestampMs, setAnalysisTimestampMs] = useState(SESSION_START_MS)
  const [resetViewSignal, setResetViewSignal] = useState(0)
  const simulation = useSimulationClock(SESSION_START_MS)

  const selectedBody = useMemo(
    () => [sun, ...celestialBodies].find((body) => body.id === selectedBodyId) ?? null,
    [selectedBodyId],
  )

  const selectBody = (bodyId) => {
    setSelectedBodyId(bodyId)
    if (bodyId) {
      simulation.setPlaying(false)
      setAnalysisTimestampMs(simulation.timestampMs)
    }
  }

  const togglePlaying = () => {
    if (simulation.playing && selectedBodyId && selectedBodyId !== 'sun') {
      setAnalysisTimestampMs(simulation.timestampMs)
    }
    simulation.setPlaying(!simulation.playing)
  }

  const setSimulationDate = (timestampMs) => {
    simulation.setPlaying(false)
    simulation.setTimestampMs(timestampMs)
    if (selectedBodyId && selectedBodyId !== 'sun') setAnalysisTimestampMs(timestampMs)
  }

  return (
    <main className="app-shell" data-selected-body-id={selectedBodyId ?? ''}>
      <section className="map-section">
        <header className="app-header">
          <p className="eyebrow">Destination map</p>
          <h1>Solar Light<br />Propagation</h1>
          <p className="instructions">Click a world to focus · Scroll to zoom · Drag to orbit</p>
          <button
            className="reset-view-button"
            type="button"
            onClick={() => {
              setSelectedBodyId(null)
              setResetViewSignal((value) => value + 1)
            }}
          >
            Reset view
          </button>
        </header>

        <div className="scene-shell" aria-label="Interactive 3D Solar System destination map">
          <SolarSystemScene
            bodies={celestialBodies}
            selectedBodyId={selectedBodyId}
            onSelectBody={selectBody}
            resetViewSignal={resetViewSignal}
            simulationTimestampMs={simulation.timestampMs}
            focusTimestampMs={analysisTimestampMs}
          />
        </div>

        <SimulationControls
          timestampMs={simulation.timestampMs}
          playing={simulation.playing}
          speed={simulation.speed}
          onTogglePlaying={togglePlaying}
          onSpeedChange={simulation.setSpeed}
          onDateChange={setSimulationDate}
          onReset={() => {
            simulation.reset()
            if (selectedBodyId && selectedBodyId !== 'sun') {
              setAnalysisTimestampMs(SESSION_START_MS)
            }
          }}
        />

        {selectedBody && (
          <p className="current-selection" aria-live="polite">
            Selected: <strong>{selectedBody.name}</strong>
          </p>
        )}
        <p className="map-disclaimer">
          Coplanar Keplerian positions are approximate. Distances and sizes are compressed only for display.
        </p>
      </section>

      <ResultPanel
        body={selectedBody}
        bodies={celestialBodies}
        simulationTimestampMs={analysisTimestampMs}
      />
    </main>
  )
}
