"""Security alert routes."""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import Alert, ContainerRecord


alerts_bp = Blueprint("alerts", __name__)


def _serialize(alert: Alert) -> dict:
    container = db.session.get(ContainerRecord, alert.container_id) if alert.container_id else None
    return {
        "id": alert.id,
        "container_id": container.docker_id if container else None,
        "container_name": container.name if container else None,
        "rule_code": alert.rule_code,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "recommendation": alert.recommendation,
        "status": alert.status,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }


@alerts_bp.get("/alerts")
@login_required
def list_page():
    """Render open and resolved alerts."""

    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template("alerts/list.html", alerts=alerts)


@alerts_bp.get("/api/alerts")
@login_required
def list_api():
    """Return alerts as JSON."""

    status = request.args.get("status", "").upper()
    query = Alert.query.order_by(Alert.created_at.desc())
    if status in {"OPEN", "RESOLVED"}:
        query = query.filter_by(status=status)
    alerts = query.all()
    return jsonify({"alerts": [_serialize(alert) for alert in alerts], "count": len(alerts)})


@alerts_bp.post("/alerts/<int:alert_id>/resolve")
@login_required
def resolve(alert_id: int):
    """Mark an alert as resolved."""

    alert = db.session.get(Alert, alert_id)
    if alert is None:
        return jsonify({"error": "Alert not found"}), 404

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.now(timezone.utc)
    db.session.commit()
    if "application/json" in (request.headers.get("Accept") or ""):
        return jsonify(_serialize(alert))
    return redirect(url_for("alerts.list_page"))

