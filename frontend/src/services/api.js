const API_ROOT = import.meta.env.VITE_API_ROOT ?? ''
const REQUEST_TIMEOUT_MS = 30_000
const RESULT_CACHE_LIMIT = 64
const RESULT_CACHE_VERSION = 'physics-1.0.0:model-1.0.0:spectral-1.0.0'
const resultCache = new Map()

function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`
  }
  return JSON.stringify(value)
}

function readCachedResult(key) {
  const result = resultCache.get(key)
  if (!result) return null
  resultCache.delete(key)
  resultCache.set(key, result)
  return result
}

function cacheResult(key, result) {
  resultCache.set(key, result)
  while (resultCache.size > RESULT_CACHE_LIMIT) {
    resultCache.delete(resultCache.keys().next().value)
  }
  return result
}

export function clearAnalysisCache() {
  resultCache.clear()
}

export function getAnalysisCacheSize() {
  return resultCache.size
}

export async function getHealth() {
  const response = await fetch(`${API_ROOT}/api/health`)
  if (!response.ok) throw new Error(`Health request failed: ${response.status}`)
  return response.json()
}

export async function getBodies() {
  const response = await fetch(`${API_ROOT}/api/bodies`)
  if (!response.ok) throw new Error(`Catalog request failed: ${response.status}`)
  return response.json()
}

async function requestJson(path, signal, options = {}) {
  const requestController = new AbortController()
  let timedOut = false
  const forwardAbort = () => requestController.abort()
  signal?.addEventListener('abort', forwardAbort, { once: true })
  const timeout = setTimeout(() => {
    timedOut = true
    requestController.abort()
  }, REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(`${API_ROOT}${path}`, {
      ...options,
      signal: requestController.signal,
      headers: options.body ? { 'Content-Type': 'application/json', ...options.headers } : options.headers,
    })
    if (!response.ok) {
      const error = new Error(`Request failed: ${response.status}`)
      error.status = response.status
      throw error
    }
    return response.json()
  } catch (error) {
    if (timedOut) throw new Error('Request timed out.')
    throw error
  } finally {
    clearTimeout(timeout)
    signal?.removeEventListener('abort', forwardAbort)
  }
}

export async function getScenarioLightResult(destinationId, scenario, { signal, simulatedTime } = {}) {
  const cacheKey = [
    RESULT_CACHE_VERSION,
    'scenario',
    destinationId,
    simulatedTime ?? 'reference',
    stableStringify(scenario),
  ].join(':')
  const cached = readCachedResult(cacheKey)
  if (cached) return cached
  const query = simulatedTime ? `?at=${encodeURIComponent(simulatedTime)}` : ''
  const result = await requestJson(`/api/analyze/${destinationId}/scenario${query}`, signal, {
    method: 'POST',
    body: JSON.stringify(scenario),
  })
  return cacheResult(cacheKey, result)
}

function deterministicFallbackResponse(analysis, warning) {
  return {
    destination: analysis.destination,
    name: analysis.name,
    bodyType: analysis.bodyType,
    method: 'deterministic_fallback',
    modelName: null,
    modelVersion: 'deterministic',
    hasAtmosphere: analysis.hasAtmosphere,
    results: analysis.results,
    validation: {
      valid: analysis.validation.valid,
      fallbackUsed: true,
      corrected: false,
      energySum: analysis.validation.energySum,
      warnings: [warning, ...analysis.validation.warnings],
    },
    baselineComparison: null,
    sourceIds: analysis.sourceIds,
    astronomy: analysis.astronomy ?? null,
  }
}

export async function getLightResult(destinationId, { signal, simulatedTime } = {}) {
  const cacheKey = [
    RESULT_CACHE_VERSION,
    'prediction',
    destinationId,
    simulatedTime ?? 'reference',
  ].join(':')
  const cached = readCachedResult(cacheKey)
  if (cached) return cached
  const query = simulatedTime ? `?at=${encodeURIComponent(simulatedTime)}` : ''
  try {
    const prediction = await requestJson(`/api/predict/${destinationId}${query}`, signal)
    if (prediction.validation?.valid) return cacheResult(cacheKey, prediction)
    throw new Error('Prediction response failed validation.')
  } catch (predictionError) {
    if (predictionError.name === 'AbortError' || predictionError.status === 404) {
      throw predictionError
    }
    const analysis = await requestJson(`/api/analyze/${destinationId}${query}`, signal)
    if (!analysis.validation?.valid) {
      throw new Error('No validated light result is available.')
    }
    return cacheResult(cacheKey, deterministicFallbackResponse(
      analysis,
      `Prediction request unavailable: ${predictionError.message}`,
    ))
  }
}
