# VarhadCrop API Reference

The VarhadCrop API serves observed historical agricultural statistics, climate feature tables, calibrated LightGBM predictions, conformal prediction intervals, climate stress simulations, and analog rankings for Vidarbha, Maharashtra.

Base URL: `http://localhost:5000` (configurable via `PORT` and `HOST` environment variables)
CORS Origin: Configurable via `CORS_ORIGIN` (defaults to `*`)

All responses return standard JSON. Every successful response includes a `provenance` metadata block stating the source database, licenses, spatial units, and model version.

---

## Error Handling

All error responses adhere to a uniform structure:

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [
    {
      "loc": ["temp_shift"],
      "msg": "Input should be less than or equal to 10",
      "type": "less_than_equal"
    }
  ]
}
```

Standard HTTP status codes:
- `200 OK`: Request succeeded.
- `400 Bad Request`: Query parameter or payload validation error.
- `404 Not Found`: Unknown district, crop, or endpoint.
- `500 Internal Server Error`: Unhandled server exception.

---

## Endpoints

### 1. System Health
`GET /api/health`

Returns operational status and loaded records count.

**Response Example:**
```json
{
  "status": "ok",
  "service": "VarhadCrop API",
  "districts_loaded": 8,
  "records_loaded": 507
}
```

---

### 2. Metadata and Provenance
`GET /api/meta`

Returns data source citations, licenses, spatial harmonization definitions, and model versions.

**Response Example:**
```json
{
  "service": "VarhadCrop API",
  "version": "2.1.0",
  "provenance": {
    "yield_source": "ICRISAT District Level Database (DLD) for Indian Agriculture, DOI: 10.21421/D2/XFB1BZ (CC BY 4.0)",
    "weather_source": "NASA POWER Daily Agroclimatology (Public Domain) & IMD Gridded Climatology",
    "spatial_resolution": "1966 District Boundaries (8 parent units covering all 11 modern Vidarbha districts)",
    "history_span": "1966 - 2017 (Observed Yield Panel, 2,912 records); 1981 - 2023 (Observed Daily Weather, 125,640 records)",
    "model_version": "2.1-calibrated-cqr",
    "build_date": "2026-10-14"
  },
  "districts_count": 8,
  "crops": ["Chickpea", "Cotton", "Pigeonpea", "Rice", "Sorghum", "Soybean", "Wheat"]
}
```

---

### 3. Districts and Boundaries
`GET /api/districts` (Alias: `/api/regions`)

Returns the list of 8 Vidarbha parent districts with modern split mappings, subregions, and GeoJSON geometry for client-side rendering.

**Response Example:**
```json
{
  "districts": [
    {
      "id": "Akola",
      "name": "Akola",
      "parent_1966": "Akola",
      "modern_districts_included": ["Akola", "Washim"],
      "subregion": "West Vidarbha",
      "centroid": [77.05, 20.7],
      "primary_soil": "Deep Black Clay (Vertisols)",
      "irrigation_pct": 12.5
    }
  ],
  "geojson": {
    "type": "FeatureCollection",
    "features": [...]
  }
}
```

---

### 4. Crops Catalog
`GET /api/crops`

Returns supported crops, their agricultural season (Kharif / Rabi), thermal base temperature, and early-warning cutoff stages.

**Response Example:**
```json
{
  "crops": [
    {
      "crop": "Cotton",
      "season_type": "Kharif",
      "start_month_day": "06-01",
      "cutoffs": ["07-15", "08-15", "09-15", "10-31"],
      "base_temp_c": 15.0,
      "description": "Major rainfed Kharif crop (Cotton)"
    }
  ]
}
```

---

### 5. Risk Map
`GET /api/risk-map?crop=Cotton&cutoff=10-31&year=2017`

Returns spatial risk distributions across Vidarbha districts for a specified crop, cutoff date, and agricultural year.

**Parameters:**
- `crop` (required, string): Crop name (e.g. `Cotton`, `Soybean`).
- `cutoff` (optional, string): Cutoff date (`MM-DD`, default: end of season).
- `year` (optional, integer): Test year (`2008` to `2017`, default: `2017`).

**Response Example:**
```json
{
  "crop": "Cotton",
  "cutoff": "10-31",
  "year": 2017,
  "available_years": [2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017],
  "decision_threshold": 0.21,
  "districts": [
    {
      "district": "Akola",
      "subregion": "West Vidarbha",
      "predicted_shortfall_prob": 0.38,
      "predicted_anomaly": -0.042,
      "ci_lower": -0.892,
      "ci_upper": 0.808,
      "shortfall_pred_class": 1,
      "actual_shortfall_event": 1,
      "actual_yield_anomaly": -0.18,
      "top_drivers": "Gdd (2715.9) was an associated driver, statistically contributing -0.038 to predicted relative yield anomaly."
    }
  ]
}
```

---

### 6. District Detail and History
`GET /api/district/<district_id>?crop=Cotton` (Alias: `/api/yield-history?district=Akola&crop=Cotton`)

Returns complete historical yield statistics (1966-2017), expanding trend, PMFBY-style threshold yield, 10-year out-of-sample backtest predictions with conformal prediction intervals, SHAP drivers, and honest skill assessment against baseline.

**Response Example:**
```json
{
  "district": "Akola",
  "crop": "Cotton",
  "history": [
    {
      "year": 1966,
      "yield_kg_ha": 105.0,
      "trend_asof": 105.0,
      "yield_anomaly": 0.0,
      "pmfby_threshold_80": null,
      "shortfall_event": 0
    }
  ],
  "backtest": [
    {
      "year": 2017,
      "actual_yield_kg_ha": 312.0,
      "actual_anomaly": -0.18,
      "predicted_anomaly": -0.042,
      "ci_lower": -0.892,
      "ci_upper": 0.808,
      "in_interval": true,
      "predicted_shortfall_prob": 0.38,
      "shortfall_pred_class": 1,
      "actual_shortfall_event": 1,
      "top_drivers": "..."
    }
  ],
  "skill_assessment": {
    "skill_pct": 5.4,
    "status": "beats_baseline",
    "statement": "Model demonstrates +5.4% variance reduction over historical trend baseline.",
    "conformal_test_coverage_pct": 69.8
  }
}
```

---

### 7. Early Warning and Season Tracker
`GET /api/early-warning?crop=Cotton&district=Akola`

Returns measured model skill as a function of lead time before harvest, along with season-in-progress weather tracking comparing recent observed precipitation to historical normal.

**Response Example:**
```json
{
  "crop": "Cotton",
  "lead_time_skill_progression": [
    {
      "cutoff": "07-15",
      "stage": "Mid-July (Sowing / Onset)",
      "lead_days": 105,
      "rmse": 0.4864,
      "skill_score": 0.0306,
      "pr_auc": 0.4256,
      "samples": 347
    },
    {
      "cutoff": "10-31",
      "stage": "End of Season (Harvest)",
      "lead_days": 0,
      "rmse": 0.4873,
      "skill_score": 0.0478,
      "pr_auc": 0.4922,
      "samples": 267
    }
  ],
  "season_tracker": {
    "district": "Akola",
    "recent_observed_year": 2023,
    "season": "Kharif",
    "cumulative_rainfall_mm": 682.4,
    "historical_normal_mm": 745.0,
    "percent_of_normal": 91.6,
    "dry_days_in_monsoon": 41,
    "rainfall_status": "Normal (+/- 20% of historical average)"
  }
}
```

---

### 8. Climate Scenario Simulation
`POST /api/scenario` (Alias: `/api/climate-scenario`)

Runs change-factor stress testing over 30 years of daily historical weather. Evaluates out-of-distribution (OOD) risk using multivariate distance and univariate envelope checks.

**Request Payload:**
```json
{
  "district": "Akola",
  "crop": "Cotton",
  "temp_shift": 2.0,
  "precip_shift": -0.20,
  "heat_days_shift": 5,
  "history_years": 30
}
```

**Response Example:**
```json
{
  "district": "Akola",
  "crop": "Cotton",
  "scenario_parameters": {
    "temp_shift_c": 2.0,
    "precip_shift_pct": -20.0,
    "heat_days_shift": 5,
    "weather_years_simulated": 30
  },
  "ood_guard": {
    "ood_fraction": 0.367,
    "outside_observed_range": true,
    "mean_multivariate_distance": 6.82,
    "training_p95_distance": 5.41,
    "distance_ratio": 1.26,
    "extreme_features": ["heat_days_38", "precip_total_mm"],
    "warning": "Extrapolation warning: Climate perturbation pushes local weather outside the historical observed envelope. Predictions should be interpreted with extreme caution."
  },
  "baseline_summary": {
    "median_anomaly": 0.082,
    "anomaly_iqr": [-0.12, 0.24],
    "shortfall_probability": 0.32
  },
  "scenario_summary": {
    "median_anomaly": -0.195,
    "anomaly_iqr": [-0.38, -0.04],
    "shortfall_probability": 0.58,
    "delta_shortfall_prob": 0.26,
    "ci_lower_median": -0.92,
    "ci_upper_median": 0.53
  },
  "distribution_points": {
    "years": [1988, 1989, "..."],
    "baseline_anomalies": [0.05, -0.10, "..."],
    "scenario_anomalies": [-0.18, -0.32, "..."],
    "scenario_shortfall_probs": [0.42, 0.71, "..."]
  }
}
```

---

### 9. Crop Reliability Ranking
`GET /api/reliability?district=Akola`

Ranks all cultivated crops within a district by downside severity (CVaR 20% relative loss) and shortfall frequency. Generates 95% bootstrap confidence intervals for rank positions.

**Response Example:**
```json
{
  "district": "Akola",
  "ranked_crops": [
    {
      "crop": "Wheat",
      "rank": 1,
      "rank_ci": [1, 2],
      "shortfall_probability": 0.22,
      "expected_shortfall_cvar20": -0.292,
      "expected_shortfall_label": "29.2% loss in severe years",
      "heat_sensitivity_2c": -0.04,
      "years_observed": 52
    },
    {
      "crop": "Cotton",
      "rank": 3,
      "rank_ci": [2, 4],
      "shortfall_probability": 0.36,
      "expected_shortfall_cvar20": -0.363,
      "expected_shortfall_label": "36.3% loss in severe years",
      "heat_sensitivity_2c": -0.08,
      "years_observed": 52
    }
  ],
  "indistinguishable_pairs": [
    {
      "crop_a": "Chickpea",
      "crop_b": "Cotton",
      "reason": "Overlapping 95% bootstrap intervals [2-3 vs 2-4] with small severity gap (0.01); risk difference is not statistically significant."
    }
  ]
}
```

---

### 10. Climate Analogs
`GET /api/analogs?district=Akola&temp_shift=2.0&precip_shift=-0.20` or `POST /api/analogs`

Finds existing districts in Maharashtra whose current climate vector (seasonal precipitation, CV, Tmax, extreme heat days) resembles the target district under a specified shift.

**Response Example:**
```json
{
  "target_district": "Akola",
  "perturbation": {
    "temp_shift_c": 2.0,
    "precip_shift_pct": -20.0,
    "heat_days_shift": 0
  },
  "analogs": [
    {
      "district": "Jalgaon",
      "subregion": "Khandesh",
      "climate_distance": 1.551,
      "current_climate": {
        "season_rainfall_mm": 650.0,
        "rainfall_cv": 0.28,
        "tmax_mean_c": 34.0,
        "heat_days_38": 22.0
      },
      "dominant_crops": [
        {"crop": "Cotton", "area_1000ha": 284.5, "area_share_pct": 52.1},
        {"crop": "Soybean", "area_1000ha": 142.0, "area_share_pct": 26.0}
      ]
    }
  ],
  "disclaimer": "Analog similarity reflects atmospheric and meteorological variables only. Local soil profiles, groundwater availability, canal irrigation infrastructure, and management practices vary and must be evaluated independently."
}
```

---

### 11. Evidence and Validation
`GET /api/evidence` (Aliases: `/api/model-metrics`, `/api/data-quality`)

Returns full pipeline evaluation metrics, calibration curve data, empirical conformal coverage tables, and model card summaries.

**Response Example:**
```json
{
  "metrics": {
    "regression": {
      "lightgbm_median": {
        "rmse": 0.4194,
        "skill_score": 0.0469,
        "spearman_rank_correlation": 0.3636
      }
    },
    "uncertainty_conformal_cqr": {
      "target_coverage": 0.9,
      "empirical_coverage_overall": 0.7712,
      "mean_interval_width": 1.025
    }
  },
  "plots_data": { ... }
}
```
