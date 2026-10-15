# VarhadCrop Repository Audit (Phase 0)

Date: 2026-10-14  
Branch: `rebuild/real-data`  
Author: Antigravity (Audited on local codebase)

---

## 1. Baseline Test Execution Results

Prior to any code modifications, existing tests were executed via `python -m pytest`:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Projects\BioTech-AI
plugins: anyio-3.7.1, asyncio-1.4.0
collected 13 items

tests\test_api.py ....                                                   [ 30%]
tests\test_engine.py ....                                                [ 61%]
tests\test_models.py .                                                   [ 69%]
tests\test_pipeline.py ....                                              [100%]

============================= 13 passed in 6.46s ==============================
```

All 13 tests passed, but inspection of the test assertions revealed that they validate synthetic and flawed assumptions rather than real crop dynamics:
- `tests/test_pipeline.py` tests `pipeline.synthetic_generator.generate_synthetic_data` with fictitious regions `R1` and `Wheat`.
- `tests/test_engine.py` asserts unit-muddled scores (adding yield in tons/ha multiplied by 20 to a unitless index multiplied by 0.8) and references `Rice`, which does not exist in the model.
- `tests/test_models.py` only tests a 4-row temporal split function.
- Running `pytest` directly without PYTHONPATH failed with `ModuleNotFoundError` because `src` structure was missing.

---

## 2. Verification of Section 2 Audit Findings

Every finding described in Section 2 of the specification was audited against the active codebase and confirmed:

### 2.1 Synthetic Data & Metrics Discrepancy
- **Generator**: `pipeline/vidarbha_generator.py` creates yield via a deterministic formula based solely on `t2m_avg`, `precip_mm`, and `extreme_heat_days`.
- **Metrics Mismatch**:
  - `models/artifacts/metrics.json` recorded: LightGBM R² = 0.7614, Classifier Precision = 0.0, Recall = 0.0, F1 = 0.0, Conformal Coverage = 41.09%.
  - `docs/EXPERIMENT_REPORT.md` claimed: LightGBM R² = 0.168, Classifier Precision = 0.368, Recall = 0.412, F1 = 0.389, Conformal Coverage = 52.4%.
  - The documentation had drifted completely from the actual generated artifacts.

### 2.2 Conformal Calibration & In-Sample Contamination
- In `models/train.py` (lines 102-110):
  ```python
  calib = train[train["year"] > 2015]
  calib_pred = lgb_model.predict(calib[ALL_FEATURES])
  residuals = np.abs(calib["yield_anomaly"] - calib_pred)
  q_val = float(np.percentile(residuals, 90))
  ```
  The calibration subset was drawn from `train` (years 2016-2018), which the model had already fit. The in-sample residuals were artificially tiny ($q = 0.068$), causing test set coverage on held-out years to collapse to 41.1% against the 90% target.

### 2.3 Classifier Thresholding & Performance Failure
- The classifier was trained with binary AUC objective, but evaluated with a hardcoded $0.5$ decision threshold on an unbalanced ~10% event rate (`class_pred = (class_pred_prob > 0.5).astype(int)`).
- As recorded in `metrics.json`: Precision = 0.0, Recall = 0.0, F1 = 0.0. The classifier never predicted a single shortfall event on the test set.

### 2.4 Trend Extrapolation & Downside Threshold
- Trend was estimated up to 2018 and held flat while the synthetic generator continued an upward trend, inducing positive test anomalies (+0.06 to +0.14).
- The 10th percentile downside threshold was estimated across only ~29 anomalies per series, yielding roughly 3 noisy events per district.

### 2.5 Scenario Engine (`stress_simulator`) Failure
- In `backend/engine.py` (lines 92-94):
  `oor = (t2m > 45) or (t2m < 5) or (precip < 50) or (heat < 0)`
  Because `t2m` is annual average temperature (~28 C), shifting by +1 C to +5 C produces 29 C to 33 C, which is never > 45 C. The out-of-range flag was permanently `False`.
- Tree models cannot extrapolate beyond boundary splits: tested on Akola Cotton, shifts of +1 C, +2 C, +3 C, and +5 C all output the exact same anomaly plateau (-3.8%), and heat day increments (+10, +20, +30) all produced -0.1%.
- The zero-shift scenario returned +8.2% instead of 0.0% due to trend extrapolation bias.

### 2.6 Methodological Claims vs Repository Reality
- Four API endpoints in `backend/app.py` (`/api/predict-yield`, `/api/crop-resilience`, `/api/crop-ranking`, `/api/climate-analogs`) were stubs returning empty dicts `{}`.
- SHAP values were only printed during training; no inference or explanation pipeline existed.
- `ResilienceEngine.calculate_resilience_index` used arbitrary weights, and `rank_crops` added `expected_yield * 20` to the index, mixing units across crops.

### 2.7 Frontend Deficiencies
- `frontend/index.html` had title `<title>frontend</title>`.
- Hardcoded URLs `http://127.0.0.1:5000` were present in `DataQuality.tsx` and `ScenarioLab.tsx`.
- Vite starter assets (`hero.png`, `react.svg`, `vite.svg`, `App.css`) remained in the repository.
- `DataQuality.tsx` displayed hardcoded "30" years, hardcoded "100% Complete", and read `missing_data_pct` which the API never returned.

---

## 3. Action Items for Phase 0 & Phase 1

1. Pin dependencies in `requirements.txt`.
2. Delete synthetic generators from production code, moving minimal fixtures to `tests/fixtures/`.
3. Eliminate stub endpoints and template leftovers.
4. Restructure the repository into `src/cropres/` package.
5. Ingest real ICRISAT District Level Database (DLD) panel and observed daily weather (NASA POWER / IMD).
