import sqlite3
from pathlib import Path
from flask import Flask, g
from config import Config

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db

from flask import current_app

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    with app.app_context():
        db = get_db()
        db.executescript('''CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY, text_hash TEXT NOT NULL, label TEXT NOT NULL,
            probability_fake REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS feedback (id INTEGER PRIMARY KEY,
            prediction_id INTEGER REFERENCES predictions(id), is_correct INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);''')
        db.commit()
    @app.teardown_appcontext
    def close_db(exc):
        db = g.pop("db", None)
        if db is not None: db.close()
    from app.routes import bp
    app.register_blueprint(bp)
    @app.errorhandler(413)
    def too_large(_): return "Upload exceeds the 5 MB limit.", 413
    return app


