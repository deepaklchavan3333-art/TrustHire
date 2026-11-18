import csv
import io
import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from app import get_db
from app.services.predictor import FIELDS, MAX_FIELD, Predictor, text_hash

bp = Blueprint("main", __name__)
_predictor = None


def predictor():
    global _predictor
    model_path = current_app.config["MODEL_PATH"]
    if _predictor is None or getattr(_predictor, "_path", None) != model_path:
        _predictor = Predictor(model_path)
        _predictor._path = model_path
    return _predictor


def validate(fields):
    for key in FIELDS:
        value = fields.get(key, "")
        if not isinstance(value, (str, int, float)):
            raise ValueError(f"{key.replace('_', ' ').title()} must be text.")
        fields[key] = str(value)
        if len(fields[key]) > MAX_FIELD:
            raise ValueError(f"{key.replace('_', ' ').title()} exceeds 10,000 characters.")
    if not fields["title"].strip() or not fields["description"].strip():
        raise ValueError("Title and description are required.")
    return fields


def save(fields, result):
    db = get_db()
    db.execute(
        "INSERT INTO predictions(text_hash,label,probability_fake) VALUES(?,?,?)",
        (text_hash(fields), result["label"], result["probability_fake"]),
    )
    db.commit()


def page(filename):
    return send_from_directory(current_app.static_folder, filename)


@bp.get("/")
def home():
    return page("index.html")


@bp.get("/bulk")
def bulk_page():
    return page("bulk.html")


@bp.get("/history")
def history_page():
    return page("history.html")


@bp.get("/metrics")
def metrics_page():
    return page("metrics.html")


@bp.get("/about")
def about_page():
    return page("about.html")


@bp.post("/predict")
@bp.post("/api/predict")
def api_predict():
    if not request.is_json:
        return jsonify(error="Content-Type must be application/json"), 415
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Expected a JSON object"), 400
    try:
        fields = validate({key: data.get(key, "") for key in FIELDS})
        result = predictor().predict(fields)
        save(fields, result)
        return jsonify(result)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@bp.post("/api/bulk")
def api_bulk():
    upload = request.files.get("file")
    if not upload or not upload.filename.lower().endswith(".csv"):
        return jsonify(error="Choose a CSV file."), 400
    try:
        contents = upload.stream.read(5 * 1024 * 1024 + 1)
        if len(contents) > 5 * 1024 * 1024:
            return jsonify(error="CSV exceeds the 5 MB limit."), 413
        rows = list(csv.DictReader(io.StringIO(contents.decode("utf-8-sig"))))
        if len(rows) > 5000:
            return jsonify(error="CSV can contain at most 5,000 rows."), 400
        results = []
        for row in rows:
            try:
                fields = validate({key: row.get(key, "") for key in FIELDS})
                result = predictor().predict(fields)
                save(fields, result)
                results.append({"title": fields["title"], **result})
            except ValueError as exc:
                results.append({"title": str(row.get("title", "")), "label": "error", "probability_fake": None, "top_signals": [str(exc)]})
        return jsonify(results=results)
    except (UnicodeDecodeError, csv.Error) as exc:
        return jsonify(error=f"Could not read CSV: {exc}"), 400


@bp.get("/api/history")
def api_history():
    rows = get_db().execute(
        "SELECT id,text_hash,label,probability_fake,created_at FROM predictions ORDER BY id DESC LIMIT 100"
    ).fetchall()
    return jsonify(rows=[dict(row) for row in rows])


@bp.get("/api/metrics")
def api_metrics():
    metrics_path = Path(current_app.root_path).parent / "models" / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else None
    return jsonify(metrics=metrics, model_version=predictor().version)


@bp.get("/api/health")
def health():
    return jsonify(status="ok", model_version=predictor().version)
