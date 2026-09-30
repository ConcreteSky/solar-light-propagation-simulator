import { useCallback, useEffect, useRef, useState } from 'react'

export const PLAYBACK_RATES = {
  slow: 1,
  normal: 7,
  fast: 30,
}

const SIMULATED_DAY_MS = 86_400_000
const UI_REFRESH_MS = 250

export default function useSimulationClock(initialTimestampMs = Date.now()) {
  const initialTimestamp = useRef(initialTimestampMs)
  const clock = useRef({
    timestampMs: initialTimestampMs,
    performanceMs: performance.now(),
    playing: true,
    speed: 'normal',
  })
  const [timestampMs, setTimestampMs] = useState(initialTimestampMs)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState('normal')

  const getTimestampMs = useCallback(() => {
    const current = clock.current
    if (!current.playing) return current.timestampMs
    const elapsedRealMs = performance.now() - current.performanceMs
    return current.timestampMs
      + elapsedRealMs * PLAYBACK_RATES[current.speed] * SIMULATED_DAY_MS / 1000
  }, [])

  const commitTimestamp = useCallback((nextTimestampMs) => {
    clock.current = {
      ...clock.current,
      timestampMs: nextTimestampMs,
      performanceMs: performance.now(),
    }
    setTimestampMs(nextTimestampMs)
  }, [])

  const updatePlaying = useCallback((nextPlaying) => {
    const resolved = typeof nextPlaying === 'function'
      ? nextPlaying(clock.current.playing)
      : nextPlaying
    const currentTimestampMs = getTimestampMs()
    clock.current = {
      ...clock.current,
      timestampMs: currentTimestampMs,
      performanceMs: performance.now(),
      playing: resolved,
    }
    setTimestampMs(currentTimestampMs)
    setPlaying(resolved)
  }, [getTimestampMs])

  const updateSpeed = useCallback((nextSpeed) => {
    const resolved = typeof nextSpeed === 'function'
      ? nextSpeed(clock.current.speed)
      : nextSpeed
    const currentTimestampMs = getTimestampMs()
    clock.current = {
      ...clock.current,
      timestampMs: currentTimestampMs,
      performanceMs: performance.now(),
      speed: resolved,
    }
    setTimestampMs(currentTimestampMs)
    setSpeed(resolved)
  }, [getTimestampMs])

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (clock.current.playing) setTimestampMs(getTimestampMs())
    }, UI_REFRESH_MS)
    return () => window.clearInterval(interval)
  }, [getTimestampMs])

  const reset = useCallback(() => {
    clock.current = {
      timestampMs: initialTimestamp.current,
      performanceMs: performance.now(),
      playing: true,
      speed: 'normal',
    }
    setTimestampMs(initialTimestamp.current)
    setSpeed('normal')
    setPlaying(true)
  }, [])

  return {
    timestampMs,
    getTimestampMs,
    setTimestampMs: commitTimestamp,
    playing,
    setPlaying: updatePlaying,
    speed,
    setSpeed: updateSpeed,
    reset,
  }
}
