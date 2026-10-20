"""Docker Desktop integration through the Docker SDK for Python."""

from typing import Any

import docker
from docker.errors import DockerException, NotFound


class DockerService:
    """Small, serializable wrapper around the Docker SDK."""

    def __init__(self, client: docker.DockerClient | None = None):
        self.client = client or docker.from_env()

    def ping(self) -> bool:
        """Return whether the configured Docker Engine responds."""

        return bool(self.client.ping())

    def list_containers(self) -> list[dict[str, Any]]:
        """Return all containers, including stopped containers."""

        return [self._serialize(container) for container in self.client.containers.list(all=True)]

    def get_container(self, docker_id: str) -> dict[str, Any]:
        """Return detailed metadata for one container."""

        container = self.client.containers.get(docker_id)
        return self._serialize(container, detailed=True)

    @staticmethod
    def _serialize(container: Any, detailed: bool = False) -> dict[str, Any]:
        attrs = container.attrs or {}
        config = attrs.get("Config") or {}
        host_config = attrs.get("HostConfig") or {}
        network_settings = attrs.get("NetworkSettings") or {}
        state = attrs.get("State") or {}

        mounts = [
            {
                "type": mount.get("Type"),
                "source": mount.get("Source"),
                "destination": mount.get("Destination"),
                "mode": mount.get("Mode"),
                "rw": mount.get("RW"),
            }
            for mount in attrs.get("Mounts", [])
        ]

        ports = {}
        for container_port, bindings in (network_settings.get("Ports") or {}).items():
            ports[container_port] = bindings or []

        result = {
            "id": container.id,
            "short_id": container.short_id,
            "name": container.name,
            "image": config.get("Image") or "unknown",
            "status": container.status,
            "created": attrs.get("Created"),
            "restart_policy": host_config.get("RestartPolicy") or {},
            "ports": ports,
            "networks": sorted((network_settings.get("Networks") or {}).keys()),
            "labels": config.get("Labels") or {},
        }

        if detailed:
            result.update(
                {
                    "command": config.get("Cmd") or [],
                    "entrypoint": config.get("Entrypoint") or [],
                    "user": config.get("User") or "",
                    "privileged": bool(host_config.get("Privileged", False)),
                    "cap_add": host_config.get("CapAdd") or [],
                    "cap_drop": host_config.get("CapDrop") or [],
                    "network_mode": host_config.get("NetworkMode") or "",
                    "pid_mode": host_config.get("PidMode") or "",
                    "mounts": mounts,
                    "state": state,
                }
            )

        return result


__all__ = ["DockerException", "DockerService", "NotFound"]

