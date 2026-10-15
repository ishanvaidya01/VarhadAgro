# Model Card: VarhadCrop Monotone LightGBM & CQR

## Model Details
- **Developer**: Antigravity Machine Learning Team
- **Model Architecture**: Monotone-constrained gradient boosted decision trees (LightGBM) with shallow depth, paired with Conformalized Quantile Regression (CQR) and Isotonic calibrated binary classifiers.
- **Input Features**: Season-aware precipitation totals, monthly totals, dry spell duration, temperature extremes (days above 35/38/40 C), diurnal temperature range, Hargreaves potential evapotranspiration, seasonal water balance, root-zone soil wetness, SPI-3, categorical district and crop IDs.
- **Target Variables**:
  1. Relative yield anomaly: $(y - \hat{y}_{\text{trend}}) / \hat{y}_{\text{trend}}$
  2. PMFBY-style shortfall event: actual yield below 80% indemnity threshold yield
- **License**: MIT
- **Generated From Artifact**: `artifacts/metrics.json`

---

## Intended Use
- **Primary Intended Use**: District agriculture planning, PMFBY crop insurance risk assessment, FPO agricultural advisor decision support, and climate scenario sensitivity testing for Vidarbha, Maharashtra.
- **Target Users**: District agriculture officers, insurance actuaries, agricultural researchers.
- **Out of Scope Use**: Individual farm-level yield predictions, precision agriculture field management, or causal agronomic recommendations.

---

## Training and Evaluation Data
- **Yield Panel**: ICRISAT District Level Database (DLD), 1966 to 2017, apportioned to 1966 district boundaries (DOI: 10.21421/D2/XFB1BZ).
- **Weather Panel**: NASA POWER Agroclimatology daily observed weather, 1981 to 2017 (125,640 daily records across 8 district centroids).
- **Temporal Split**:
  - Training: 1981 to 2002 (1,133 instances)
  - Validation: 2003 to 2007 (269 instances)
  - Final Test: 2008 to 2017 (507 instances, touched strictly once)

---

## Measured Performance on Final Test Block (2008-2017)
- **Anomaly Regression RMSE**: 0.4194 (Skill vs Zero Baseline: +4.7%)
- **Shortfall PR-AUC**: 0.4628 (vs test prevalence 0.3669)
- **Brier Score**: 0.2617
- **Conformal Interval Target Coverage**: 90.0%
- **Empirical Measured Coverage**: 77.1%

---

## Ethical and Practical Limitations
1. **Statistical Association Only**: All drivers and predictions represent statistical associations under historical observational data, not causal agronomic prescriptions.
2. **Extrapolation Boundaries**: Decision trees cannot extrapolate beyond observed splits. The scenario engine incorporates a multivariate out-of-distribution (OOD) detector that explicitly flags shifts exceeding historical training limits.
3. **Unobserved Agronomic Variance**: Soil type variations within districts, pest infestations (e.g. pink bollworm), and fertilizer application rates are not captured in macro-meteorological features.
