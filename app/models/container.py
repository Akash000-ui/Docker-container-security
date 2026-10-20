"""Persisted Docker container inventory records."""

from datetime import datetime, timezone

from app.extensions import db


class ContainerRecord(db.Model):
    """Latest known metadata for a Docker container."""

    __tablename__ = "containers"

    id = db.Column(db.Integer, primary_key=True)
    docker_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    docker_created_at = db.Column(db.String(64), nullable=True)
    last_seen_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<ContainerRecord {self.name!r} {self.status!r}>"


class ContainerMetric(db.Model):
    """A point-in-time runtime resource snapshot."""

    __tablename__ = "container_metrics"

    id = db.Column(db.Integer, primary_key=True)
    container_id = db.Column(db.Integer, db.ForeignKey("containers.id"), nullable=False, index=True)
    cpu_percent = db.Column(db.Float, nullable=False, default=0)
    memory_usage = db.Column(db.BigInteger, nullable=False, default=0)
    memory_limit = db.Column(db.BigInteger, nullable=False, default=0)
    memory_percent = db.Column(db.Float, nullable=False, default=0)
    network_rx = db.Column(db.BigInteger, nullable=False, default=0)
    network_tx = db.Column(db.BigInteger, nullable=False, default=0)
    block_read = db.Column(db.BigInteger, nullable=False, default=0)
    block_write = db.Column(db.BigInteger, nullable=False, default=0)
    captured_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
