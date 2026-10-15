import shap
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

FEATURE_LABELS = {
    "longest_dry_spell": "Longest dry spell",
    "heat_days_38": "Days with max temp above 38 C",
    "heat_days_40": "Days with max temp above 40 C",
    "precip_pct_normal": "Precipitation vs normal",
    "precip_total_mm": "Total season precipitation",
    "water_balance_mm": "Seasonal water balance (P - PET)",
    "gwetroot_mean": "Root-zone soil wetness",
    "heavy_rain_days": "Heavy rainfall days (>= 50 mm)",
    "tmax_mean": "Mean maximum temperature",
    "diurnal_range": "Day-night temperature range"
}


def explain_dataset(
    explainer: shap.TreeExplainer,
    df: pd.DataFrame,
    feature_names: List[str]
) -> List[List[Dict[str, Any]]]:
    """
    Vectorized TreeSHAP computation across the dataset.
    Returns a list of driver dictionaries for each row.
    """
    shap_vals = explainer.shap_values(df[feature_names])
    if isinstance(shap_vals, list) and len(shap_vals) > 1:
        # Binary classification list: [class 0, class 1]
        shap_matrix = shap_vals[1]
    elif isinstance(shap_vals, list):
        shap_matrix = shap_vals[0]
    else:
        shap_matrix = shap_vals

    all_drivers = []
    n_rows = len(df)
    
    for row_idx in range(n_rows):
        vals = shap_matrix[row_idx]
        row_dict = df.iloc[row_idx]
        
        # Top 3 drivers by absolute magnitude
        top_indices = np.argsort(np.abs(vals))[::-1][:3]
        row_drivers = []
        
        for idx in top_indices:
            feat_name = feature_names[idx]
            impact = float(vals[idx])
            val = row_dict.get(feat_name)
            label = FEATURE_LABELS.get(feat_name, feat_name.replace("_", " ").title())
            direction = "elevating shortfall risk" if impact < 0 else "supporting crop yield"
            
            # Format plain-sentence explanation safely
            if feat_name == "longest_dry_spell" and pd.notna(val):
                sentence = f"Longest dry spell was {int(val)} days, statistically {direction}."
            elif feat_name == "precip_pct_normal" and pd.notna(val):
                sentence = f"Season rainfall was {float(val):.1f}% of district normal, statistically {direction}."
            elif feat_name in ["heat_days_38", "heat_days_40"] and pd.notna(val):
                sentence = f"Experienced {int(val)} extreme heat days, statistically {direction}."
            elif feat_name == "gwetroot_mean" and pd.notna(val):
                sentence = f"Root-zone soil wetness averaged {float(val):.2f}, statistically {direction}."
            elif feat_name == "water_balance_mm" and pd.notna(val):
                sentence = f"Season water balance was {float(val):+.1f} mm, statistically {direction}."
            else:
                sentence = f"{label} ({val}) was an associated driver, statistically {direction}."
                
            # Safe value serialization
            try:
                num_val = float(val) if pd.notna(val) else None
            except (ValueError, TypeError):
                num_val = str(val) if pd.notna(val) else None
                
            row_drivers.append({
                "feature": feat_name,
                "label": label,
                "value": num_val,
                "impact": round(impact, 4),
                "sentence": sentence,
                "nature": "statistical_association_not_causal"
            })
        all_drivers.append(row_drivers)
        
    return all_drivers


def explain_single_row(
    explainer: shap.TreeExplainer,
    row_df: pd.DataFrame,
    feature_names: List[str]
) -> List[Dict[str, Any]]:
    return explain_dataset(explainer, row_df, feature_names)[0]
