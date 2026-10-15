import pytest
import pandas as pd
from backend.engine import ResilienceEngine


def test_find_analog():
    engine = ResilienceEngine(model_path="dummy")
    target = {"t2m_avg": 25.0, "precip_mm": 100.0}
    candidates = {
        "Region_A": {"t2m_avg": 25.1, "precip_mm": 102.0},
        "Region_B": {"t2m_avg": 30.0, "precip_mm": 50.0}
    }
    analog, dist = engine.find_analog(target, candidates)
    assert analog == "Region_A"
    assert dist < 5.0

def test_risk_map():
    engine = ResilienceEngine(model_path="dummy")
    data = {
        "R1": {"downside_prob": 0.25},
        "R2": {"downside_prob": 0.05}
    }
    res = engine.interactive_risk_map_data(data)
    assert res["R1"]["severity"] == "High"
    assert res["R2"]["severity"] == "Low"
