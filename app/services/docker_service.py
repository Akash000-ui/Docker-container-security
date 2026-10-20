"""Docker Desktop integration through the Docker SDK for Python."""

from typing import Any
from datetime import datetime, timezone

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

    def get_stats(self, docker_id: str) -> dict[str, Any]:
        """Collect one resource snapshot from a container."""

        container = self.client.containers.get(docker_id)
        raw = container.stats(stream=False)
        cpu_stats = raw.get("cpu_stats") or {}
        previous_cpu = raw.get("precpu_stats") or {}
        cpu_usage = cpu_stats.get("cpu_usage") or {}
        previous_usage = previous_cpu.get("cpu_usage") or {}
        cpu_delta = cpu_usage.get("total_usage", 0) - previous_usage.get("total_usage", 0)
        system_delta = cpu_stats.get("system_cpu_usage", 0) - previous_cpu.get("system_cpu_usage", 0)
        online_cpus = cpu_stats.get("online_cpus") or len(cpu_usage.get("percpu_usage") or []) or 1
        cpu_percent = (cpu_delta / system_delta) * online_cpus * 100 if system_delta > 0 else 0.0

        memory_stats = raw.get("memory_stats") or {}
        memory_usage = memory_stats.get("usage", 0)
        memory_limit = memory_stats.get("limit", 0)
        memory_percent = (memory_usage / memory_limit) * 100 if memory_limit else 0.0

        network_rx = 0
        network_tx = 0
        for network in (raw.get("networks") or {}).values():
            network_rx += network.get("rx_bytes", 0)
            network_tx += network.get("tx_bytes", 0)

        block_read = 0
        block_write = 0
        for item in raw.get("blkio_stats", {}).get("io_service_bytes_recursive") or []:
            operation = (item.get("op") or "").lower()
            if operation == "read":
                block_read += item.get("value", 0)
            elif operation == "write":
                block_write += item.get("value", 0)

        return {
            "container_id": container.id,
            "status": container.status,
            "cpu_percent": round(max(cpu_percent, 0), 2),
            "memory_usage": memory_usage,
            "memory_limit": memory_limit,
            "memory_percent": round(max(memory_percent, 0), 2),
            "network_rx": network_rx,
            "network_tx": network_tx,
            "block_read": block_read,
            "block_write": block_write,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_processes(self, docker_id: str) -> dict[str, Any]:
        """Return the process table reported by Docker."""

        return self.client.containers.get(docker_id).top()

    def get_logs(self, docker_id: str, tail: int = 200) -> str:
        """Return recent timestamped logs for a container."""

        bounded_tail = max(1, min(tail, 1000))
        logs = self.client.containers.get(docker_id).logs(tail=bounded_tail, timestamps=True)
        return logs.decode("utf-8", errors="replace")

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

