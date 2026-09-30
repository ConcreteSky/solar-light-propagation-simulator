import { useMemo } from 'react'
import { BufferAttribute, BufferGeometry } from 'three'

function seededRandom(seed) {
  let value = seed >>> 0
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0
    return value / 4294967296
  }
}

export default function AsteroidBelt({ innerRadius, outerRadius }) {
  const geometry = useMemo(() => {
    const random = seededRandom(741)
    const positions = new Float32Array(850 * 3)

    for (let index = 0; index < 850; index += 1) {
      const angle = random() * Math.PI * 2
      const radius = innerRadius + random() * (outerRadius - innerRadius)
      positions[index * 3] = Math.cos(angle) * radius
      positions[index * 3 + 1] = 0
      positions[index * 3 + 2] = Math.sin(angle) * radius
    }

    const result = new BufferGeometry()
    result.setAttribute('position', new BufferAttribute(positions, 3))
    return result
  }, [innerRadius, outerRadius])

  return (
    <points geometry={geometry} raycast={() => null}>
      <pointsMaterial color="#817262" size={0.22} sizeAttenuation transparent opacity={0.72} />
    </points>
  )
}

