"""Run and persist container security analyses."""

from datetime import datetime, timezone
from uuid import uuid4

from app.extensions import db
from app.models import ContainerRecord, SecurityCheck
from app.services.security_engine import analyze_container


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

