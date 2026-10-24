"""Build security report data and CSV exports."""

import csv
import io
from collections import Counter
from datetime import datetime, timezone

from app.models import Alert, ContainerRecord, ImageScan, SecurityCheck, Vulnerability


SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


def _counts(values) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITIES}
    for value in values:
        if value in counts:
            counts[value] += 1
    return counts


def build_security_report() -> dict:
    """Return a serializable security overview and detailed findings."""

    containers = ContainerRecord.query.order_by(ContainerRecord.name.asc()).all()
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    checks = SecurityCheck.query.filter_by(status="FAIL").order_by(SecurityCheck.detected_at.desc()).all()
    vulnerabilities = Vulnerability.query.order_by(Vulnerability.id.desc()).all()
    scans = ImageScan.query.order_by(ImageScan.created_at.desc()).all()

    return {
        "generated_at": datetime.now(timezone.utc),
        "summary": {
            "containers": len(containers),
            "running_containers": sum(container.status == "running" for container in containers),
            "open_alerts": sum(alert.status == "OPEN" for alert in alerts),
            "resolved_alerts": sum(alert.status == "RESOLVED" for alert in alerts),
            "failed_checks": len(checks),
            "vulnerabilities": len(vulnerabilities),
            "scans": len(scans),
        },
        "container_status": dict(Counter(container.status for container in containers)),
        "alert_severity": _counts(alert.severity for alert in alerts if alert.status == "OPEN"),
        "vulnerability_severity": _counts(vulnerability.severity for vulnerability in vulnerabilities),
        "containers": containers,
        "alerts": alerts,
        "checks": checks,
        "vulnerabilities": vulnerabilities,
        "scans": scans,
    }


def security_report_csv(report: dict) -> str:
    """Render report findings as a portable CSV document."""

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Container Security Monitoring Report"])
    writer.writerow(["Generated at", report["generated_at"].isoformat()])
    writer.writerow([])
    writer.writerow(["Summary", "Count"])
    for key, value in report["summary"].items():
        writer.writerow([key.replace("_", " ").title(), value])
    writer.writerow([])
    writer.writerow(["Category", "Asset", "Severity", "Status", "Identifier", "Details", "Recommendation", "Timestamp"])

    for alert in report["alerts"]:
        container_name = alert.container.name if alert.container else "-"
        writer.writerow([
            "Alert", container_name, alert.severity, alert.status, alert.rule_code,
            alert.message, alert.recommendation, alert.created_at.isoformat() if alert.created_at else "",
        ])
    for check in report["checks"]:
        writer.writerow([
            "Container check", check.container_id, check.severity, check.status, check.rule_code,
            check.description, check.recommendation, check.detected_at.isoformat() if check.detected_at else "",
        ])
    for vulnerability in report["vulnerabilities"]:
        writer.writerow([
            "Library vulnerability", vulnerability.image_scan.image_name, vulnerability.severity,
            vulnerability.image_scan.scan_status, vulnerability.cve_id or "-",
            vulnerability.title or vulnerability.description or "", vulnerability.fixed_version or "Not available", "",
        ])
    return output.getvalue()
