import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, List

class OODDetector:
    """
    Multivariate Out-of-Distribution (OOD) Detector.
    Evaluates whether a perturbed climate scenario falls outside the empirical
    envelope of observed historical training weather.
    """
    def __init__(self, training_features_df: pd.DataFrame, feature_cols: List[str]):
        self.feature_cols = [c for c in feature_cols if c in training_features_df.columns and pd.api.types.is_numeric_dtype(training_features_df[c])]
        train_matrix = training_features_df[self.feature_cols].dropna().values
        
        self.means = np.mean(train_matrix, axis=0)
        self.stds = np.std(train_matrix, axis=0)
        self.stds[self.stds == 0] = 1.0
        
        # Min and Max bounds observed in training data
        self.mins = np.min(train_matrix, axis=0)
        self.maxs = np.max(train_matrix, axis=0)
        
        # Covariance matrix for Mahalanobis-style standardized distance
        z_matrix = (train_matrix - self.means) / self.stds
        cov = np.cov(z_matrix, rowvar=False)
        # Regularized inverse covariance
        reg_cov = cov + 1e-4 * np.eye(len(self.feature_cols))
        self.inv_cov = np.linalg.pinv(reg_cov)
        
        # Training distance distribution
        train_distances = [
            float(np.sqrt(np.dot(np.dot(z, self.inv_cov), z)))
            for z in z_matrix
        ]
        self.dist_p95 = float(np.percentile(train_distances, 95))
        self.dist_p99 = float(np.percentile(train_distances, 99))

    def evaluate_scenario(
        self,
        scenario_features_df: pd.DataFrame,
        tolerance_quantile: float = 0.95
    ) -> Dict[str, Any]:
        """
        Evaluates a set of scenario years against the training envelope.
        Returns:
        - ood_fraction: fraction of scenario years that exceed historical bounds or distance threshold
        - outside_observed_range: boolean flag (True if ood_fraction >= 0.25)
        - max_distance_ratio: ratio of maximum scenario distance to training p95
        - extreme_features: list of features where scenario exceeds min/max bounds
        """
        if len(scenario_features_df) == 0:
            return {"ood_fraction": 0.0, "outside_observed_range": False, "extreme_features": []}
            
        scen_matrix = scenario_features_df[self.feature_cols].values
        n_years = len(scenario_features_df)
        
        exceeded_years = 0
        extreme_features = set()
        distances = []
        
        for i in range(n_years):
            row = scen_matrix[i]
            z = (row - self.means) / self.stds
            d = float(np.sqrt(np.dot(np.dot(z, self.inv_cov), z)))
            distances.append(d)
            
            # Check individual feature bounds
            univariate_out = False
            for j, f in enumerate(self.feature_cols):
                val = row[j]
                if val < self.mins[j] or val > self.maxs[j]:
                    univariate_out = True
                    extreme_features.add(f)
                    
            if d > self.dist_p95 or univariate_out:
                exceeded_years += 1

        ood_fraction = round(float(exceeded_years / n_years), 3)
        outside_range = bool(ood_fraction >= 0.25)
        
        return {
            "ood_fraction": ood_fraction,
            "outside_observed_range": outside_range,
            "mean_multivariate_distance": round(float(np.mean(distances)), 2),
            "training_p95_distance": round(self.dist_p95, 2),
            "distance_ratio": round(float(np.mean(distances) / self.dist_p95), 2),
            "extreme_features": sorted(list(extreme_features)),
            "warning": (
                "Extrapolation warning: Climate perturbation pushes local weather outside the historical observed envelope. Predictions should be interpreted with extreme caution."
                if outside_range else None
            )
        }
