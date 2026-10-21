"""Tests for Phase 7 scoring."""

from app.services.scoring_service import calculate_score


def test_score_categories_and_deductions():
    result = calculate_score(
        [
            {"severity": "CRITICAL"},
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
        ]
    )

    assert result["score"] == 40
    assert result["risk_level"] == "Risky"
    assert result["deductions"] == 60
    assert result["severity_counts"] == {"CRITICAL": 1, "HIGH": 1, "MEDIUM": 1, "LOW": 0}


def test_score_is_clamped_at_zero_and_secure_is_one_hundred():
    assert calculate_score([])["risk_level"] == "Secure"
    assert calculate_score([])["score"] == 100
    assert calculate_score([{"severity": "CRITICAL"}] * 5)["score"] == 0

