# Fake Job Postings Detector

Flask mini project with plain HTML, CSS, and browser JavaScript. Pages are static files; Flask returns JSON for predictions, CSV processing, history, metrics, and health. No Jinja templates are used.

## Run locally

1. Install Python 3.10 or newer.
2. Create and activate a virtual environment (`python -m venv .venv`; activate it for your shell).
3. Install dependencies: `pip install -r requirements.txt`.
4. Start the app: `python run.py`, then open http://127.0.0.1:5000.

The app runs without a dataset using an explicitly labeled phrase-based fallback. For a model, place the EMSCAD CSV at `data/fake_job_postings.csv` and run `python ml/train.py`. The CSV should contain a `fraudulent` target and standard EMSCAD text columns. Training writes `models/job_model.joblib` and `models/metrics.json`; restart the app to load the model.

## Routes

- `/`: individual posting check
- `/bulk`: CSV upload (5 MB max; up to 5,000 rows)
- `/history`: recent checks (hash and verdict only)
- `/metrics`: evaluation results when trained
- `/about`: project details
- `POST /api/predict` (also `POST /predict`): JSON prediction; accepts title, location, company_profile, description, requirements, benefits, employment_type
- `POST /api/bulk`: multipart form upload under field `file`
- `GET /api/history`, `GET /api/metrics`, `GET /api/health`: JSON data endpoints

CSV headers: `title`, `location`, `company_profile`, `description`, `requirements`, `benefits`, `employment_type`. Title and description are required per row.

## Privacy and configuration

Posting text is used in memory and is not persisted. SQLite stores a SHA-256 input hash, label, probability, and timestamp. Set `SECRET_KEY`, `DATABASE`, and `MODEL_PATH` environment variables for deployment. Use a production WSGI server and a strong secret key outside local development.
