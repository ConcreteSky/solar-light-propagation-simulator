import { OrbitControls } from '@react-three/drei'
import { useFrame, useThree } from '@react-three/fiber'
import { useEffect, useRef } from 'react'
import { Vector3 } from 'three'

const OVERVIEW_POSITION = new Vector3(0, 270, 120)
const SYSTEM_CENTER = new Vector3(0, 0, 0)

export default function CameraControls({ resetSignal, focusPosition }) {
  const controlsRef = useRef(null)
  const resetting = useRef(false)
  const focusing = useRef(false)
  const requestedFocus = useRef(new Vector3())
  const nextTarget = useRef(new Vector3())
  const targetShift = useRef(new Vector3())
  const camera = useThree((state) => state.camera)
  const canvas = useThree((state) => state.gl.domElement)

  useEffect(() => {
    if (resetSignal > 0) resetting.current = true
  }, [resetSignal])

  useEffect(() => {
    requestedFocus.current.fromArray(focusPosition)
    focusing.current = true
  }, [focusPosition])

  useEffect(() => {
    const cancelAutomaticMove = () => {
      focusing.current = false
    }

    canvas.addEventListener('pointerdown', cancelAutomaticMove)
    return () => {
      canvas.removeEventListener('pointerdown', cancelAutomaticMove)
    }
  }, [canvas])

  useFrame(() => {
    const controls = controlsRef.current
    if (!controls) return

    if (resetting.current) {
      focusing.current = false
      camera.position.lerp(OVERVIEW_POSITION, 0.13)
      controls.target.lerp(SYSTEM_CENTER, 0.13)
      controls.update()

      if (
        camera.position.distanceToSquared(OVERVIEW_POSITION) < 0.04
        && controls.target.distanceToSquared(SYSTEM_CENTER) < 0.01
      ) {
        camera.position.copy(OVERVIEW_POSITION)
        controls.target.copy(SYSTEM_CENTER)
        controls.update()
        resetting.current = false
      }
      return
    }

    if (focusing.current) {
      nextTarget.current.copy(controls.target).lerp(requestedFocus.current, 0.13)
      targetShift.current.copy(nextTarget.current).sub(controls.target)
      controls.target.copy(nextTarget.current)
      camera.position.add(targetShift.current)
      controls.update()

      if (controls.target.distanceToSquared(requestedFocus.current) < 0.01) {
        controls.target.copy(requestedFocus.current)
        controls.update()
        focusing.current = false
      }
    }
  })

  return (
    <OrbitControls
      ref={controlsRef}
      makeDefault
      enableDamping
      dampingFactor={0.07}
      minDistance={18}
      maxDistance={370}
      minPolarAngle={0.22}
      maxPolarAngle={Math.PI / 2.04}
      panSpeed={0.55}
      rotateSpeed={0.55}
      zoomSpeed={1}
      screenSpacePanning
    />
  )
}
