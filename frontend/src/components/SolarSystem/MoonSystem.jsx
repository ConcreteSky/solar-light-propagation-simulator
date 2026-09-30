import CelestialBody from '../CelestialBody/CelestialBody.jsx'
import OrbitPath from '../Orbit/OrbitPath.jsx'
import {
  getVisualBodyRadius,
  getVisualMoonOrbitRadius,
} from '../../utils/sceneScale.js'
import { getRenderedBodyPosition } from '../../utils/orbitalModel.js'

export default function MoonSystem({
  moons,
  parentRadius,
  selectedBodyId,
  onSelectBody,
  simulationTimestampMs,
}) {
  return moons.map((moon, index) => {
    const orbitRadius = getVisualMoonOrbitRadius(parentRadius, index)
    const position = getRenderedBodyPosition(moon, simulationTimestampMs, index, parentRadius)

    return (
      <group key={moon.id}>
        <OrbitPath radius={orbitRadius} eccentricity={moon.orbit.eccentricity} moon />
        <CelestialBody
          body={moon}
          position={position}
          radius={getVisualBodyRadius(moon)}
          selected={moon.id === selectedBodyId}
          showLabel={false}
          onSelect={onSelectBody}
        />
      </group>
    )
  })
}
