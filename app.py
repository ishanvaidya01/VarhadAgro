from flask import Flask, render_template, request, jsonify
from model import CropYieldModel

app = Flask(__name__)

# Initialize model in Python (loads dataset and trains in < 0.3s)
model = CropYieldModel()


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        districts=model.districts,
        crops=model.crops,
        seasons=model.seasons,
        metrics=model.metrics,
        inputs={},
        prediction=None,
    )


@app.route("/predict", methods=["POST"])
def predict():
    is_json = request.is_json
    data = request.get_json() if is_json else request.form

    try:
        district = data.get("district", "Nagpur")
        crop = data.get("crop", "Soybean")
        season = data.get("season", "Kharif")
        area_1000ha = float(data.get("area_1000ha", 100.0))
        rainfall_mm = float(data.get("rainfall_mm", 800.0))
        temp_mean_c = float(data.get("temp_mean_c", 26.5))
        rainy_days = int(float(data.get("rainy_days", 45)))
        dry_spell_days = int(float(data.get("dry_spell_days", 14)))
        heat_wave_days = int(float(data.get("heat_wave_days", 2)))

        result = model.predict(
            district=district,
            crop=crop,
            season=season,
            area_1000ha=area_1000ha,
            rainfall_mm=rainfall_mm,
            temp_mean_c=temp_mean_c,
            rainy_days=rainy_days,
            dry_spell_days=dry_spell_days,
            heat_wave_days=heat_wave_days,
        )

        inputs_summary = {
            "district": district,
            "crop": crop,
            "season": season,
            "area_1000ha": area_1000ha,
            "rainfall_mm": rainfall_mm,
            "temp_mean_c": temp_mean_c,
            "rainy_days": rainy_days,
            "dry_spell_days": dry_spell_days,
            "heat_wave_days": heat_wave_days,
        }

        if is_json:
            return jsonify(
                {
                    "status": "success",
                    "predicted_yield_kg_ha": result["yield_kg_ha"],
                    "predicted_yield_quintal_acre": result["yield_quintal_acre"],
                    "inputs": inputs_summary,
                }
            )

        return render_template(
            "index.html",
            districts=model.districts,
            crops=model.crops,
            seasons=model.seasons,
            metrics=model.metrics,
            inputs=inputs_summary,
            prediction={
                "kg_ha": result["yield_kg_ha"],
                "quintal_acre": result["yield_quintal_acre"],
            },
        )

    except Exception as e:
        if is_json:
            return jsonify({"status": "error", "message": str(e)}), 400
        return render_template(
            "index.html",
            districts=model.districts,
            crops=model.crops,
            seasons=model.seasons,
            metrics=model.metrics,
            inputs={},
            error=f"Prediction error: {str(e)}",
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
