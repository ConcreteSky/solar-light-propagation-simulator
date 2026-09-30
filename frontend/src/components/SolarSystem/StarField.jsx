import { useMemo } from 'react'
import { BufferAttribute, BufferGeometry } from 'three'

export default function StarField() {
  const geometry = useMemo(() => {
    let seed = 9241
    const random = () => {
      seed = (seed * 16807) % 2147483647
      return (seed - 1) / 2147483646
    }
    const positions = new Float32Array(700 * 3)

    for (let index = 0; index < 700; index += 1) {
      const radius = 180 + random() * 140
      const theta = random() * Math.PI * 2
      const phi = Math.acos(2 * random() - 1)
      positions[index * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[index * 3 + 1] = radius * Math.cos(phi)
      positions[index * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta)
    }

    const result = new BufferGeometry()
    result.setAttribute('position', new BufferAttribute(positions, 3))
    return result
  }, [])

  return (
    <points geometry={geometry} raycast={() => null}>
      <pointsMaterial color="#d8e3ff" size={0.7} sizeAttenuation transparent opacity={0.72} />
    </points>
  )
}

