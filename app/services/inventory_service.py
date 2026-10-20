"""Synchronization of Docker inventory into SQLite."""

from datetime import datetime, timezone

from app.extensions import db
from app.models import ContainerMetric, ContainerRecord


def sync_inventory(containers: list[dict]) -> list[ContainerRecord]:
    """Upsert the latest Docker container metadata and return database records."""

    records = []
    now = datetime.now(timezone.utc)

    for container in containers:
        record = ContainerRecord.query.filter_by(docker_id=container["id"]).first()
        if record is None:
            record = ContainerRecord(docker_id=container["id"])
            db.session.add(record)

        record.name = container["name"]
        record.image = container.get("image")
        record.status = container["status"]
        record.docker_created_at = container.get("created")
        record.last_seen_at = now
        records.append(record)

    db.session.commit()
    return records


def record_metric(stats: dict) -> ContainerMetric | None:
    """Store a runtime snapshot when its inventory record is known."""

    record = ContainerRecord.query.filter_by(docker_id=stats["container_id"]).first()
    if record is None:
        return None

    metric = ContainerMetric(
        container_id=record.id,
        cpu_percent=stats["cpu_percent"],
        memory_usage=stats["memory_usage"],
        memory_limit=stats["memory_limit"],
        memory_percent=stats["memory_percent"],
        network_rx=stats["network_rx"],
        network_tx=stats["network_tx"],
        block_read=stats["block_read"],
        block_write=stats["block_write"],
    )
    db.session.add(metric)
    db.session.commit()
    return metric

