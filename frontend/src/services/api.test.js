import {
  clearAnalysisCache,
  getAnalysisCacheSize,
  getLightResult,
  getScenarioLightResult,
} from './api.js'
import { atmosphericPrediction } from '../test/fixtures.js'

function response(body, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  }
}

const deterministicAnalysis = {
  destination: 'mars',
  name: 'Mars',
  bodyType: 'planet',
  hasAtmosphere: true,
  results: atmosphericPrediction.results,
  validation: { valid: true, energySum: 1, warnings: [] },
  sourceIds: ['test-source'],
}

describe('light API service', () => {
  beforeEach(() => clearAnalysisCache())

  it('returns a validated prediction response', async () => {
    global.fetch = vi.fn().mockResolvedValue(response(atmosphericPrediction))
    await expect(getLightResult('mars')).resolves.toEqual(atmosphericPrediction)
    expect(fetch).toHaveBeenCalledWith(
      '/api/predict/mars',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
  })

  it('uses deterministic analysis when prediction transport fails', async () => {
    global.fetch = vi
      .fn()
      .mockResolvedValueOnce(response({}, 503))
      .mockResolvedValueOnce(response(deterministicAnalysis))
    const result = await getLightResult('mars')
    expect(result.method).toBe('deterministic_fallback')
    expect(result.validation.fallbackUsed).toBe(true)
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it('preserves invalid destination errors without inventing a result', async () => {
    global.fetch = vi.fn().mockResolvedValue(response({}, 404))
    await expect(getLightResult('unknown')).rejects.toMatchObject({ status: 404 })
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it('posts Scenario Mode inputs to the deterministic analysis endpoint', async () => {
    global.fetch = vi.fn().mockResolvedValue(response(deterministicAnalysis))
    const scenario = { hasAtmosphere: true, composition: {} }
    await getScenarioLightResult('mars', scenario)
    expect(fetch).toHaveBeenCalledWith(
      '/api/analyze/mars/scenario',
      expect.objectContaining({ method: 'POST', body: JSON.stringify(scenario) }),
    )
  })

  it('reuses identical results and keeps the cache bounded', async () => {
    global.fetch = vi.fn().mockResolvedValue(response(atmosphericPrediction))
    await getLightResult('mars')
    await getLightResult('mars')
    expect(fetch).toHaveBeenCalledOnce()

    for (let index = 0; index < 80; index += 1) {
      await getLightResult(`destination-${index}`)
    }
    expect(getAnalysisCacheSize()).toBe(64)
  })
})
