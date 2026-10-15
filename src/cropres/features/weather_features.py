import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

# Crop season definitions
CROP_SEASONS = {
    "Cotton": {
        "season_type": "Kharif",
        "start_month": 6, "start_day": 1,
        "end_month": 10, "end_day": 31,
        "sowing_end_month": 7, "sowing_end_day": 15,
        "t_base": 10.0,
        "cutoffs": ["07-15", "08-15", "09-15", "10-31"]
    },
    "Soybean": {
        "season_type": "Kharif",
        "start_month": 6, "start_day": 1,
        "end_month": 10, "end_day": 15,
        "sowing_end_month": 7, "sowing_end_day": 15,
        "t_base": 10.0,
        "cutoffs": ["07-15", "08-15", "09-15", "10-15"]
    },
    "Pigeonpea": {
        "season_type": "Kharif",
        "start_month": 6, "start_day": 1,
        "end_month": 10, "end_day": 31,
        "sowing_end_month": 7, "sowing_end_day": 15,
        "t_base": 10.0,
        "cutoffs": ["07-15", "08-15", "09-15", "10-31"]
    },
    "Sorghum": {
        "season_type": "Kharif",
        "start_month": 6, "start_day": 1,
        "end_month": 10, "end_day": 31,
        "sowing_end_month": 7, "sowing_end_day": 15,
        "t_base": 10.0,
        "cutoffs": ["07-15", "08-15", "09-15", "10-31"]
    },
    "Rice": {
        "season_type": "Kharif",
        "start_month": 6, "start_day": 1,
        "end_month": 10, "end_day": 31,
        "sowing_end_month": 7, "sowing_end_day": 15,
        "t_base": 10.0,
        "cutoffs": ["07-15", "08-15", "09-15", "10-31"]
    },
    "Wheat": {
        "season_type": "Rabi",
        "start_month": 11, "start_day": 1,
        "end_month": 3, "end_day": 31,
        "sowing_end_month": 12, "sowing_end_day": 15,
        "t_base": 5.0,
        "cutoffs": ["12-15", "01-15", "02-15", "03-31"]
    },
    "Chickpea": {
        "season_type": "Rabi",
        "start_month": 10, "start_day": 15,
        "end_month": 3, "end_day": 15,
        "sowing_end_month": 11, "sowing_end_day": 30,
        "t_base": 5.0,
        "cutoffs": ["11-30", "12-31", "01-31", "03-15"]
    }
}


def compute_hargreaves_pet(
    t_mean: float,
    t_max: float,
    t_min: float,
    sfc_sw_dwn: Optional[float] = None
) -> float:
    """
    Computes daily Potential Evapotranspiration (PET) in mm/day.
    Uses Hargreaves-Samani formulation:
    PET = 0.0023 * (Tmean + 17.8) * sqrt(Tmax - Tmin) * Ra_equivalent
    """
    t_diff = max(0.0, t_max - t_min)
    temp_factor = max(0.0, t_mean + 17.8)
    
    # 1 MJ/m^2/day is equivalent to ~0.408 mm/day evaporation of water
    if sfc_sw_dwn is not None and sfc_sw_dwn > 0:
        ra_mm = sfc_sw_dwn * 0.408
    else:
        ra_mm = 15.0 * 0.408  # Default tropical solar radiation equivalent
        
    pet = 0.0023 * temp_factor * np.sqrt(t_diff) * (ra_mm / 0.408)
    return float(max(0.0, pet))


def compute_longest_dry_spell(precip_series: np.ndarray, threshold: float = 2.5) -> int:
    """
    Calculates the longest consecutive sequence of days with precip < threshold (mm).
    """
    max_spell = 0
    current_spell = 0
    for p in precip_series:
        if p < threshold:
            current_spell += 1
            if current_spell > max_spell:
                max_spell = current_spell
        else:
            current_spell = 0
    return max_spell


