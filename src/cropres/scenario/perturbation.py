import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
import lightgbm as lgb

from cropres.features.weather_features import (
    CROP_SEASONS,
    extract_season_features_for_window
)
from cropres.models.train import (
    MODEL_NUM_FEATURES,
    CAT_FEATURES,
    ALL_FEATURES
)
from cropres.scenario.ood import OODDetector


class ScenarioEngine:
    def __init__(
        self,
        artifacts_dir: str = "artifacts",
        weather_parquet: str = "data/raw/weather_daily_vidarbha.parquet",
        feature_parquet: str = "data/processed/feature_table_full.parquet"
    ):
        self.artifacts_dir = artifacts_dir
        self.weather_parquet = weather_parquet
        
        # Load category mapping
        with open(f"{artifacts_dir}/models/cat_maps.json") as f:
            self.cat_maps = json.load(f)
            
        # Load models
        self.lgb_regressor = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_regressor_median.txt")
        self.lgb_q_low = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_q_low.txt")
        self.lgb_q_high = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_q_high.txt")
        self.lgb_classifier = lgb.Booster(model_file=f"{artifacts_dir}/models/lgb_classifier.txt")
        
        with open(f"{artifacts_dir}/models/isotonic_calibrator.pkl", "rb") as f:
            self.iso_calibrator = pickle.load(f)
        with open(f"{artifacts_dir}/conformal/conformal_cqr_params.json") as f:
            self.cqr_params = json.load(f)
            
        # Load daily weather
        self.daily_w = pd.read_parquet(weather_parquet)
        self.daily_w["date_dt"] = pd.to_datetime(self.daily_w["date"])
        
        # Initialize OOD detector from training feature table
        feat_df = pd.read_parquet(feature_parquet)
        train_feats = feat_df[feat_df["year"] <= 2002]
        # Precompute precip normals per (district, crop) from training years EOS
        self.precip_normals = {}
        eos_train = train_feats[train_feats["is_eos"]]
        for (d, c), grp in eos_train.groupby(["district", "crop"]):
            mean_p = float(grp["precip_total_mm"].mean())
            std_p = float(grp["precip_total_mm"].std())
            self.precip_normals[(d, c)] = (mean_p, std_p if std_p > 0 else 1.0)
            
        self.ood_detector = OODDetector(train_feats, MODEL_NUM_FEATURES)

    def run_simulation(
        self,
        district: str,
        crop: str,
        temp_shift: float = 0.0,
        precip_shift: float = 0.0,
        heat_days_shift: int = 0,
        history_years: int = 30
    ) -> Dict[str, Any]:
        """
        Runs change-factor climate stress-testing over real historical daily weather.
        
        Parameters:
        - temp_shift: temperature delta in degrees C (e.g. +1.5, +3.0)
        - precip_shift: fractional rainfall change (e.g. -0.20 for -20%, +0.10 for +10%)
        - heat_days_shift: additional extreme heat days applied to sensitive window
        - history_years: number of recent historical weather years to simulate (default 30)
        """
        if district not in self.cat_maps["district"]:
            raise ValueError(f"Unknown district '{district}'")
        if crop not in self.cat_maps["crop"]:
            raise ValueError(f"Unknown crop '{crop}'")

        season_def = CROP_SEASONS[crop]
        season_type = season_def["season_type"]
        cutoff = season_def["cutoffs"][-1]  # End of season
        
        # Get district weather
        dist_w = self.daily_w[self.daily_w["district"] == district].copy()
        all_years = sorted(dist_w["year"].unique())
        sim_years = [y for y in all_years if y <= 2017][-history_years:]

        mean_p, std_p = self.precip_normals.get((district, crop), (750.0, 150.0))

        baseline_features = []
        scenario_features = []
        
        for y in sim_years:
            if season_type == "Kharif":
                start_dt = pd.Timestamp(year=y, month=season_def["start_month"], day=season_def["start_day"])
                end_m, end_d = [int(v) for v in cutoff.split("-")]
                end_dt = pd.Timestamp(year=y, month=end_m, day=end_d)
            else:
                sowing_y = y - 1
                start_dt = pd.Timestamp(year=sowing_y, month=season_def["start_month"], day=season_def["start_day"])
                end_m, end_d = [int(v) for v in cutoff.split("-")]
                c_y = sowing_y if end_m >= 10 else y
                end_dt = pd.Timestamp(year=c_y, month=end_m, day=end_d)
                
            w_win = dist_w[(dist_w["date_dt"] >= start_dt) & (dist_w["date_dt"] <= end_dt)].copy()
            if len(w_win) == 0:
                continue
                
            # Baseline features
            b_feat = extract_season_features_for_window(w_win, crop, cutoff, t_base=season_def["t_base"])
            b_feat["precip_pct_normal"] = round((b_feat["precip_total_mm"] / mean_p) * 100.0, 1) if mean_p > 0 else 100.0
            b_feat["spi3_asof"] = round(float((b_feat["precip_total_mm"] - mean_p) / std_p), 2) if std_p > 0 else 0.0
            b_feat["district"] = district
            b_feat["crop"] = crop
            b_feat["year"] = y
            baseline_features.append(b_feat)
            
            # Perturbed scenario weather
            w_scen = w_win.copy()
            w_scen["t2m"] = w_scen["t2m"] + temp_shift
            w_scen["t2m_max"] = w_scen["t2m_max"] + temp_shift
            w_scen["t2m_min"] = w_scen["t2m_min"] + temp_shift
            
            # Rainfall factor perturbation (precip >= 0)
            rain_factor = max(0.0, 1.0 + precip_shift)
            w_scen["precip_mm"] = w_scen["precip_mm"] * rain_factor
            
            s_feat = extract_season_features_for_window(w_scen, crop, cutoff, t_base=season_def["t_base"])
            # Apply heat days shift
            s_feat["heat_days_38"] = max(0, s_feat["heat_days_38"] + heat_days_shift)
            s_feat["heat_days_40"] = max(0, s_feat["heat_days_40"] + max(0, heat_days_shift // 2))
            s_feat["precip_pct_normal"] = round((s_feat["precip_total_mm"] / mean_p) * 100.0, 1) if mean_p > 0 else 100.0
            s_feat["spi3_asof"] = round(float((s_feat["precip_total_mm"] - mean_p) / std_p), 2) if std_p > 0 else 0.0
            s_feat["district"] = district
            s_feat["crop"] = crop
            s_feat["year"] = y
            scenario_features.append(s_feat)

        df_base = pd.DataFrame(baseline_features)
        df_scen = pd.DataFrame(scenario_features)
        
        # Prepare categorical types
        for col in CAT_FEATURES:
            df_base[col] = pd.Categorical(df_base[col], categories=self.cat_maps[col])
            df_scen[col] = pd.Categorical(df_scen[col], categories=self.cat_maps[col])
            
        # Run OOD detection on scenario
        ood_result = self.ood_detector.evaluate_scenario(df_scen)
        
        # Predict baseline distribution
        b_anom = self.lgb_regressor.predict(df_base[ALL_FEATURES])
        b_raw_p = self.lgb_classifier.predict(df_base[ALL_FEATURES])
        b_prob = self.iso_calibrator.predict(b_raw_p)
        
        # Predict scenario distribution
        s_anom = self.lgb_regressor.predict(df_scen[ALL_FEATURES])
        s_raw_p = self.lgb_classifier.predict(df_scen[ALL_FEATURES])
        s_prob = self.iso_calibrator.predict(s_raw_p)
        
        # Quantile predictions for uncertainty
        s_q_low = self.lgb_q_low.predict(df_scen[ALL_FEATURES])
        s_q_high = self.lgb_q_high.predict(df_scen[ALL_FEATURES])
        c_adj = self.cqr_params["crop_corrections"].get(crop, self.cqr_params["global_correction"])
        
        # If outside observed range, widen interval penalty
        if ood_result["outside_observed_range"]:
            c_adj = c_adj * 1.5
            
        ci_low = s_q_low - c_adj
        ci_high = s_q_high + c_adj

        return {
            "district": district,
            "crop": crop,
            "scenario_parameters": {
                "temp_shift_c": temp_shift,
                "precip_shift_pct": round(precip_shift * 100.0, 1),
                "heat_days_shift": heat_days_shift,
                "weather_years_simulated": len(df_scen)
            },
            "ood_guard": ood_result,
            "baseline_summary": {
                "median_anomaly": round(float(np.median(b_anom)), 4),
                "anomaly_iqr": [round(float(np.percentile(b_anom, 25)), 4), round(float(np.percentile(b_anom, 75)), 4)],
                "shortfall_probability": round(float(np.mean(b_prob)), 4)
            },
            "scenario_summary": {
                "median_anomaly": round(float(np.median(s_anom)), 4),
                "anomaly_iqr": [round(float(np.percentile(s_anom, 25)), 4), round(float(np.percentile(s_anom, 75)), 4)],
                "shortfall_probability": round(float(np.mean(s_prob)), 4),
                "delta_shortfall_prob": round(float(np.mean(s_prob) - np.mean(b_prob)), 4),
                "ci_lower_median": round(float(np.median(ci_low)), 4),
                "ci_upper_median": round(float(np.median(ci_high)), 4)
            },
            "distribution_points": {
                "years": [int(y) for y in df_scen["year"].values],
                "baseline_anomalies": [round(float(v), 4) for v in b_anom],
                "scenario_anomalies": [round(float(v), 4) for v in s_anom],
                "scenario_shortfall_probs": [round(float(v), 4) for v in s_prob]
            }
        }
