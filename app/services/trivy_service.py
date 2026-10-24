"""Trivy command-line integration and JSON parsing."""

import json
import os
import shutil
import subprocess
from typing import Any


class TrivyError(RuntimeError):
    """Raised when Trivy cannot complete or parse an image scan."""


class TrivyService:
    """Run Trivy locally and normalize its JSON output."""

    def __init__(self, binary: str | None = None):
        configured = binary or os.getenv("TRIVY_BINARY", "trivy")
        self.binary = shutil.which(configured) or configured

    def version(self) -> str:
        """Return the installed Trivy version."""

        result = subprocess.run([self.binary, "--version"], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise TrivyError(result.stderr.strip() or "Trivy is unavailable.")
        return result.stdout.strip()

    def scan_image(self, image_name: str) -> dict[str, Any]:
        """Scan an image and return normalized vulnerability records."""

        image_name = image_name.strip()
        if not image_name:
            raise TrivyError("An image name is required.")

        try:
            result = subprocess.run(
                [self.binary, "image", "--format", "json", "--scanners", "vuln", "--no-progress", image_name],
                capture_output=True,
                text=True,
                timeout=300,
            )
        except FileNotFoundError as error:
            raise TrivyError(f"Trivy executable not found: {self.binary}") from error
        except subprocess.TimeoutExpired as error:
            raise TrivyError("Trivy scan timed out after five minutes.") from error

        if result.returncode != 0:
            error_output = (result.stderr or result.stdout).strip()
            raise TrivyError(error_output or "Trivy returned a non-zero exit code.")

        try:
            payload = json.loads(result.stdout.lstrip("\ufeff"))
        except json.JSONDecodeError as error:
            raise TrivyError("Trivy returned invalid JSON output.") from error

        vulnerabilities = []
        for scan_result in payload.get("Results") or []:
            target = scan_result.get("Target")
            for item in scan_result.get("Vulnerabilities") or []:
                vulnerabilities.append(
                    {
                        "cve_id": item.get("VulnerabilityID"),
                        "package_name": item.get("PkgName"),
                        "installed_version": item.get("InstalledVersion"),
                        "fixed_version": item.get("FixedVersion"),
                        "severity": (item.get("Severity") or "UNKNOWN").upper(),
                        "title": item.get("Title"),
                        "description": item.get("Description"),
                        "target": target,
                    }
                )

        return {
            "image_name": image_name,
            "schema_version": payload.get("SchemaVersion"),
            "vulnerabilities": vulnerabilities,
        }

