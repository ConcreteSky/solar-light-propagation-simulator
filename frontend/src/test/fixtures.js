export function makePrediction(overrides = {}) {
  return {
    destination: 'mars',
    name: 'Mars',
    bodyType: 'planet',
    method: 'machine_learning',
    modelName: 'hist_gradient_boosting',
    modelVersion: '1.0.0',
    hasAtmosphere: true,
    results: {
      transmitted: 0.7,
      scattered: 0.2,
      absorbed: 0.1,
      relativeBrightness: 0.43,
      dominantColor: 'yellow',
      apparentSizeCategory: 'small',
    },
    validation: {
      valid: true,
      fallbackUsed: false,
      corrected: true,
      energySum: 1,
      warnings: [],
    },
    baselineComparison: null,
    sourceIds: ['test-source'],
    ...overrides,
  }
}

export const atmosphericPrediction = makePrediction()

export const airlessPrediction = makePrediction({
  destination: 'moon',
  name: 'Moon',
  bodyType: 'moon',
  hasAtmosphere: false,
  results: {
    transmitted: 0.85,
    scattered: 0.1,
    absorbed: 0.05,
    relativeBrightness: 0.9,
    dominantColor: 'white',
    apparentSizeCategory: 'medium',
  },
})

export const fallbackPrediction = makePrediction({
  method: 'deterministic_fallback',
  modelName: null,
  validation: {
    valid: true,
    fallbackUsed: true,
    corrected: false,
    energySum: 1,
    warnings: ['ML fallback: missing pressure.'],
  },
})
