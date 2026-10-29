from backend.app.schemas.light_analysis import AtmosphereScenario
from backend.app.services.light_calculation_service import analyze_destination
from backend.app.services.solar_environment_service import analyze_solar_environment, load_environment_catalog
import csv
from pathlib import Path


def test_environment_catalog_covers_all_destinations():
    version, notice, records = load_environment_catalog()
    assert version == "1.0.0"
    assert len(records) == 32
    assert "not dosimetry" in notice


def test_distinct_magnetic_families_are_preserved():
    records = load_environment_catalog()[2]
    expected = {
        "venus": "induced", "earth": "intrinsic_dipole", "mars": "crustal_remnant",
        "saturn": "intrinsic_aligned", "uranus": "intrinsic_tilted_offset",
        "ganymede": "intrinsic_mini", "io": "parent_plasma", "pluto": "unknown",
    }
    assert {key: records[key].magnetic.family for key in expected} == expected


def test_scenario_atmosphere_changes_shielding_without_inventing_magnetic_data():
    real = analyze_solar_environment(analyze_destination("mars"))
    thick = analyze_solar_environment(analyze_destination("mars", scenario=AtmosphereScenario(
        hasAtmosphere=True, surfacePressurePa=1_000_000, atmosphericDensityKgM3=8,
        composition={"CO2": 0.95, "N2": 0.05, "O2": 0, "CH4": 0, "H2": 0, "He": 0},
    )))
    assert real.magnetic.family == thick.magnetic.family == "crustal_remnant"
    assert real.dynamic.atmosphericShielding == "limited"
    assert thick.dynamic.atmosphericShielding == "substantial"
    assert thick.dynamic.scenarioAdjustedSurfaceExposure != real.dynamic.scenarioAdjustedSurfaceExposure


def test_unknowns_remain_explicit_and_proxy_is_labeled():
    result = analyze_solar_environment(analyze_destination("eris"))
    assert result.magnetic.globalField is None
    assert result.dataQuality == "unknown"
    assert "not a space-weather forecast" in result.dynamic.fluxProxyBasis


def test_research_summary_is_a_complete_catalog_extraction():
    path = Path(__file__).resolve().parents[2] / "research" / "solar_environment_v1" / "body_environment_summary.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    records = load_environment_catalog()[2]
    assert len(rows) == 32
    assert {row["id"] for row in rows} == set(records)
    assert all(row["magnetic_family"] == records[row["id"]].magnetic.family for row in rows)
