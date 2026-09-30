import { Canvas } from '@react-three/fiber'
import { Suspense, useMemo } from 'react'
import AsteroidBelt from '../AsteroidBelt/AsteroidBelt.jsx'
import CelestialBody from '../CelestialBody/CelestialBody.jsx'
import OrbitPath from '../Orbit/OrbitPath.jsx'
import { sun } from '../../data/catalog.js'
import {
  getVisualBodyRadius,
  getVisualOrbitRadius,
} from '../../utils/sceneScale.js'
import {
  getRenderedBodyPosition,
  getRenderedHeliocentricPosition,
} from '../../utils/orbitalModel.js'
import MoonSystem from './MoonSystem.jsx'
import StarField from './StarField.jsx'
import CameraControls from './CameraControls.jsx'

function SolarSystem({ bodies, selectedBodyId, onSelectBody, simulationTimestampMs }) {
  const primaryBodies = useMemo(() => bodies.filter((body) => body.type !== 'moon'), [bodies])
  const moonsByParent = useMemo(() => {
    const groups = new Map()
    bodies.filter((body) => body.type === 'moon').forEach((moon) => {
      groups.set(moon.parent, [...(groups.get(moon.parent) ?? []), moon])
    })
    return groups
  }, [bodies])

  const marsOrbit = getVisualOrbitRadius(bodies.find((body) => body.id === 'mars').orbit.semimajor_axis_km)
  const jupiterOrbit = getVisualOrbitRadius(bodies.find((body) => body.id === 'jupiter').orbit.semimajor_axis_km)

  return (
    <>
      <color attach="background" args={['#030610']} />
      <fog attach="fog" args={['#030610', 175, 330]} />
      <ambientLight intensity={0.46} color="#7890bd" />
      <hemisphereLight args={['#a9c8ff', '#14182a', 0.45]} />
      <pointLight position={[0, 0, 0]} intensity={3.4} decay={0} color="#ffd18a" />
      <StarField />

      <CelestialBody
        body={sun}
        position={[0, 0, 0]}
        radius={4.25}
        selected={selectedBodyId === 'sun'}
        showLabel
        onSelect={onSelectBody}
      />

      <AsteroidBelt innerRadius={marsOrbit + 4.5} outerRadius={jupiterOrbit - 5} />

      {primaryBodies.map((body) => {
        const orbitRadius = getVisualOrbitRadius(body.orbit.semimajor_axis_km)
        const position = getRenderedBodyPosition(body, simulationTimestampMs)
        const bodyRadius = getVisualBodyRadius(body)
        const moons = moonsByParent.get(body.id) ?? []

        return (
          <group key={body.id}>
            <OrbitPath radius={orbitRadius} eccentricity={body.orbit.eccentricity} />
            <CelestialBody
              body={body}
              position={position}
              radius={bodyRadius}
              selected={selectedBodyId === body.id}
              showLabel
              onSelect={onSelectBody}
            />
            {moons.length > 0 && (
              <group position={position}>
                <MoonSystem
                  moons={moons}
                  parentRadius={bodyRadius}
                  selectedBodyId={selectedBodyId}
                  onSelectBody={onSelectBody}
                  simulationTimestampMs={simulationTimestampMs}
                />
              </group>
            )}
          </group>
        )
      })}
    </>
  )
}

export default function SolarSystemScene({
  bodies,
  selectedBodyId,
  onSelectBody,
  resetViewSignal,
  simulationTimestampMs,
  focusTimestampMs,
}) {
  const focusPosition = useMemo(() => {
    if (!selectedBodyId || selectedBodyId === 'sun') return [0, 0, 0]

    const body = bodies.find((candidate) => candidate.id === selectedBodyId)
    if (!body) return [0, 0, 0]

    return getRenderedHeliocentricPosition(body, bodies, focusTimestampMs)
  }, [bodies, selectedBodyId, focusTimestampMs])

  return (
    <Canvas
      camera={{ position: [0, 270, 120], fov: 45, near: 0.1, far: 600 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      onCreated={({ gl }) => { gl.toneMappingExposure = 1.12 }}
      onPointerMissed={() => onSelectBody(null)}
    >
      <Suspense fallback={null}>
        <SolarSystem
          bodies={bodies}
          selectedBodyId={selectedBodyId}
          onSelectBody={onSelectBody}
          simulationTimestampMs={simulationTimestampMs}
        />
      </Suspense>
      <CameraControls resetSignal={resetViewSignal} focusPosition={focusPosition} />
    </Canvas>
  )
}
