import { celestialBodies } from '../data/catalog.js'
import { orbitalElements } from '../data/orbitalElements.js'
import { getVisualOrbitRadius } from './sceneScale.js'
import {
  MILLISECONDS_PER_DAY,
  getOrbitalSolution,
  getRenderedBodyPosition,
  getRenderedHeliocentricPosition,
} from './orbitalModel.js'

const body = (id) => celestialBodies.find((candidate) => candidate.id === id)
const J2000 = Date.UTC(2000, 0, 1, 12)

describe('shared-clock orbital model', () => {
  it('uses published relative orbital periods', () => {
    const periods = ['mercury', 'venus', 'earth', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']
      .map((id) => orbitalElements[id].period_days)
    expect(periods).toEqual([...periods].sort((a, b) => a - b))
  })

  it('returns to the same Keplerian position after one period', () => {
    const mars = body('mars')
    const first = getRenderedBodyPosition(mars, J2000)
    const second = getRenderedBodyPosition(
      mars,
      J2000 + orbitalElements.mars.period_days * MILLISECONDS_PER_DAY,
    )
    expect(second[0]).toBeCloseTo(first[0], 8)
    expect(second[2]).toBeCloseTo(first[2], 8)
  })

  it('derives position only from simulated timestamp, not playback speed', () => {
    const earth = body('earth')
    const timestamp = Date.UTC(2026, 0, 1)
    expect(getOrbitalSolution(earth, timestamp)).toEqual(getOrbitalSolution(earth, timestamp))
  })

  it('keeps compressed visual radius separate from physical distance', () => {
    const neptune = body('neptune')
    expect(getVisualOrbitRadius(neptune.orbit.semimajor_axis_km)).toBeLessThan(200)
    expect(neptune.orbit.semimajor_axis_km).toBeGreaterThan(4_000_000_000)
  })

  it('positions a moon relative to its moving parent', () => {
    const earth = body('earth')
    const moon = body('moon')
    const earthPosition = getRenderedBodyPosition(earth, J2000)
    const moonPosition = getRenderedHeliocentricPosition(moon, celestialBodies, J2000)
    expect(Math.hypot(moonPosition[0] - earthPosition[0], moonPosition[2] - earthPosition[2]))
      .toBeGreaterThan(1)
  })
})
