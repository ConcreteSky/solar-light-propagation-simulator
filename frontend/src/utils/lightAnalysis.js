const COLOR_LABELS = new Set([
  'white',
  'yellow',
  'orange',
  'red',
  'blue',
  'pale blue',
  'pale yellow',
  'gray-white',
])

export function createAppearanceSummary(body, analysis) {
  const size = analysis?.results?.apparentSizeCategory
  const color = analysis?.results?.dominantColor
  const brightness = analysis?.results?.relativeBrightness
  const sizePhrase = ['large', 'medium', 'small', 'very small'].includes(size)
    ? size
    : 'an uncertain size'

  let appearance = COLOR_LABELS.has(color) ? color : null
  if (color === 'dim white' || (!appearance && Number.isFinite(brightness) && brightness < 0.12)) {
    appearance = 'dim'
  }
  if (!appearance) appearance = 'neutral in color'

  return `From ${body.name}, the Sun looks ${sizePhrase} and ${appearance}.`
}

export function getAverageSolarDistanceKm(body, bodies) {
  if (body.orbit?.reference === 'sun') return body.orbit.semimajor_axis_km
  const parent = bodies.find((candidate) => candidate.id === body.parent)
  return parent?.orbit?.semimajor_axis_km ?? null
}

export function formatDistance(value) {
  if (!Number.isFinite(value)) return 'Data unavailable'
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)} km`
}

export function formatIrradiance(value) {
  if (!Number.isFinite(value)) return 'Data unavailable'
  const digits = value < 10 ? 3 : value < 100 ? 2 : 1
  return `${value.toFixed(digits)} W/m²`
}

export function formatTravelTime(value) {
  if (!Number.isFinite(value)) return 'Data unavailable'
  return `${new Intl.NumberFormat('en-US', { maximumFractionDigits: 1 }).format(value)} s`
}

export function formatPercent(value) {
  if (!Number.isFinite(value)) return 'Data unavailable'
  return `${(value * 100).toFixed(1)}%`
}
