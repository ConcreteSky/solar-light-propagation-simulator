import json
from functools import lru_cache
from pathlib import Path

from ..schemas.celestial_body import CelestialBody

CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "celestialBodies.json"


@lru_cache(maxsize=1)
def load_catalog() -> list[CelestialBody]:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        payload = json.load(catalog_file)
    return [CelestialBody.model_validate(item) for item in payload["bodies"]]

