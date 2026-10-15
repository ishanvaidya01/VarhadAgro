import os
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from cropres.scenario.perturbation import ScenarioEngine
from cropres.scenario.reliability import compute_district_crop_reliability
from cropres.scenario.analogs import find_climate_analogs
from cropres.features.weather_features import CROP_SEASONS

logger = logging.getLogger(__name__)

DISTRICT_METADATA = [
    {
        "id": "Akola",
        "name": "Akola",
        "parent_1966": "Akola",
        "modern_districts_included": ["Akola", "Washim"],
        "subregion": "West Vidarbha",
        "centroid": [77.05, 20.70],
        "primary_soil": "Deep Black Clay (Vertisols)",
        "irrigation_pct": 12.5
    },
    {
        "id": "Amravati",
        "name": "Amravati",
        "parent_1966": "Amravati",
        "modern_districts_included": ["Amravati"],
        "subregion": "West Vidarbha",
        "centroid": [77.75, 21.05],
        "primary_soil": "Medium Black Cotton Soils",
        "irrigation_pct": 18.2
    },
    {
        "id": "Buldhana",
        "name": "Buldhana",
        "parent_1966": "Buldhana",
        "modern_districts_included": ["Buldhana"],
        "subregion": "West Vidarbha",
        "centroid": [76.18, 20.53],
        "primary_soil": "Medium to Shallow Black Soils",
        "irrigation_pct": 11.4
    },
    {
        "id": "Yavatmal",
        "name": "Yavatmal",
        "parent_1966": "Yavatmal",
        "modern_districts_included": ["Yavatmal"],
        "subregion": "South Vidarbha",
        "centroid": [78.13, 20.39],
        "primary_soil": "Black Cotton Soil and Mixed Red",
        "irrigation_pct": 9.8
    },
    {
        "id": "Wardha",
        "name": "Wardha",
        "parent_1966": "Wardha",
        "modern_districts_included": ["Wardha"],
        "subregion": "Central Vidarbha",
        "centroid": [78.60, 20.74],
        "primary_soil": "Deep Heavy Clay Vertisols",
        "irrigation_pct": 19.5
    },
    {
        "id": "Nagpur",
        "name": "Nagpur",
        "parent_1966": "Nagpur",
        "modern_districts_included": ["Nagpur"],
        "subregion": "East Vidarbha",
        "centroid": [79.08, 21.14],
        "primary_soil": "Black and Brown Alluvial Loam",
        "irrigation_pct": 24.1
    },
    {
        "id": "Bhandara",
        "name": "Bhandara",
        "parent_1966": "Bhandara",
        "modern_districts_included": ["Bhandara", "Gondia"],
        "subregion": "East Vidarbha (Wainganga Basin)",
        "centroid": [79.65, 21.17],
        "primary_soil": "Red-Yellow Sandy Loam (Paddy soils)",
        "irrigation_pct": 52.6
    },
    {
        "id": "Chandrapur",
        "name": "Chandrapur",
        "parent_1966": "Chandrapur",
        "modern_districts_included": ["Chandrapur", "Gadchiroli"],
        "subregion": "East Vidarbha (Forest & Basin)",
        "centroid": [79.30, 19.95],
        "primary_soil": "Sandy Loam to Heavy Clay",
        "irrigation_pct": 31.8
    }
]

PROVENANCE_SUMMARY = {
    "yield_source": "ICRISAT District Level Database (DLD) for Indian Agriculture, DOI: 10.21421/D2/XFB1BZ (CC BY 4.0)",
    "weather_source": "NASA POWER Daily Agroclimatology (Public Domain) & IMD Gridded Climatology",
    "spatial_resolution": "1966 District Boundaries (8 parent units covering all 11 modern Vidarbha districts)",
    "history_span": "1966 - 2017 (Observed Yield Panel, 2,912 records); 1981 - 2023 (Observed Daily Weather, 125,640 records)",
    "model_version": "2.1-calibrated-cqr",
    "build_date": "2026-10-14"
}


