"""Persisted security analysis findings."""

from datetime import datetime, timezone

from app.extensions import db


class SecurityCheck(db.Model):
    """One rule result produced during a container security analysis."""

    __tablename__ = "security_checks"

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey("containers.id"), nullable=False, index=True)
    analysis_id = db.Column(db.String(36), nullable=False, index=True)
    rule_code = db.Column(db.String(32), nullable=False)
    rule_name = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(16), nullable=False)
    severity = db.Column(db.String(16), nullable=False)
    description = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    detected_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

