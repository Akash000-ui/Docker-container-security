"""Authentication tests for Phase 3."""

import pytest

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-key",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        }
    )

    with application.app_context():
        user = User(username="admin")
        user.set_password("correct-password")
        db.session.add(user)
        db.session.commit()

    yield application


def test_dashboard_requires_authentication(app):
    client = app.test_client()

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_invalid_credentials_are_rejected(app):
    client = app.test_client()

    response = client.post(
        "/login", data={"username": "admin", "password": "wrong-password"}
    )

    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_valid_login_and_logout(app):
    client = app.test_client()

    login_response = client.post(
        "/login", data={"username": "admin", "password": "correct-password"}
    )
    dashboard_response = client.get("/dashboard")
    logout_response = client.post("/logout")

    assert login_response.status_code == 302
    assert dashboard_response.status_code == 200
    assert b"admin" in dashboard_response.data
    assert logout_response.status_code == 302

