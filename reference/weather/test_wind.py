import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from spotmap_wind import angular_sector_match, suitability_for_hour

BASE = {"spot_id": "example-spot", "discipline_id": "boat-wakesurf", "version": "draft-v1", "approved": True,
        "sectors": [{"from_deg": 315, "to_deg": 45, "verdict": "good", "max_wind_mps": 4, "max_gust_mps": 6, "note": "Тестовый вручную заданный сектор"}]}

def test_not_configured():
    assert suitability_for_hour(None, {"direction_from_deg": 0, "wind_mps": 2})["status"] == "not_configured"

def test_not_approved():
    assert suitability_for_hour({**BASE, "approved": False}, {"direction_from_deg": 0, "wind_mps": 2})["verdict"] is None

def test_cross_north():
    assert angular_sector_match(350,315,45)
    assert angular_sector_match(10,315,45)
    assert not angular_sector_match(180,315,45)

def test_good_manual():
    res=suitability_for_hour(BASE,{"direction_from_deg": 350,"wind_mps":3,"gust_mps":5})
    assert res["status"] == "estimated" and res["verdict"] == "good"

def test_wind_exceeds_manual_limit():
    assert suitability_for_hour(BASE,{"direction_from_deg":0,"wind_mps":5,"gust_mps":5})["verdict"] == "unsuitable"

def test_gust_exceeds_manual_limit():
    assert suitability_for_hour(BASE,{"direction_from_deg":0,"wind_mps":3,"gust_mps":7})["verdict"] == "unsuitable"

def test_no_sector():
    assert suitability_for_hour(BASE,{"direction_from_deg":180,"wind_mps":3,"gust_mps":4})["status"] == "no_rule_for_direction"

def test_no_gust_when_required():
    assert suitability_for_hour(BASE,{"direction_from_deg":0,"wind_mps":3})["status"] == "missing_forecast"

def test_overlapping_rules_rejected():
    profile={**BASE,"sectors":[BASE["sectors"][0], {"from_deg":350,"to_deg":60,"verdict":"limited"}]}
    assert suitability_for_hour(profile,{"direction_from_deg":0,"wind_mps":2})["status"] == "ambiguous_profile"

def test_invalid_sector():
    profile={**BASE,"sectors":[{"from_deg":-1,"to_deg":45,"verdict":"good"}]}
    assert suitability_for_hour(profile,{"direction_from_deg":0,"wind_mps":3})["status"] == "invalid_profile"

def test_invalid_forecast_direction():
    assert suitability_for_hour(BASE,{"direction_from_deg":361,"wind_mps":3,"gust_mps":5})["status"] == "invalid_forecast"
