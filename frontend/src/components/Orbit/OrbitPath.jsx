import { Line } from '@react-three/drei'
import { memo, useMemo } from 'react'
import { createEllipsePoints } from '../../utils/sceneScale.js'

function OrbitPath({ radius, eccentricity, moon = false }) {
  const points = useMemo(
    () => createEllipsePoints(radius, eccentricity, moon ? 72 : 180),
    [eccentricity, moon, radius],
  )

  return (
    <Line
      points={points}
      color={moon ? '#526078' : '#34445f'}
      lineWidth={moon ? 0.65 : 0.8}
      transparent
      opacity={moon ? 0.45 : 0.62}
      position={[0, -0.035, 0]}
    />
  )
}

export default memo(OrbitPath)
