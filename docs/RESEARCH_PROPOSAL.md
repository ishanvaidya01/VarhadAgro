# Research Proposal

## Problem Statement
Current agricultural yield models prioritize maximizing next-year yield prediction (R²) but frequently fail to estimate tail risk (downside events) and lack proper uncertainty calibration under shifting climate conditions.

## Hypothesis
Integrating a machine learning approach (LightGBM) with split-conformal prediction alongside fixed-effects panel regression will provide a superior, calibrated estimation of downside crop risk and allow for reliable ranking of crop resilience.

## Related Work
- Blanc & Schlenker (2017) demonstrated the utility of panel regression for capturing marginal temperature impacts.
- Crane-Droesch (2018) highlighted machine learning's capability in non-linear climate interactions.

## Proposed Contribution
VarhadCrop uniquely combines a transparent index with split-conformal bounds and explicitly optimizes for tail risk classification (PR-AUC) over simple R², evaluated strictly via chronological holding.

## Datasets
- (Planned) ICRISAT District Level Data / FAOSTAT.
- Current validation uses a 30-year synthetic dataset simulating weather impacts on 5 crop varieties across 10 regions.

## Methodology & Experimental Design
1. **Detrending:** LOESS fitted strictly on training spans (<= 2018).
2. **Models:** Panel Fixed-Effects (OLS) and LightGBM.
3. **Evaluation:** Chronological holdout (>2018). Metrics include MAE, Skill Score, and Split-Conformal empirical coverage.

## Limitations and Future Work
Synthetic data cannot validate real-world agronomic interactions. Future work requires resolving API access to ingest real global weather grids (NASA POWER) and historical district yields.
