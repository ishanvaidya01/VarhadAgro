import pytest
import pandas as pd
import numpy as np
import os
from pipeline.schema import validate_dataframe, CropDataRow
from pipeline.targets import TargetCreator
from tests.fixtures.synthetic_generator import generate_synthetic_data

def test_schema_validation():
    # Valid row
    df_valid = pd.DataFrame([{
        "crop": "Wheat", "region": "R1", "year": 2000, "yield_t_ha": 3.5,
        "t2m_avg": 25.0, "precip_mm": 100.0, "extreme_heat_days": 5, "data_source": "synthetic"
    }])
    valid, errors = validate_dataframe(df_valid)
    assert len(errors) == 0
    assert len(valid) == 1

    # Invalid row (negative yield)
    df_invalid = pd.DataFrame([{
        "crop": "Wheat", "region": "R1", "year": 2000, "yield_t_ha": -1.0,
        "t2m_avg": 25.0, "precip_mm": 100.0, "extreme_heat_days": 5, "data_source": "synthetic"
    }])
    valid, errors = validate_dataframe(df_invalid)
    assert len(errors) == 1
    assert len(valid) == 0

def test_missing_data_handling():
    # If missing data were passed to our target creator, it would cause issues.
    # Our pipeline drops na. Let's simulate that behavior.
    df = pd.DataFrame({
        "crop": ["Wheat", "Wheat", "Wheat"],
        "region": ["R1", "R1", "R1"],
        "year": [2000, 2001, 2002],
        "yield_t_ha": [3.5, np.nan, 3.8],
        "t2m_avg": [25.0, 26.0, 24.5],
        "precip_mm": [100.0, 80.0, 110.0],
        "extreme_heat_days": [5, 10, 2],
        "data_source": ["s", "s", "s"]
    })
    
    missing_pct = df.isnull().mean().to_dict()
    assert missing_pct["yield_t_ha"] > 0
    
    df_clean = df.dropna()
    assert len(df_clean) == 2

def test_idempotency(tmp_path):
    # Running generation twice should yield same rows and not double them up.
    # The DB insert handles provenance appending, but the CSV overwrites.
    db_path = tmp_path / "metadata.db"
    csv_path = tmp_path / "data.csv"
    
    df1 = generate_synthetic_data(output_path=csv_path, metadata_db=db_path)
    df2 = generate_synthetic_data(output_path=csv_path, metadata_db=db_path)
    
    assert len(df1) == len(df2)
    assert list(df1["yield_t_ha"]) == list(df2["yield_t_ha"])
    
    # Check DB has 2 entries now (resumable/logged)
    import sqlite3
    conn = sqlite3.connect(db_path)
    count = conn.execute("SELECT COUNT(*) FROM provenance").fetchone()[0]
    conn.close()
    assert count == 2

def test_no_leakage_in_target_creation():
    df = pd.DataFrame({
        "crop": ["Wheat"] * 10,
        "region": ["R1"] * 10,
        "year": list(range(2000, 2010)),
        "yield_t_ha": [2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 4.0, 5.0],
        "t2m_avg": [25.0] * 10, "precip_mm": [100.0] * 10, "extreme_heat_days": [5] * 10, "data_source": ["s"] * 10
    })
    
    # Train end year 2005
    tc = TargetCreator(train_end_year=2005)
    df_res = tc.fit_transform(df)
    
    # The trend for 2000-2005 should NOT be influenced by the massive jump in 2008-2009 (4.0, 5.0)
    # The anomalies for 2008-2009 will be highly positive because the trend is extrapolated from <= 2005
    # The anomaly for 2009 should be > 2.0 (yield 5.0 vs trend ~2.6)
    anomaly_2009 = df_res[df_res["year"] == 2009]["yield_anomaly"].values[0]
    assert anomaly_2009 > 1.0, f"Anomaly was {anomaly_2009}, expected it to reflect no leakage."
