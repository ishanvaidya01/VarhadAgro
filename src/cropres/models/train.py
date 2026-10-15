import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import lightgbm as lgb
from sklearn.linear_model import Ridge
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import fbeta_score

MODEL_NUM_FEATURES = [
    "precip_total_mm",
    "rainy_days",
    "heavy_rain_days",
    "longest_dry_spell",
    "heat_days_35",
    "heat_days_38",
    "heat_days_40",
    "diurnal_range",
    "t2m_mean",
    "tmax_mean",
    "gdd",
    "pet_total_mm",
    "water_balance_mm",
    "gwetroot_mean",
    "gwetroot_min",
    "precip_pct_normal",
    "spi3_asof"
]

CAT_FEATURES = ["district", "crop"]
ALL_FEATURES = MODEL_NUM_FEATURES + CAT_FEATURES

# Monotone constraints for LightGBM regressor on relative anomaly:
# longest_dry_spell: -1, heat_days_38: -1, heat_days_40: -1, gwetroot_mean: 1
MONOTONE_CONSTRAINTS = [
    0,   # precip_total_mm (nonlinear: flood / drought)
    0,   # rainy_days
    0,   # heavy_rain_days
    -1,  # longest_dry_spell (adverse)
    0,   # heat_days_35
    -1,  # heat_days_38 (adverse)
    -1,  # heat_days_40 (adverse)
    0,   # diurnal_range
    0,   # t2m_mean
    0,   # tmax_mean
    0,   # gdd
    0,   # pet_total_mm
    0,   # water_balance_mm
    1,   # gwetroot_mean (beneficial for rainfed)
    0,   # gwetroot_min
    0,   # precip_pct_normal
    0,   # spi3_asof
    0,   # district (cat)
    0    # crop (cat)
]


def split_data(df: pd.DataFrame, train_end_year: int = 2018) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simple 2-way temporal split by year.
    """
    train = df[df["year"] <= train_end_year].copy()
    test = df[df["year"] > train_end_year].copy()
    return train, test


def split_panel_by_years(
    df: pd.DataFrame,
    train_end_year: int = 2002,
    val_end_year: int = 2007
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Temporal rolling-origin partition:
    Train: years <= train_end_year (1981-2002)
    Val: train_end_year < years <= val_end_year (2003-2007)
    Test: years > val_end_year (2008-2017, touched strictly once)
    """
    train = df[df["year"] <= train_end_year].copy()
    val = df[(df["year"] > train_end_year) & (df["year"] <= val_end_year)].copy()
    test = df[df["year"] > val_end_year].copy()
    return train, val, test


def prepare_datasets(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame):
    """
    Encodes categorical features consistently across train, val, test.
    """
    cat_maps = {}
    for col in CAT_FEATURES:
        cats = sorted(train_df[col].unique().tolist())
        cat_maps[col] = cats
        train_df[col] = pd.Categorical(train_df[col], categories=cats)
        val_df[col] = pd.Categorical(val_df[col], categories=cats)
        test_df[col] = pd.Categorical(test_df[col], categories=cats)
    return train_df, val_df, test_df, cat_maps


