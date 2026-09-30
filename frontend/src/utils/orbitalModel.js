import { orbitalElements } from '../data/orbitalElements.js'
import {
  getEllipsePosition,
  getVisualBodyRadius,
  getVisualMoonOrbitRadius,
  getVisualOrbitRadius,
} from './sceneScale.js'

export const MILLISECONDS_PER_DAY = 86_400_000
export const UNIX_EPOCH_JULIAN_DAY = 2_440_587.5

export function timestampToJulianDay(timestampMs) {
  return timestampMs / MILLISECONDS_PER_DAY + UNIX_EPOCH_JULIAN_DAY
}

export function solveKepler(meanAnomaly, eccentricity) {
  const normalizedMeanAnomaly = ((meanAnomaly % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2)
  let eccentricAnomaly = eccentricity >= 0.8 ? Math.PI : normalizedMeanAnomaly
  for (let iteration = 0; iteration < 20; iteration += 1) {
    const delta = (
      eccentricAnomaly - eccentricity * Math.sin(eccentricAnomaly) - normalizedMeanAnomaly
    ) / (1 - eccentricity * Math.cos(eccentricAnomaly))
    eccentricAnomaly -= delta
    if (Math.abs(delta) < 1e-12) break
  }
  return eccentricAnomaly
}

export function getOrbitalSolution(body, timestampMs) {
  const element = orbitalElements[body.id]
  if (!element || !Number.isFinite(body.orbit?.semimajor_axis_km)) return null
  const elapsedDays = timestampToJulianDay(timestampMs) - element.epoch_jd
  const direction = element.direction ?? 1
  const meanAnomaly = (
    element.mean_anomaly_deg * Math.PI / 180
    + direction * Math.PI * 2 * elapsedDays / element.period_days
  )
  const eccentricity = Math.min(Math.max(body.orbit.eccentricity ?? 0, 0), 0.95)
  const eccentricAnomaly = solveKepler(meanAnomaly, eccentricity)
  return { eccentricAnomaly, eccentricity, element }
}

export function getRenderedBodyPosition(body, timestampMs, moonIndex = 0, parentRadius = 1) {
  const solution = getOrbitalSolution(body, timestampMs)
  if (!solution) return [0, 0, 0]
  const semimajorAxis = body.type === 'moon'
    ? getVisualMoonOrbitRadius(parentRadius, moonIndex)
    : getVisualOrbitRadius(body.orbit.semimajor_axis_km)
  return getEllipsePosition(semimajorAxis, solution.eccentricity, solution.eccentricAnomaly)
}

export function getRenderedHeliocentricPosition(body, bodies, timestampMs) {
  if (body.type !== 'moon') return getRenderedBodyPosition(body, timestampMs)
  const parent = bodies.find((candidate) => candidate.id === body.parent)
  if (!parent) return [0, 0, 0]
  const siblings = bodies.filter((candidate) => candidate.type === 'moon' && candidate.parent === body.parent)
  const moonIndex = siblings.findIndex((candidate) => candidate.id === body.id)
  const parentPosition = getRenderedBodyPosition(parent, timestampMs)
  const moonPosition = getRenderedBodyPosition(
    body,
    timestampMs,
    moonIndex,
    getVisualBodyRadius(parent),
  )
  return parentPosition.map((coordinate, index) => coordinate + moonPosition[index])
}
