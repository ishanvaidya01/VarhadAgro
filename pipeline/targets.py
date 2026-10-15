import pandas as pd
import numpy as np
from statsmodels.nonparametric.smoothers_lowess import lowess
from scipy.interpolate import interp1d

class TargetCreator:
    def __init__(self, train_end_year=2018):
        self.train_end_year = train_end_year
        self.trend_models = {}
        self.thresholds = {}

    def fit_transform(self, df):
        # We need to compute the trend per region and crop, based ONLY on years <= train_end_year
        # Then calculate anomalies for all years based on that fitted trend.
        
        results = []
        
        grouped = df.groupby(["region", "crop"])
        
        for (region, crop), group in grouped:
            group = group.sort_values("year").copy()
            train_group = group[group["year"] <= self.train_end_year]
            
            if len(train_group) < 5:
                # Not enough data to fit a trend, fallback to mean or linear
                trend_yield = [group["yield_t_ha"].mean()] * len(group)
                group["trend_yield"] = trend_yield
                group["yield_anomaly"] = group["yield_t_ha"] - group["trend_yield"]
                self.thresholds[(region, crop)] = np.percentile(train_group["yield_anomaly"].dropna(), 10) if len(train_group) > 0 else 0
                
            else:
                # Fit LOESS on training data
                y_train = train_group["yield_t_ha"].values
                x_train = train_group["year"].values
                
                # fraction of data used for smoothing
                frac = min(0.6, 15.0 / len(x_train))
                
                lowess_res = lowess(y_train, x_train, frac=frac, it=3, return_sorted=False)
                
                # Create an interpolation function to apply to all years (including test)
                # Extrapolate flat for future years
                interp_func = interp1d(x_train, lowess_res, kind='linear', fill_value=(lowess_res[0], lowess_res[-1]), bounds_error=False)
                
                self.trend_models[(region, crop)] = interp_func
                
                group["trend_yield"] = interp_func(group["year"].values)
                group["yield_anomaly"] = group["yield_t_ha"] - group["trend_yield"]
                
                # Downside event threshold (10th percentile of training anomalies)
                train_anomalies = group[group["year"] <= self.train_end_year]["yield_anomaly"]
                threshold = np.percentile(train_anomalies, 10)
                self.thresholds[(region, crop)] = threshold
                
            group["downside_event"] = (group["yield_anomaly"] < self.thresholds.get((region, crop), 0)).astype(int)
            results.append(group)
            
        return pd.concat(results, ignore_index=True)

