import os
import logging
from typing import Any
from flask import Flask, request, jsonify, Blueprint, send_from_directory
from flask_cors import CORS
from pydantic import ValidationError

from cropres.api.service import ArtifactService
from cropres.api.schemas import ScenarioRequest, AnalogRequest

logger = logging.getLogger("cropres.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

api_bp = Blueprint("cropres_api", __name__, url_prefix="/api")


def structured_error(code: str, message: str, status_code: int = 400, details: Any = None):
    response = {
        "error": code,
        "message": message
    }
    if details is not None:
        response["details"] = details
    return jsonify(response), status_code


# ── Routes ───────────────────────────────────────────────────────────────────

@api_bp.route("/health", methods=["GET"])
def health():
    service = ArtifactService.get_instance()
    return jsonify({
        "status": "ok",
        "service": "VarhadCrop API",
        "districts_loaded": len(service.boundaries_geojson["features"]),
        "records_loaded": len(service.backtest_df)
    })


@api_bp.route("/meta", methods=["GET"])
def get_meta():
    service = ArtifactService.get_instance()
    return jsonify(service.get_meta())


@api_bp.route("/districts", methods=["GET"])
@api_bp.route("/regions", methods=["GET"])  # Alias for compatibility
def get_districts():
    service = ArtifactService.get_instance()
    return jsonify(service.get_districts())


@api_bp.route("/crops", methods=["GET"])
def get_crops():
    service = ArtifactService.get_instance()
    return jsonify(service.get_crops())


@api_bp.route("/risk-map", methods=["GET"])
def get_risk_map():
    crop = request.args.get("crop", "Cotton").strip()
    cutoff = request.args.get("cutoff", None)
    year_str = request.args.get("year", None)
    year = int(year_str) if year_str and year_str.isdigit() else None

    service = ArtifactService.get_instance()
    try:
        data = service.get_risk_map(crop=crop, cutoff=cutoff, year=year)
        return jsonify(data)
    except ValueError as e:
        return structured_error("invalid_parameter", str(e), status_code=400)


@api_bp.route("/district/<district_id>", methods=["GET"])
def get_district_detail(district_id: str):
    crop = request.args.get("crop", "").strip()
    if not crop:
        return structured_error("missing_parameter", "Query parameter 'crop' is required.", status_code=400)

    service = ArtifactService.get_instance()
    try:
        data = service.get_district_detail(district=district_id, crop=crop)
        return jsonify(data)
    except ValueError as e:
        return structured_error("not_found", str(e), status_code=404)


@api_bp.route("/yield-history", methods=["GET"])
def yield_history_compat():
    district = (request.args.get("district") or request.args.get("region") or "").strip()
    crop = request.args.get("crop", "").strip()
    if not district or not crop:
        return structured_error("missing_parameter", "'district' (or 'region') and 'crop' parameters are required.", status_code=400)

    service = ArtifactService.get_instance()
    try:
        data = service.get_district_detail(district=district, crop=crop)
        return jsonify(data)
    except ValueError as e:
        return structured_error("not_found", str(e), status_code=404)


@api_bp.route("/early-warning", methods=["GET"])
def early_warning():
    crop = request.args.get("crop", "Cotton").strip()
    district = request.args.get("district", None)

    service = ArtifactService.get_instance()
    try:
        data = service.get_early_warning_and_season(crop=crop, district=district)
        return jsonify(data)
    except ValueError as e:
        return structured_error("invalid_parameter", str(e), status_code=400)


@api_bp.route("/scenario", methods=["POST"])
@api_bp.route("/climate-scenario", methods=["POST"])  # Alias for compatibility
def run_scenario():
    body = request.get_json(silent=True)
    if not body:
        return structured_error("empty_body", "JSON request body required.", status_code=400)

    # Allow 'region' as alias for 'district'
    if "region" in body and "district" not in body:
        body["district"] = body["region"]

    try:
        req = ScenarioRequest(**body)
    except ValidationError as e:
        clean_errors = [{"loc": list(err["loc"]), "msg": str(err["msg"]), "type": str(err["type"])} for err in e.errors()]
        return structured_error("validation_error", "Request validation failed", status_code=400, details=clean_errors)

    service = ArtifactService.get_instance()
    try:
        res = service.run_scenario(
            district=req.district,
            crop=req.crop,
            temp_shift=req.temp_shift,
            precip_shift=req.precip_shift,
            heat_days_shift=req.heat_days_shift,
            history_years=req.history_years
        )
        return jsonify(res)
    except Exception as e:
        logger.exception("Scenario execution error")
        return structured_error("scenario_error", str(e), status_code=500)


@api_bp.route("/reliability", methods=["GET"])
def crop_reliability():
    district = request.args.get("district", "Akola").strip()
    service = ArtifactService.get_instance()
    try:
        data = service.get_crop_reliability(district=district)
        return jsonify(data)
    except ValueError as e:
        return structured_error("invalid_parameter", str(e), status_code=400)


@api_bp.route("/analogs", methods=["GET", "POST"])
def climate_analogs():
    service = ArtifactService.get_instance()
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        try:
            req = AnalogRequest(**body)
            data = service.get_analogs(
                district=req.district,
                temp_shift=req.temp_shift,
                precip_shift=req.precip_shift,
                heat_days_shift=req.heat_days_shift,
                top_k=req.top_k
            )
            return jsonify(data)
        except ValidationError as e:
            clean_errors = [{"loc": list(err["loc"]), "msg": str(err["msg"]), "type": str(err["type"])} for err in e.errors()]
            return structured_error("validation_error", "Validation failed", status_code=400, details=clean_errors)
    else:
        dist = request.args.get("district", "Akola").strip()
        t_shift = float(request.args.get("temp_shift", 0.0))
        p_shift = float(request.args.get("precip_shift", 0.0))
        h_shift = int(request.args.get("heat_days_shift", 0))
        top_k = int(request.args.get("top_k", 4))
        try:
            data = service.get_analogs(
                district=dist,
                temp_shift=t_shift,
                precip_shift=p_shift,
                heat_days_shift=h_shift,
                top_k=top_k
            )
            return jsonify(data)
        except ValueError as e:
            return structured_error("invalid_parameter", str(e), status_code=400)


@api_bp.route("/evidence", methods=["GET"])
@api_bp.route("/model-metrics", methods=["GET"])  # Alias for compatibility
@api_bp.route("/data-quality", methods=["GET"])   # Alias for compatibility
def get_evidence():
    service = ArtifactService.get_instance()
    return jsonify(service.get_evidence())


def create_app(config: dict = None) -> Flask:
    app = Flask(__name__)
    if config:
        app.config.update(config)

    # CORS configuration
    cors_origin = os.getenv("CORS_ORIGIN", "*")
    CORS(app, resources={r"/api/*": {"origins": cors_origin}})

    app.register_blueprint(api_bp)

    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "dist"))

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_spa(path):
        if path.startswith("api/"):
            return structured_error("not_found", "The requested API endpoint was not found.", status_code=404)
        if os.path.exists(dist_dir):
            target_path = os.path.join(dist_dir, path)
            if path and os.path.exists(target_path) and os.path.isfile(target_path):
                return send_from_directory(dist_dir, path)
            index_path = os.path.join(dist_dir, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(dist_dir, "index.html")
        return structured_error("not_found", "The requested API endpoint was not found.", status_code=404)

    @app.errorhandler(404)
    def handle_404(e):
        return structured_error("not_found", "The requested API endpoint was not found.", status_code=404)

    @app.errorhandler(500)
    def handle_500(e):
        return structured_error("internal_error", "An internal server error occurred.", status_code=500)

    return app