def extract_season_features_for_window(
    daily_df: pd.DataFrame,
    crop: str,
    cutoff_mm_dd: str,
    t_base: float = 10.0
) -> Dict[str, float]:
    """
    Computes summary features from daily weather strictly up to the cutoff date.
    
    daily_df must be filtered to the relevant calendar/agricultural year and window:
    For Kharif: start June 1 up to cutoff_mm_dd.
    For Rabi: start season_start up to cutoff_mm_dd.
    """
    if len(daily_df) == 0:
        return {}
        
    precip = daily_df["precip_mm"].fillna(0.0).values
    t2m = daily_df["t2m"].values
    tmax = daily_df["t2m_max"].values
    tmin = daily_df["t2m_min"].values
    gwet = daily_df["gwetroot"].dropna().values if "gwetroot" in daily_df.columns else np.array([])
    sw = daily_df["sfc_sw_dwn"].values if "sfc_sw_dwn" in daily_df.columns else None

    # Cumulative precipitation
    precip_total = float(np.sum(precip))
    rainy_days = int(np.sum(precip >= 2.5))
    heavy_rain_days = int(np.sum(precip >= 50.0))
    
    # Longest dry spell (in July-Sep or available period)
    jul_sep_mask = daily_df["month"].isin([7, 8, 9])
    if jul_sep_mask.any():
        dry_spell_precip = daily_df.loc[jul_sep_mask, "precip_mm"].fillna(0.0).values
        longest_dry_spell = compute_longest_dry_spell(dry_spell_precip)
    else:
        longest_dry_spell = compute_longest_dry_spell(precip)

    # Monthly rainfall breakdowns (if passed in window)
    monthly_p = {}
    for m in [6, 7, 8, 9, 10, 11, 12, 1, 2, 3]:
        m_mask = daily_df["month"] == m
        if m_mask.any():
            monthly_p[f"precip_month_{m}"] = float(daily_df.loc[m_mask, "precip_mm"].sum())
        else:
            monthly_p[f"precip_month_{m}"] = 0.0

    # Temperature extremes
    heat_days_35 = int(np.sum(tmax >= 35.0))
    heat_days_38 = int(np.sum(tmax >= 38.0))
    heat_days_40 = int(np.sum(tmax >= 40.0))
    
    diurnal_range = float(np.mean(tmax - tmin))
    t2m_mean = float(np.mean(t2m))
    tmax_mean = float(np.mean(tmax))
    
    # Growing Degree Days
    gdd = float(np.sum(np.maximum(0.0, t2m - t_base)))
    
    # Daily PET and water balance
    daily_pet = [
        compute_hargreaves_pet(t2m[i], tmax[i], tmin[i], sw[i] if sw is not None else None)
        for i in range(len(daily_df))
    ]
    pet_total = float(np.sum(daily_pet))
    water_balance = float(precip_total - pet_total)
    
    # Root zone soil wetness
    gwet_mean = float(np.mean(gwet)) if len(gwet) > 0 else 0.5
    gwet_min = float(np.min(gwet)) if len(gwet) > 0 else 0.1

    features = {
        "precip_total_mm": round(precip_total, 2),
        "rainy_days": rainy_days,
        "heavy_rain_days": heavy_rain_days,
        "longest_dry_spell": longest_dry_spell,
        "heat_days_35": heat_days_35,
        "heat_days_38": heat_days_38,
        "heat_days_40": heat_days_40,
        "diurnal_range": round(diurnal_range, 2),
        "t2m_mean": round(t2m_mean, 2),
        "tmax_mean": round(tmax_mean, 2),
        "gdd": round(gdd, 1),
        "pet_total_mm": round(pet_total, 2),
        "water_balance_mm": round(water_balance, 2),
        "gwetroot_mean": round(gwet_mean, 3),
        "gwetroot_min": round(gwet_min, 3),
    }
    features.update(monthly_p)
    return features
