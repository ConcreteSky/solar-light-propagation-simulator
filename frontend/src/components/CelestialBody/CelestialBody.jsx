import { Html, useTexture } from '@react-three/drei'
import { useEffect, useState } from 'react'
import { RepeatWrapping, SRGBColorSpace } from 'three'
import { resolveTexture } from '../../data/textureRegistry.js'

function TexturedSurface({ radius, textureUrl, bodyScale }) {
  const texture = useTexture(textureUrl)

  useEffect(() => {
    texture.colorSpace = SRGBColorSpace
    texture.wrapS = RepeatWrapping
    texture.needsUpdate = true
  }, [texture])

  return (
    <mesh scale={bodyScale}>
      <sphereGeometry args={[radius, 28, 18]} />
      <meshStandardMaterial map={texture} color="#ffffff" roughness={0.85} />
    </mesh>
  )
}

function ColorSurface({ body, radius, bodyScale }) {
  const isSun = body.id === 'sun'
  return (
    <mesh scale={bodyScale}>
      <sphereGeometry args={[radius, 28, 18]} />
      {isSun ? (
        <meshBasicMaterial color={body.visual.baseColor} toneMapped={false} />
      ) : (
        <meshStandardMaterial color={body.visual.baseColor} roughness={0.82} metalness={0.02} />
      )}
    </mesh>
  )
}

function SaturnRings({ radius }) {
  return (
    <group rotation={[Math.PI / 2, 0, 0]}>
      <mesh>
        <ringGeometry args={[radius * 1.28, radius * 2.08, 72]} />
        <meshBasicMaterial color="#cfbd93" transparent opacity={0.72} side={2} />
      </mesh>
      <mesh position={[0, 0, 0.012]}>
        <ringGeometry args={[radius * 1.56, radius * 1.68, 72]} />
        <meshBasicMaterial color="#786e5c" transparent opacity={0.48} side={2} />
      </mesh>
    </group>
  )
}

export default function CelestialBody({
  body,
  position,
  radius,
  selected,
  showLabel,
  onSelect,
}) {
  const [hovered, setHovered] = useState(false)
  const textureUrl = resolveTexture(body.visual.texture)
  const bodyScale = body.id === 'haumea' ? [1.35, 0.74, 0.82] : [1, 1, 1]
  const highlighted = selected || hovered

  const handlePointerOver = (event) => {
    event.stopPropagation()
    setHovered(true)
    document.body.style.cursor = 'pointer'
  }

  const handlePointerOut = () => {
    setHovered(false)
    document.body.style.cursor = 'default'
  }

  return (
    <group
      position={position}
      scale={selected ? 1.12 : hovered ? 1.05 : 1}
      onClick={(event) => {
        event.stopPropagation()
        onSelect(body.id)
      }}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
      userData={{ bodyId: body.id, destination: body.id !== 'sun' }}
    >
      {textureUrl ? (
        <TexturedSurface radius={radius} textureUrl={textureUrl} bodyScale={bodyScale} />
      ) : (
        <ColorSurface body={body} radius={radius} bodyScale={bodyScale} />
      )}

      {body.id === 'saturn' && <SaturnRings radius={radius} />}

      {highlighted && (
        <mesh scale={bodyScale}>
          <sphereGeometry args={[radius * 1.16, 20, 14]} />
          <meshBasicMaterial color="#ffe7a3" transparent opacity={selected ? 0.22 : 0.11} wireframe />
        </mesh>
      )}

      {(showLabel || selected || hovered) && (
        <Html center position={[0, radius + 1.2, 0]} className="body-label-wrapper">
          <span className={`body-label ${selected ? 'body-label-selected' : ''}`}>{body.name}</span>
        </Html>
      )}
    </group>
  )
}
