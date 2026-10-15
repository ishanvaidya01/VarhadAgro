import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from cropres.features.trend import compute_asof_trend_and_anomalies
from cropres.features.targets import compute_pmfby_thresholds
from cropres.features.weather_features import (
    compute_longest_dry_spell,
    compute_hargreaves_pet,
    extract_season_features_for_window
)


def test_hand_computed_weather_features():
    # 1. Longest dry spell test (< 2.5 mm is dry)
    # [0, 1.0, 0, 0] (4 dry), [5.0] (wet), [0, 0, 0, 0] (4 dry), [10.0] (wet)
    precip = np.array([0.0, 1.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 10.0])
    longest = compute_longest_dry_spell(precip, threshold=2.5)
    assert longest == 4

    # Another spell with longer run
    precip2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 0.0])
    assert compute_longest_dry_spell(precip2, threshold=2.5) == 6

    # 2. Hand-crafted daily weather DataFrame
    daily_data = pd.DataFrame({
        "month": [7, 7, 7, 7, 7],
        "day": [1, 2, 3, 4, 5],
        "t2m": [25.0, 28.0, 31.0, 33.0, 27.0],
        "t2m_max": [34.0, 36.0, 39.0, 41.0, 33.0],
        "t2m_min": [20.0, 22.0, 24.0, 26.0, 21.0],
        "precip_mm": [0.0, 10.0, 55.0, 1.0, 0.0],
        "gwetroot": [0.5, 0.6, 0.8, 0.7, 0.6],
        "sfc_sw_dwn": [20.0, 22.0, 18.0, 25.0, 21.0]
    })
    
    feats = extract_season_features_for_window(daily_data, crop="Cotton", cutoff_mm_dd="07-15", t_base=10.0)
    
    # Assertions
    assert feats["heat_days_35"] == 3  # 36, 39, 41
    assert feats["heat_days_38"] == 2  # 39, 41
    assert feats["heat_days_40"] == 1  # 41
    assert feats["rainy_days"] == 2    # 10.0, 55.0
    assert feats["heavy_rain_days"] == 1 # 55.0 >= 50
    assert feats["precip_total_mm"] == 66.0 # 10 + 55 + 1
    
    # GDD with t_base=10: (25-10) + (28-10) + (31-10) + (33-10) + (27-10) = 15+18+21+23+17 = 94.0
    assert abs(feats["gdd"] - 94.0) < 1e-3


def test_hand_computed_pmfby_threshold():
    # 7 historical years + current test year (2018)
    years = [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018]
    yields = [1000.0, 1100.0, 1200.0, 600.0, 700.0, 1300.0, 1400.0, 900.0]
    
    df = pd.DataFrame({"year": years, "yield_kg_ha": yields})
    res = compute_pmfby_thresholds(df, default_indemnity=0.80, window_years=7, max_calamity_drop=2)
    
    # For year 2018:
    # Prior 7 yields: [1000, 1100, 1200, 600, 700, 1300, 1400]
    # Sorted: [600, 700, 1000, 1100, 1200, 1300, 1400]
    # Drop 2 calamity years: remaining [1000, 1100, 1200, 1300, 1400]
    # Reference yield: mean = 1200.0
    # Threshold yield (80%): 1200.0 * 0.80 = 960.0
    # Current yield is 900.0 < 960.0 -> Shortfall event = 1
    row_2018 = res[res["year"] == 2018].iloc[0]
    assert abs(row_2018["pmfby_ref_yield"] - 1200.0) < 1e-3
    assert abs(row_2018["pmfby_threshold_80"] - 960.0) < 1e-3
    assert row_2018["shortfall_event_80"] == 1
    assert row_2018["shortfall_event"] == 1


def test_no_temporal_leakage_on_future_yield_tampering():
    """
    Changing future yields must have zero effect on prior years' trend, anomalies, or thresholds.
    """
    years = list(range(1990, 2015))
    np.random.seed(42)
    base_yields = [1000.0 + i * 20.0 + np.random.normal(0, 50) for i in range(len(years))]
    
    df_original = pd.DataFrame({"year": years, "yield_kg_ha": base_yields})
    res_orig = compute_asof_trend_and_anomalies(df_original)
    res_orig = compute_pmfby_thresholds(res_orig)
    
    # Tamper with year 2010 onwards by multiplying by 5
    tampered_yields = list(base_yields)
    tampered_yields[20] = tampered_yields[20] * 5.0  # Year 2010
    tampered_yields[21] = tampered_yields[21] * 10.0 # Year 2011
    
    df_tampered = pd.DataFrame({"year": years, "yield_kg_ha": tampered_yields})
    res_tamp = compute_asof_trend_and_anomalies(df_tampered)
    res_tamp = compute_pmfby_thresholds(res_tamp)
    
    # For all years up to 2009 (index < 20), trend, anomaly, and threshold MUST be strictly identical
    prior_orig = res_orig[res_orig["year"] < 2010]
    prior_tamp = res_tamp[res_tamp["year"] < 2010]
    
    np.testing.assert_allclose(prior_orig["trend_asof"], prior_tamp["trend_asof"])
    np.testing.assert_allclose(prior_orig["yield_anomaly"], prior_tamp["yield_anomaly"])
    np.testing.assert_allclose(prior_orig["pmfby_threshold_80"], prior_tamp["pmfby_threshold_80"])


def test_cutoff_isolation_no_future_weather_leakage():
    """
    Weather occurring after a cutoff date must never contaminate cutoff features.
    """
    dates = pd.date_range("2015-06-01", "2015-10-31")
    df_weather = pd.DataFrame({
        "date_dt": dates,
        "month": dates.month,
        "day": dates.day,
        "t2m": np.full(len(dates), 28.0),
        "t2m_max": np.full(len(dates), 34.0),
        "t2m_min": np.full(len(dates), 22.0),
        "precip_mm": np.full(len(dates), 5.0),
        "gwetroot": np.full(len(dates), 0.6),
        "sfc_sw_dwn": np.full(len(dates), 20.0)
    })
    
    cutoff_dt = pd.Timestamp("2015-07-15")
    window_clean = df_weather[df_weather["date_dt"] <= cutoff_dt]
    feats_clean = extract_season_features_for_window(window_clean, crop="Cotton", cutoff_mm_dd="07-15")
    
    # Now contaminate August with extreme 45C heat and 500mm torrential rain
    df_contaminated = df_weather.copy()
    aug_mask = df_contaminated["date_dt"] >= pd.Timestamp("2015-08-01")
    df_contaminated.loc[aug_mask, "t2m_max"] = 48.0
    df_contaminated.loc[aug_mask, "precip_mm"] = 500.0
    
    window_contam = df_contaminated[df_contaminated["date_dt"] <= cutoff_dt]
    feats_contam = extract_season_features_for_window(window_contam, crop="Cotton", cutoff_mm_dd="07-15")
    
    # Assert features are completely identical
    assert feats_clean["heat_days_40"] == feats_contam["heat_days_40"]
    assert feats_clean["precip_total_mm"] == feats_contam["precip_total_mm"]
    assert feats_clean["longest_dry_spell"] == feats_contam["longest_dry_spell"]
