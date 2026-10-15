import os
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cropres.features.trend import compute_asof_trend_and_anomalies
from cropres.features.targets import compute_pmfby_thresholds
from cropres.features.weather_features import (
    CROP_SEASONS,
    extract_season_features_for_window
)

def update_provenance(record_key, info):
    prov_file = "data/provenance.json"
    os.makedirs(os.path.dirname(prov_file), exist_ok=True)
    prov = {}
    if os.path.exists(prov_file):
        try:
            with open(prov_file, "r") as f:
                prov = json.load(f)
        except Exception:
            prov = {}
    prov[record_key] = info
    with open(prov_file, "w") as f:
        json.dump(prov, f, indent=2)

def build_feature_table(
    yield_csv: str = "data/interim/vidarbha_yield_panel.csv",
    weather_parquet: str = "data/raw/weather_daily_vidarbha.parquet",
    output_dir: str = "data/processed"
) -> pd.DataFrame:
    """
    Constructs the leakage-free, season-aware district-crop-year-cutoff panel.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading yield panel: {yield_csv}")
    ydf = pd.read_csv(yield_csv)
    print(f"Loading weather panel: {weather_parquet}")
    wdf = pd.read_parquet(weather_parquet)
    wdf["date_dt"] = pd.to_datetime(wdf["date"])
    
    # Filter valid district-crop series: >= 25 years and mean area >= 2k ha
    valid_pairs = []
    for (dist, crop), group in ydf.groupby(["district", "crop"]):
        valid_y = group[group["yield_kg_ha"].notna() & (group["yield_kg_ha"] > 0)]
        mean_area = valid_y["area_1000ha"].mean() if len(valid_y) else 0.0
        if len(valid_y) >= 25 and mean_area >= 2.0:
            valid_pairs.append((dist, crop))
            
    print(f"Admitted {len(valid_pairs)} district-crop series into feature table.")
    
    # 1. Compute trends and targets per valid series
    series_targets = []
    for dist, crop in valid_pairs:
        sub = ydf[(ydf["district"] == dist) & (ydf["crop"] == crop)].copy()
        # Compute as-of trend and relative anomalies
        sub = compute_asof_trend_and_anomalies(sub, min_history=5)
        # Compute PMFBY thresholds and shortfall targets
        sub = compute_pmfby_thresholds(sub, indemnity_levels=[0.70, 0.80, 0.90], default_indemnity=0.80)
        series_targets.append(sub)
        
    targets_df = pd.concat(series_targets, ignore_index=True)
    
    # Filter to model overlap years where weather is available: 1981 to 2017
    targets_df = targets_df[(targets_df["year"] >= 1981) & (targets_df["year"] <= 2017)].copy()
    print(f"Yield targets available for {len(targets_df)} district-crop-years in 1981-2017.")
    
    # 2. Extract weather features across all cutoffs
    panel_rows = []
    for _, y_row in targets_df.iterrows():
        dist = y_row["district"]
        crop = y_row["crop"]
        year = int(y_row["year"])
        season_def = CROP_SEASONS[crop]
        season_type = season_def["season_type"]
        
        # Determine weather window for this crop and year
        if season_type == "Kharif":
            # June 1 to cutoff in current year
            season_start = pd.Timestamp(year=year, month=season_def["start_month"], day=season_def["start_day"])
            dist_w = wdf[wdf["district"] == dist]
            
            for cutoff in season_def["cutoffs"]:
                m_str, d_str = cutoff.split("-")
                cutoff_dt = pd.Timestamp(year=year, month=int(m_str), day=int(d_str))
                
                # STRICT NO-LEAKAGE FILTER: date <= cutoff_dt
                window_w = dist_w[(dist_w["date_dt"] >= season_start) & (dist_w["date_dt"] <= cutoff_dt)].copy()
                feats = extract_season_features_for_window(window_w, crop, cutoff, t_base=season_def["t_base"])
                
                row_dict = {
                    "district": dist,
                    "crop": crop,
                    "year": year,
                    "season": season_type,
                    "cutoff": cutoff,
                    "is_eos": (cutoff == season_def["cutoffs"][-1]),
                    "area_1000ha": y_row["area_1000ha"],
                    "yield_kg_ha": y_row["yield_kg_ha"],
                    "trend_asof": y_row["trend_asof"],
                    "yield_anomaly": y_row["yield_anomaly"],
                    "pmfby_ref_yield": y_row["pmfby_ref_yield"],
                    "pmfby_threshold_80": y_row["pmfby_threshold_80"],
                    "pmfby_threshold_70": y_row["pmfby_threshold_70"],
                    "pmfby_threshold_90": y_row["pmfby_threshold_90"],
                    "shortfall_event": y_row["shortfall_event_80"],
                    "severe_shortfall_event": y_row["severe_shortfall_event"],
                }
                row_dict.update(feats)
                panel_rows.append(row_dict)
                
        else: # Rabi (e.g. Wheat, Chickpea)
            # Rabi spans two calendar years: starts in (year-1) or autumn of year
            # ICRISAT Rabi year corresponds to harvest year t (sowing in t-1)
            dist_w = wdf[wdf["district"] == dist]
            sowing_year = year - 1
            season_start = pd.Timestamp(year=sowing_year, month=season_def["start_month"], day=season_def["start_day"])
            
            for cutoff in season_def["cutoffs"]:
                m_str, d_str = cutoff.split("-")
                cutoff_month = int(m_str)
                cutoff_day = int(d_str)
                # If cutoff month >= 10, it is in sowing_year; if <= 5, in harvest year
                c_year = sowing_year if cutoff_month >= 10 else year
                cutoff_dt = pd.Timestamp(year=c_year, month=cutoff_month, day=cutoff_day)
                
                # STRICT NO-LEAKAGE FILTER
                window_w = dist_w[(dist_w["date_dt"] >= season_start) & (dist_w["date_dt"] <= cutoff_dt)].copy()
                feats = extract_season_features_for_window(window_w, crop, cutoff, t_base=season_def["t_base"])
                
                row_dict = {
                    "district": dist,
                    "crop": crop,
                    "year": year,
                    "season": season_type,
                    "cutoff": cutoff,
                    "is_eos": (cutoff == season_def["cutoffs"][-1]),
                    "area_1000ha": y_row["area_1000ha"],
                    "yield_kg_ha": y_row["yield_kg_ha"],
                    "trend_asof": y_row["trend_asof"],
                    "yield_anomaly": y_row["yield_anomaly"],
                    "pmfby_ref_yield": y_row["pmfby_ref_yield"],
                    "pmfby_threshold_80": y_row["pmfby_threshold_80"],
                    "pmfby_threshold_70": y_row["pmfby_threshold_70"],
                    "pmfby_threshold_90": y_row["pmfby_threshold_90"],
                    "shortfall_event": y_row["shortfall_event_80"],
                    "severe_shortfall_event": y_row["severe_shortfall_event"],
                }
                row_dict.update(feats)
                panel_rows.append(row_dict)

    feature_df = pd.DataFrame(panel_rows)
    print(f"Total feature table rows across all cutoffs: {len(feature_df)}")
    
    # 3. Add as-of rainfall normal percentage and SPI-3 strictly without future leakage
    # Normal is computed using only years < t
    feature_df["precip_pct_normal"] = np.nan
    feature_df["spi3_asof"] = np.nan
    
    for (dist, crop, cutoff), group in feature_df.groupby(["district", "crop", "cutoff"]):
        sorted_grp = group.sort_values("year")
        years = sorted_grp["year"].values
        precips = sorted_grp["precip_total_mm"].values
        indices = sorted_grp.index.values
        
        for idx_i, current_year in enumerate(years):
            past_mask = years < current_year
            if np.sum(past_mask) >= 5:
                past_p = precips[past_mask]
                mean_p = np.mean(past_p)
                std_p = np.std(past_p)
                current_p = precips[idx_i]
                
                # Normal percentage
                pct_norm = (current_p / mean_p) * 100.0 if mean_p > 0 else 100.0
                feature_df.loc[indices[idx_i], "precip_pct_normal"] = round(pct_norm, 1)
                
                # SPI-3 approximation (standardized z-score on training history)
                if std_p > 0:
                    spi = (current_p - mean_p) / std_p
                    feature_df.loc[indices[idx_i], "spi3_asof"] = round(float(spi), 2)
            else:
                feature_df.loc[indices[idx_i], "precip_pct_normal"] = 100.0
                feature_df.loc[indices[idx_i], "spi3_asof"] = 0.0

    # 4. Save artifacts
    parquet_path = os.path.join(output_dir, "feature_table_full.parquet")
    csv_path = os.path.join(output_dir, "feature_table_full.csv.gz")
    eos_csv_path = os.path.join(output_dir, "model_ready_data.csv")
    
    feature_df.to_parquet(parquet_path, index=False)
    feature_df.to_csv(csv_path, index=False, compression="gzip")
    
    # EOS subset for standard end-of-season modeling
    eos_df = feature_df[feature_df["is_eos"]].copy()
    eos_df.to_csv(eos_csv_path, index=False)
    print(f"Saved feature tables:\n  Full: {parquet_path}\n  Model ready (EOS): {eos_csv_path} ({len(eos_df)} rows)")
    
    update_provenance("feature_table", {
        "description": "Leakage-free, season-aware features with PMFBY shortfall targets",
        "total_rows_full": len(feature_df),
        "total_rows_eos": len(eos_df),
        "years": [int(feature_df["year"].min()), int(feature_df["year"].max())],
        "cutoffs": sorted(feature_df["cutoff"].unique().tolist()),
        "crops": sorted(feature_df["crop"].unique().tolist()),
        "districts": sorted(feature_df["district"].unique().tolist()),
        "features": [c for c in feature_df.columns if c not in ["district", "crop", "year", "cutoff", "is_eos", "yield_kg_ha", "yield_anomaly", "shortfall_event", "severe_shortfall_event"]],
        "generated_timestamp": datetime.now(timezone.utc).isoformat()
    })
    return feature_df

if __name__ == "__main__":
    build_feature_table()
