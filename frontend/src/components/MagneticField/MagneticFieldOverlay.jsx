import { Line } from '@react-three/drei'
import { useFrame } from '@react-three/fiber'
import { memo, useRef } from 'react'
import { Vector3 } from 'three'

const VISIBLE_FAMILIES = new Set([
  'intrinsic_dipole', 'intrinsic_aligned', 'intrinsic_tilted_offset',
  'induced', 'crustal_remnant', 'intrinsic_mini', 'parent_plasma',
])

export function getMagneticVisualKind(environment) {
  const family = environment?.magnetic?.family ?? 'unknown'
  return VISIBLE_FAMILIES.has(family) ? family : null
}

export function getMagneticVisualScale(environment) {
  return ({ extreme: 1.6, substantial: 1, moderate: 0.85, limited: 0.7, none: 0.65 })[environment?.magnetic?.shielding] ?? 0.8
}

function arcPoints(scale, height, tail = 1) {
  return Array.from({ length: 20 }, (_, index) => {
    const t = -Math.PI / 2 + (Math.PI * index) / 19
    return [Math.cos(t) * scale * tail, 0, Math.sin(t) * height]
  })
}

function IntrinsicLines({ radius, tilted = false, mini = false, aligned = false }) {
  const size = radius * (mini ? 1.8 : aligned ? 3.2 : 2.8)
  const tilt = tilted ? Math.PI / 3 : 0
  return (
    <group rotation={[0, tilt, 0]}>
      {[0.75, 1, 1.25].map((factor) => (
        <group key={factor}>
          <Line points={arcPoints(size * factor, size * factor * 0.72)} color="#60dfff" transparent opacity={0.58} lineWidth={1} />
          <Line points={arcPoints(-size * factor * 1.45, size * factor * 0.72)} color="#60dfff" transparent opacity={0.4} lineWidth={1} />
        </group>
      ))}
    </group>
  )
}

function DrapedLines({ radius }) {
  const size = radius * 2.3
  return <>{[-0.9, -0.45, 0.45, 0.9].map((offset) => <Line key={offset} points={[[-size, 0, offset * radius], [-radius * 0.7, 0, offset * radius * 1.5], [size * 2.3, 0, offset * radius * 1.1]]} color="#58e5d5" transparent opacity={0.5} lineWidth={1} />)}</>
}

function CrustalPatches({ radius }) {
  return <>{[-0.7, 0, 0.7].map((offset) => <Line key={offset} points={arcPoints(radius * 0.55, radius * 0.32).map(([x, y, z]) => [x + offset * radius, y, z + radius])} color="#f0a5ff" transparent opacity={0.7} lineWidth={1.2} />)}</>
}

function ParentPlasma({ radius }) {
  const size = radius * 3
  return <>{[-1, -0.5, 0, 0.5, 1].map((offset) => <Line key={offset} points={[[-size, 0, offset * radius], [0, 0, offset * radius + Math.sin(offset * 3) * radius * 0.25], [size, 0, offset * radius]]} color="#ff79ba" transparent opacity={0.42} lineWidth={0.8} />)}</>
}

const worldPosition = new Vector3()

function MagneticFieldOverlay({ environment, radius }) {
  const family = getMagneticVisualKind(environment)
  const visualScale = getMagneticVisualScale(environment)
  const groupRef = useRef()
  useFrame(() => {
    if (!groupRef.current) return
    groupRef.current.getWorldPosition(worldPosition)
    groupRef.current.rotation.y = -Math.atan2(worldPosition.z, worldPosition.x)
  })
  if (!family) return null
  return (
    <group ref={groupRef} scale={visualScale} userData={{ magneticFamily: family, visualScale }}>
      {family === 'intrinsic_dipole' && <IntrinsicLines radius={radius} />}
      {family === 'intrinsic_aligned' && <IntrinsicLines radius={radius} aligned />}
      {family === 'intrinsic_tilted_offset' && <group position={[radius * 0.25, 0, 0]}><IntrinsicLines radius={radius} tilted /></group>}
      {family === 'intrinsic_mini' && <IntrinsicLines radius={radius} mini />}
      {family === 'induced' && <DrapedLines radius={radius} />}
      {family === 'crustal_remnant' && <CrustalPatches radius={radius} />}
      {family === 'parent_plasma' && <ParentPlasma radius={radius} />}
    </group>
  )
}

export default memo(MagneticFieldOverlay)
