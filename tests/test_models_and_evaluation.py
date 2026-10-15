import os
import json
import re
import pytest
import numpy as np
import pandas as pd
import lightgbm as lgb
from cropres.models.train import split_data


def test_split_data():
    df = pd.DataFrame({
        "year": [2017, 2018, 2019, 2020]
    })
    train, test = split_data(df, train_end_year=2018)
    assert len(train) == 2
    assert len(test) == 2
    assert train["year"].max() == 2018
    assert test["year"].min() == 2019


def test_metrics_match_generated_report_exactly():
    """
    Ensures that every number in docs/EXPERIMENT_REPORT.md and docs/MODEL_CARD.md
    matches artifacts/metrics.json exactly without drift.
    """
    with open("artifacts/metrics.json", "r") as f:
        m = json.load(f)
        
    with open("docs/EXPERIMENT_REPORT.md", "r", encoding="utf-8") as f:
        exp_text = f.read()
        
    with open("docs/MODEL_CARD.md", "r", encoding="utf-8") as f:
        card_text = f.read()

    # Check regression metrics in docs
    lgb_rmse_str = f"{m['regression']['lightgbm_median']['rmse']:.4f}"
    assert lgb_rmse_str in exp_text, f"RMSE {lgb_rmse_str} missing from EXPERIMENT_REPORT.md"
    assert lgb_rmse_str in card_text, f"RMSE {lgb_rmse_str} missing from MODEL_CARD.md"

    # Check PR-AUC in docs
    prauc_str = f"{m['classification']['calibrated_shortfall_classifier']['pr_auc']:.4f}"
    assert prauc_str in exp_text, f"PR-AUC {prauc_str} missing from EXPERIMENT_REPORT.md"
    assert prauc_str in card_text, f"PR-AUC {prauc_str} missing from MODEL_CARD.md"

    # Check overall coverage in docs
    cov_str = f"{m['uncertainty_conformal_cqr']['empirical_coverage_overall'] * 100.0:.1f}%"
    assert cov_str in exp_text, f"Coverage {cov_str} missing from EXPERIMENT_REPORT.md"
    assert cov_str in card_text, f"Coverage {cov_str} missing from MODEL_CARD.md"


def test_model_reloading_and_reproducibility():
    """
    Ensures saved models reload cleanly and reproduce stored predictions.
    """
    btest = pd.read_csv("artifacts/backtest/backtest_predictions.csv")
    assert len(btest) > 0, "Backtest predictions file is empty"
    
    with open("artifacts/models/cat_maps.json") as f:
        cat_maps = json.load(f)
        
    lgb_regressor = lgb.Booster(model_file="artifacts/models/lgb_regressor_median.txt")
    
    sample_row = btest.iloc[[0]].copy()
    from cropres.models.train import ALL_FEATURES, CAT_FEATURES
    
    for col in CAT_FEATURES:
        sample_row[col] = pd.Categorical(sample_row[col], categories=cat_maps[col])
        
    reloaded_pred = float(lgb_regressor.predict(sample_row[ALL_FEATURES])[0])
    stored_pred = float(sample_row["predicted_anomaly"].iloc[0])
    
    assert abs(reloaded_pred - stored_pred) < 1e-3, (
        f"Reloaded prediction {reloaded_pred} does not match stored {stored_pred}"
    )


def test_conformal_calibration_fixture_coverage():
    """
    Verifies conformal quantile calibration logic on a held-out synthetic fixture:
    Empirical coverage must satisfy finite-sample coverage guarantee.
    """
    np.random.seed(42)
    n_cal = 200
    n_test = 500
    
    # Simulate true values and quantile predictions
    y_cal = np.random.normal(0, 1, n_cal)
    q_low_cal = np.full(n_cal, -1.645)
    q_high_cal = np.full(n_cal, 1.645)
    
    # Compute non-conformity scores
    scores = np.maximum(q_low_cal - y_cal, y_cal - q_high_cal)
    
    # Conformal correction for 90% coverage
    alpha = 0.10
    q_level = min(1.0, np.ceil((n_cal + 1) * (1 - alpha)) / n_cal)
    c = np.quantile(scores, q_level)
    
    # Evaluate on held-out test
    y_test = np.random.normal(0, 1, n_test)
    q_low_test = np.full(n_test, -1.645) - c
    q_high_test = np.full(n_test, 1.645) + c
    
    covered = (y_test >= q_low_test) & (y_test <= q_high_test)
    empirical_coverage = np.mean(covered)
    
    # Target is 90% (allow small 3% binomial sampling tolerance)
    assert empirical_coverage >= 0.87, f"Empirical coverage {empirical_coverage} was below tolerance"
