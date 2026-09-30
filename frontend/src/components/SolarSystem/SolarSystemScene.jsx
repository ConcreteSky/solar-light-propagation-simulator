import { Canvas, useFrame } from '@react-three/fiber'
import { memo, Suspense, useCallback, useMemo, useRef } from 'react'
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

function OrbitingPrimary({
  body,
  moons,
  selectedBodyId,
  onSelectBody,
  getSimulationTimestampMs,
}) {
  const groupRef = useRef()
  const bodyRadius = useMemo(() => getVisualBodyRadius(body), [body])
  const orbitRadius = useMemo(
    () => getVisualOrbitRadius(body.orbit.semimajor_axis_km),
    [body],
  )
  const initialPosition = useMemo(
    () => getRenderedBodyPosition(body, getSimulationTimestampMs()),
    [body, getSimulationTimestampMs],
  )

  useFrame(() => {
    const position = getRenderedBodyPosition(body, getSimulationTimestampMs())
    groupRef.current?.position.set(...position)
  })

  return (
    <>
      <OrbitPath radius={orbitRadius} eccentricity={body.orbit.eccentricity} />
      <group ref={groupRef} position={initialPosition}>
        <CelestialBody
          body={body}
          position={[0, 0, 0]}
          radius={bodyRadius}
          selected={selectedBodyId === body.id}
          showLabel
          onSelect={onSelectBody}
        />
        {moons.length > 0 && (
          <MoonSystem
            moons={moons}
            parentRadius={bodyRadius}
            selectedBodyId={selectedBodyId}
            onSelectBody={onSelectBody}
            getSimulationTimestampMs={getSimulationTimestampMs}
          />
        )}
      </group>
    </>
  )
}

function SolarSystem({ bodies, selectedBodyId, onSelectBody, getSimulationTimestampMs }) {
  const primaryBodies = useMemo(() => bodies.filter((body) => body.type !== 'moon'), [bodies])
  const moonsByParent = useMemo(() => {
    const groups = new Map()
    bodies.filter((body) => body.type === 'moon').forEach((moon) => {
      groups.set(moon.parent, [...(groups.get(moon.parent) ?? []), moon])
    })
    return groups
  }, [bodies])

  const asteroidBeltRadii = useMemo(() => {
    const mars = bodies.find((body) => body.id === 'mars')
    const jupiter = bodies.find((body) => body.id === 'jupiter')
    return {
      inner: getVisualOrbitRadius(mars.orbit.semimajor_axis_km) + 4.5,
      outer: getVisualOrbitRadius(jupiter.orbit.semimajor_axis_km) - 5,
    }
  }, [bodies])

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

      <AsteroidBelt innerRadius={asteroidBeltRadii.inner} outerRadius={asteroidBeltRadii.outer} />

      {primaryBodies.map((body) => {
        const moons = moonsByParent.get(body.id) ?? []

        return (
          <OrbitingPrimary
            key={body.id}
            body={body}
            moons={moons}
            selectedBodyId={selectedBodyId}
            onSelectBody={onSelectBody}
            getSimulationTimestampMs={getSimulationTimestampMs}
          />
        )
      })}
    </>
  )
}

function SolarSystemScene({
  bodies,
  selectedBodyId,
  onSelectBody,
  resetViewSignal,
  getSimulationTimestampMs,
  focusTimestampMs,
}) {
  const focusPosition = useMemo(() => {
    if (!selectedBodyId || selectedBodyId === 'sun') return [0, 0, 0]

    const body = bodies.find((candidate) => candidate.id === selectedBodyId)
    if (!body) return [0, 0, 0]

    return getRenderedHeliocentricPosition(body, bodies, focusTimestampMs)
  }, [bodies, selectedBodyId, focusTimestampMs])
  const clearSelection = useCallback(() => onSelectBody(null), [onSelectBody])

  return (
    <Canvas
      camera={{ position: [0, 270, 120], fov: 45, near: 0.1, far: 600 }}
      dpr={[1, 1.5]}
      gl={{ antialias: true, powerPreference: 'high-performance' }}
      onCreated={({ gl }) => { gl.toneMappingExposure = 1.12 }}
      onPointerMissed={clearSelection}
    >
      <Suspense fallback={null}>
        <SolarSystem
          bodies={bodies}
          selectedBodyId={selectedBodyId}
          onSelectBody={onSelectBody}
          getSimulationTimestampMs={getSimulationTimestampMs}
        />
      </Suspense>
      <CameraControls resetSignal={resetViewSignal} focusPosition={focusPosition} />
    </Canvas>
  )
}

export default memo(SolarSystemScene)
