from typing import Literal

from pydantic import BaseModel


Level = Literal["none", "minimal", "limited", "low", "moderate", "substantial", "high", "extreme", "intense", "unknown", "not_applicable"]


class NumericRange(BaseModel):
    min: float | None = None
    max: float | None = None
    basis: str


class MagneticEnvironment(BaseModel):
    globalField: bool | None
    family: str
    type: str
    origin: str
    surfaceStrengthMicrotesla: NumericRange | None
    tiltDeg: float | None
    offsetBodyRadii: float | None
    geometry: str
    magnetospherePresence: str
    extentBodyRadii: NumericRange | None
    shape: str
    shielding: str
    notes: str


class ParticleEnvironment(BaseModel):
    solarWindExposure: str
    radiationLevel: str
    trappedRadiation: str
    interactionType: str
    surfaceExposure: str
    notes: str


class SolarEnvironmentRecord(BaseModel):
    id: str
    dataQuality: Literal["supported", "limited", "unknown"]
    approximate: bool
    magnetic: MagneticEnvironment
    particleEnvironment: ParticleEnvironment
    summary: str
    sourceIds: list[str]


class DynamicEnvironment(BaseModel):
    solarIrradianceWm2: float
    steadyStateSolarWindFluxProxy: float
    fluxProxyBasis: str
    uvContext: str
    atmosphericShielding: str
    magneticShielding: str
    combinedShielding: str
    scenarioAdjustedSurfaceExposure: str
    consequence: str


class SolarEnvironmentAnalysis(BaseModel):
    schemaVersion: str
    classificationNotice: str
    destination: str
    dataQuality: Literal["supported", "limited", "unknown"]
    approximate: bool
    magnetic: MagneticEnvironment
    particleEnvironment: ParticleEnvironment
    dynamic: DynamicEnvironment
    summary: str
    sourceIds: list[str]
