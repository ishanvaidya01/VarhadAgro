import pytest
import json
from cropres.api.app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


def test_health(client):
    rv = client.get("/api/health")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["status"] == "ok"
    assert data["districts_loaded"] == 8


def test_meta_endpoint(client):
    rv = client.get("/api/meta")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "provenance" in data
    assert "ICRISAT" in data["provenance"]["yield_source"]
    assert "NASA POWER" in data["provenance"]["weather_source"]
    assert data["districts_count"] == 8
    assert "Cotton" in data["crops"]


def test_districts_endpoint(client):
    rv = client.get("/api/districts")
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data["districts"]) == 8
    assert "geojson" in data
    assert data["geojson"]["type"] == "FeatureCollection"
    assert len(data["geojson"]["features"]) == 8


def test_crops_endpoint(client):
    rv = client.get("/api/crops")
    assert rv.status_code == 200
    data = rv.get_json()
    crops = [c["crop"] for c in data["crops"]]
    assert "Cotton" in crops
    assert "Wheat" in crops
    assert "Soybean" in crops


def test_risk_map_endpoint(client):
    rv = client.get("/api/risk-map?crop=Cotton")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["crop"] == "Cotton"
    assert len(data["districts"]) == 8
    assert "decision_threshold" in data
    assert "provenance" in data

    # Test invalid crop
    rv_err = client.get("/api/risk-map?crop=Banana")
    assert rv_err.status_code == 400
    assert rv_err.get_json()["error"] == "invalid_parameter"


def test_district_detail_endpoint(client):
    rv = client.get("/api/district/Akola?crop=Cotton")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["district"] == "Akola"
    assert data["crop"] == "Cotton"
    assert len(data["history"]) >= 30
    assert len(data["backtest"]) == 10
    assert "skill_assessment" in data
    assert "statement" in data["skill_assessment"]

    # Missing crop
    rv_miss = client.get("/api/district/Akola")
    assert rv_miss.status_code == 400

    # Unknown district
    rv_unknown = client.get("/api/district/Atlantis?crop=Cotton")
    assert rv_unknown.status_code == 404


def test_yield_history_compat(client):
    rv = client.get("/api/yield-history?region=Akola&crop=Cotton")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["district"] == "Akola"


def test_early_warning_endpoint(client):
    rv = client.get("/api/early-warning?crop=Cotton&district=Akola")
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data["lead_time_skill_progression"]) == 4
    assert "season_tracker" in data
    assert data["season_tracker"]["recent_observed_year"] == 2023
    assert data["season_tracker"]["cumulative_rainfall_mm"] > 0


def test_scenario_endpoint(client):
    payload = {
        "district": "Akola",
        "crop": "Cotton",
        "temp_shift": 1.5,
        "precip_shift": -0.15,
        "heat_days_shift": 5
    }
    rv = client.post("/api/scenario", json=payload)
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["district"] == "Akola"
    assert "ood_guard" in data
    assert "baseline_summary" in data
    assert "scenario_summary" in data
    assert "distribution_points" in data


def test_scenario_validation_errors(client):
    # Empty body
    rv = client.post("/api/scenario", json={})
    assert rv.status_code == 400
    assert rv.get_json()["error"] in ("empty_body", "validation_error")

    # Invalid crop
    rv_crop = client.post("/api/scenario", json={"district": "Akola", "crop": "Pineapple"})
    assert rv_crop.status_code == 400
    assert rv_crop.get_json()["error"] == "validation_error"

    # Extreme unrealistic shift outside bounds
    rv_temp = client.post("/api/scenario", json={"district": "Akola", "crop": "Cotton", "temp_shift": 99.0})
    assert rv_temp.status_code == 400


def test_crop_reliability_endpoint(client):
    rv = client.get("/api/reliability?district=Akola")
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["district"] == "Akola"
    assert len(data["ranked_crops"]) >= 4
    assert data["ranked_crops"][0]["rank"] == 1


def test_climate_analogs_endpoint(client):
    # GET
    rv_get = client.get("/api/analogs?district=Akola&temp_shift=2.0&precip_shift=-0.20")
    assert rv_get.status_code == 200
    data_get = rv_get.get_json()
    assert data_get["target_district"] == "Akola"
    assert len(data_get["analogs"]) == 4

    # POST
    payload = {"district": "Akola", "temp_shift": 2.0, "precip_shift": -0.20, "top_k": 3}
    rv_post = client.post("/api/analogs", json=payload)
    assert rv_post.status_code == 200
    data_post = rv_post.get_json()
    assert len(data_post["analogs"]) == 3


def test_evidence_endpoint(client):
    rv = client.get("/api/evidence")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "metrics" in data
    assert "plots_data" in data
    assert "model_card_summary" in data
    assert data["metrics"]["uncertainty_conformal_cqr"]["target_coverage"] == 0.9


def test_unknown_route_returns_404(client):
    rv = client.get("/api/does-not-exist")
    assert rv.status_code == 404
    data = rv.get_json()
    assert data["error"] == "not_found"
