import os
import json
import pickle
from typing import Dict, List, Tuple, Any
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    precision_recall_curve,
    auc,
    brier_score_loss,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    confusion_matrix
)
from sklearn.calibration import calibration_curve
import lightgbm as lgb
import shap

from cropres.models.train import (
    MODEL_NUM_FEATURES,
    CAT_FEATURES,
    ALL_FEATURES,
    split_panel_by_years,
    prepare_datasets
)
from cropres.models.explain import explain_dataset


def block_bootstrap_ci(
    df: pd.DataFrame,
    metric_fn,
    n_bootstraps: int = 500,
    alpha: float = 0.05
) -> Tuple[float, float, float]:
    """
    Computes metric mean and 95% block-bootstrap CI by sampling calendar years.
    """
    years = df["year"].unique()
    val_point = metric_fn(df)
    boot_vals = []
    
    np.random.seed(42)
    for _ in range(n_bootstraps):
        sampled_years = np.random.choice(years, size=len(years), replace=True)
        boot_df = pd.concat([df[df["year"] == y] for y in sampled_years], ignore_index=True)
        if len(boot_df) > 0:
            try:
                boot_vals.append(metric_fn(boot_df))
            except Exception:
                pass
                
    if len(boot_vals) > 10:
        low = float(np.percentile(boot_vals, 100.0 * (alpha / 2.0)))
        high = float(np.percentile(boot_vals, 100.0 * (1.0 - alpha / 2.0)))
    else:
        low, high = val_point, val_point
    return float(val_point), low, high


