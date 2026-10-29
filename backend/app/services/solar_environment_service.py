from functools import lru_cache
import json
from pathlib import Path

from ..schemas.light_analysis import LightAnalysis
from ..schemas.solar_environment import DynamicEnvironment, SolarEnvironmentAnalysis, SolarEnvironmentRecord


DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "solarEnvironment.v1.json"
EARTH_IRRADIANCE_W_M2 = 1361.0
LEVEL_SCORE = {"none": 0, "minimal": 0, "limited": 1, "low": 1, "moderate": 2, "substantial": 3, "high": 3, "intense": 4, "extreme": 4, "unknown": None, "not_applicable": None}


@lru_cache(maxsize=1)
def load_environment_catalog() -> tuple[str, str, dict[str, SolarEnvironmentRecord]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    records = [SolarEnvironmentRecord.model_validate(item) for item in payload["records"]]
    indexed = {record.id: record for record in records}
    if len(records) != 32 or len(indexed) != 32:
        raise ValueError("Solar-environment catalog must contain 32 unique destinations.")
    return payload["schema_version"], payload["classification_notice"], indexed


def get_environment_record(destination_id: str) -> SolarEnvironmentRecord:
    return load_environment_catalog()[2][destination_id.strip().lower()]


def _atmospheric_shielding(baseline: LightAnalysis, surface_exposure: str) -> str:
    if surface_exposure == "not_applicable":
        return "not_applicable"
    if baseline.hasAtmosphere is False:
        return "none"
    if baseline.hasAtmosphere is None:
        return "unknown"
    pressure = baseline.inputs.surfacePressurePa
    if pressure is None:
        return "unknown"
    if pressure < 100:
        return "minimal"
    if pressure < 10_000:
        return "limited"
    if pressure < 500_000:
        return "moderate"
    return "substantial"


def _combined_shielding(magnetic: str, atmospheric: str) -> str:
    known = [LEVEL_SCORE.get(level) for level in (magnetic, atmospheric)]
    known = [score for score in known if score is not None]
    if atmospheric == "not_applicable":
        return magnetic
    if not known:
        return "unknown"
    score = max(known)
    return ("none", "limited", "moderate", "substantial", "extreme")[min(score, 4)]


def _adjusted_exposure(base: str, shielding: str) -> str:
    if base in {"unknown", "not_applicable"}:
        return base
    base_score = LEVEL_SCORE.get(base)
    shield_score = LEVEL_SCORE.get(shielding)
    if base_score is None or shield_score is None:
        return "unknown"
    score = max(1, base_score - max(0, shield_score - 1))
    return {1: "low", 2: "moderate", 3: "high", 4: "extreme"}[score]


def analyze_solar_environment(baseline: LightAnalysis) -> SolarEnvironmentAnalysis:
    schema_version, notice, records = load_environment_catalog()
    record = records[baseline.destination]
    irradiance = baseline.inputs.solarIrradianceWm2
    flux_proxy = irradiance / EARTH_IRRADIANCE_W_M2
    if flux_proxy >= 2:
        uv_context = "elevated steady solar input"
    elif flux_proxy >= 0.5:
        uv_context = "Earth-order steady solar input"
    elif flux_proxy >= 0.05:
        uv_context = "reduced steady solar input"
    else:
        uv_context = "very low steady solar input"
    atmospheric = _atmospheric_shielding(baseline, record.particleEnvironment.surfaceExposure)
    magnetic = record.magnetic.shielding
    combined = _combined_shielding(magnetic, atmospheric)
    exposure = _adjusted_exposure(record.particleEnvironment.surfaceExposure, combined)
    consequence = (
        "No solid reference surface; exposure describes the modeled environment."
        if exposure == "not_applicable"
        else "Surface particle exposure is unknown because the available evidence is insufficient."
        if exposure == "unknown"
        else f"The qualitative surface particle-exposure category is {exposure} under this atmosphere scenario."
    )
    return SolarEnvironmentAnalysis(
        schemaVersion=schema_version,
        classificationNotice=notice,
        destination=record.id,
        dataQuality=record.dataQuality,
        approximate=record.approximate,
        magnetic=record.magnetic,
        particleEnvironment=record.particleEnvironment,
        dynamic=DynamicEnvironment(
            solarIrradianceWm2=round(irradiance, 9),
            steadyStateSolarWindFluxProxy=round(flux_proxy, 9),
            fluxProxyBasis="inverse-square steady-state proxy from irradiance relative to 1361 W/m²; not a space-weather forecast",
            uvContext=uv_context,
            atmosphericShielding=atmospheric,
            magneticShielding=magnetic,
            combinedShielding=combined,
            scenarioAdjustedSurfaceExposure=exposure,
            consequence=consequence,
        ),
        summary=record.summary,
        sourceIds=record.sourceIds,
    )
