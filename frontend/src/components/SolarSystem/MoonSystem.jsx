import { useFrame } from '@react-three/fiber'
import { memo, useMemo, useRef } from 'react'
import CelestialBody from '../CelestialBody/CelestialBody.jsx'
import OrbitPath from '../Orbit/OrbitPath.jsx'
import {
  getVisualBodyRadius,
  getVisualMoonOrbitRadius,
} from '../../utils/sceneScale.js'
import { getRenderedBodyPosition } from '../../utils/orbitalModel.js'

function OrbitingMoon({
  moon,
  index,
  parentRadius,
  selectedBodyId,
  onSelectBody,
  getSimulationTimestampMs,
}) {
  const groupRef = useRef()
  const orbitRadius = useMemo(
    () => getVisualMoonOrbitRadius(parentRadius, index),
    [index, parentRadius],
  )
  const radius = useMemo(() => getVisualBodyRadius(moon), [moon])
  const initialPosition = useMemo(
    () => getRenderedBodyPosition(
      moon,
      getSimulationTimestampMs(),
      index,
      parentRadius,
    ),
    [getSimulationTimestampMs, index, moon, parentRadius],
  )

  useFrame(() => {
    const position = getRenderedBodyPosition(
      moon,
      getSimulationTimestampMs(),
      index,
      parentRadius,
    )
    groupRef.current?.position.set(...position)
  })

  return (
    <>
      <OrbitPath radius={orbitRadius} eccentricity={moon.orbit.eccentricity} moon />
      <group ref={groupRef} position={initialPosition}>
        <CelestialBody
          body={moon}
          position={[0, 0, 0]}
          radius={radius}
          selected={moon.id === selectedBodyId}
          showLabel={false}
          onSelect={onSelectBody}
        />
      </group>
    </>
  )
}

function MoonSystem({
  moons,
  parentRadius,
  selectedBodyId,
  onSelectBody,
  getSimulationTimestampMs,
}) {
  return moons.map((moon, index) => (
    <OrbitingMoon
      key={moon.id}
      moon={moon}
      index={index}
      parentRadius={parentRadius}
      selectedBodyId={selectedBodyId}
      onSelectBody={onSelectBody}
      getSimulationTimestampMs={getSimulationTimestampMs}
    />
  ))
}

export default memo(MoonSystem)
