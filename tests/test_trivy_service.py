"""Tests for Trivy JSON normalization."""

import json

from app.services.trivy_service import TrivyService


def test_trivy_json_is_normalized(monkeypatch):
    payload = {
        "SchemaVersion": 2,
        "Results": [
            {
                "Target": "alpine:latest (alpine 3.20)",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-0001",
                        "PkgName": "openssl",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "1.1",
                        "Severity": "high",
                        "Title": "Example issue",
                        "Description": "Example description",
                    }
                ],
            }
        ],
    }

    class Completed:
        returncode = 0
        stdout = json.dumps(payload)
        stderr = ""

    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return Completed()

    monkeypatch.setattr("subprocess.run", fake_run)
    result = TrivyService(binary="trivy").scan_image("alpine:latest")

    command = calls[0][0][0]
    assert command[command.index("--pkg-types") + 1] == "library"
    assert result["image_name"] == "alpine:latest"
    assert result["vulnerabilities"][0]["cve_id"] == "CVE-2026-0001"
    assert result["vulnerabilities"][0]["severity"] == "HIGH"

