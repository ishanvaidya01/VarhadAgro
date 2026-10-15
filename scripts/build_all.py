import os
import sys
import time

from cropres.features.builder import build_feature_table
from cropres.models.train import train_models_pipeline
from cropres.models.evaluate import run_evaluation
from scripts.generate_model_docs import generate_docs
from scripts.generate_data_card import generate_data_card

def build_all():
    t_start = time.time()
    print("==================================================================")
    print("VarhadCrop: Full End-to-End Build Pipeline")
    print("==================================================================")
    
    # Step 1: Ingest & Build Features
    print("\n[Step 1/4] Building leakage-free feature table from observed data...")
    feature_df = build_feature_table()
    print(f"Feature table built: {len(feature_df)} rows across all cutoffs.")
    
    # Step 2: Train Models & Uncertainty Calibration
    print("\n[Step 2/4] Training models and calibrating uncertainty...")
    train_results = train_models_pipeline()
    print("Models and CQR parameters saved to artifacts/models and artifacts/conformal.")
    
    # Step 3: Evaluate on Final Held-Out Test Block (2008-2017)
    print("\n[Step 3/4] Evaluating models and generating backtest predictions...")
    metrics = run_evaluation()
    print(f"Metrics generated: RMSE skill score = {metrics['regression']['lightgbm_median']['skill_score']*100:.1f}%, CQR overall coverage = {metrics['uncertainty_conformal_cqr']['empirical_coverage_overall']*100:.1f}%.")
    
    # Step 4: Auto-Generate Documentation from Artifacts
    print("\n[Step 4/4] Auto-generating documentation and data cards...")
    generate_docs()
    generate_data_card()
    print("Updated docs/EXPERIMENT_REPORT.md, docs/MODEL_CARD.md, and docs/DATA_CARD.md.")
    
    elapsed = time.time() - t_start
    print(f"\n==================================================================")
    print(f"Build completed successfully in {elapsed:.1f} seconds.")
    print("==================================================================")

if __name__ == "__main__":
    build_all()
