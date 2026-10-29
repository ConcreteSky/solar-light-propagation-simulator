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
    solarEnvironment: {
      schemaVersion: '1.0.0',
      classificationNotice: 'Qualitative categories; not dosimetry or a space-weather forecast.',
      destination: 'mars', dataQuality: 'supported', approximate: true,
      magnetic: {
        globalField: false, family: 'crustal_remnant', type: 'crustal remanent fields',
        origin: 'magnetized crust', surfaceStrengthMicrotesla: null, tiltDeg: null,
        offsetBodyRadii: null, geometry: 'localized patches', magnetospherePresence: 'hybrid',
        extentBodyRadii: null, shape: 'patchy', shielding: 'limited', notes: 'test',
      },
      particleEnvironment: {
        solarWindExposure: 'direct', radiationLevel: 'high', trappedRadiation: 'limited',
        interactionType: 'induced and crustal', surfaceExposure: 'high', notes: 'test',
      },
      dynamic: {
        solarIrradianceWm2: 588.6, steadyStateSolarWindFluxProxy: 0.432,
        fluxProxyBasis: 'test proxy', uvContext: 'reduced steady solar input',
        atmosphericShielding: 'limited', magneticShielding: 'limited', combinedShielding: 'limited',
        scenarioAdjustedSurfaceExposure: 'high', consequence: 'Qualitative test consequence.',
      },
      summary: 'Mars has no global dynamo; local crustal fields create patchy interactions.',
      sourceIds: ['test-source'],
    },
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
