import { useEffect, useRef, useState } from 'react'

export const PLAYBACK_RATES = {
  slow: 1,
  normal: 7,
  fast: 30,
}

const SIMULATED_DAY_MS = 86_400_000

export default function useSimulationClock(initialTimestampMs = Date.now()) {
  const initialTimestamp = useRef(initialTimestampMs)
  const lastTick = useRef(performance.now())
  const [timestampMs, setTimestampMs] = useState(initialTimestampMs)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState('normal')

  useEffect(() => {
    if (!playing) return undefined
    lastTick.current = performance.now()
    const interval = window.setInterval(() => {
      const now = performance.now()
      const elapsedRealMs = now - lastTick.current
      lastTick.current = now
      setTimestampMs((value) => value + elapsedRealMs * PLAYBACK_RATES[speed] * SIMULATED_DAY_MS / 1000)
    }, 100)
    return () => window.clearInterval(interval)
  }, [playing, speed])

  const reset = () => {
    setTimestampMs(initialTimestamp.current)
    setSpeed('normal')
    setPlaying(true)
  }

  return {
    timestampMs,
    setTimestampMs,
    playing,
    setPlaying,
    speed,
    setSpeed,
    reset,
  }
}
