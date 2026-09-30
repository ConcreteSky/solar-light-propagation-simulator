from typing import Literal

from pydantic import BaseModel

from .light_analysis import AnalysisResults


class PredictionValidation(BaseModel):
    valid: bool
    fallbackUsed: bool
    corrected: bool
    energySum: float
    warnings: list[str]


class BaselineComparison(BaseModel):
    transmittedAbsoluteError: float
    scatteredAbsoluteError: float
    absorbedAbsoluteError: float
    relativeBrightnessAbsoluteError: float


class LightPrediction(BaseModel):
    destination: str
    name: str
    bodyType: Literal["planet", "moon", "dwarf_planet"]
    method: Literal["machine_learning", "deterministic_fallback"]
    modelName: str | None
    modelVersion: str
    hasAtmosphere: bool | None
    results: AnalysisResults
    validation: PredictionValidation
    baselineComparison: BaselineComparison
    sourceIds: list[str]
