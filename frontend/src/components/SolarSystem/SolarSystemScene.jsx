import { Canvas } from '@react-three/fiber'
import { Suspense, useMemo } from 'react'
import AsteroidBelt from '../AsteroidBelt/AsteroidBelt.jsx'
import CelestialBody from '../CelestialBody/CelestialBody.jsx'
import OrbitPath from '../Orbit/OrbitPath.jsx'
import { sun } from '../../data/catalog.js'
import {
  getEllipsePosition,
  getStablePhase,
  getVisualBodyRadius,
  getVisualMoonOrbitRadius,
  getVisualOrbitRadius,
} from '../../utils/sceneScale.js'
import MoonSystem from './MoonSystem.jsx'
import StarField from './StarField.jsx'
import CameraControls from './CameraControls.jsx'

function SolarSystem({ bodies, selectedBodyId, onSelectBody }) {
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
      <ambientLight intensity={0.2} color="#7890bd" />
      <pointLight position={[0, 4, 0]} intensity={1250} distance={175} decay={1.75} color="#ffd18a" />
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
        const position = getEllipsePosition(orbitRadius, body.orbit.eccentricity, getStablePhase(body.id))
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
                />
              </group>
            )}
          </group>
        )
      })}
    </>
  )
}

export default function SolarSystemScene({ bodies, selectedBodyId, onSelectBody, resetViewSignal }) {
  const focusPosition = useMemo(() => {
    if (!selectedBodyId || selectedBodyId === 'sun') return [0, 0, 0]

    const body = bodies.find((candidate) => candidate.id === selectedBodyId)
    if (!body) return [0, 0, 0]

    if (body.type !== 'moon') {
      return getEllipsePosition(
        getVisualOrbitRadius(body.orbit.semimajor_axis_km),
        body.orbit.eccentricity,
        getStablePhase(body.id),
      )
    }

    const parent = bodies.find((candidate) => candidate.id === body.parent)
    if (!parent) return [0, 0, 0]

    const parentPosition = getEllipsePosition(
      getVisualOrbitRadius(parent.orbit.semimajor_axis_km),
      parent.orbit.eccentricity,
      getStablePhase(parent.id),
    )
    const siblings = bodies.filter((candidate) => candidate.type === 'moon' && candidate.parent === body.parent)
    const moonIndex = siblings.findIndex((candidate) => candidate.id === body.id)
    const moonPosition = getEllipsePosition(
      getVisualMoonOrbitRadius(getVisualBodyRadius(parent), moonIndex),
      body.orbit.eccentricity,
      getStablePhase(body.id),
    )

    return parentPosition.map((coordinate, index) => coordinate + moonPosition[index])
  }, [bodies, selectedBodyId])

  return (
    <Canvas
      camera={{ position: [0, 270, 120], fov: 45, near: 0.1, far: 600 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      onPointerMissed={() => onSelectBody(null)}
    >
      <Suspense fallback={null}>
        <SolarSystem bodies={bodies} selectedBodyId={selectedBodyId} onSelectBody={onSelectBody} />
      </Suspense>
      <CameraControls resetSignal={resetViewSignal} focusPosition={focusPosition} />
    </Canvas>
  )
}
