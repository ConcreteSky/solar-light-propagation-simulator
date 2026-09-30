from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .celestial_body import AtmosphericComposition


ColorCategory = Literal[
    "white",
    "yellow",
    "orange",
    "red",
    "blue",
    "pale blue",
    "pale yellow",
    "dim white",
    "gray-white",
]
SizeCategory = Literal["large", "medium", "small", "very small"]


class ModeledLightColor(BaseModel):
    label: Literal[
        "neutral",
        "white",
        "yellow",
        "orange",
        "red",
        "blue",
        "cyan",
        "pale blue",
        "pale yellow",
        "dim white",
        "gray-white",
    ]
    rgb: tuple[int, int, int]
    spectralBand: Literal["short-visible", "blue-green-visible", "broad-visible"] | None
    confidence: Literal["supported", "modeled", "fallback"]
    basis: Literal[
        "molecular-rayleigh-scattering",
        "methane-red-absorption",
        "nitrogen-methane-photochemical-haze",
        "existing-dominant-light-classification",
        "neutral-fallback",
    ]

    @field_validator("rgb")
    @classmethod
    def validate_rgb(cls, value: tuple[int, int, int]) -> tuple[int, int, int]:
        if any(channel < 0 or channel > 255 for channel in value):
            raise ValueError("RGB channels must be between 0 and 255.")
        return value


class AnalysisInputs(BaseModel):
    distanceFromSunKm: float = Field(gt=0)
    solarIrradianceWm2: float = Field(ge=0)
    derivedSolarIrradianceWm2: float = Field(ge=0)
    irradianceSource: Literal["stored_reference", "inverse_square"]
    surfacePressurePa: float | None = Field(default=None, ge=0)
    atmosphericDensityKgM3: float | None = Field(default=None, ge=0)
    composition: AtmosphericComposition
    solarSpectrumVisibleFraction: float = Field(ge=0, le=1)
    solarSpectrumRangeNm: list[float] = Field(min_length=2, max_length=2)


class AnalysisResults(BaseModel):
    transmitted: float = Field(ge=0, le=1)
    scattered: float = Field(ge=0, le=1)
    absorbed: float = Field(ge=0, le=1)
    relativeBrightness: float = Field(ge=0, le=1)
    dominantColor: ColorCategory
    scatteredLightColor: ModeledLightColor
    transmittedLightColor: ModeledLightColor
    apparentSizeCategory: SizeCategory


class AtmosphereScenario(BaseModel):
    hasAtmosphere: bool
    surfacePressurePa: float | None = Field(default=None, ge=0)
    atmosphericDensityKgM3: float | None = Field(default=None, ge=0)
    composition: AtmosphericComposition


class AnalysisValidation(BaseModel):
    energySum: float
    valid: bool
    warnings: list[str]


class AstronomicalState(BaseModel):
    simulatedTime: str
    distanceFromSunKm: float = Field(gt=0)
    orbitalAngleDeg: float = Field(ge=0, lt=360)
    lightTravelTimeSeconds: float = Field(gt=0)
    solarIrradianceWm2: float = Field(ge=0)
    apparentSolarAngularDiameterDeg: float = Field(gt=0)
    orbitalPeriodDays: float = Field(gt=0)
    referenceEpochJd: float
    phaseStatus: str
    approximate: bool = True


class LightAnalysis(BaseModel):
    destination: str
    name: str
    bodyType: Literal["planet", "moon", "dwarf_planet"]
    hasAtmosphere: bool | None
    calculationStatus: Literal["complete", "partial"]
    inputs: AnalysisInputs
    results: AnalysisResults
    validation: AnalysisValidation
    sourceIds: list[str]
    astronomy: AstronomicalState | None = None
