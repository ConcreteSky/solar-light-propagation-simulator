from typing import Literal

from pydantic import BaseModel, Field


class PhysicalProperties(BaseModel):
    radius_km: float | None
    diameter_km: float | None
    mass_kg: float | None
    surface_gravity_ms2: float | None


class OrbitProperties(BaseModel):
    reference: Literal["sun", "parent"]
    semimajor_axis_km: float | None
    eccentricity: float | None
    periapsis_km: float | None
    apoapsis_km: float | None


class AtmosphericComposition(BaseModel):
    CO2: float | None = Field(ge=0, le=1)
    N2: float | None = Field(ge=0, le=1)
    O2: float | None = Field(ge=0, le=1)
    CH4: float | None = Field(ge=0, le=1)
    H2: float | None = Field(ge=0, le=1)
    He: float | None = Field(ge=0, le=1)


class AtmosphereProperties(BaseModel):
    hasAtmosphere: bool | None
    surface_pressure_pa: float | None
    density_kg_m3: float | None
    composition: AtmosphericComposition


class LightReference(BaseModel):
    solar_irradiance_w_m2: float | None
    light_travel_time_seconds: float | None
    distance_basis: Literal["body_semimajor_axis", "parent_semimajor_axis"]


class VisualProperties(BaseModel):
    baseColor: str
    texture: str | None
    material: str


class CelestialBody(BaseModel):
    id: str
    name: str
    type: Literal["planet", "moon", "dwarf_planet"]
    parent: str
    physical: PhysicalProperties
    orbit: OrbitProperties
    atmosphere: AtmosphereProperties
    light_reference: LightReference
    visual: VisualProperties
    source_ids: list[str]

