import numpy as np
import pandas as pd
from typing import Optional, List

def compute_pmfby_thresholds(
    df_series: pd.DataFrame,
    year_col: str = "year",
    yield_col: str = "yield_kg_ha",
    indemnity_levels: List[float] = [0.70, 0.80, 0.90],
    default_indemnity: float = 0.80,
    window_years: int = 7,
    max_calamity_drop: int = 2
) -> pd.DataFrame:
    """
    Computes PMFBY-style threshold yields and shortfall indicator targets.
    
    Rule based on PMFBY Operational Guidelines:
    - For target year t, looks at up to 7 prior years (years < t).
    - If at least 5 prior years are available, drops up to `max_calamity_drop` 
      lowest calamity/disaster years from the moving average.
    - Reference Yield = Average of the remaining prior years.
    - Threshold Yield (TY) = Reference Yield * Indemnity Level (e.g. 80%).
    - Shortfall occurs when actual yield_t < Threshold Yield.
    - Severe shortfall occurs when yield_t < 60% of trend_asof (or yield_anomaly < -0.4).
    """
    df = df_series.sort_values(year_col).copy()
    years = df[year_col].values
    yields = df[yield_col].values
    n = len(df)
    
    # Pre-allocate columns for indemnity levels
    ref_yields = np.full(n, np.nan)
    thresholds_80 = np.full(n, np.nan)
    thresholds_70 = np.full(n, np.nan)
    thresholds_90 = np.full(n, np.nan)
    shortfall_80 = np.full(n, np.nan)
    shortfall_70 = np.full(n, np.nan)
    shortfall_90 = np.full(n, np.nan)
    severe_shortfall = np.full(n, np.nan)
    
    for i in range(n):
        current_year = years[i]
        past_mask = (years < current_year) & (years >= current_year - window_years)
        past_yields = yields[past_mask]
        past_valid = past_yields[pd.notna(past_yields) & (past_yields > 0)]
        
        if len(past_valid) >= 3:
            # Sort past yields ascending
            sorted_past = np.sort(past_valid)
            # Exclude up to max_calamity_drop lowest years if enough history
            if len(sorted_past) >= 5:
                kept_past = sorted_past[max_calamity_drop:]
            elif len(sorted_past) >= 4:
                kept_past = sorted_past[1:]
            else:
                kept_past = sorted_past
                
            ref_yield = float(np.mean(kept_past))
            ref_yields[i] = ref_yield
            
            # Threshold yields
            ty70 = ref_yield * 0.70
            ty80 = ref_yield * 0.80
            ty90 = ref_yield * 0.90
            
            thresholds_70[i] = ty70
            thresholds_80[i] = ty80
            thresholds_90[i] = ty90
            
            curr_y = yields[i]
            if pd.notna(curr_y):
                shortfall_70[i] = 1 if curr_y < ty70 else 0
                shortfall_80[i] = 1 if curr_y < ty80 else 0
                shortfall_90[i] = 1 if curr_y < ty90 else 0
                
        # Severe shortfall: check against trend if present, otherwise against 60% of ref_yield
        curr_y = yields[i]
        trend_val = df["trend_asof"].iloc[i] if "trend_asof" in df.columns else np.nan
        if pd.notna(curr_y):
            if pd.notna(trend_val) and trend_val > 0:
                severe_shortfall[i] = 1 if curr_y < (0.60 * trend_val) else 0
            elif pd.notna(ref_yields[i]):
                severe_shortfall[i] = 1 if curr_y < (0.60 * ref_yields[i]) else 0

    df["pmfby_ref_yield"] = ref_yields
    df["pmfby_threshold_70"] = thresholds_70
    df["pmfby_threshold_80"] = thresholds_80
    df["pmfby_threshold_90"] = thresholds_90
    df["shortfall_event_70"] = shortfall_70
    df["shortfall_event_80"] = shortfall_80
    df["shortfall_event_90"] = shortfall_90
    df["shortfall_event"] = shortfall_80  # Default 80% indemnity
    df["severe_shortfall_event"] = severe_shortfall
    
    return df
