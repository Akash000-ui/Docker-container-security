"""Run and persist container security analyses."""

from datetime import datetime, timezone
from uuid import uuid4

from app.extensions import db
from app.models import Alert, ContainerRecord, SecurityCheck
from app.services.security_engine import analyze_container
from app.services.scoring_service import calculate_score


def analyze_and_store(docker_id: str, container: dict) -> tuple[str, list[dict]]:
    """Evaluate a container and persist the results for this analysis run."""

    record = ContainerRecord.query.filter_by(docker_id=docker_id).first()
    if record is None:
        raise ValueError("Container must be synchronized before security analysis.")

    analysis_id = str(uuid4())
    detected_at = datetime.now(timezone.utc)
    findings = analyze_container(container)
    for finding in findings:
        db.session.add(
            SecurityCheck(
                container_id=record.id,
                analysis_id=analysis_id,
                detected_at=detected_at,
                **finding,
            )
        )
    db.session.commit()
    return analysis_id, findings


def run_security_analysis(docker_id: str, container: dict) -> dict:
    """Analyze, score, and alert on a container configuration."""

    analysis_id, findings = analyze_and_store(docker_id, container)
    score = calculate_score(findings)
    record = ContainerRecord.query.filter_by(docker_id=docker_id).first()
    alerts = []

    for finding in findings:
        alert = Alert.query.filter_by(
            container_id=record.id,
            rule_code=finding["rule_code"],
            status="OPEN",
        ).first()
        if alert is None:
            alert = Alert(
                container_id=record.id,
                rule_code=finding["rule_code"],
                alert_type=finding["rule_name"],
                severity=finding["severity"],
                message=finding["description"],
                recommendation=finding["recommendation"],
                status="OPEN",
            )
            db.session.add(alert)
        else:
            alert.severity = finding["severity"]
            alert.message = finding["description"]
            alert.recommendation = finding["recommendation"]
        alerts.append(alert)

    db.session.commit()
    return {
        "analysis_id": analysis_id,
        "findings": findings,
        **score,
        "alerts": [
            {
                "id": alert.id,
                "rule_code": alert.rule_code,
                "severity": alert.severity,
                "status": alert.status,
            }
            for alert in alerts
        ],
    }

