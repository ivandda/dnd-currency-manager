"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User


class TestRegister:
    """Test user registration."""

    def test_register_success(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "secret123",
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_sets_refresh_cookie(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "cookieuser",
            "password": "secret123",
        })
        assert response.status_code == 201
        assert "refresh_token" in response.cookies

    def test_register_duplicate_username(self, client: TestClient, test_user: User):
        response = client.post("/api/auth/register", json={
            "username": test_user.username,
            "password": "secret123",
        })
        assert response.status_code == 409
        assert "already taken" in response.json()["detail"]

    def test_register_short_username(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "ab",
            "password": "secret123",
        })
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "validuser",
            "password": "123",
        })
        assert response.status_code == 422


class TestLogin:
    """Test user login."""

    def test_login_success(self, client: TestClient, test_user: User):
        response = client.post("/api/auth/login", json={
            "username": "testplayer",
            "password": "password123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in response.cookies

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        response = client.post("/api/auth/login", json={
            "username": "testplayer",
            "password": "wrongpassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post("/api/auth/login", json={
            "username": "nobody",
            "password": "password123",
        })
        assert response.status_code == 401


class TestRefreshToken:
    """Test token refresh."""

    def test_refresh_success(self, client: TestClient, test_user: User):
        # First login to get refresh cookie
        login_response = client.post("/api/auth/login", json={
            "username": "testplayer",
            "password": "password123",
        })
        assert login_response.status_code == 200

        # Now refresh
        response = client.post("/api/auth/refresh")
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_refresh_without_cookie(self, client: TestClient):
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401


class TestProtectedRoutes:
    """Test that protected routes require authentication."""

    def test_get_me_unauthorized(self, client: TestClient):
        response = client.get("/api/users/me")
        assert response.status_code == 401

    def test_get_me_success(self, client: TestClient, auth_headers: dict):
        response = client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["username"] == "testplayer"

    def test_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401


class TestLogout:
    """Test logout."""

    def test_logout_clears_cookie(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"
