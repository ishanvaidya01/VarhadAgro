# VarhadCrop Architectural & Product Decisions Log

This document records the architectural, methodological, and design decisions made during the VarhadCrop real-data rebuild, the evidence justifying them, and the rejected alternatives.

---

## 1. Data Sources & Provenance

### Decision 1: Adoption of ICRISAT District Level Database (DLD) as Primary Yield Panel
- **Decision:** Ingest observed yearly area, production, and yield for Vidarbha crops (1966-2017) directly from ICRISAT DLD (DOI 10.21421/D2/XFB1BZ, CC BY 4.0).
- **Reason:** Real government statistics with 52 years of continuous observations allow credible empirical backtesting across multiple drought cycles (1972, 1987, 2014-2015).
- **Alternatives Rejected:**
  - *Synthetic generator formulas:* Completely eliminated. Recovering a synthetic equation produces fake R2 numbers that have no agronomic validity.
  - *Short modern state statistical abstracts (2018-2023):* Excluded because 5 years of recent data lacks the statistical power required for rolling-origin out-of-sample evaluation.

### Decision 2: Spatial Unit Harmonization to 1966 Parent District Boundaries
- **Decision:** Aggregate modern child districts back to their 1966 parent units:
  - Washim merged into Akola
  - Gondia merged into Bhandara
  - Gadchiroli merged into Chandrapur
- **Reason:** Several Vidarbha districts were split between 1982 and 1999. Fabricating early series for new districts creates artificial discontinuities. Harmonizing to 1966 boundaries preserves historical integrity.
- **Alternatives Rejected:**
  - *Ignoring parent relationships:* Would result in abrupt level breaks and truncation of historical depth for split districts.

### Decision 3: Observed Daily Weather from NASA POWER Agroclimatology
- **Decision:** Query daily weather parameters (T2M, T2M_MAX, T2M_MIN, PRECTOTCORR, GWETROOT, ALLSKY_SFC_SW_DWN) from NASA POWER (1981-2023) at district centroids.
- **Reason:** Open public domain agroclimatology with daily temporal resolution allows exact computation of intra-seasonal dry spells, heat stress days, and Hargreaves PET.
- **Alternatives Rejected:**
  - *Annual district rainfall totals:* Cannot capture dry spells in the critical flowering window or terminal heat during grain filling.

---

## 2. Feature Engineering & Target Formulation

### Decision 4: Strictly Leakage-Free Expanding Trend and Relative Anomalies
- **Decision:** For prediction year t, trend is computed using only years strictly before t (expanding window robust linear trend). The target is relative: `(yield - trend_asof) / trend_asof`.
- **Reason:** In-sample LOESS or flat post-hoc extrapolation leaks future productivity trends into past evaluations. Relative anomalies make risk comparable across high-yielding and low-yielding crops.
- **Alternatives Rejected:**
  - *Flat extrapolation after fixed cutoff:* Biases test anomalies systematically upward.
  - *Absolute yield levels:* Conflates technological trend with climatic vulnerability.

### Decision 5: PMFBY-Style 80% Threshold Yield Target
- **Decision:** Target event is yield falling below the moving average of the previous 7 years (excluding up to 2 calamity years) multiplied by an indemnity level (80% default, configurable 70/90%).
- **Reason:** Grounded directly in official PMFBY operational guidelines, providing decision-relevant risk metrics for insurance planners and district agricultural officers.
- **Alternatives Rejected:**
  - *Arbitrary 10th percentile:* On a 30-year series, 10th percentile corresponds to approximately 3 events, which is far too noisy.

### Decision 6: Crop-Specific Season Windows and Cutoff Dates
- **Decision:** Weather features are computed within crop-specific calendar bounds (Kharif: June 1 to October 31; Rabi: November 1 to March 31) and isolated across 4 cutoff stages (15 Jul, 15 Aug, 15 Sep, Harvest).
- **Reason:** Simulates realistic early-warning availability without temporal leakage from future weather.

