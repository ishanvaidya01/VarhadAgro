import numpy as np
import pandas as pd
import lightgbm as lgb
import json
import os


FEATURES = ["t2m_avg", "precip_mm", "extreme_heat_days"]
CAT_FEATURES = ["region", "crop"]
ALL_FEATURES = FEATURES + CAT_FEATURES


class ResilienceEngine:
    def __init__(self, model_path=None):
        if model_path is None:
            # Default: resolve relative to this file
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_path = os.path.join(base, "models", "artifacts")
        self.model_path = model_path
        self._load_models()

    def _load_models(self):
        self.lgb_model     = None
        self.cat_maps      = {}
        self.baselines     = None

        reg_path  = os.path.join(self.model_path, "lgb_regressor.txt")
        cat_path  = os.path.join(self.model_path, "cat_maps.json")
        base_path = os.path.join(self.model_path, "district_baselines.csv")

        if os.path.exists(reg_path):
            self.lgb_model = lgb.Booster(model_file=reg_path)

        if os.path.exists(cat_path):
            with open(cat_path) as f:
                self.cat_maps = json.load(f)

        if os.path.exists(base_path):
            self.baselines = pd.read_csv(base_path)

    def _get_baseline(self, region: str, crop: str) -> dict:
        """Return mean climate values from training data for this region+crop combo."""
        if self.baselines is None:
            return {"t2m_avg": 28.0, "precip_mm": 900.0, "extreme_heat_days": 35}
        row = self.baselines[
            (self.baselines["region"] == region) &
            (self.baselines["crop"]   == crop)
        ]
        if len(row) == 0:
            return {"t2m_avg": 28.0, "precip_mm": 900.0, "extreme_heat_days": 35}
        return {
            "t2m_avg":           float(row["t2m_avg_mean"].iloc[0]),
            "precip_mm":         float(row["precip_mm_mean"].iloc[0]),
            "extreme_heat_days": float(row["extreme_heat_days_mean"].iloc[0]),
        }

    def _build_feature_row(self, region: str, crop: str, t2m: float,
                           precip: float, heat_days: float) -> pd.DataFrame:
        """Build a properly typed single-row DataFrame for prediction."""
        row = {
            "t2m_avg":           t2m,
            "precip_mm":         precip,
            "extreme_heat_days": heat_days,
            "region":            region,
            "crop":              crop,
        }
        df = pd.DataFrame([row])
        for col in CAT_FEATURES:
            cats = self.cat_maps.get(col)
            if cats:
                df[col] = pd.Categorical(df[col], categories=cats)
            else:
                df[col] = df[col].astype("category")
        return df[ALL_FEATURES]

    def stress_simulator(self, region: str, crop: str,
                         temp_shift: float = 0.0,
                         precip_shift: float = 0.0,
                         heat_days_shift: int = 0):
        """
        Uses the real district+crop baseline climate, applies user shifts,
        and returns (predicted_yield_anomaly, out_of_range_flag).
        """
        if self.lgb_model is None:
            return 0.0, True

        base = self._get_baseline(region, crop)
        t2m    = base["t2m_avg"]           + temp_shift
        precip = base["precip_mm"]         * (1.0 + precip_shift)
        heat   = base["extreme_heat_days"] + heat_days_shift

        # Out-of-range: beyond plausible Vidarbha extremes
        oor = (t2m > 45) or (t2m < 5) or (precip < 50) or (heat < 0)

        features_df = self._build_feature_row(region, crop, t2m, precip, heat)
        pred = float(self.lgb_model.predict(features_df)[0])
        return pred, oor

    # ── Index and ranking helpers (unchanged) ────────────────────────────

    def find_analog(self, target_climate, candidate_climates,
                    variables=None):
        variables = variables or ["t2m_avg", "precip_mm"]
        t = np.array([target_climate[v] for v in variables])
        best, best_dist = None, float("inf")
        for name, c in candidate_climates.items():
            d = float(np.linalg.norm(t - np.array([c[v] for v in variables])))
            if d < best_dist:
                best_dist, best = d, name
        return best, best_dist

    def interactive_risk_map_data(self, regions_data):
        out = {}
        for region, metrics in regions_data.items():
            p = metrics["downside_prob"]
            out[region] = {
                "severity": "High" if p > 0.2 else "Medium" if p > 0.1 else "Low",
                "prob": p,
            }
        return out
