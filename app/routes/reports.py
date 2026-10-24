"""Security report and dashboard summary routes."""

from flask import Blueprint, Response, jsonify, render_template
from flask_login import login_required

from app.services.report_service import build_security_report, security_report_csv


reports_bp = Blueprint("reports", __name__)


def _iso(value):
    return value.isoformat() if value else None


@reports_bp.get("/api/dashboard/summary")
@login_required
def dashboard_summary():
    """Return chart-ready dashboard aggregates."""

    report = build_security_report()
    return jsonify({
        "summary": report["summary"],
        "container_status": report["container_status"],
        "alert_severity": report["alert_severity"],
        "vulnerability_severity": report["vulnerability_severity"],
        "generated_at": _iso(report["generated_at"]),
    })


@reports_bp.get("/reports/security")
@login_required
def security_report():
    """Render the administrator security report."""

    return render_template("reports/security.html", report=build_security_report())


@reports_bp.get("/reports/security.csv")
@login_required
def security_report_csv_download():
    """Download the current security report as CSV."""

    report = build_security_report()
    return Response(
        security_report_csv(report),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=container-security-report.csv"},
    )
