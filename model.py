"""
model.py
--------
Pure Python Machine Learning model for Crop Yield Prediction.
Loads historical agricultural and weather data, trains a Random Forest
regression pipeline, and provides an easy-to-use prediction method.
"""

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_absolute_error, root_mean_squared_error


class CropYieldModel:
    """
    Crop Yield Prediction Model for Vidarbha, Maharashtra.
    """

    def __init__(self, data_path="data/crop_yield_data.csv"):
        self.data_path = data_path
        self.pipeline = None
        self.metrics = {}
        self.districts = []
        self.crops = []
        self.seasons = []

        self.cat_features = ["district", "crop", "season"]
        self.num_features = [
            "area_1000ha",
            "rainfall_mm",
            "temp_mean_c",
            "rainy_days",
            "dry_spell_days",
            "heat_wave_days",
        ]

        if os.path.exists(self.data_path):
            self.train()
        else:
            raise FileNotFoundError(f"Dataset not found at {self.data_path}")

    def train(self):
        """Loads data, prepares pipeline, and trains the model."""
        df = pd.read_csv(self.data_path)

        self.districts = sorted(df["district"].unique().tolist())
        self.crops = sorted(df["crop"].unique().tolist())
        self.seasons = sorted(df["season"].unique().tolist())

        X = df[self.cat_features + self.num_features]
        y = df["yield_kg_ha"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        preprocessor = ColumnTransformer(
            transformers=[
                ("cat", OneHotEncoder(handle_unknown="ignore"), self.cat_features),
                ("num", StandardScaler(), self.num_features),
            ]
        )

        self.pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                (
                    "regressor",
                    RandomForestRegressor(
                        n_estimators=100,
                        max_depth=16,
                        min_samples_split=4,
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        )

        self.pipeline.fit(X_train, y_train)

        # Evaluate performance on test data
        train_preds = self.pipeline.predict(X_train)
        test_preds = self.pipeline.predict(X_test)

        self.metrics = {
            "train_r2": round(r2_score(y_train, train_preds), 4),
            "test_r2": round(r2_score(y_test, test_preds), 4),
            "test_mae": round(mean_absolute_error(y_test, test_preds), 2),
            "test_rmse": round(root_mean_squared_error(y_test, test_preds), 2),
        }

    def predict(
        self,
        district: str,
        crop: str,
        season: str,
        area_1000ha: float,
        rainfall_mm: float,
        temp_mean_c: float,
        rainy_days: int,
        dry_spell_days: int,
        heat_wave_days: int,
    ) -> dict:
        """
        Predict crop yield given agricultural and weather parameters.
        Returns predicted yield in kg/ha and quintals/acre.
        """
        if self.pipeline is None:
            raise RuntimeError("Model is not trained.")

        input_data = pd.DataFrame(
            [
                {
                    "district": district,
                    "crop": crop,
                    "season": season,
                    "area_1000ha": float(area_1000ha),
                    "rainfall_mm": float(rainfall_mm),
                    "temp_mean_c": float(temp_mean_c),
                    "rainy_days": int(rainy_days),
                    "dry_spell_days": int(dry_spell_days),
                    "heat_wave_days": int(heat_wave_days),
                }
            ]
        )

        pred_kg_ha = float(self.pipeline.predict(input_data)[0])
        pred_kg_ha = max(0.0, round(pred_kg_ha, 2))
        pred_quintal_acre = round((pred_kg_ha / 100.0) / 2.471, 2)

        return {
            "yield_kg_ha": pred_kg_ha,
            "yield_quintal_acre": pred_quintal_acre,
        }


if __name__ == "__main__":
    print("Initializing CropYieldModel from data/crop_yield_data.csv...")
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
    print("\nSample Prediction:")
    print(f"Nagpur Soybean (Kharif): {sample['yield_kg_ha']} kg/ha (~{sample['yield_quintal_acre']} quintals/acre)")

