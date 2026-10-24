"""Tests for Phase 9 dashboard summaries and reports."""

import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "report-test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )
    with application.app_context():
        user = User(username="admin")
        user.set_password("correct-password")
        db.session.add(user)
        db.session.commit()
    yield application


def test_report_routes_require_authentication(app):
    client = app.test_client()
    assert client.get("/api/dashboard/summary").status_code == 302
    assert client.get("/reports/security").status_code == 302
    assert client.get("/reports/security.csv").status_code == 302


def test_summary_and_csv_report_after_login(app):
    client = app.test_client()
    client.post("/login", data={"username": "admin", "password": "correct-password"})

    summary = client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json["summary"]["containers"] == 0

    report = client.get("/reports/security")
    assert report.status_code == 200
    assert b"Security report" in report.data

    csv_report = client.get("/reports/security.csv")
    assert csv_report.status_code == 200
    assert csv_report.content_type.startswith("text/csv")
    assert b"Container Security Monitoring Report" in csv_report.data