---

## 3. Modeling & Evaluation

### Decision 7: Rolling-Origin Temporal Split (Train <= 2002, Val 2003-2007, Test 2008-2017)
- **Decision:** Evaluated models strictly on 10 held-out test years (2008-2017), with hyperparameter choice and calibration thresholds locked on validation years (2003-2007).
- **Reason:** Temporal holdout tests true forecasting skill. Random k-fold cross-validation inflates performance through temporal autocorrelation.
- **Alternatives Rejected:**
  - *Random k-fold splitting:* Unacceptable for time-series forecasting due to lookahead leakage.

### Decision 8: Monotone Constraints on LightGBM Trees
- **Decision:** Applied strict monotone constraints to LightGBM regressor:
  - `longest_dry_spell`: -1 (longer dry spell never increases yield)
  - `heat_days_38`: -1 (extreme heat never increases yield)
  - `heat_days_40`: -1 (extreme heat never increases yield)
  - `gwetroot_mean`: +1 (higher root moisture is beneficial)
- **Reason:** Prevents unconstrained tree models from producing erratic or counter-intuitive responses when stressed.

### Decision 9: Split-Conformal Quantile Regression (CQR)
- **Decision:** Quantile predictions (0.05 and 0.95) calibrated using non-conformity scores computed strictly on the validation block (2003-2007).
- **Reason:** Prevents in-sample undercoverage. Measured test coverage (77.1%) is reported honestly alongside crop-specific coverage (Cotton 90%, Wheat 92.5%).
- **Alternatives Rejected:**
  - *In-sample residuals calibration:* Produces deceptively narrow intervals that fail in real drought years.

---

## 4. Scenario Stress-Testing & Reliability

### Decision 10: Change-Factor Weather Perturbation with Multivariate OOD Guards
- **Decision:** Perturb 30 years of daily weather observations and evaluate each perturbed season against historical bounds using Mahalanobis distance and univariate envelopes.
- **Reason:** Tree-based models plateau outside their training range. When a scenario moves outside the historical envelope, the OOD guard fires a prominent warning and widens the uncertainty band.
- **Alternatives Rejected:**
  - *Static delta adjustment on annual features:* Fails to capture non-linear threshold crossings (e.g. daily Tmax > 38 C).

### Decision 11: CVaR-20% and Bootstrap Intervals for Crop Reliability
- **Decision:** Ranked crops within districts by Expected Shortfall in the worst 20% of seasons (CVaR 20%) and shortfall probability, with 1,000 bootstrap iterations on rank uncertainty.
- **Reason:** Avoids mixing arbitrary weights across different crops. Crops with overlapping rank confidence intervals are explicitly reported as indistinguishable.
- **Alternatives Rejected:**
  - *Arbitrary composite scoring (e.g. index + 20 * yield):* Mathematically invalid due to mixing non-standardized units.

---

## 5. Frontend & Art Direction

### Decision 12: Data-Journalism Paper Aesthetic over Startup Templates
- **Decision:** Warm paper background (`#F3EFE6`), near-black ink (`#1B1A17`), hairline rules (`#D6CFBF`), restrained deep teal accent (`#1E5144`), Newsreader serif headings, and IBM Plex fonts.
- **Reason:** Cultivates credibility and calm focus suitable for public policy, agricultural planning, and scientific review.
- **Alternatives Rejected:**
  - *SaaS startup templates:* Purple gradients, glassmorphism, glowing borders, and pill buttons look trivial and erode credibility.

### Decision 13: Client-Side D3-Geo SVG Mapping without Map Tiles
- **Decision:** Render simplified Vidarbha parent district geometries directly as SVG using `d3-geo`.
- **Reason:** Fast, self-contained (75.9 KB geometry), requires no third-party tile providers or API keys, works offline, and renders sharply at any resolution.
