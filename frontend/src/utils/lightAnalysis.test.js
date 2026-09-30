import { createAppearanceSummary, formatDistance, formatIrradiance, formatTravelTime } from './lightAnalysis.js'
import { atmosphericPrediction } from '../test/fixtures.js'

describe('light analysis formatting', () => {
  it('creates exactly one short deterministic appearance sentence', () => {
    const sentence = createAppearanceSummary({ name: 'Mars' }, atmosphericPrediction)
    expect(sentence).toBe('From Mars, the Sun looks small and yellow.')
    expect(sentence.match(/\./g)).toHaveLength(1)
  })

  it('shows explicit scientific units and unavailable values', () => {
    expect(formatDistance(227_900_000)).toBe('227,900,000 km')
    expect(formatIrradiance(588.6)).toBe('588.6 W/m²')
    expect(formatTravelTime(760.2)).toBe('760.2 s')
    expect(formatIrradiance(null)).toBe('Data unavailable')
  })
})
