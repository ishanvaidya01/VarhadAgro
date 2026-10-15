# VarhadCrop

District-level crop shortfall risk, calibrated uncertainty, and climate stress-testing for Vidarbha, Maharashtra. Built on 52 years of observed government yield statistics and 43 years of daily agroclimatology, with uncertainty calibrated on held-out years.

[![CI Status](https://github.com/ishanvaidya01/VarhadCrop/actions/workflows/ci.yml/badge.svg)](https://github.com/ishanvaidya01/VarhadCrop/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%7C%20TypeScript%20%7C%20Vite-61dafb.svg)](frontend/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Data: ICRISAT & NASA](https://img.shields.io/badge/Data-ICRISAT%20DLD%20%2B%20NASA%20POWER-orange.svg)](docs/DATA_CARD.md)
[![Design Verified](https://img.shields.io/badge/Design%20Rules-Strict%20Enforcement-success.svg)](scripts/check_design_rules.py)

---

![VarhadCrop Vidarbha Risk Map](docs/screenshots/risk_map_1440px.png)

---

## 1. Mission and Operational Focus

VarhadCrop is an open-source, evidence-first decision-support platform designed for the drought-prone and climate-vulnerable Vidarbha region of Maharashtra, India. It translates historical agronomic panel data and observed weather records into operational risk metrics for:

- **District Agriculture Officers (DAOs):** Formulating district contingency plans for delayed monsoon onset, extended mid-season dry spells, or terminal heat stress.
- **Pradhan Mantri Fasal Bima Yojana (PMFBY) Analysts:** Evaluating district-level yield shortfall probabilities against official 80% indemnity reference yields.
- **Agri-Lending & FPO Risk Teams:** Assessing downside yield volatility and shortfall probability across major kharif and rabi crops.
- **Agricultural Climate Scientists:** Benchmarking machine learning architectures against strictly causal, expanding-window historical baselines.

### Concrete Questions Answered by the Platform

1. **Shortfall Likelihood:** What is the probability that crop *C* in district *D* suffers a yield drop below the 80% PMFBY indemnity threshold, and how early in the season can that risk be detected?
2. **Climate Stress Sensitivity:** How does shortfall risk respond to systematic temperature increments (+1 deg C to +5 deg C), rainfall anomalies (-40% to +40%), and heat wave frequency?
3. **Extrapolation Boundaries:** When do synthetic climate stress scenarios cross beyond the historical multivariate envelope (out-of-distribution guard), requiring wider uncertainty bounds?
4. **Crop Downside Reliability:** Which crops minimize shortfall frequencies and downside loss variance under local rainfall volatility?
5. **Spatial Climate Analogs:** Which district in Maharashtra today exhibits the seasonal agroclimatic profile that district *D* will experience under altered weather regimes?

---

## 2. Methodology: Why Typical Crop Yield Demos Fail

Standard crop yield machine learning demonstrations frequently suffer from critical methodological flaws: they train unconstrained regression algorithms on next-year point yields, report inflated in-sample R2 scores, evaluate models across random train/test splits that introduce temporal leakage, and produce fragile predictions outside observed weather ranges.

VarhadCrop is engineered from the ground up to eliminate these failure modes:

| Problem in Typical Demos | Methodological Solution in VarhadCrop | Reference File |
| :--- | :--- | :--- |
| **Synthetic or Mock Data** | Strictly grounded in 52 years of official yield statistics (ICRISAT District Level Database, 1966-2017) and 43 years of daily observed weather (NASA POWER, 1981-2023). Zero synthetic data in production. | [DATA_CARD.md](docs/DATA_CARD.md) |
| **Temporal Data Leakage** | Expanding historical window trends (`trend_asof`) and 7-year moving-average reference yields computed strictly using years prior to the target year. | [trend.py](src/cropres/features/trend.py) |
| **Irrelevant Targets** | Models PMFBY-style threshold shortfalls ($Y_t < 0.80 \times \bar{Y}_{\text{past}}$), aligning with real crop insurance indemnities. | [targets.py](src/cropres/features/targets.py) |
| **Over-optimistic Intervals** | Employs Conformalized Quantile Regression (CQR) with non-conformity calibration on held-out years, reporting exact empirical test coverage. | [evaluate.py](src/cropres/models/evaluate.py) |
| **Unbounded Tree Extrapolation** | Dual Out-of-Distribution (OOD) guard (multivariate Mahalanobis distance + univariate historical envelopes) warns users when scenario shifts leave empirical reality. | [ood.py](src/cropres/scenario/ood.py) |
| **Nonsensical Gradient Responses** | Enforces monotone negative constraints on heat stress features: increasing extreme heat days cannot spuriously increase crop yields. | [train.py](src/cropres/models/train.py) |
| **Selective Reporting** | Where weather features do not beat a simple historical trend baseline, the system explicitly reports "Exposure and sensitivity only" rather than claiming artificial predictive skill. | [EXPERIMENT_REPORT.md](docs/EXPERIMENT_REPORT.md) |

---

## 3. Core Platform Capabilities

### 3.1 Vidarbha Risk Map & District Screening
Visualizes district-by-district shortfall probabilities across the 8 parent administrative units of Vidarbha (covering all 11 modern districts: Akola, Washim, Amravati, Buldhana, Yavatmal, Wardha, Nagpur, Bhandara, Gondia, Chandrapur, Gadchiroli). Displays calibrated shortfall probability, indemnity status, and historical yield anomalies.

### 3.2 Climate Stress-Testing Scenario Lab
An interactive simulation engine allowing planners to perturb seasonal temperature, rainfall, and heat day totals. Real-time inference couples LightGBM quantile regressors, regularized panel ridge models, and an automated OOD detector that flags extrapolation risk.

![Scenario Lab](docs/screenshots/scenario_lab_1440px.png)

### 3.3 Crop Downside Reliability Profiler
Evaluates the comparative resilience of candidate crops (Cotton, Soybean, Pigeonpea, Sorghum, Rice, Wheat, Chickpea) within each district across multi-decade weather variance. Computes empirical shortfall rates, downside semi-variance, and rank stability.

![Crop Reliability](docs/screenshots/crop_reliability_1440px.png)

### 3.4 Historical Climate Analogs
Finds historical district-season pairs whose thermal and precipitation profiles match a user-defined scenario or target year. Enables agronomists to identify established cropping practices and management strategies from analogous agroecological zones.

![Climate Analogs](docs/screenshots/climate_analogs_1440px.png)

### 3.5 In-Season Phenological Weather Tracker
Monitors cumulative growing degree days (GDD), precipitation totals, dry spells, and heat-stress intervals across crop-specific calendar windows (Kharif sowing to harvest, Rabi post-monsoon).

![Season Tracker](docs/screenshots/season_tracker_1440px.png)

### 3.6 Evidence Ledger & Empirical Audit
A dedicated transparency interface exposing all pipeline artifacts, empirical calibration curves, held-out test coverage tables, and explicit system limitations. Every metric displayed in the UI links directly to pipeline build outputs.

![Evidence Page](docs/screenshots/evidence_1440px.png)

---

## 4. Empirical Evaluation on Held-Out Test Block

All models were evaluated on a strictly separated 10-year rolling held-out test block (2008-2017) comprising 507 real district-crop instances:

| Model / Architecture | Test RMSE | Skill Score over Baseline A | Evaluation Finding |
| :--- | :--- | :--- | :--- |
| **Baseline A (Historical Trend Only)** | 0.4401 | 0.00% (Reference) | Zero relative anomaly; assumes yield follows local technological trend. |
| **Panel Ridge (Fixed Effects)** | **0.4044** | **+8.11%** [95% CI: +2.8%, +11.8%] | Regularized linear panel captures multi-district weather sensitivity effectively. |
| **LightGBM (Monotone Constrained)** | **0.4194** | **+4.69%** [95% CI: +1.0%, +7.5%] | Non-linear tree model with enforced physics-based monotonicity on heat stress. |
| **Calibrated Shortfall Classifier** | PR-AUC: **0.4628** | Base Prevalence: 36.69% | Isotonic calibration yields 49.3% precision at operational threshold (0.21). |
| **Conformal Prediction Band (90% Target)** | Coverage: **77.12%** | Cotton: 90.0%, Wheat: 92.5% | Finite-sample CQR band calibrated on held-out residual quantiles. |

For detailed breakdowns by crop and district, consult the [Experiment Report](docs/EXPERIMENT_REPORT.md) and [Model Card](docs/MODEL_CARD.md).

---

## 5. System Architecture & Repository Layout

```text
VarhadCrop/
├── artifacts/                     # Serialized production models, calibration params, and metrics
│   ├── conformal/                 # CQR calibration cutoffs and empirical intervals
│   ├── models/                    # Trained LightGBM boosters, Ridge panel, and isotonic calibrator
│   ├── metrics.json               # Canonical evaluation metrics matching documentation
│   └── plots_data.json            # Pre-computed calibration and residual distribution curves
├── backend/                       # Production WSGI application entrypoint
│   └── app.py                     # Flask server launcher with environment configuration
├── data/                          # Data store and governance metadata
│   ├── processed/                 # Model-ready feature tables and Vidarbha GeoJSON boundaries
│   └── provenance.json            # SHA-256 hashes, retrieval timestamps, and data licenses
├── docs/                          # In-depth architectural and scientific documentation
│   ├── API.md                     # Complete OpenAPI/REST endpoint specifications
│   ├── AUDIT.md                   # Initial codebase audit and refactoring log
│   ├── DATA_CARD.md               # Datasheet for agroclimatic and yield panel datasets
│   ├── DECISIONS.md               # Architectural and methodological decision records
│   ├── DEPLOY.md                  # Cloud deployment and production operations manual
│   ├── EXPERIMENT_REPORT.md       # Benchmark results, ablation experiments, and error analysis
│   ├── METHODOLOGY.md             # Formal mathematical and agronomic problem formulation
│   ├── MODEL_CARD.md              # Model card documenting performance and operational scope
│   ├── PROGRESS.md                # Task tracking and milestone ledger
│   └── screenshots/               # High-resolution desktop and mobile application previews
├── frontend/                      # React 19 + TypeScript + Vite web client
│   ├── src/                       # Page components, Leaflet map views, and API connectors
│   └── package.json               # Frontend dependencies and build scripts
├── scripts/                       # Orchestration, data downloading, and verification scripts
│   ├── build_all.py               # Single master command for full end-to-end pipeline rebuild
│   ├── check_design_rules.py      # Automated linter enforcing aesthetic and design constraints
│   ├── download_weather_data.py   # Automated NASA POWER daily agroclimatology fetcher
│   ├── download_yield_data.py     # Automated ICRISAT DLD panel ingestion and harmonization
│   └── generate_test_weather.py   # Deterministic fixture generator for headless CI test runs
├── src/cropres/                   # Core Python library package
│   ├── api/                       # Flask application factory, routes, and response schemas
│   ├── data/                      # Pydantic schemas, validation rules, and spatial mappers
│   ├── features/                  # Trend estimation, PMFBY logic, and weather feature builders
│   ├── models/                    # Training routines, monotonic LightGBM, and evaluation suite
│   └── scenario/                  # Scenario perturbation engine, OOD guard, and analog search
├── tests/                         # Pytest test suite (unit, leakage, calibration, and API)
├── Dockerfile                     # Multi-stage production container configuration
├── pyproject.toml                 # Package definition and build system metadata
└── requirements.txt               # Pinned Python dependencies
```

---

## 6. Quickstart: Running Locally

### Prerequisites
- **Python:** 3.10, 3.11, or 3.12
- **Node.js:** 18+ or 20+ (with npm)
- **Git**

### Step 1: Clone and Set Up the Python Environment

```bash
# Clone the repository
git clone https://github.com/ishanvaidya01/VarhadCrop.git
cd VarhadCrop

# Create and activate a virtual environment
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Linux / macOS:
source venv/bin/activate

# Install dependencies and install package in editable mode
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### Step 2: Start the Backend API Server

```bash
python -m backend.app
```
The REST API will initialize and listen on `http://127.0.0.1:5000`. You can verify API health at `http://127.0.0.1:5000/api/health`.

### Step 3: Start the Frontend Client

In a separate terminal:

```bash
cd frontend
npm ci
npm run dev
```
Open `http://localhost:5173` in your browser to interact with the full dashboard.

---

## 7. Container Deployment with Docker

A production-ready Dockerfile is included for containerized deployment:

```bash
# Build the container image
docker build -t varhadcrop:latest .

# Run the container
docker run -d -p 5000:5000 --name varhadcrop-api varhadcrop:latest

# Verify health status
curl http://localhost:5000/api/health
```

For production deployment instructions including Nginx reverse proxy setup and systemd service configuration, refer to [docs/DEPLOY.md](docs/DEPLOY.md).

---

## 8. Reproducing the End-to-End Build Pipeline

VarhadCrop includes a single master command that executes the entire machine learning and documentation pipeline from scratch:

```bash
python -m scripts.build_all
```

This single command autonomously performs:
1. **Feature Engineering:** Computes as-of expanding trends, PMFBY indemnity baselines, and intra-seasonal agroclimatic features across all cutoff dates.
2. **Model Training:** Trains monotonic LightGBM quantile boosters, regularized Ridge panel models, and isotonic probability calibrators.
3. **Conformal Calibration:** Calibrates non-conformity scores on held-out residual blocks to generate valid prediction intervals.
4. **Held-Out Backtesting:** Generates test predictions for the 2008-2017 test block and updates `artifacts/metrics.json`.
5. **Documentation Synchronization:** Automatically refreshes `docs/EXPERIMENT_REPORT.md`, `docs/MODEL_CARD.md`, and `docs/DATA_CARD.md` directly from the newly generated metrics.

---

## 9. Testing & Quality Assurance

The codebase includes an extensive suite of automated tests verifying numerical correctness, temporal causal isolation, and API integrity:

```bash
# 1. Run all Python unit, integration, and leakage tests
pytest -v

# 2. Verify strict design rules (no buzzwords, no em dashes, no style violations)
python scripts/check_design_rules.py

# 3. Frontend linting and type-checking
cd frontend
npm run lint
npm run build
```

### Test Coverage Highlights
- **Temporal Causal Isolation:** Modifying future yields produces zero variance in past trend estimations, anomalies, or PMFBY thresholds ([test_features_and_leakage.py](tests/test_features_and_leakage.py)).
- **Cutoff Weather Isolation:** Weather events occurring after a cutoff date never contaminate feature vectors for that cutoff.
- **Monotonicity:** Extreme heat days strictly adhere to non-increasing yield anomalies in scenario perturbations.
- **Metric Verification:** Automated test asserts that all numbers in published markdown reports match `artifacts/metrics.json` without discrepancy.

---

## 10. Technical Documentation Index

| Document | Primary Audience | Key Contents |
| :--- | :--- | :--- |
| [API Specification](docs/API.md) | Developers & Integrators | OpenAPI request/response schemas for all 9 REST endpoints. |
| [Agronomic Methodology](docs/METHODOLOGY.md) | Agronomists & Researchers | Mathematical formulation of PMFBY targets, CQR, and GDD. |
| [Model Card](docs/MODEL_CARD.md) | ML Engineers & Evaluators | Model architectures, intended use, training data, and metrics. |
| [Datasheet / Data Card](docs/DATA_CARD.md) | Data Engineers & Auditors | Provenance, spatial units, preprocessing, and missingness report. |
| [Experiment Report](docs/EXPERIMENT_REPORT.md) | Reviewers & Researchers | Full ablation tables, baseline comparisons, and calibration curves. |
| [Deployment Guide](docs/DEPLOY.md) | DevOps & System Admins | Docker instructions, Nginx configuration, and scaling guide. |
| [Architectural Decisions](docs/DECISIONS.md) | Architects & Maintainers | Architecture Decision Records (ADRs) for key technical choices. |
| [Repository Audit](docs/AUDIT.md) | Project Governance | Complete record of the Phase 0 audit and refactoring findings. |

---

## 11. Known Limitations & Operational Boundaries

1. **Spatial Aggregation:** Data is harmonized at the 1966 parent district level (8 spatial units covering the 11 modern districts of Vidarbha). It is not designed to forecast field-level precision agricultural yields without high-resolution soil tests and hyper-local farm management data.
2. **Statistical Correlation vs. Crop Physiology:** Models capture empirical associations between seasonal agroclimatic features and district yield statistics. They do not simulate detailed crop physiological processes such as nutrient uptake or pest infestation.
3. **Tree Extrapolation Safeguards:** Decision trees cannot extrapolate outside observed training ranges. When scenario perturbations exceed historical bounds, the OOD guard warns the user and expands the conformal uncertainty interval.
4. **Advisory Disclaimer:** VarhadCrop provides decision-support analytics for planning and research purposes. It is not an official legal determination for insurance payouts under PMFBY. Official claims remain governed by state crop cutting experiments (CCEs).

---

## 12. License & Attribution

- **Code:** Licensed under the [MIT License](LICENSE).
- **Yield Statistics:** [ICRISAT District Level Database (DLD)](http://data.icrisat.org/dld/), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Agroclimatology:** [NASA POWER Project](https://power.larc.nasa.gov/), US Government Public Domain / Open Data.
- **Administrative Boundaries:** Adapted from Survey of India / Datameet open spatial archives.
