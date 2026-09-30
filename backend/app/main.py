from contextlib import asynccontextmanager
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas.celestial_body import CelestialBody
from .schemas.light_analysis import LightAnalysis
from .schemas.light_prediction import LightPrediction
from .services.catalog import load_catalog
from .services.light_calculation_service import analyze_destination
from .services.ml_prediction_service import preload_model, predict_destination


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        preload_model()
    except Exception:
        # Prediction requests expose the precise failure and use the deterministic fallback.
        pass
    yield

app = FastAPI(
    title="Solar Light Propagation Simulator API",
    version="0.4.0",
    description="Deterministic solar-light analysis and local ML surrogate API.",
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
    allow_methods=["GET"],
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
