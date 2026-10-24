"""Trivy vulnerability scan routes."""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app.extensions import db
from app.models import ImageScan, Vulnerability
from app.services.docker_service import DockerException, DockerService
from app.services.trivy_service import TrivyError, TrivyService
from app.services.vulnerability_service import scan_and_store


vulnerabilities_bp = Blueprint("vulnerabilities", __name__)


def _serialize_scan(scan: ImageScan) -> dict:
    return {
        "id": scan.id,
        "image_name": scan.image_name,
        "scan_status": scan.scan_status,
        "scanner": scan.scanner,
        "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None,
        "error_message": scan.error_message,
        "total_vulnerabilities": scan.total_vulnerabilities,
        "severity_counts": _severity_counts(scan.vulnerabilities),
        "vulnerabilities": [_serialize_vulnerability(item) for item in scan.vulnerabilities],
    }


def _serialize_vulnerability(item: Vulnerability) -> dict:
    return {
        "id": item.id,
        "cve_id": item.cve_id,
        "package_name": item.package_name,
        "installed_version": item.installed_version,
        "fixed_version": item.fixed_version,
        "severity": item.severity,
        "title": item.title,
        "description": item.description,
        "target": item.target,
    }


def _severity_counts(items) -> dict[str, int]:
    counts = {severity: 0 for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")}
    for item in items:
        if item.severity in counts:
            counts[item.severity] += 1
    return counts


@vulnerabilities_bp.get("/vulnerabilities")
@login_required
def list_page():
    """Render local images, scan history, and the latest vulnerability results."""

    images = []
    docker_error = None
    try:
        images = DockerService().list_images()
    except DockerException as error:
        docker_error = str(error)

    scans = ImageScan.query.order_by(ImageScan.created_at.desc()).limit(20).all()
    return render_template(
        "vulnerabilities/list.html",
        images=images,
        scans=scans,
        docker_error=docker_error,
        prefill_image=request.args.get("image", ""),
    )


@vulnerabilities_bp.post("/vulnerabilities/scan")
@login_required
def scan_form():
    """Run a scan submitted from the dashboard form."""

    image_name = request.form.get("image_name", "").strip()
    try:
        scan = scan_and_store(image_name)
        flash(f"Scan completed for {scan.image_name}: {scan.total_vulnerabilities} vulnerabilities found.", "success")
    except (TrivyError, ValueError) as error:
        flash(f"Scan failed: {error}", "error")
    return redirect(url_for("vulnerabilities.list_page"))


@vulnerabilities_bp.post("/api/images/<path:image_name>/scan")
@login_required
def scan_api(image_name: str):
    """Run a Trivy scan and return the stored result."""

    try:
        scan = scan_and_store(image_name)
        return jsonify(_serialize_scan(scan)), 201
    except (TrivyError, ValueError) as error:
        return jsonify({"error": "Image scan failed", "detail": str(error)}), 502


@vulnerabilities_bp.get("/api/scans/<int:scan_id>")
@login_required
def scan_api_detail(scan_id: int):
    """Return one stored scan and its vulnerabilities."""

    scan = db.session.get(ImageScan, scan_id)
    if scan is None:
        return jsonify({"error": "Scan not found"}), 404
    return jsonify(_serialize_scan(scan))


@vulnerabilities_bp.get("/api/vulnerabilities")
@login_required
def vulnerabilities_api():
    """Return stored vulnerabilities, optionally filtered by severity."""

    severity = request.args.get("severity", "").upper()
    query = Vulnerability.query.order_by(Vulnerability.id.desc())
    if severity:
        query = query.filter_by(severity=severity)
    items = query.limit(500).all()
    return jsonify({"vulnerabilities": [_serialize_vulnerability(item) for item in items], "count": len(items)})