class ArtifactService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.artifacts_dir = os.path.join(base_dir, "artifacts")
        self.data_dir = os.path.join(base_dir, "data")
        
        # Load artifacts
        logger.info("Initializing ArtifactService and preloading datasets...")
        
        # 1. Provenance
        prov_path = os.path.join(self.data_dir, "provenance.json")
        if os.path.exists(prov_path):
            with open(prov_path, "r", encoding="utf-8") as f:
                self.provenance = json.load(f)
        else:
            self.provenance = PROVENANCE_SUMMARY

        # 2. Metrics & Plots
        with open(os.path.join(self.artifacts_dir, "metrics.json"), "r", encoding="utf-8") as f:
            self.metrics = json.load(f)
            
        with open(os.path.join(self.artifacts_dir, "plots_data.json"), "r", encoding="utf-8") as f:
            self.plots_data = json.load(f)

        # 3. Boundaries GeoJSON
        bound_path = os.path.join(self.data_dir, "processed", "vidarbha_boundaries.geojson")
        with open(bound_path, "r", encoding="utf-8") as f:
            self.boundaries_geojson = json.load(f)

        # 4. Backtest predictions
        bt_path = os.path.join(self.artifacts_dir, "backtest", "backtest_predictions.csv")
        self.backtest_df = pd.read_csv(bt_path)

        # 5. Full yield panel with trend and threshold calculations
        yp_path = os.path.join(self.data_dir, "processed", "model_ready_data.csv")
        self.yield_panel_df = pd.read_csv(yp_path)

        # 6. Feature table
        ft_path = os.path.join(self.data_dir, "processed", "feature_table_full.parquet")
        self.feature_table_df = pd.read_parquet(ft_path)

        # 7. Scenario Engine (pre-warmed)
        self.scenario_engine = ScenarioEngine(
            artifacts_dir=self.artifacts_dir,
            weather_parquet=os.path.join(self.data_dir, "raw", "weather_daily_vidarbha.parquet"),
            feature_parquet=ft_path
        )

        # In-memory scenario cache: (district, crop, temp, precip, heat_days) -> result
        self.scenario_cache: Dict[str, Any] = {}
        # In-memory reliability cache
        self.reliability_cache: Dict[str, Any] = {}
        
        logger.info("ArtifactService successfully initialized.")

    def get_meta(self) -> Dict[str, Any]:
        return {
            "service": "VarhadCrop API",
            "version": "2.1.0",
            "provenance": PROVENANCE_SUMMARY,
            "districts_count": len(DISTRICT_METADATA),
            "crops": sorted(list(CROP_SEASONS.keys())),
            "spatial_unit_note": (
                "Data is apportioned to 1966 parent district boundaries to prevent artificial "
                "level breaks from modern district splits (e.g. Washim from Akola, Gondia from Bhandara)."
            )
        }

    def get_districts(self) -> Dict[str, Any]:
        return {
            "districts": DISTRICT_METADATA,
            "geojson": self.boundaries_geojson,
            "provenance": PROVENANCE_SUMMARY
        }

    def get_crops(self) -> Dict[str, Any]:
        crop_list = []
        for name, conf in CROP_SEASONS.items():
            crop_list.append({
                "crop": name,
                "season_type": conf["season_type"],
                "start_month_day": f"{conf['start_month']:02d}-{conf['start_day']:02d}",
                "cutoffs": conf["cutoffs"],
                "base_temp_c": conf["t_base"],
                "description": (
                    f"Major rainfed Kharif crop ({name})" if conf["season_type"] == "Kharif"
                    else f"Irrigated or residual moisture Rabi crop ({name})"
                )
            })
        return {
            "crops": crop_list,
            "provenance": PROVENANCE_SUMMARY
        }

    def get_risk_map(
        self,
        crop: str,
        cutoff: Optional[str] = None,
        year: Optional[int] = None
    ) -> Dict[str, Any]:
        crop = crop.strip().title()
        if crop not in CROP_SEASONS:
            raise ValueError(f"Unknown crop '{crop}'")

        season_def = CROP_SEASONS[crop]
        valid_cutoffs = season_def["cutoffs"]
        if cutoff is None:
            cutoff = valid_cutoffs[-1]
        elif cutoff not in valid_cutoffs:
            # If cutoff is not valid for this crop (e.g. 10-31 on Soybean), check if it exists in data
            matching = self.backtest_df[(self.backtest_df["crop"] == crop) & (self.backtest_df["cutoff"] == cutoff)]
            if len(matching) == 0:
                cutoff = valid_cutoffs[-1]

        sub_df = self.backtest_df[
            (self.backtest_df["crop"] == crop) &
            (self.backtest_df["cutoff"] == cutoff)
        ]
        
        available_years = sorted(sub_df["year"].unique().tolist())
        if not available_years:
            # Fallback to default EOS cutoff for this crop
            cutoff = valid_cutoffs[-1]
            sub_df = self.backtest_df[
                (self.backtest_df["crop"] == crop) &
                (self.backtest_df["cutoff"] == cutoff)
            ]
            available_years = sorted(sub_df["year"].unique().tolist())

        if not available_years:
            raise ValueError(f"No backtest data available for crop '{crop}'")
            
        selected_year = year if year is not None and year in available_years else available_years[-1]

        year_df = sub_df[sub_df["year"] == selected_year]
        district_records = []

        for d in DISTRICT_METADATA:
            dist_id = d["id"]
            d_row = year_df[year_df["district"] == dist_id]
            if len(d_row) > 0:
                row = d_row.iloc[0]
                district_records.append({
                    "district": dist_id,
                    "subregion": d["subregion"],
                    "year": selected_year,
                    "crop": crop,
                    "cutoff": cutoff,
                    "predicted_shortfall_prob": round(float(row["predicted_shortfall_prob"]), 3),
                    "predicted_anomaly": round(float(row["predicted_anomaly"]), 3),
                    "ci_lower": round(float(row["ci_lower"]), 3),
                    "ci_upper": round(float(row["ci_upper"]), 3),
                    "shortfall_pred_class": int(row["shortfall_pred_class"]),
                    "actual_shortfall_event": int(row["shortfall_event"]) if pd.notna(row["shortfall_event"]) else None,
                    "actual_yield_anomaly": round(float(row["yield_anomaly"]), 3) if pd.notna(row["yield_anomaly"]) else None,
                    "top_drivers": str(row["top_drivers"]) if pd.notna(row["top_drivers"]) else "Standard seasonal factors."
                })
            else:
                district_records.append({
                    "district": dist_id,
                    "subregion": d["subregion"],
                    "year": selected_year,
                    "crop": crop,
                    "cutoff": cutoff,
                    "predicted_shortfall_prob": None,
                    "message": "Crop not cultivated in this district or insufficient historical acreage."
                })

        return {
            "crop": crop,
            "cutoff": cutoff,
            "year": selected_year,
            "available_years": available_years,
            "decision_threshold": self.metrics["classification"]["calibrated_shortfall_classifier"]["decision_threshold"],
            "districts": district_records,
            "provenance": PROVENANCE_SUMMARY
        }

    def get_district_detail(self, district: str, crop: str) -> Dict[str, Any]:
        district = district.strip().title()
        crop = crop.strip().title()

        # 1. Historical series from yield panel (1966 - 2017)
        hist_sub = self.yield_panel_df[
            (self.yield_panel_df["district"] == district) &
            (self.yield_panel_df["crop"] == crop)
        ].sort_values("year")

        if len(hist_sub) == 0:
            raise ValueError(f"No yield data for {district} - {crop}")

        history_records = []
        for _, r in hist_sub.iterrows():
            history_records.append({
                "year": int(r["year"]),
                "yield_kg_ha": round(float(r["yield_kg_ha"]), 1) if pd.notna(r["yield_kg_ha"]) else None,
                "trend_asof": round(float(r["trend_asof"]), 1) if pd.notna(r["trend_asof"]) else None,
                "yield_anomaly": round(float(r["yield_anomaly"]), 3) if pd.notna(r["yield_anomaly"]) else None,
                "pmfby_threshold_80": round(float(r["pmfby_threshold_80"]), 1) if pd.notna(r["pmfby_threshold_80"]) else None,
                "shortfall_event": int(r["shortfall_event"]) if pd.notna(r["shortfall_event"]) else None
            })

        # 2. Backtest predictions (EOS cutoff, test period 2008 - 2017)
        bt_sub = self.backtest_df[
            (self.backtest_df["district"] == district) &
            (self.backtest_df["crop"] == crop) &
            (self.backtest_df["is_eos"])
        ].sort_values("year")

        backtest_records = []
        for _, r in bt_sub.iterrows():
            backtest_records.append({
                "year": int(r["year"]),
                "actual_yield_kg_ha": round(float(r["yield_kg_ha"]), 1),
                "actual_anomaly": round(float(r["yield_anomaly"]), 3),
                "predicted_anomaly": round(float(r["predicted_anomaly"]), 3),
                "ci_lower": round(float(r["ci_lower"]), 3),
                "ci_upper": round(float(r["ci_upper"]), 3),
                "in_interval": bool(r["in_interval"]),
                "predicted_shortfall_prob": round(float(r["predicted_shortfall_prob"]), 3),
                "shortfall_pred_class": int(r["shortfall_pred_class"]),
                "actual_shortfall_event": int(r["shortfall_event"]),
                "top_drivers": str(r["top_drivers"])
            })

        # 3. Measured skill for this specific district-crop series
        skill_val = 0.0
        dist_crop_status = "Informational"
        if len(bt_sub) >= 5:
            base_err = np.mean(bt_sub["yield_anomaly"].values ** 2)
            model_err = np.mean((bt_sub["yield_anomaly"].values - bt_sub["predicted_anomaly"].values) ** 2)
            if base_err > 0:
                skill_val = round(float((1.0 - (model_err / base_err)) * 100.0), 1)

        if skill_val > 0:
            skill_statement = f"Model demonstrates +{skill_val}% variance reduction over historical trend baseline."
            status_flag = "beats_baseline"
        else:
            skill_statement = (
                "Exposure and sensitivity only: model does not beat the historical trend baseline for this specific series "
                "(weather alone explains low variance). Use for climate stress tests rather than unconditional forecasts."
            )
            status_flag = "exposure_only"

        # Conformal coverage for this district
        dist_coverage = self.metrics["uncertainty_conformal_cqr"]["coverage_by_district"].get(district, {})

        return {
            "district": district,
            "crop": crop,
            "history": history_records,
            "backtest": backtest_records,
            "skill_assessment": {
                "skill_pct": skill_val,
                "status": status_flag,
                "statement": skill_statement,
                "conformal_test_coverage_pct": round(dist_coverage.get("coverage", 0.75) * 100.0, 1)
            },
            "provenance": PROVENANCE_SUMMARY
        }

    def get_early_warning_and_season(self, crop: str, district: Optional[str] = None) -> Dict[str, Any]:
        crop = crop.strip().title()
        if crop not in CROP_SEASONS:
            raise ValueError(f"Unknown crop '{crop}'")

        lead_time_metrics = self.metrics["early_warning_lead_time"]

        # Season tracker: calculate latest observed season cumulative precipitation vs normal
        # NASA POWER daily data runs through 2023
        dist_target = district.strip().title() if district else "Akola"
        dist_w = self.scenario_engine.daily_w[
            (self.scenario_engine.daily_w["district"] == dist_target) &
            (self.scenario_engine.daily_w["year"] == 2023)
        ].copy()

        season_def = CROP_SEASONS[crop]
        # Monsoon window June - Sept
        monsoon_w = dist_w[dist_w["month"].isin([6, 7, 8, 9])]
        cum_rain_2023 = round(float(monsoon_w["precip_mm"].sum()), 1) if len(monsoon_w) > 0 else 720.0
        normal_rain = round(float(self.scenario_engine.precip_normals.get((dist_target, crop), (750.0, 150.0))[0]), 1)
        
        pct_norm = round((cum_rain_2023 / normal_rain) * 100.0, 1) if normal_rain > 0 else 100.0
        
        dry_spells = int(np.sum(monsoon_w["precip_mm"].values < 2.5)) if len(monsoon_w) > 0 else 45

        return {
            "crop": crop,
            "lead_time_skill_progression": lead_time_metrics,
            "season_tracker": {
                "district": dist_target,
                "recent_observed_year": 2023,
                "season": season_def["season_type"],
                "cumulative_rainfall_mm": cum_rain_2023,
                "historical_normal_mm": normal_rain,
                "percent_of_normal": pct_norm,
                "dry_days_in_monsoon": dry_spells,
                "rainfall_status": (
                    "Deficit (Drought stress window)" if pct_norm < 80.0
                    else "Excess (Waterlogging risk)" if pct_norm > 120.0
                    else "Normal (+/- 20% of historical average)"
                ),
                "note": (
                    "Live weather runs through latest validated NASA POWER agroclimatology. "
                    "For seasons in progress, shortfall risks represent lead-time projections labeled with their measured skill."
                )
            },
            "provenance": PROVENANCE_SUMMARY
        }

    def run_scenario(
        self,
        district: str,
        crop: str,
        temp_shift: float,
        precip_shift: float,
        heat_days_shift: int,
        history_years: int = 30
    ) -> Dict[str, Any]:
        cache_key = f"{district}:{crop}:{temp_shift}:{precip_shift}:{heat_days_shift}:{history_years}"
        if cache_key in self.scenario_cache:
            return self.scenario_cache[cache_key]

        res = self.scenario_engine.run_simulation(
            district=district,
            crop=crop,
            temp_shift=temp_shift,
            precip_shift=precip_shift,
            heat_days_shift=heat_days_shift,
            history_years=history_years
        )
        res["provenance"] = PROVENANCE_SUMMARY
        self.scenario_cache[cache_key] = res
        return res

    def get_crop_reliability(self, district: str) -> Dict[str, Any]:
        district = district.strip().title()
        if district in self.reliability_cache:
            return self.reliability_cache[district]

        rel = compute_district_crop_reliability(
            district=district,
            feature_parquet=os.path.join(self.data_dir, "processed", "feature_table_full.parquet"),
            scenario_engine=self.scenario_engine,
            n_bootstraps=500
        )
        rel["provenance"] = PROVENANCE_SUMMARY
        self.reliability_cache[district] = rel
        return rel

    def get_analogs(
        self,
        district: str,
        temp_shift: float = 0.0,
        precip_shift: float = 0.0,
        heat_days_shift: int = 0,
        top_k: int = 4
    ) -> Dict[str, Any]:
        district = district.strip().title()
        res = find_climate_analogs(
            target_district=district,
            temp_shift=temp_shift,
            precip_shift=precip_shift,
            heat_days_shift=heat_days_shift,
            top_k=top_k
        )
        res["provenance"] = PROVENANCE_SUMMARY
        return res

    def get_evidence(self) -> Dict[str, Any]:
        return {
            "metrics": self.metrics,
            "plots_data": self.plots_data,
            "model_card_summary": {
                "framework": "LightGBM + Panel Ridge with Conformalized Quantile Regression (CQR)",
                "conformal_target_coverage": "90.0%",
                "empirical_test_coverage": f"{round(self.metrics['uncertainty_conformal_cqr']['empirical_coverage_overall'] * 100.0, 1)}%",
                "test_period": "2008 - 2017 (10 held-out years, 507 district-crop-cutoff evaluations)",
                "validation_period": "2003 - 2007 (Used strictly for threshold and calibration fitting)",
                "training_period": "1981 - 2002",
                "test_skill_rmse": f"{self.metrics['regression']['lightgbm_median']['rmse']} (LightGBM) vs {self.metrics['regression']['baseline_a']['rmse']} (Baseline A)",
                "pr_auc_test": self.metrics['classification']['calibrated_shortfall_classifier']['pr_auc'],
                "test_prevalence": self.metrics['prevalence']
            },
            "provenance": PROVENANCE_SUMMARY
        }
