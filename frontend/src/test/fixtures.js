export function makePrediction(overrides = {}) {
  return {
    destination: 'mars',
    name: 'Mars',
    bodyType: 'planet',
    method: 'machine_learning',
    resultSource: 'ML surrogate',
    modelName: 'hist_gradient_boosting',
    modelVersion: '1.0.0',
    hasAtmosphere: true,
    results: {
      transmitted: 0.7,
      scattered: 0.2,
      absorbed: 0.1,
      relativeBrightness: 0.43,
      dominantColor: 'yellow',
      scatteredLightColor: {
        label: 'blue', rgb: [132, 180, 242], spectralBand: 'short-visible',
        confidence: 'modeled', basis: 'molecular-rayleigh-scattering',
      },
      transmittedLightColor: {
        label: 'yellow', rgb: [255, 214, 107], spectralBand: 'broad-visible',
        confidence: 'modeled', basis: 'existing-dominant-light-classification',
      },
      apparentSizeCategory: 'small',
    },
    validation: {
      valid: true,
      fallbackUsed: false,
      corrected: true,
      energySum: 1,
      warnings: [],
    },
    baselineComparison: {
      transmittedAbsoluteError: 0.01,
      scatteredAbsoluteError: 0.005,
      absorbedAbsoluteError: 0.005,
      relativeBrightnessAbsoluteError: 0.02,
    },
    aiResults: {
      transmitted: 0.7, scattered: 0.2, absorbed: 0.1, relativeBrightness: 0.43,
    },
    deterministicResults: {
      transmitted: 0.71, scattered: 0.195, absorbed: 0.095, relativeBrightness: 0.45,
    },
    reliability: {
      classification: 'reliable',
      decision: 'use_ai',
      fallbackReason: null,
      physicalViolations: [],
      uncertainty: { score: 0.001, threshold: 0.008, perOutput: {}, method: 'ensemble spread' },
      ood: { score: 0.9, q95: 1.47, q99: 1.76, classification: 'in_distribution', method: 'standardized distance' },
    },
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
    scatteredLightColor: {
      label: 'neutral', rgb: [244, 232, 190], spectralBand: 'broad-visible',
      confidence: 'fallback', basis: 'neutral-fallback',
    },
    transmittedLightColor: {
      label: 'white', rgb: [244, 244, 238], spectralBand: 'broad-visible',
      confidence: 'modeled', basis: 'existing-dominant-light-classification',
    },
    apparentSizeCategory: 'medium',
  },
})

export const fallbackPrediction = makePrediction({
  method: 'deterministic_fallback',
  resultSource: 'Deterministic fallback',
  modelName: null,
  validation: {
    valid: true,
    fallbackUsed: true,
    corrected: false,
    energySum: 1,
    warnings: ['ML fallback: missing pressure.'],
  },
})