def train_models_pipeline(
    feature_parquet: str = "data/processed/feature_table_full.parquet",
    artifacts_dir: str = "artifacts"
) -> Dict[str, Any]:
    """
    Fits baseline models, Ridge panel model, LightGBM quantile and median models,
    Isotonic calibrated classifier, and Conformalized Quantile Regression.
    """
    os.makedirs(f"{artifacts_dir}/models", exist_ok=True)
    os.makedirs(f"{artifacts_dir}/conformal", exist_ok=True)
    
    full_df = pd.read_parquet(feature_parquet)
    # Filter to end-of-season (EOS) instances for primary models
    eos_df = full_df[full_df["is_eos"]].dropna(subset=["yield_anomaly", "shortfall_event"]).copy()
    
    train_df, val_df, test_df = split_panel_by_years(eos_df, train_end_year=2002, val_end_year=2007)
    train_df, val_df, test_df, cat_maps = prepare_datasets(train_df, val_df, test_df)
    
    print(f"Data split: Train={len(train_df)} (1981-2002), Val={len(val_df)} (2003-2007), Test={len(test_df)} (2008-2017)")
    
    # Save category mapping
    with open(f"{artifacts_dir}/models/cat_maps.json", "w") as f:
        json.dump(cat_maps, f, indent=2)
        
    X_train = train_df[ALL_FEATURES]
    y_train_anomaly = train_df["yield_anomaly"].values
    y_train_shortfall = train_df["shortfall_event"].values
    
    X_val = val_df[ALL_FEATURES]
    y_val_anomaly = val_df["yield_anomaly"].values
    y_val_shortfall = val_df["shortfall_event"].values
    
    X_test = test_df[ALL_FEATURES]
    y_test_anomaly = test_df["yield_anomaly"].values
    y_test_shortfall = test_df["shortfall_event"].values
    
    # ── 1. Baseline Models ────────────────────────────────────────────────────────
    # Baseline A: Zero relative anomaly forecast
    # Baseline B: District-crop historical shortfall frequency
    baseline_b_lookup = train_df.groupby(["district", "crop"])["shortfall_event"].mean().to_dict()
    global_shortfall_rate = float(train_df["shortfall_event"].mean())
    
    # ── 2. Regularized Panel Linear Model (Ridge) ─────────────────────────────────
    # Create one-hot encodings for categorical features
    X_train_num = pd.get_dummies(train_df[ALL_FEATURES], drop_first=True)
    X_val_num = pd.get_dummies(val_df[ALL_FEATURES], drop_first=True)
    X_test_num = pd.get_dummies(test_df[ALL_FEATURES], drop_first=True)
    
    # Align columns
    X_train_num, X_val_num = X_train_num.align(X_val_num, join="left", axis=1, fill_value=0)
    X_train_num, X_test_num = X_train_num.align(X_test_num, join="left", axis=1, fill_value=0)
    
    ridge_model = Ridge(alpha=10.0)
    ridge_model.fit(X_train_num, y_train_anomaly)
    with open(f"{artifacts_dir}/models/ridge_panel_model.pkl", "wb") as f:
        pickle.dump({"model": ridge_model, "columns": list(X_train_num.columns)}, f)
        
    # ── 3. LightGBM Monotone Regressor (Median Anomaly: alpha=0.50) ───────────────
    lgb_train_ds = lgb.Dataset(X_train, label=y_train_anomaly, categorical_feature=CAT_FEATURES)
    lgb_val_ds = lgb.Dataset(X_val, label=y_val_anomaly, reference=lgb_train_ds, categorical_feature=CAT_FEATURES)
    
    reg_params = {
        "objective": "regression",
        "metric": "rmse",
        "num_leaves": 15,
        "max_depth": 4,
        "learning_rate": 0.03,
        "min_child_samples": 25,
        "monotone_constraints": MONOTONE_CONSTRAINTS,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "verbosity": -1,
        "seed": 42
    }
    lgb_regressor = lgb.train(
        reg_params,
        lgb_train_ds,
        num_boost_round=150,
        valid_sets=[lgb_val_ds]
    )
    lgb_regressor.save_model(f"{artifacts_dir}/models/lgb_regressor_median.txt")
    
    # ── 4. LightGBM Quantile Models for CQR (alpha=0.05 and alpha=0.95 for 90% CQR) ─
    q_low_params = {
        "objective": "quantile",
        "alpha": 0.05,
        "metric": "quantile",
        "num_leaves": 15,
        "max_depth": 4,
        "learning_rate": 0.03,
        "min_child_samples": 25,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "verbosity": -1,
        "seed": 42
    }
    lgb_q_low = lgb.train(q_low_params, lgb_train_ds, num_boost_round=120)
    lgb_q_low.save_model(f"{artifacts_dir}/models/lgb_q_low.txt")
    
    q_high_params = q_low_params.copy()
    q_high_params["alpha"] = 0.95
    lgb_q_high = lgb.train(q_high_params, lgb_train_ds, num_boost_round=120)
    lgb_q_high.save_model(f"{artifacts_dir}/models/lgb_q_high.txt")
    
    # ── 5. Conformalized Quantile Regression (CQR) Calibration on Validation Block ─
    # Non-conformity score on validation: E_i = max(q_low(x_i) - y_i, y_i - q_high(x_i))
    val_pred_low = lgb_q_low.predict(X_val)
    val_pred_high = lgb_q_high.predict(X_val)
    val_nonconformity = np.maximum(val_pred_low - y_val_anomaly, y_val_anomaly - val_pred_high)
    
    # Conformal correction factor Q_{1-alpha} with finite-sample adjustment (1 - alpha = 0.90)
    n_val = len(val_df)
    alpha_target = 0.10
    q_idx = int(np.ceil((n_val + 1) * (1.0 - alpha_target))) / n_val
    q_idx = min(1.0, max(0.0, q_idx))
    conformal_c = float(np.quantile(val_nonconformity, q_idx))
    
    # Grouped conformal adjustment by crop to account for crop-specific residual spread
    crop_conformal_adj = {}
    for crop in cat_maps["crop"]:
        crop_mask = val_df["crop"] == crop
        if crop_mask.sum() >= 5:
            crop_nc = val_nonconformity[crop_mask]
            crop_c = float(np.quantile(crop_nc, min(1.0, (len(crop_nc) + 1) * 0.90 / len(crop_nc))))
            crop_conformal_adj[crop] = max(0.0, crop_c)
        else:
            crop_conformal_adj[crop] = max(0.0, conformal_c)
            
    cqr_params = {
        "target_coverage": 0.90,
        "global_correction": round(conformal_c, 4),
        "crop_corrections": crop_conformal_adj,
        "n_calibration_samples": n_val
    }
    with open(f"{artifacts_dir}/conformal/conformal_cqr_params.json", "w") as f:
        json.dump(cqr_params, f, indent=2)
    print(f"CQR Calibrated on Validation block: Global correction c={conformal_c:.4f}")
    
    # ── 6. Shortfall Classifier & Isotonic Calibration ────────────────────────────
    class_train_ds = lgb.Dataset(X_train, label=y_train_shortfall, categorical_feature=CAT_FEATURES)
    class_val_ds = lgb.Dataset(X_val, label=y_val_shortfall, reference=class_train_ds, categorical_feature=CAT_FEATURES)
    
    class_params = {
        "objective": "binary",
        "metric": "auc",
        "num_leaves": 15,
        "max_depth": 4,
        "learning_rate": 0.03,
        "min_child_samples": 25,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 1,
        "verbosity": -1,
        "seed": 42
    }
    lgb_classifier = lgb.train(class_params, class_train_ds, num_boost_round=120, valid_sets=[class_val_ds])
    lgb_classifier.save_model(f"{artifacts_dir}/models/lgb_classifier.txt")
    
    # Raw probabilities on validation block
    val_raw_prob = lgb_classifier.predict(X_val)
    
    # Fit Isotonic Calibration on validation block strictly
    iso_calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    iso_calibrator.fit(val_raw_prob, y_val_shortfall)
    with open(f"{artifacts_dir}/models/isotonic_calibrator.pkl", "wb") as f:
        pickle.dump(iso_calibrator, f)
        
    val_calib_prob = iso_calibrator.predict(val_raw_prob)
    
    # Explicit Decision Threshold Selection on Validation Block:
    # Maximize F2 score (prioritizing recall of shortfall events) with false alarm rate <= 0.25
    candidate_thresholds = np.linspace(0.15, 0.70, 56)
    best_threshold = 0.50
    best_f2 = -1.0
    
    for t_cand in candidate_thresholds:
        preds = (val_calib_prob >= t_cand).astype(int)
        f2 = fbeta_score(y_val_shortfall, preds, beta=2.0, zero_division=0)
        # Check false alarm rate (FPR)
        neg_mask = y_val_shortfall == 0
        fpr = float(np.mean(preds[neg_mask])) if neg_mask.sum() > 0 else 0.0
        if fpr <= 0.25 and f2 > best_f2:
            best_f2 = f2
            best_threshold = float(t_cand)
            
    # Fallback to maximize F2 if no threshold met FPR <= 0.25
    if best_f2 < 0:
        for t_cand in candidate_thresholds:
            preds = (val_calib_prob >= t_cand).astype(int)
            f2 = fbeta_score(y_val_shortfall, preds, beta=2.0, zero_division=0)
            if f2 > best_f2:
                best_f2 = f2
                best_threshold = float(t_cand)
                
    decision_config = {
        "optimal_threshold": round(best_threshold, 3),
        "validation_f2": round(best_f2, 4),
        "criterion": "Maximize F2 on validation block subject to false alarm rate <= 25%"
    }
    with open(f"{artifacts_dir}/models/decision_config.json", "w") as f:
        json.dump(decision_config, f, indent=2)
    print(f"Decision threshold chosen on validation block: T* = {best_threshold:.3f} (F2={best_f2:.3f})")
    
    return {
        "train_df": train_df,
        "val_df": val_df,
        "test_df": test_df,
        "cat_maps": cat_maps,
        "cqr_params": cqr_params,
        "decision_config": decision_config
    }

if __name__ == "__main__":
    train_models_pipeline()
