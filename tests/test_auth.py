"""Tests for auth routes."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_and_login(client: AsyncClient):
    resp = await client.post("/api/auth/signup", json={
        "name": "Sam Rivera", "email": "sam@example.com", "password": "password123"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "sam@example.com"

    resp2 = await client.post("/api/auth/login", json={
        "email": "sam@example.com", "password": "password123"
    })
    assert resp2.status_code == 200
    assert "token" in resp2.json()


@pytest.mark.asyncio
async def test_duplicate_email(client: AsyncClient):
    body = {"name": "Sam", "email": "dup@example.com", "password": "password123"}
    await client.post("/api/auth/signup", json=body)
    resp = await client.post("/api/auth/signup", json=body)
    assert resp.status_code == 409
    assert resp.json()["detail"]["error"]["code"] == "EMAIL_IN_USE"


@pytest.mark.asyncio
async def test_wrong_password(client: AsyncClient):
    await client.post("/api/auth/signup", json={
        "name": "Sam", "email": "sam2@example.com", "password": "correct-password"
    })
    resp = await client.post("/api/auth/login", json={
        "email": "sam2@example.com", "password": "wrong"
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_token(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code in (401, 403)  # HTTPBearer returns 401 or 403 when no header


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient):
    await client.post("/api/auth/signup", json={
        "name": "Alice", "email": "alice@example.com", "password": "password123"
    })
    login = await client.post("/api/auth/login", json={
        "email": "alice@example.com", "password": "password123"
    })
    token = login.json()["token"]
    resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_forgot_password_always_200(client: AsyncClient):
    resp = await client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


@pytest.mark.asyncio
async def test_oauth_returns_501(client: AsyncClient):
    resp = await client.post("/api/auth/oauth", json={"provider": "google", "credential": "tok"})
    assert resp.status_code == 501
