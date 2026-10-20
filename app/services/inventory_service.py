"""Synchronization of Docker inventory into SQLite."""

from datetime import datetime, timezone

from app.extensions import db
from app.models import ContainerRecord


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

