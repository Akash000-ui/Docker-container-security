"""Deterministic Docker configuration security rules."""

from typing import Any


def _finding(code: str, name: str, severity: str, description: str, recommendation: str) -> dict[str, str]:
    return {
        "rule_code": code,
        "rule_name": name,
        "status": "FAIL",
        "severity": severity,
        "description": description,
        "recommendation": recommendation,
    }


def analyze_container(container: dict[str, Any]) -> list[dict[str, str]]:
    """Return failed security checks for serialized Docker metadata."""

    findings = []
    user = str(container.get("user") or "").strip().lower()
    if user in {"", "0", "root", "0:0"}:
        findings.append(_finding("CFG-001", "Container runs as root", "HIGH", "The container user is root or the image default user is unspecified.", "Set a dedicated non-root USER in the image or container configuration."))

    if container.get("privileged"):
        findings.append(_finding("CFG-002", "Privileged mode enabled", "CRITICAL", "The container has extended host privileges.", "Disable privileged mode and add only the capabilities required by the workload."))

    if str(container.get("network_mode", "")).lower() == "host":
        findings.append(_finding("CFG-003", "Host network mode enabled", "HIGH", "The container shares the host network namespace.", "Use an isolated Docker network unless host networking is strictly required."))

    if str(container.get("pid_mode", "")).lower() == "host":
        findings.append(_finding("CFG-004", "Host PID mode enabled", "HIGH", "The container can see processes from the host namespace.", "Remove host PID mode and use the container's private process namespace."))

    mounts = container.get("mounts") or []
    docker_socket = any(str(mount.get("source", "")).replace("\\", "/").lower().endswith("/var/run/docker.sock") for mount in mounts)
    if docker_socket:
        findings.append(_finding("CFG-005", "Docker socket mounted", "CRITICAL", "The container can communicate directly with the Docker daemon.", "Remove the Docker socket mount or use a narrowly scoped proxy."))

    sensitive_prefixes = ("/etc", "/root", "/proc", "/sys", "/var/run")
    sensitive_mounts = [
        mount.get("source", "")
        for mount in mounts
        if str(mount.get("source", "")).replace("\\", "/").lower().startswith(sensitive_prefixes)
        and not str(mount.get("source", "")).replace("\\", "/").lower().endswith("/var/run/docker.sock")
    ]
    if sensitive_mounts:
        findings.append(_finding("CFG-006", "Sensitive host path mounted", "CRITICAL", f"Sensitive host paths are mounted into the container: {', '.join(sensitive_mounts)}.", "Remove sensitive host mounts and use a named volume or a restricted application path."))

    dangerous_capabilities = {"all", "sys_admin", "net_admin", "sys_ptrace", "sys_rawio", "dac_read_search", "sys_module"}
    capabilities = {str(cap).lower() for cap in (container.get("cap_add") or [])}
    dangerous_found = sorted(capabilities.intersection(dangerous_capabilities))
    if dangerous_found:
        findings.append(_finding("CFG-007", "Dangerous capability enabled", "HIGH", f"The container adds dangerous Linux capabilities: {', '.join(dangerous_found)}.", "Drop unnecessary capabilities and follow least privilege."))

    public_ports = []
    for port, bindings in (container.get("ports") or {}).items():
        for binding in bindings or []:
            host_ip = str(binding.get("HostIp", ""))
            if host_ip in {"", "0.0.0.0", "::"}:
                public_ports.append(port)
    if public_ports:
        findings.append(_finding("CFG-008", "Public port exposed", "MEDIUM", f"The container publishes ports to all host interfaces: {', '.join(public_ports)}.", "Bind services to a specific interface and expose only required ports."))

    if not container.get("memory_limit") and not container.get("cpu_limit"):
        findings.append(_finding("CFG-009", "Resource limits missing", "MEDIUM", "No CPU or memory limit is configured for the container.", "Set CPU and memory limits to reduce resource exhaustion risk."))

    image = str(container.get("image") or "")
    if image.endswith(":latest") or ":" not in image.rsplit("/", 1)[-1]:
        findings.append(_finding("CFG-010", "Image uses a floating tag", "LOW", "The image uses the latest tag or has no explicit version tag.", "Pin the image to a reviewed, immutable version or digest."))

    return findings

