"""
train.py
--------
Train and evaluate the CropYieldModel in Python.
"""

from model import CropYieldModel


def main():
    print("Initializing and training CropYieldModel...")
    model = CropYieldModel()

    print("\nModel trained successfully!")
    print("-" * 35)
    print(f"Train R² Score : {model.metrics['train_r2']}")
    print(f"Test  R² Score : {model.metrics['test_r2']}")
    print(f"Test  MAE      : {model.metrics['test_mae']} kg/ha")
    print(f"Test  RMSE     : {model.metrics['test_rmse']} kg/ha")
    print("-" * 35)

    sample = model.predict(
        district="Nagpur",
        crop="Soybean",
        season="Kharif",
        area_1000ha=140,
        rainfall_mm=880,
        temp_mean_c=27.2,
        rainy_days=45,
        dry_spell_days=14,
        heat_wave_days=2,
    )
    print("\nSample Prediction (Nagpur, Soybean):")
    print(
        f"Estimated Yield: {sample['yield_kg_ha']} kg/ha (~{sample['yield_quintal_acre']} quintals/acre)"
    )


if __name__ == "__main__":
    main()