def run_evaluation(
    feature_parquet: str = "data/processed/feature_table_full.parquet",
    artifacts_dir: str = "artifacts"
) -> Dict[str, Any]:
    """
    Evaluates trained models strictly on the final test block (2008-2017)
    and across all lead-time cutoffs for early warning.
    """
    os.makedirs(f"{artifacts_dir}/backtest", exist_ok=True)
    
    full_df = pd.read_parquet(feature_parquet)
    eos_df = full_df[full_df["is_eos"]].dropna(subset=["yield_anomaly", "shortfall_event"]).copy()
    
    train_df, val_df, test_df = split_panel_by_years(eos_df, train_end_year=2002, val_end_year=2007)
    train_df, val_df, test_df, cat_maps = prepare_datasets(train_df, val_df, test_df)
    
    # Load trained models & parameters
    with open(f"{artifacts_dir}/models/decision_config.json") as f:
        decision_config = json.load(f)
    with open(f"{artifacts_dir}/conformal/conformal_cqr_params.json") as f:
        cqr_params = json.load(f)
        
    lgb_regressor = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_regressor_median.txt")
    lgb_q_low = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_q_low.txt")
    lgb_q_high = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_q_high.txt")
    lgb_classifier = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_classifier.txt")
    
    with open(f"{artifacts_dir}/models/isotonic_calibrator.pkl", "rb") as f:
        iso_calibrator = pickle.load(f)
    with open(f"{artifacts_dir}/models/ridge_panel_model.pkl", "rb") as f:
        ridge_dict = pickle.load(f)
        ridge_model = ridge_dict["model"]
        ridge_cols = ridge_dict["columns"]

    # ── Test Set Predictions ──────────────────────────────────────────────────────
    X_test = test_df[ALL_FEATURES]
    y_test_anomaly = test_df["yield_anomaly"].values
    y_test_shortfall = test_df["shortfall_event"].values
    
    # Baseline A: Zero relative anomaly
    pred_baseline_a = np.zeros(len(test_df))
    
    # Baseline B: District-crop historical shortfall rate (from train+val)
    hist_rate_lookup = pd.concat([train_df, val_df]).groupby(["district", "crop"])["shortfall_event"].mean().to_dict()
    global_hist_rate = float(pd.concat([train_df, val_df])["shortfall_event"].mean())
    pred_baseline_b = np.array([
        hist_rate_lookup.get((d, c), global_hist_rate)
        for d, c in zip(test_df["district"], test_df["crop"])
    ])

    # Ridge predictions
    X_test_num = pd.get_dummies(test_df[ALL_FEATURES], drop_first=True)
    X_test_num = X_test_num.reindex(columns=ridge_cols, fill_value=0)
    pred_ridge = ridge_model.predict(X_test_num)

    # LightGBM Regressor predictions (median anomaly)
    pred_lgb_median = lgb_regressor.predict(X_test)
    
    # Conformal Quantile Predictions (CQR)
    raw_q_low = lgb_q_low.predict(X_test)
    raw_q_high = lgb_q_high.predict(X_test)
    global_c = cqr_params["global_correction"]
    crop_corrections = cqr_params["crop_corrections"]
    
    cqr_low = np.array([
        raw_q_low[i] - crop_corrections.get(c, global_c)
        for i, c in enumerate(test_df["crop"])
    ])
    cqr_high = np.array([
        raw_q_high[i] + crop_corrections.get(c, global_c)
        for i, c in enumerate(test_df["crop"])
    ])
    in_interval = (y_test_anomaly >= cqr_low) & (y_test_anomaly <= cqr_high)

    # Shortfall Classifier Predictions (raw & calibrated)
    pred_raw_prob = lgb_classifier.predict(X_test)
    pred_calib_prob = iso_calibrator.predict(pred_raw_prob)
    threshold = decision_config["optimal_threshold"]
    pred_class = (pred_calib_prob >= threshold).astype(int)

    # ── SHAP Explanations for Test Instances ──────────────────────────────────────
    explainer = shap.TreeExplainer(lgb_classifier)
    dataset_drivers = explain_dataset(explainer, test_df, ALL_FEATURES)
    top_driver_sentences = [
        "; ".join([d["sentence"] for d in drivers])
        for drivers in dataset_drivers
    ]

    # Attach predictions to test_df for official EOS metric evaluation
    test_backtest = test_df.copy()
    test_backtest["predicted_anomaly"] = np.round(pred_lgb_median, 4)
    test_backtest["ci_lower"] = np.round(cqr_low, 4)
    test_backtest["ci_upper"] = np.round(cqr_high, 4)
    test_backtest["in_interval"] = in_interval
    test_backtest["predicted_shortfall_prob"] = np.round(pred_calib_prob, 4)
    test_backtest["shortfall_pred_class"] = pred_class
    test_backtest["top_drivers"] = top_driver_sentences

    # ── Predict across ALL cutoffs in the test block (2008-2017) ─────────────────
    test_all_df = full_df[full_df["year"] > 2007].dropna(subset=["yield_anomaly", "shortfall_event"]).copy()
    for col in CAT_FEATURES:
        test_all_df[col] = pd.Categorical(test_all_df[col], categories=cat_maps[col])
        
    X_all = test_all_df[ALL_FEATURES]
    pred_all_median = lgb_regressor.predict(X_all)
    all_q_low = lgb_q_low.predict(X_all)
    all_q_high = lgb_q_high.predict(X_all)
    
    all_cqr_low = np.array([
        all_q_low[i] - crop_corrections.get(c, global_c)
        for i, c in enumerate(test_all_df["crop"])
    ])
    all_cqr_high = np.array([
        all_q_high[i] + crop_corrections.get(c, global_c)
        for i, c in enumerate(test_all_df["crop"])
    ])
    all_in_interval = (test_all_df["yield_anomaly"].values >= all_cqr_low) & (test_all_df["yield_anomaly"].values <= all_cqr_high)
    all_raw_prob = lgb_classifier.predict(X_all)
    all_calib_prob = iso_calibrator.predict(all_raw_prob)
    all_pred_class = (all_calib_prob >= threshold).astype(int)
    
    # Map SHAP drivers for EOS instances, and descriptive drivers for intra-season cutoffs
    eos_driver_map = dict(zip(
        test_df["district"].astype(str) + "_" + test_df["crop"].astype(str) + "_" + test_df["year"].astype(str),
        top_driver_sentences
    ))
    
    all_drivers = []
    for _, row in test_all_df.iterrows():
        key = f"{row['district']}_{row['crop']}_{row['year']}"
        if row["is_eos"] and key in eos_driver_map:
            all_drivers.append(eos_driver_map[key])
        else:
            rain = row.get("precip_total_mm", 0.0)
            dry = row.get("longest_dry_spell", 0.0)
            heat = row.get("heat_days_38", 0.0)
            drivers = []
            if dry > 10:
                drivers.append(f"Extended dry spell ({dry:.0f} rainless days)")
            if heat > 3:
                drivers.append(f"Thermal stress ({heat:.0f} days >38 C)")
            if rain < 350:
                drivers.append(f"Cumulative rainfall deficit ({rain:.1f} mm)")
            elif rain > 850:
                drivers.append(f"Excess cumulative precipitation ({rain:.1f} mm)")
            if not drivers:
                drivers.append(f"Cumulative precipitation {rain:.1f} mm within seasonal expectations")
            all_drivers.append("; ".join(drivers) + ".")
            
    test_all_df["predicted_anomaly"] = np.round(pred_all_median, 4)
    test_all_df["ci_lower"] = np.round(all_cqr_low, 4)
    test_all_df["ci_upper"] = np.round(all_cqr_high, 4)
    test_all_df["in_interval"] = all_in_interval
    test_all_df["predicted_shortfall_prob"] = np.round(all_calib_prob, 4)
    test_all_df["shortfall_pred_class"] = all_pred_class
    test_all_df["top_drivers"] = all_drivers
    
    backtest_csv = f"{artifacts_dir}/backtest/backtest_predictions.csv"
    test_all_df.to_csv(backtest_csv, index=False)
    print(f"Saved full test backtest predictions ({len(test_all_df)} rows across all cutoffs) to {backtest_csv}")

    # ── Metric Calculations with Block Bootstrap CIs ──────────────────────────────
    def compute_mae(df, pred_col):
        return mean_absolute_error(df["yield_anomaly"], df[pred_col])
        
    def compute_rmse(df, pred_col):
        return np.sqrt(mean_squared_error(df["yield_anomaly"], df[pred_col]))
        
    def compute_skill(df, pred_col):
        base_rmse = np.sqrt(mean_squared_error(df["yield_anomaly"], np.zeros(len(df))))
        model_rmse = np.sqrt(mean_squared_error(df["yield_anomaly"], df[pred_col]))
        return 1.0 - (model_rmse / base_rmse) if base_rmse > 0 else 0.0

    eval_df = test_backtest.copy()
    eval_df["pred_baseline_a"] = pred_baseline_a
    eval_df["pred_ridge"] = pred_ridge
    eval_df["pred_lgb"] = pred_lgb_median

    base_mae, b_mae_l, b_mae_h = block_bootstrap_ci(eval_df, lambda d: compute_mae(d, "pred_baseline_a"))
    base_rmse, b_rmse_l, b_rmse_h = block_bootstrap_ci(eval_df, lambda d: compute_rmse(d, "pred_baseline_a"))
    
    ridge_mae, r_mae_l, r_mae_h = block_bootstrap_ci(eval_df, lambda d: compute_mae(d, "pred_ridge"))
    ridge_rmse, r_rmse_l, r_rmse_h = block_bootstrap_ci(eval_df, lambda d: compute_rmse(d, "pred_ridge"))
    ridge_skill, r_sk_l, r_sk_h = block_bootstrap_ci(eval_df, lambda d: compute_skill(d, "pred_ridge"))
    
    lgb_mae, l_mae_l, l_mae_h = block_bootstrap_ci(eval_df, lambda d: compute_mae(d, "pred_lgb"))
    lgb_rmse, l_rmse_l, l_rmse_h = block_bootstrap_ci(eval_df, lambda d: compute_rmse(d, "pred_lgb"))
    lgb_skill, l_sk_l, l_sk_h = block_bootstrap_ci(eval_df, lambda d: compute_skill(d, "pred_lgb"))
    spearman_corr, _ = spearmanr(eval_df["yield_anomaly"], eval_df["pred_lgb"])

    # Classification Metrics
    prevalence = float(np.mean(y_test_shortfall))
    brier_baseline = float(brier_score_loss(y_test_shortfall, pred_baseline_b))
    brier_lgb = float(brier_score_loss(y_test_shortfall, pred_calib_prob))
    brier_skill = 1.0 - (brier_lgb / brier_baseline) if brier_baseline > 0 else 0.0
    
    precision_curve, recall_curve, _ = precision_recall_curve(y_test_shortfall, pred_calib_prob)
    pr_auc = float(auc(recall_curve, precision_curve))
    
    tn, fp, fn, tp = confusion_matrix(y_test_shortfall, pred_class, labels=[0, 1]).ravel()
    prec = float(precision_score(y_test_shortfall, pred_class, zero_division=0))
    rec = float(recall_score(y_test_shortfall, pred_class, zero_division=0))
    f1 = float(f1_score(y_test_shortfall, pred_class, zero_division=0))
    f2 = float(fbeta_score(y_test_shortfall, pred_class, beta=2.0, zero_division=0))
    far = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    # Calibration Curve (Reliability)
    prob_true, prob_pred = calibration_curve(y_test_shortfall, pred_calib_prob, n_bins=5, strategy="uniform")

    # Conformal Coverage Breakdown
    empirical_coverage_overall = float(np.mean(in_interval))
    mean_interval_width = float(np.mean(cqr_high - cqr_low))
    
    crop_coverage = {}
    for crop in sorted(test_df["crop"].unique()):
        c_mask = test_df["crop"] == crop
        crop_coverage[crop] = {
            "coverage": round(float(np.mean(in_interval[c_mask])), 3),
            "n_samples": int(c_mask.sum()),
            "mean_width": round(float(np.mean(cqr_high[c_mask] - cqr_low[c_mask])), 3)
        }
        
    district_coverage = {}
    for dist in sorted(test_df["district"].unique()):
        d_mask = test_df["district"] == dist
        district_coverage[dist] = {
            "coverage": round(float(np.mean(in_interval[d_mask])), 3),
            "n_samples": int(d_mask.sum())
        }

    # ── Early Warning Lead-Time Skill ─────────────────────────────────────────────
    # Evaluate model skill across cutoffs
    lead_time_skill = []
    # Map cutoffs to human-readable lead time
    cutoff_meta = {
        "07-15": {"lead_days": 105, "stage": "Mid-July (Sowing / Onset)"},
        "08-15": {"lead_days": 75, "stage": "Mid-August (Vegetative / Flowering)"},
        "09-15": {"lead_days": 45, "stage": "Mid-September (Pod Fill / Bolling)"},
        "10-31": {"lead_days": 0, "stage": "End of Season (Harvest)"},
        "10-15": {"lead_days": 0, "stage": "End of Season (Soybean Harvest)"},
        "11-30": {"lead_days": 105, "stage": "Late November (Rabi Sowing)"},
        "12-15": {"lead_days": 90, "stage": "Mid-December (Vegetative)"},
        "01-15": {"lead_days": 60, "stage": "Mid-January (Flowering)"},
        "02-15": {"lead_days": 30, "stage": "Mid-February (Grain Fill)"},
        "03-31": {"lead_days": 0, "stage": "End of Season (Rabi Harvest)"}
    }
    
    # Filter full table for Kharif crops across standard 4 cutoffs
    kharif_cutoffs = ["07-15", "08-15", "09-15", "10-31"]
    for c_off in kharif_cutoffs:
        sub_c = full_df[
            (full_df["cutoff"] == c_off) & (full_df["season"] == "Kharif")
        ].dropna(subset=["yield_anomaly", "shortfall_event"]).copy()
        tr, va, te = split_panel_by_years(sub_c, 2002, 2007)
        if len(te) > 0:
            for col in CAT_FEATURES:
                te[col] = pd.Categorical(te[col], categories=cat_maps[col])
            p_lgb = lgb_regressor.predict(te[ALL_FEATURES])
            base_r = np.sqrt(mean_squared_error(te["yield_anomaly"], np.zeros(len(te))))
            mod_r = np.sqrt(mean_squared_error(te["yield_anomaly"], p_lgb))
            sk = 1.0 - (mod_r / base_r) if base_r > 0 else 0.0
            
            p_class = lgb_classifier.predict(te[ALL_FEATURES])
            p_cal = iso_calibrator.predict(p_class)
            pc, rc, _ = precision_recall_curve(te["shortfall_event"], p_cal)
            prauc_c = float(auc(rc, pc))
            
            lead_time_skill.append({
                "cutoff": c_off,
                "stage": cutoff_meta.get(c_off, {}).get("stage", c_off),
                "lead_days": cutoff_meta.get(c_off, {}).get("lead_days", 0),
                "rmse": round(float(mod_r), 4),
                "skill_score": round(float(sk), 4),
                "pr_auc": round(float(prauc_c), 4),
                "samples": len(te)
            })

    # ── Compile Unified Metrics JSON ──────────────────────────────────────────────
    metrics = {
        "evaluation_period": "2008-2017 (10 held-out years)",
        "total_test_instances": len(test_df),
        "prevalence": round(prevalence, 4),
        "regression": {
            "baseline_a": {
                "name": "Zero Anomaly Baseline",
                "mae": round(base_mae, 4),
                "mae_ci": [round(b_mae_l, 4), round(b_mae_h, 4)],
                "rmse": round(base_rmse, 4),
                "rmse_ci": [round(b_rmse_l, 4), round(b_rmse_h, 4)],
                "skill_score": 0.0
            },
            "ridge_panel": {
                "name": "Regularized Panel Ridge Regression",
                "mae": round(ridge_mae, 4),
                "mae_ci": [round(r_mae_l, 4), round(r_mae_h, 4)],
                "rmse": round(ridge_rmse, 4),
                "rmse_ci": [round(r_rmse_l, 4), round(r_rmse_h, 4)],
                "skill_score": round(ridge_skill, 4),
                "skill_score_ci": [round(r_sk_l, 4), round(r_sk_h, 4)]
            },
            "lightgbm_median": {
                "name": "Monotone-Constrained LightGBM",
                "mae": round(lgb_mae, 4),
                "mae_ci": [round(l_mae_l, 4), round(l_mae_h, 4)],
                "rmse": round(lgb_rmse, 4),
                "rmse_ci": [round(l_rmse_l, 4), round(l_rmse_h, 4)],
                "skill_score": round(lgb_skill, 4),
                "skill_score_ci": [round(l_sk_l, 4), round(l_sk_h, 4)],
                "spearman_rank_correlation": round(float(spearman_corr), 4)
            }
        },
        "classification": {
            "baseline_b_historical_rate": {
                "brier_score": round(brier_baseline, 4)
            },
            "calibrated_shortfall_classifier": {
                "pr_auc": round(pr_auc, 4),
                "brier_score": round(brier_lgb, 4),
                "brier_skill_score": round(brier_skill, 4),
                "decision_threshold": round(threshold, 3),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "f2_score": round(f2, 4),
                "false_alarm_rate": round(far, 4),
                "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}
            }
        },
        "uncertainty_conformal_cqr": {
            "target_coverage": 0.90,
            "empirical_coverage_overall": round(empirical_coverage_overall, 4),
            "mean_interval_width": round(mean_interval_width, 4),
            "coverage_by_crop": crop_coverage,
            "coverage_by_district": district_coverage
        },
        "early_warning_lead_time": lead_time_skill
    }

    metrics_path = f"{artifacts_dir}/metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved verified evaluation metrics to {metrics_path}")

    # Save visual data for frontend charts
    plots_data = {
        "calibration_curve": {
            "prob_pred": [round(float(p), 4) for p in prob_pred],
            "prob_true": [round(float(p), 4) for p in prob_true]
        },
        "pr_curve": {
            "precision": [round(float(p), 4) for p in precision_curve[::5]],
            "recall": [round(float(r), 4) for r in recall_curve[::5]]
        },
        "lead_time_skill": lead_time_skill,
        "crop_coverage": [
            {"crop": k, "coverage": v["coverage"], "target": 0.90, "mean_width": v["mean_width"]}
            for k, v in crop_coverage.items()
        ]
    }
    plots_path = f"{artifacts_dir}/plots_data.json"
    with open(plots_path, "w") as f:
        json.dump(plots_data, f, indent=2)
    print(f"Saved plots data to {plots_path}")
    
    return metrics

if __name__ == "__main__":
    run_evaluation()
