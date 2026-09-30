import { MathUtils } from 'three'

const INNER_ORBIT_KM = 57_900_000
const ORBIT_BASE = 18
const ORBIT_LOG_FACTOR = 42

export function getVisualOrbitRadius(realSemimajorAxisKm) {
  if (!Number.isFinite(realSemimajorAxisKm) || realSemimajorAxisKm <= 0) return ORBIT_BASE
  return ORBIT_BASE + ORBIT_LOG_FACTOR * Math.log10(realSemimajorAxisKm / INNER_ORBIT_KM)
}

export function getVisualBodyRadius(body) {
  const realRadius = body.physical?.radius_km ?? (body.physical?.diameter_km ?? 1000) / 2

  if (body.type === 'moon') {
    return MathUtils.clamp(0.42 + Math.log10(Math.max(realRadius, 6)) * 0.12, 0.5, 0.86)
  }

  if (body.type === 'dwarf_planet') {
    return MathUtils.clamp(0.72 + Math.log10(Math.max(realRadius, 200)) * 0.1, 0.86, 1.08)
  }

  return MathUtils.clamp(0.72 + Math.log10(Math.max(realRadius, 1000)) * 0.48, 1.2, 3.25)
}

export function getVisualMoonOrbitRadius(parentRadius, moonIndex) {
  return parentRadius + 2.15 + moonIndex * 1.45
}

export function createEllipsePoints(semimajorAxis, eccentricity = 0, segments = 160) {
  const safeEccentricity = MathUtils.clamp(eccentricity ?? 0, 0, 0.88)
  const semiminorAxis = semimajorAxis * Math.sqrt(1 - safeEccentricity ** 2)

  return Array.from({ length: segments + 1 }, (_, index) => {
    const angle = (index / segments) * Math.PI * 2
    return [
      semimajorAxis * (Math.cos(angle) - safeEccentricity),
      0,
      semiminorAxis * Math.sin(angle),
    ]
  })
}

export function getStablePhase(id) {
  let hash = 0
  for (const character of id) hash = (hash * 31 + character.charCodeAt(0)) >>> 0
  return ((hash % 360) * Math.PI) / 180
}

export function getEllipsePosition(semimajorAxis, eccentricity, phase) {
  const safeEccentricity = MathUtils.clamp(eccentricity ?? 0, 0, 0.88)
  const semiminorAxis = semimajorAxis * Math.sqrt(1 - safeEccentricity ** 2)
  return [
    semimajorAxis * (Math.cos(phase) - safeEccentricity),
    0,
    semiminorAxis * Math.sin(phase),
  ]
}

