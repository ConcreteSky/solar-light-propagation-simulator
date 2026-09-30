from .catalog import load_catalog
from ..schemas.celestial_body import CelestialBody


def get_body(destination_id: str) -> CelestialBody:
    """Return one catalog body by its stable ID."""
    normalized_id = destination_id.strip().lower()
    for body in load_catalog():
        if body.id == normalized_id:
            return body
    raise KeyError(normalized_id)


def get_body_index() -> dict[str, CelestialBody]:
    return {body.id: body for body in load_catalog()}
