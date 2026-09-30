import { useMemo, useState } from 'react'
import SolarSystemScene from './components/SolarSystem/SolarSystemScene.jsx'
import ResultPanel from './components/ResultPanel/ResultPanel.jsx'
import { celestialBodies, sun } from './data/catalog.js'

export default function App() {
  const [selectedBodyId, setSelectedBodyId] = useState(null)
  const [resetViewSignal, setResetViewSignal] = useState(0)

  const selectedBody = useMemo(
    () => [sun, ...celestialBodies].find((body) => body.id === selectedBodyId) ?? null,
    [selectedBodyId],
  )

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
            onSelectBody={setSelectedBodyId}
            resetViewSignal={resetViewSignal}
          />
        </div>

        {selectedBody && (
          <p className="current-selection" aria-live="polite">
            Selected: <strong>{selectedBody.name}</strong>
          </p>
        )}
        <p className="map-disclaimer">
          Orbital distances, sizes, and inclinations are simplified for visualization.
        </p>
      </section>

      <ResultPanel body={selectedBody} bodies={celestialBodies} />
    </main>
  )
}
