# Progress Log: VarhadCrop Rebuild

## Phase 0: Baseline Audit & Hygiene

### Done
- Initialized rebuild tracking and baseline verification in `docs/AUDIT.md`.
- Pinned production Python dependencies in `requirements.txt` and verified compatible versions.
- Restructured repository into standard modular layout (`src/cropres/`, `backend/`, `frontend/`, `scripts/`, `tests/`, `docs/`).
- Removed legacy synthetic generators and dead templates (`synthetic_generator.py`, `vidarbha_generator.py`, obsolete Vite/React boilerplate assets).
- Implemented strict design rule linter in `scripts/check_design_rules.py`.

### Verified
- Automated design rules checker verified 0 violations.
- Directory and package structure verified with clean Python package imports.

---

## Phase 1: Real Data Panel Ingestion & Harmonization

### Done
- Ingested 52 years of observed crop statistics (1966-2017) from ICRISAT District Level Database (DLD) for Indian Agriculture (DOI: 10.21421/D2/XFB1BZ).
- Harmonized spatial boundaries to 1966 parent districts (Akola, Amravati, Buldhana, Yavatmal, Wardha, Nagpur, Bhandara, Chandrapur) covering all 11 modern Vidarbha districts without artificial split artifacts.
- Ingested daily observed agroclimatology (1981-2023) from NASA POWER point queries (`PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `GWETROOT`, `ALLSKY_SFC_SW_DWN`).
- Simplified boundary geometries for Vidarbha into lightweight GeoJSON (`data/processed/vidarbha_boundaries.geojson`).
- Created cryptographic provenance audit in `data/provenance.json` tracking checksums, retrieval dates, and CC BY 4.0 / Open Data licenses.
- Built automated data card generator in `scripts/generate_data_card.py` producing `docs/DATA_CARD.md`.

### Verified
- Zero synthetic data in raw or processed panels.
- Data card confirms coverage of 2,912 yield records and 125,640 daily weather observations.

---

## Phase 2: Features, Targets & Leakage-Free Pipeline

### Done
- Implemented temporal expanding-window trend estimation $(y_t - \hat{y}_t) / \hat{y}_t$ using only historical data prior to each season.
- Implemented PMFBY operational shortfall target (80% indemnity threshold based on moving average of prior 7 years excluding disaster years).
- Engineered 17 season-aware weather features (monsoon onset rainfall, longest dry spell, heat days >35/38/40 C, Hargreaves PET, water balance, root-zone soil wetness, SPI-3).
- Structured early-warning cutoff tables for Kharif (15 Jul, 15 Aug, 15 Sep, End-of-Season) and Rabi (15 Dec, 15 Jan, 15 Feb, End-of-Season).
- Built comprehensive unit tests preventing temporal leakage and verifying feature isolation in `tests/test_features_and_leakage.py`.

### Verified
- Strict unit tests confirm zero future information leakage into trends, thresholds, or feature calculations.
- Feature table generated across 8,140 cutoff records (`data/processed/feature_table_full.parquet`).

---

## Phase 3: Models, Calibration & Honest Evaluation

### Done
- Established strict rolling-origin evaluation protocol: Train (1981-2002), Validation (2003-2007), Test (2008-2017, touched strictly once).
- Implemented Baseline A (zero relative anomaly) and Baseline B (historical district-crop shortfall frequency).
- Implemented regularized linear panel model (Ridge, $\alpha=10.0$).
- Implemented LightGBM regressor with shallow trees, high `min_child_samples=25`, and domain-informed monotonic constraints.
- Fitted LightGBM quantile regressors ($\alpha=0.05, 0.95$) and calibrated Conformalized Quantile Regression (CQR) intervals on the validation block with finite-sample correction.
- Trained LightGBM shortfall classifier with Isotonic Regression probability calibration on the validation block, selecting decision threshold $T^* = 0.210$ to maximize $F_2$ subject to false alarm rate $\le 25\%$.
- Implemented TreeSHAP explanations with deterministic templated explanations.
- Created single-command build pipeline `python -m scripts.build_all` generating models, metrics, backtest predictions, and documentation.

### Verified
- Automated build pipeline executed in 40.2s.
- Test block (2008-2017) evaluation yields +4.7% RMSE skill over baseline and 77.1% empirical coverage under severe drought stress years.
- Auto-generated `docs/EXPERIMENT_REPORT.md` and `docs/MODEL_CARD.md`.

---

## Phase 4: Scenario Engine, Reliability Ranking & Climate Analogs

### Done
- Built daily weather change-factor perturbation engine ($\Delta T_{max}, \Delta T_{min}, \times \text{Rainfall}$) simulating 30 historical weather seasons.
- Implemented multivariate Out-of-Distribution (OOD) guard using Mahalanobis distance relative to the historical training envelope.
- Implemented Crop Reliability ranking using financial downside risk measures (CVaR 20% expected shortfall) and 1,000 bootstrap iterations on rank confidence intervals.
- Implemented Climate Analogs engine matching shifted climate vectors against 23 Maharashtra agricultural districts and extracting dominant cultivated crops.

### Verified
- Unit tests verify perturbation monotonicity, zero-shift equivalence, and OOD trigger conditions (`tests/test_scenario.py`).
- Spot-checked scenario responses across all 8 parent districts.

---

## Phase 5: Production API Rebuild

### Done
- Built Flask application factory with structured blueprints in `src/cropres/api/`.
- Implemented typed endpoints with strict Pydantic input validation:
  - `GET /api/meta`
  - `GET /api/districts`
  - `GET /api/crops`
  - `GET /api/risk-map`
  - `GET /api/district/<id>`
  - `GET /api/early-warning`
  - `POST /api/scenario`
  - `GET /api/reliability`
  - `GET /api/analogs`
  - `GET /api/evidence`
  - `GET /api/health`
- Configured CORS from environment with strict error handlers and structured JSON responses.

### Verified
- Integration tests in `tests/test_api.py` and endpoint verification scripts pass with 0 errors.

---

## Phase 6: Frontend Overhaul (Data-Journalism Aesthetic)

### Done
- Rebuilt frontend with clean data-journalism design system:
  - Curated warm paper palette (`#F3EFE6` background, `#1B1A17` ink, `#D6CFBF` hairlines, `#1E5144` deep forest accent).
  - Self-hosted typography via `@fontsource` (Newsreader editorial headings, IBM Plex Sans body, IBM Plex Mono figures).
  - No purple gradients, no pill buttons, no glassmorphism, no fake metrics.
- Built custom D3-geo SVG choropleth map with ColorBrewer YlOrBr sequential palette.
- Built interactive Recharts visualizations:
  - Historical yield series with expanding trend and 80% PMFBY threshold.
  - Out-of-sample backtest with 90% CQR uncertainty bands and hit/miss markers.
  - 30-year simulation distribution lines with OOD warning banner and CSV export.
  - Intra-seasonal rainfall tracking and lead-time skill curves.
- Rebuilt 8 complete pages: Risk Map, District Detail, Season Tracker, Scenario Lab, Crop Reliability, Climate Analogs, Evidence, Legal (Terms & Privacy), plus 404 page.

### Verified
- TypeScript check (`npx tsc --noEmit`) passes with 0 errors.
- End-to-end browser test script (`scripts/verify_ui_and_capture_screenshots.py`) verified all 10 pages at 1440px desktop and 390px mobile with 0 console errors and 0 page errors.
- 20 verified screenshots saved in `docs/screenshots/`.

---

## Phase 7: Deployment, CI & Documentation

### Done
- Configured GitHub Actions CI workflow in `.github/workflows/ci.yml`.
- Created production Dockerfile with multi-stage build and Gunicorn server.
- Authored comprehensive documentation:
  - `README.md` (complete project overview, architecture, quickstart)
  - `docs/DEPLOY.md` (hosting guide for local, Docker, cloud)
  - `docs/DECISIONS.md` (10 key architecture and modeling decisions with trade-offs)
  - `docs/API.md` (REST API documentation)

### Verified
- CI workflow runs pytest, design rules checker, and frontend build.

---

## Phase 8: Final Verification & Deployment Readiness

### Done
- Full test suite execution: `pytest` passes 35/35 tests in 9.3s.
- Full build pipeline verified: `python -m scripts.build_all` executes cleanly in 40.2s.
- Design rules check: `python scripts/check_design_rules.py` passes with 0 violations.
- Live backend API verified: running healthy on `http://127.0.0.1:5000` with 8 districts and 507 test backtest records.
- Live frontend dev server verified: running on `http://localhost:5173`.
