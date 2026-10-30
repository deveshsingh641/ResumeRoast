import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import database
from app.services.pro_auth import create_pro_token

@pytest.fixture
def auth_client():
    return TestClient(app)


def test_auth_login_invalid_email(auth_client):
    response = auth_client.post("/api/auth/login", json={"email": "invalid-email"})
    assert response.status_code == 422
    assert "valid email" in response.json()["detail"].lower()


def test_auth_login_free_user(auth_client):
    email = "freeuser@example.com"
    response = auth_client.post("/api/auth/login", json={"email": email})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["email"] == email
    assert data["is_pro"] is False
    assert data["subscription_status"] == "free"
    assert data["token"] is None
    assert "resumeroast_pro_token" not in response.cookies


def test_auth_login_pro_user(auth_client):
    email = "prouser@example.com"
    database.create_or_get_user(email)
    database.update_subscription(email, "pro")

    response = auth_client.post("/api/auth/login", json={"email": email})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["email"] == email
    assert data["is_pro"] is True
    assert data["subscription_status"] == "pro"
    assert data["token"] is not None
    assert "resumeroast_pro_token" in response.cookies


def test_auth_me_unauthenticated(auth_client):
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is False
    assert data["is_pro"] is False


def test_auth_me_authenticated_pro(auth_client):
    email = "vip@example.com"
    database.create_or_get_user(email)
    database.update_subscription(email, "pro")
    token = create_pro_token(email)

    auth_client.cookies.set("resumeroast_pro_token", token)
    response = auth_client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["email"] == email
    assert data["is_pro"] is True
    assert data["subscription_status"] == "pro"


def test_auth_logout(auth_client):
    response = auth_client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["ok"] is True
