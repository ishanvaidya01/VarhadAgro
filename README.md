# VarhadAgro - Crop Yield Prediction

A simple machine learning project to predict crop yields for districts across Vidarbha, Maharashtra based on seasonal weather conditions and cultivated area.

## Overview

The model estimates crop yield in **kg/hectare** (and equivalent **quintals/acre**) using historical agricultural and meteorological observations.

- **Districts:** Akola, Amravati, Bhandara, Buldhana, Chandrapur, Nagpur, Wardha, Yavatmal
- **Crops:** Chickpea, Cotton, Pigeonpea, Rice, Sorghum, Soybean, Wheat
- **Seasons:** Kharif, Rabi
- **Input Features:** District, crop, season, cultivated area (1,000 ha), total rainfall (mm), mean temperature (°C), rainy days, longest dry spell (days), and heatwave days (>38°C).

## Project Structure

```
VarhadAgro/
│
├── data/
│   └── crop_yield_data.csv     # Clean historical dataset (2,035 records)
├── templates/
│   └── index.html              # Clean web interface
├── app.py                      # Flask web application & REST API
├── model.py                    # Pure Python ML model definition & predictor
├── train.py                    # Evaluation & testing script
├── requirements.txt            # Python dependencies (Flask, pandas, scikit-learn)
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run / Test the Python Model

Run the model script directly to train, evaluate, and test sample predictions in Python:

```bash
python model.py
```

Output:
```text
Initializing CropYieldModel from data/crop_yield_data.csv...

Model trained successfully!
-----------------------------------
Train R² Score : 0.9269
Test  R² Score : 0.7484
Test  MAE      : 170.45 kg/ha
Test  RMSE     : 244.00 kg/ha
-----------------------------------

Sample Prediction:
Nagpur Soybean (Kharif): 925.64 kg/ha (~3.75 quintals/acre)
```

### 3. Run the Web Application

```bash
python app.py
```

Open your browser and navigate to `http://localhost:5000`. You can test sample presets with one click (e.g. *Nagpur Soybean*, *Akola Cotton*) or enter custom weather values to see yield predictions.

## API Usage

The application also exposes a JSON endpoint for predictions at `/predict`:

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "district": "Nagpur",
    "crop": "Soybean",
    "season": "Kharif",
    "area_1000ha": 140,
    "rainfall_mm": 880,
    "temp_mean_c": 27.2,
    "rainy_days": 45,
    "dry_spell_days": 14,
    "heat_wave_days": 2
  }'
```

Response:
```json
{
  "status": "success",
  "predicted_yield_kg_ha": 925.64,
  "predicted_yield_quintal_acre": 3.75,
  "inputs": {
    "district": "Nagpur",
    "crop": "Soybean",
    "season": "Kharif",
    "area_1000ha": 140.0,
    "rainfall_mm": 880.0,
    "temp_mean_c": 27.2,
    "rainy_days": 45,
    "dry_spell_days": 14,
    "heat_wave_days": 2
  }
}
```

## License

MIT License. See [LICENSE](LICENSE) for details.
