"""Initial application routes."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, render_template
from flask_login import login_required

from app.extensions import db
from app.models import Alert, Vulnerability
from app.services.docker_service import DockerException, DockerService
from app.services.inventory_service import sync_inventory


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
@login_required
def index():
    """Show the initial dashboard during the foundation phase."""

    return render_template("dashboard.html")


@main_bp.get("/dashboard")
@login_required
def dashboard():
    """Render the dashboard with the current Docker inventory summary."""

    containers = []
    docker_error = None
    try:
        containers = DockerService().list_containers()
        sync_inventory(containers)
    except DockerException as error:
        docker_error = str(error)

    running = sum(container["status"] == "running" for container in containers)
    return render_template(
        "dashboard.html",
        containers=containers[:5],
        total_containers=len(containers),
        running_containers=running,
        stopped_containers=len(containers) - running,
        open_alerts=Alert.query.filter_by(status="OPEN").count(),
        vulnerability_count=Vulnerability.query.count(),
        docker_error=docker_error,
    )


@main_bp.get("/health")
def health():
    """Return application and database health for local verification."""

    database_status = "ok"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception:
        db.session.rollback()
        database_status = "error"

    docker_status = "ok"
    try:
        DockerService().ping()
    except DockerException:
        docker_status = "unavailable"

    status_code = 200 if database_status == "ok" and docker_status == "ok" else 503
    return jsonify(
        {
            "status": "ok" if status_code == 200 else "degraded",
            "database": database_status,
            "docker": docker_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ), status_code

