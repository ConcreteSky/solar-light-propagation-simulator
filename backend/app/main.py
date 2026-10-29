from contextlib import asynccontextmanager
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas.celestial_body import CelestialBody
from .schemas.light_analysis import AtmosphereScenario, LightAnalysis
from .schemas.light_prediction import LightPrediction
from .schemas.solar_environment import SolarEnvironmentAnalysis
from .services.catalog import load_catalog
from .services.light_calculation_service import analyze_destination
from .services.ml_prediction_service import preload_model, predict_destination, predict_scenario
from .services.solar_environment_service import analyze_solar_environment


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        preload_model()
    except Exception:
        # Prediction requests expose the precise failure and use the deterministic fallback.
        pass
    yield

app = FastAPI(
    title="Solar Environment Simulator API",
    version="0.5.0",
    description="Solar light, magnetic-field, particle-environment, and shielding analysis API.",
    lifespan=lifespan,
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str | int]:
    return {"status": "online", "body_count": len(load_catalog())}


@app.get("/api/bodies", response_model=list[CelestialBody])
def bodies() -> list[CelestialBody]:
    return load_catalog()


@app.get("/api/analyze/{destination_id}", response_model=LightAnalysis)
def analyze(
    destination_id: str,
    at: datetime | None = None,
) -> LightAnalysis:
    try:
        return analyze_destination(destination_id, at)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown destination ID: {destination_id}",
        ) from error


@app.get("/api/environment/{destination_id}", response_model=SolarEnvironmentAnalysis)
def environment(destination_id: str, at: datetime | None = None) -> SolarEnvironmentAnalysis:
    try:
        return analyze_solar_environment(analyze_destination(destination_id, at))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=f"Unknown destination ID: {destination_id}") from error


@app.post("/api/analyze/{destination_id}/scenario", response_model=LightAnalysis)
def analyze_scenario(
    destination_id: str,
    scenario: AtmosphereScenario,
    at: datetime | None = None,
) -> LightAnalysis:
    try:
        return analyze_destination(destination_id, at, scenario)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown destination ID: {destination_id}",
        ) from error


@app.get("/api/predict/{destination_id}", response_model=LightPrediction)
def predict(
    destination_id: str,
    at: datetime | None = None,
) -> LightPrediction:
    try:
        return predict_destination(destination_id, at)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown destination ID: {destination_id}",
        ) from error


@app.post("/api/predict/{destination_id}/scenario", response_model=LightPrediction)
def predict_hypothetical_scenario(
    destination_id: str,
    scenario: AtmosphereScenario,
    at: datetime | None = None,
) -> LightPrediction:
    try:
        return predict_scenario(destination_id, scenario, at)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown destination ID: {destination_id}",
        ) from error
