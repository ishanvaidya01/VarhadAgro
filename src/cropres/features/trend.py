import numpy as np
import pandas as pd
from typing import Tuple, Dict

def compute_asof_trend_and_anomalies(
    df_series: pd.DataFrame,
    year_col: str = "year",
    yield_col: str = "yield_kg_ha",
    min_history: int = 5
) -> pd.DataFrame:
    """
    Computes expanding-window as-of trend and relative anomalies strictly without future leakage.
    
    For each target year t:
    - Only observations with year < t are used to fit the historical trend.
    - Fits a robust linear trend (via Huber/Theil-Sen or OLS with min_history) on past years.
    - Extrapolates trend to year t: trend_asof_t.
    - Relative anomaly is computed as: (yield_t - trend_asof_t) / trend_asof_t.
    
    Returns a DataFrame with columns:
    [year, yield_kg_ha, trend_asof, yield_anomaly]
    """
    df = df_series.dropna(subset=[yield_col]).sort_values(year_col).copy()
    years = df[year_col].values
    yields = df[yield_col].values
    n = len(df)
    
    trend_asof = np.full(n, np.nan)
    anomalies = np.full(n, np.nan)
    
    for i in range(n):
        current_year = years[i]
        curr_yield = yields[i]
        
        # Only use strictly positive historical yields
        past_mask = (years < current_year) & (yields > 0)
        past_years = years[past_mask]
        past_yields = yields[past_mask]
        
        if len(past_years) >= min_history and curr_yield > 0:
            # Fit linear trend: y = m * (year - mean_past_year) + c
            x = past_years - np.mean(past_years)
            y = past_yields
            
            # Simple robust linear fit (avoiding negative trend extrapolation slope if anomalous)
            if np.var(x) > 0:
                slope = np.cov(x, y)[0, 1] / np.var(x)
                intercept = np.mean(y)
                # Extrapolate to current_year
                x_t = current_year - np.mean(past_years)
                pred_trend = intercept + slope * x_t
            else:
                pred_trend = np.mean(y)
                
            # Yield must be positive: safeguard floor at 50% of historical past mean and min 10 kg/ha
            past_mean = np.mean(past_yields)
            pred_trend = max(pred_trend, max(10.0, 0.5 * past_mean))
            
            trend_asof[i] = pred_trend
            anomalies[i] = (curr_yield - pred_trend) / pred_trend
        elif len(past_years) > 0 and curr_yield > 0:
            # Before min_history, use expanding mean as baseline
            past_mean = float(np.mean(past_yields))
            if past_mean > 0:
                trend_asof[i] = past_mean
                anomalies[i] = (curr_yield - past_mean) / past_mean
            else:
                trend_asof[i] = np.nan
                anomalies[i] = np.nan
        else:
            trend_asof[i] = np.nan
            anomalies[i] = np.nan
            
    df["trend_asof"] = trend_asof
    df["yield_anomaly"] = anomalies
    return df
