import CelestialBody from '../CelestialBody/CelestialBody.jsx'
import OrbitPath from '../Orbit/OrbitPath.jsx'
import {
  getEllipsePosition,
  getStablePhase,
  getVisualBodyRadius,
  getVisualMoonOrbitRadius,
} from '../../utils/sceneScale.js'

export default function MoonSystem({ moons, parentRadius, selectedBodyId, onSelectBody }) {
  return moons.map((moon, index) => {
    const orbitRadius = getVisualMoonOrbitRadius(parentRadius, index)
    const phase = getStablePhase(moon.id)
    const position = getEllipsePosition(orbitRadius, moon.orbit.eccentricity, phase)

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

