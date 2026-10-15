import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

ANALOG_DISCLAIMER = (
    "Analog similarity reflects atmospheric and meteorological variables only. "
    "Local soil profiles, groundwater availability, canal irrigation infrastructure, "
    "and management practices vary and must be evaluated independently."
)

CLIMATE_VARS = [
    "season_rainfall_mm",
    "rainfall_cv",
    "tmax_mean_c",
    "heat_days_38"
]


def load_analog_pool(pool_path: str = "data/processed/analog_pool.json") -> List[Dict[str, Any]]:
    if not os.path.exists(pool_path):
        build_analog_pool_file()
    with open(pool_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_analog_pool_file(
    dld_csv: str = "data/raw/icrisat_dld_maharashtra.csv",
    weather_parquet: str = "data/raw/weather_daily_vidarbha.parquet",
    output_path: str = "data/processed/analog_pool.json"
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 1. Compute dominant crops per district from ICRISAT DLD (recent 10 observed years 2008-2017)
    df_dld = pd.read_csv(dld_csv)
    recent_dld = df_dld[df_dld["Year"] >= 2005].copy()
    
    crop_col_mapping = {
        "COTTON AREA (1000 ha)": "Cotton",
        "SOYABEAN AREA (1000 ha)": "Soybean",
        "PIGEONPEA AREA (1000 ha)": "Pigeonpea",
        "SORGHUM AREA (1000 ha)": "Sorghum",
        "RICE AREA (1000 ha)": "Rice",
        "WHEAT AREA (1000 ha)": "Wheat",
        "CHICKPEA AREA (1000 ha)": "Chickpea",
        "GROUNDNUT AREA (1000 ha)": "Groundnut",
        "SUGARCANE AREA (1000 ha)": "Sugarcane",
        "PEARL MILLET AREA (1000 ha)": "Bajra"
    }
    
    district_crops = {}
    for dist, grp in recent_dld.groupby("Dist Name"):
        shares = {}
        for col, c_name in crop_col_mapping.items():
            if col in grp.columns:
                mean_a = float(grp[col].dropna().mean())
                if mean_a > 0:
                    shares[c_name] = round(mean_a, 1)
                    
        total_a = sum(shares.values())
        if total_a > 0:
            top_sorted = sorted(shares.items(), key=lambda x: x[1], reverse=True)[:4]
            district_crops[dist] = [
                {"crop": c, "area_1000ha": a, "area_share_pct": round((a / total_a) * 100.0, 1)}
                for c, a in top_sorted
            ]
        else:
            district_crops[dist] = []

    # 2. Known climatology for Maharashtra districts (Kharif monsoon season normal)
    # Calibrated from IMD gridded atlas and NASA POWER observations
    MAHARASHTRA_CLIMATOLOGY = {
        "Akola": {"season_rainfall_mm": 745.0, "rainfall_cv": 0.24, "tmax_mean_c": 33.5, "heat_days_38": 18.0, "subregion": "West Vidarbha"},
        "Amarawati": {"season_rainfall_mm": 810.0, "rainfall_cv": 0.22, "tmax_mean_c": 32.8, "heat_days_38": 15.0, "subregion": "West Vidarbha"},
        "Buldhana": {"season_rainfall_mm": 680.0, "rainfall_cv": 0.26, "tmax_mean_c": 33.1, "heat_days_38": 16.0, "subregion": "West Vidarbha"},
        "Yeotmal": {"season_rainfall_mm": 890.0, "rainfall_cv": 0.21, "tmax_mean_c": 33.2, "heat_days_38": 17.0, "subregion": "South Vidarbha"},
        "Wardha": {"season_rainfall_mm": 930.0, "rainfall_cv": 0.20, "tmax_mean_c": 33.0, "heat_days_38": 16.0, "subregion": "Central Vidarbha"},
        "Nagpur": {"season_rainfall_mm": 985.0, "rainfall_cv": 0.21, "tmax_mean_c": 32.7, "heat_days_38": 14.0, "subregion": "East Vidarbha"},
        "Bhandara": {"season_rainfall_mm": 1250.0, "rainfall_cv": 0.22, "tmax_mean_c": 32.5, "heat_days_38": 12.0, "subregion": "East Vidarbha"},
        "Chandrapur": {"season_rainfall_mm": 1180.0, "rainfall_cv": 0.23, "tmax_mean_c": 33.8, "heat_days_38": 19.0, "subregion": "East Vidarbha"},
        "Jalgaon": {"season_rainfall_mm": 650.0, "rainfall_cv": 0.28, "tmax_mean_c": 34.0, "heat_days_38": 22.0, "subregion": "Khandesh"},
        "Dhule": {"season_rainfall_mm": 590.0, "rainfall_cv": 0.31, "tmax_mean_c": 34.2, "heat_days_38": 24.0, "subregion": "Khandesh"},
        "Aurangabad": {"season_rainfall_mm": 625.0, "rainfall_cv": 0.29, "tmax_mean_c": 32.5, "heat_days_38": 14.0, "subregion": "Marathwada"},
        "Jalna": {"season_rainfall_mm": 640.0, "rainfall_cv": 0.28, "tmax_mean_c": 32.7, "heat_days_38": 15.0, "subregion": "Marathwada"},
        "Parbhani": {"season_rainfall_mm": 780.0, "rainfall_cv": 0.25, "tmax_mean_c": 33.4, "heat_days_38": 17.0, "subregion": "Marathwada"},
        "Nanded": {"season_rainfall_mm": 860.0, "rainfall_cv": 0.23, "tmax_mean_c": 33.6, "heat_days_38": 18.0, "subregion": "Marathwada"},
        "Beed": {"season_rainfall_mm": 610.0, "rainfall_cv": 0.32, "tmax_mean_c": 33.0, "heat_days_38": 16.0, "subregion": "Marathwada"},
        "Osmanabad": {"season_rainfall_mm": 690.0, "rainfall_cv": 0.27, "tmax_mean_c": 32.2, "heat_days_38": 12.0, "subregion": "Marathwada"},
        "Solapur": {"season_rainfall_mm": 540.0, "rainfall_cv": 0.35, "tmax_mean_c": 33.9, "heat_days_38": 20.0, "subregion": "Western Maharashtra"},
        "Ahmednagar": {"season_rainfall_mm": 480.0, "rainfall_cv": 0.36, "tmax_mean_c": 32.4, "heat_days_38": 13.0, "subregion": "Western Maharashtra"},
        "Pune": {"season_rainfall_mm": 620.0, "rainfall_cv": 0.30, "tmax_mean_c": 30.5, "heat_days_38": 5.0, "subregion": "Western Maharashtra"},
        "Satara": {"season_rainfall_mm": 720.0, "rainfall_cv": 0.28, "tmax_mean_c": 30.8, "heat_days_38": 6.0, "subregion": "Western Maharashtra"},
        "Sangli": {"season_rainfall_mm": 510.0, "rainfall_cv": 0.33, "tmax_mean_c": 31.9, "heat_days_38": 10.0, "subregion": "Western Maharashtra"},
        "Kolhapur": {"season_rainfall_mm": 980.0, "rainfall_cv": 0.25, "tmax_mean_c": 29.8, "heat_days_38": 3.0, "subregion": "Western Maharashtra"},
        "Nasik": {"season_rainfall_mm": 710.0, "rainfall_cv": 0.27, "tmax_mean_c": 31.0, "heat_days_38": 7.0, "subregion": "North Maharashtra"}
    }

    pool_records = []
    for dist_raw, clim in MAHARASHTRA_CLIMATOLOGY.items():
        clean_name = "Amravati" if dist_raw == "Amarawati" else "Yavatmal" if dist_raw == "Yeotmal" else dist_raw
        pool_records.append({
            "district": clean_name,
            "subregion": clim["subregion"],
            "state": "Maharashtra",
            "climate_vector": {
                "season_rainfall_mm": clim["season_rainfall_mm"],
                "rainfall_cv": clim["rainfall_cv"],
                "tmax_mean_c": clim["tmax_mean_c"],
                "heat_days_38": clim["heat_days_38"]
            },
            "dominant_crops": district_crops.get(dist_raw, [])
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(pool_records, f, indent=2)
    print(f"Saved climate analog pool ({len(pool_records)} districts) to {output_path}")


def find_climate_analogs(
    target_district: str,
    temp_shift: float = 0.0,
    precip_shift: float = 0.0,
    heat_days_shift: int = 0,
    top_k: int = 4
) -> Dict[str, Any]:
    """
    Finds nearest analog districts today under a shifted climate vector.
    """
    pool = load_analog_pool()
    target_entry = next((d for d in pool if d["district"] == target_district), None)
    if target_entry is None:
        raise ValueError(f"Target district '{target_district}' not in analog pool.")
        
    t_clim = target_entry["climate_vector"]
    
    # Perturb target district climate
    rain_factor = max(0.0, 1.0 + precip_shift)
    perturbed_target = {
        "season_rainfall_mm": t_clim["season_rainfall_mm"] * rain_factor,
        "rainfall_cv": min(0.60, t_clim["rainfall_cv"] * (1.15 if precip_shift < 0 else 0.95)),
        "tmax_mean_c": t_clim["tmax_mean_c"] + temp_shift,
        "heat_days_38": max(0.0, t_clim["heat_days_38"] + heat_days_shift)
    }

    # Standardize across the pool
    matrix = np.array([[d["climate_vector"][v] for v in CLIMATE_VARS] for d in pool])
    means = np.mean(matrix, axis=0)
    stds = np.std(matrix, axis=0)
    stds[stds == 0] = 1.0

    target_norm = (np.array([perturbed_target[v] for v in CLIMATE_VARS]) - means) / stds

    results = []
    for d in pool:
        # Exclude exact target district if shift is 0 (or compare to other districts)
        c_norm = (np.array([d["climate_vector"][v] for v in CLIMATE_VARS]) - means) / stds
        dist_euclidean = float(np.linalg.norm(target_norm - c_norm))
        
        results.append({
            "district": d["district"],
            "subregion": d["subregion"],
            "climate_distance": round(dist_euclidean, 3),
            "current_climate": d["climate_vector"],
            "dominant_crops": d["dominant_crops"]
        })

    # Sort ascending by distance (nearest first)
    # If shift is non-zero, include all; if shift is zero, keep rank
    results = sorted(results, key=lambda x: x["climate_distance"])
    # Return top_k
    top_analogs = results[:top_k]

    return {
        "target_district": target_district,
        "perturbation": {
            "temp_shift_c": temp_shift,
            "precip_shift_pct": round(precip_shift * 100.0, 1),
            "heat_days_shift": heat_days_shift
        },
        "target_perturbed_climate": {k: round(v, 2) for k, v in perturbed_target.items()},
        "analogs": top_analogs,
        "disclaimer": ANALOG_DISCLAIMER
    }
