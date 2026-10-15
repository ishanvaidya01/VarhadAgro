# Methodology and Evaluation Protocol

**Product**: VarhadCrop (Vidarbha, Maharashtra)  
**Version**: 2.0 (Real Data Rebuild)  
**Author**: Antigravity Machine Learning Team  
**Status**: Frozen Prior to Final Test Evaluation  

---

## 1. Problem Formulation

The objective is to quantify district-level crop shortfall risk and evaluate climate stress response for major crops in Vidarbha, Maharashtra: Cotton, Soybean, Pigeonpea (Tur), Sorghum (Jowar), Rice, Wheat, and Chickpea (Gram).

Rather than forecasting raw next-year yield (which is dominated by technological yield trends), the modeling framework isolates climatically driven downside shortfall risk through three targets:
1. **Relative Yield Anomaly**:
   $$a_{d,c,t} = \frac{y_{d,c,t} - \hat{y}_{d,c,t}^{\text{trend}}}{\hat{y}_{d,c,t}^{\text{trend}}}$$
   where $\hat{y}_{d,c,t}^{\text{trend}}$ is an expanding-window linear trend estimated strictly using historical years prior to $t$ (years $\tau < t$). Relative anomalies allow direct comparison across distinct crops with different yield magnitudes.
2. **PMFBY-Style Shortfall Event**:
   Based on the Government of India Pradhan Mantri Fasal Bima Yojana (PMFBY) Operational Guidelines:
   $$\text{Threshold Yield}_{d,c,t} = \text{Average}(y_{d,c,\tau} \text{ for } \tau \in [t-7, t-1], \text{ excluding up to 2 calamity years}) \times \text{Indemnity Level}$$
   Default Indemnity Level is set to 80% (configurable to 70% or 90%).  
   The binary target indicates whether actual yield fell below threshold:
   $$S_{d,c,t} = \mathbf{1}(y_{d,c,t} < \text{Threshold Yield}_{d,c,t})$$
3. **Severe Shortfall Event**:
   $$S^{\text{severe}}_{d,c,t} = \mathbf{1}(y_{d,c,t} < 0.60 \times \hat{y}_{d,c,t}^{\text{trend}})$$

---

## 2. Evaluation Protocol

To prevent temporal leakage and realistic out-of-sample assessment, evaluation follows strict temporal and spatial partitioning:

### 2.1 Temporal Partitioning (Rolling-Origin by Year)
The coupled observed panel covers 1981 to 2017 (37 continuous years):
- **Training Block**: 1981 to 2002 (22 years).
- **Validation / Calibration Block**: 2003 to 2007 (5 years). Used strictly for hyperparameter validation, isotonic calibration of classifier probabilities, decision threshold selection, and conformal interval calibration.
- **Test Block**: 2008 to 2017 (10 continuous years, 550 district-crop-year instances).
- **Protocol Rule**: The test block is evaluated once. No model hyperparameters, features, or thresholds may be modified based on test set results.

### 2.2 Spatial Generalization (Leave-One-District-Out)
As a secondary evaluation of geographic transferability, models are trained on 7 districts and evaluated on the held-out 8th district.

### 2.3 Statistical Uncertainty
All test metrics are reported with 95% confidence intervals derived from 1,000 block-bootstrap iterations over calendar years to preserve contemporaneous spatial correlations across districts.

---

## 3. Models

### 3.1 Baseline A (Zero Anomaly Baseline)
Predicts $\hat{a}_{d,c,t} = 0.0$ for all instances (i.e., assuming yield matches the as-of technology trend).

### 3.2 Baseline B (Historical Shortfall Frequency)
Predicts shortfall probability equal to the district-crop's historical shortfall rate observed strictly prior to year $t$:
$$\hat{p}_{d,c,t} = \frac{1}{|\tau < t|} \sum_{\tau < t} S_{d,c,\tau}$$

### 3.3 Regularized Panel Model (Ridge Regression)
Panel linear regression with crop and district fixed effects, season rainfall, temperature diurnal range, extreme heat days, and water balance ($P - \text{PET}$), with L2 regularization chosen via cross-validation on the training/validation block.

### 3.4 Monotone-Constrained LightGBM
Gradient boosted decision trees with domain-grounded monotonic constraints:
- Monotone decreasing (-1) on `longest_dry_spell`: prolonged dry spells cannot increase yield.
- Monotone decreasing (-1) on `heat_days_38` and `heat_days_40`: extreme heat stress during sensitive growth stages cannot increase yield.
- Monotone increasing (+1) on root-zone soil wetness during peak monsoon.

Tree architecture is constrained to prevent overfitting:
- Shallow trees (`max_depth = 4`, `num_leaves = 15`)
- High minimum sample per leaf (`min_child_samples = 25`)
- Quantile regression models fit at quantiles $\alpha \in \{0.10, 0.50, 0.90\}$.

---

## 4. Uncertainty Calibration (Conformalized Quantile Regression)

To produce valid prediction intervals with verified coverage:
1. Two quantile regressors are trained on the training block to predict lower and upper quantiles $\hat{q}_{\alpha/2}$ and $\hat{q}_{1 - \alpha/2}$ (target coverage $1 - \alpha = 0.90$).
2. On the validation block (years 2003-2007), non-conformity scores are computed:
   $$E_i = \max(\hat{q}_{\alpha/2}(x_i) - y_i, y_i - \hat{q}_{1 - \alpha/2}(x_i))$$
3. The conformal correction $Q_{1 - \alpha}(E, \text{val})$ is determined as the $\lceil (n+1)(1-\alpha) \rceil / n$ empirical quantile of non-conformity scores.
4. Conformal prediction interval for new input $x$:
   $$C(x) = [\hat{q}_{\alpha/2}(x) - Q_{1 - \alpha}, \hat{q}_{1 - \alpha/2}(x) + Q_{1 - \alpha}]$$
5. Empirical coverage is evaluated on the final test block (2008-2017) overall, per crop, and per district. Where coverage falls below 90%, it is reported explicitly.

---

## 5. Classification Calibration & Threshold Selection

1. Raw classifier probabilities are calibrated using Isotonic Regression fit strictly on the validation block.
2. The operational decision threshold is chosen on the validation block by optimizing $F_2$ score (prioritizing recall of shortfall events while maintaining false alarm rate $\le 0.25$).
3. Metrics reported on test block: PR-AUC, Brier Score, Brier Skill Score vs Baseline B, Precision, Recall, and False Alarm Rate.

---

## 6. Early-Warning Skill vs Lead Time

Models are trained independently for each lead-time cutoff:
- Kharif: July 15 (sowing), August 15 (flowering), September 15 (pod fill/bolling), October 31 (harvest).
- Rabi: December 15 (vegetative), January 15 (tillering), February 15 (grain fill), March 31 (harvest).
Skill scores ($1 - \text{RMSE}/\text{RMSE}_{\text{baseline}}$) and PR-AUC are measured and plotted as a function of lead time.

---

## 7. Statistical Association vs Agronomic Causation

All model drivers extracted via TreeSHAP represent observed statistical associations under empirical weather variations. They do not constitute controlled agronomic trials or causal claims. Explanations in the product are deterministically generated and explicitly labeled as statistical associations.
