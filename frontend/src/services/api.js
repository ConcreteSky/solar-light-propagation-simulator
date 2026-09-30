const API_ROOT = import.meta.env.VITE_API_ROOT ?? ''
const REQUEST_TIMEOUT_MS = 30_000

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

async function requestJson(path, signal) {
  const requestController = new AbortController()
  let timedOut = false
  const forwardAbort = () => requestController.abort()
  signal?.addEventListener('abort', forwardAbort, { once: true })
  const timeout = setTimeout(() => {
    timedOut = true
    requestController.abort()
  }, REQUEST_TIMEOUT_MS)

  try {
    const response = await fetch(`${API_ROOT}${path}`, { signal: requestController.signal })
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
  }
}

export async function getLightResult(destinationId, { signal } = {}) {
  try {
    const prediction = await requestJson(`/api/predict/${destinationId}`, signal)
    if (prediction.validation?.valid) return prediction
    throw new Error('Prediction response failed validation.')
  } catch (predictionError) {
    if (predictionError.name === 'AbortError' || predictionError.status === 404) {
      throw predictionError
    }
    const analysis = await requestJson(`/api/analyze/${destinationId}`, signal)
    if (!analysis.validation?.valid) {
      throw new Error('No validated light result is available.')
    }
    return deterministicFallbackResponse(
      analysis,
      `Prediction request unavailable: ${predictionError.message}`,
    )
  }
}
