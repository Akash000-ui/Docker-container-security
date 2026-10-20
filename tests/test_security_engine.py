"""Unit tests for Phase 6 security rules."""

from app.services.security_engine import analyze_container


def test_secure_container_has_no_findings():
    container = {
        "user": "1000",
        "privileged": False,
        "network_mode": "bridge",
        "pid_mode": "",
        "mounts": [],
        "cap_add": [],
        "ports": {},
        "memory_limit": 268435456,
        "cpu_limit": 100000,
        "image": "nginx:1.27.2",
    }

    assert analyze_container(container) == []


def test_risky_container_finds_expected_rules():
    container = {
        "user": "root",
        "privileged": True,
        "network_mode": "host",
        "pid_mode": "host",
        "mounts": [
            {"source": "/var/run/docker.sock", "destination": "/var/run/docker.sock"},
            {"source": "/etc", "destination": "/host-etc"},
        ],
        "cap_add": ["SYS_ADMIN"],
        "ports": {"8080/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
        "memory_limit": 0,
        "cpu_limit": 0,
        "image": "nginx:latest",
    }

    findings = analyze_container(container)
    codes = {finding["rule_code"] for finding in findings}

    assert codes == {
        "CFG-001",
        "CFG-002",
        "CFG-003",
        "CFG-004",
        "CFG-005",
        "CFG-006",
        "CFG-007",
        "CFG-008",
        "CFG-009",
        "CFG-010",
    }
    assert all(finding["status"] == "FAIL" for finding in findings)

