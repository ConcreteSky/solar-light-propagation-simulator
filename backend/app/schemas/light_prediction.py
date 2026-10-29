from typing import Literal

from pydantic import BaseModel

from .light_analysis import AnalysisResults, AstronomicalState
from .solar_environment import SolarEnvironmentAnalysis


class UncertaintyEstimate(BaseModel):
    score: float
    threshold: float
    perOutput: dict[str, float]
    method: str


class OodAssessment(BaseModel):
    score: float
    q95: float
    q99: float
    classification: Literal["in_distribution", "near_boundary", "severe"]
    method: str


class ReliabilityAssessment(BaseModel):
    classification: Literal["reliable", "caution", "unreliable"]
    decision: Literal["use_ai", "defer_to_physics"]
    fallbackReason: str | None
    physicalViolations: list[str]
    uncertainty: UncertaintyEstimate | None
    ood: OodAssessment | None
    rawAiPrediction: list[float] | None = None


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
    resultSource: Literal["ML surrogate", "Deterministic fallback"]
    modelName: str | None
    modelVersion: str
    hasAtmosphere: bool | None
    results: AnalysisResults
    validation: PredictionValidation
    baselineComparison: BaselineComparison
    aiResults: AnalysisResults | None = None
    deterministicResults: AnalysisResults
    reliability: ReliabilityAssessment
    sourceIds: list[str]
    astronomy: AstronomicalState | None = None
    solarEnvironment: SolarEnvironmentAnalysis
