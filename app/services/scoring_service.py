"""Project-defined security scoring."""

SEVERITY_DEDUCTIONS = {
    "CRITICAL": 30,
    "HIGH": 20,
    "MEDIUM": 10,
    "LOW": 5,
}


def calculate_score(findings: list[dict]) -> dict:
    """Calculate a 0-100 configuration risk score from failed findings."""

    deductions = sum(SEVERITY_DEDUCTIONS.get(finding.get("severity", ""), 0) for finding in findings)
    score = max(0, min(100, 100 - deductions))
    if score >= 90:
        risk_level = "Secure"
    elif score >= 70:
        risk_level = "Moderate"
    elif score >= 40:
        risk_level = "Risky"
    else:
        risk_level = "Critical"

    severity_counts = {severity: 0 for severity in SEVERITY_DEDUCTIONS}
    for finding in findings:
        severity = finding.get("severity", "")
        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "score": score,
        "risk_level": risk_level,
        "deductions": deductions,
        "severity_counts": severity_counts,
    }

