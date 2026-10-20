"""Initial application routes."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template

from app.extensions import db


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    """Show the initial dashboard during the foundation phase."""

    return render_template("dashboard.html")


@main_bp.get("/dashboard")
def dashboard():
    """Render the dashboard landing page."""

    return render_template("dashboard.html")


@main_bp.get("/health")
def health():
    """Return application and database health for local verification."""

    database_status = "ok"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db.session.rollback()
        database_status = "error"

    status_code = 200 if database_status == "ok" else 503
    return jsonify(
        {
            "status": "ok" if status_code == 200 else "degraded",
            "database": database_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ), status_code

