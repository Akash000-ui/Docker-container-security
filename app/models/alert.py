"""Security alert model."""

from datetime import datetime, timezone

from app.extensions import db


class Alert(db.Model):
    """Actionable alert generated from a security finding."""

    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey("containers.id"), nullable=True, index=True)
    container = db.relationship("ContainerRecord", backref="alerts")
    rule_code = db.Column(db.String(32), nullable=False, index=True)
    alert_type = db.Column(db.String(120), nullable=False)
    severity = db.Column(db.String(16), nullable=False)
    message = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(16), nullable=False, default="OPEN", index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

