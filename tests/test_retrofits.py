"""Tests for /api/retrofits routes."""
import pytest
from httpx import AsyncClient

ASSESS_PAYLOAD = {
    "lat": 49.8951,
    "lon": -97.1384,
    "propertyType": "house",
    "roofOrLotSize": "medium",
    "siteFeatures": [],
    "monthlyBill": "100_200",
    "heatingType": "gas",
    "goals": ["lower_bill"],
    "options": {"taxYear": 2026},
}


async def _signup_and_token(client: AsyncClient, email="user@test.com") -> str:
    await client.post("/api/auth/signup", json={"name": "Test", "email": email, "password": "password123"})
    resp = await client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return resp.json()["token"]


async def _run_assess(client: AsyncClient) -> str:
    resp = await client.post("/api/assess", json=ASSESS_PAYLOAD)
    assert resp.status_code == 200
    return resp.json()["assessmentId"]


@pytest.mark.asyncio
async def test_save_and_list(client: AsyncClient):
    token = await _signup_and_token(client)
    aid = await _run_assess(client)

    save = await client.post(
        "/api/retrofits",
        json={"assessmentId": aid, "label": "Our house"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert save.status_code == 201
    rid = save.json()["id"]
    assert rid.startswith("rtf_")

    lst = await client.get("/api/retrofits", headers={"Authorization": f"Bearer {token}"})
    assert lst.status_code == 200
    assert any(r["id"] == rid for r in lst.json()["retrofits"])


@pytest.mark.asyncio
async def test_get_retrofit_detail(client: AsyncClient):
    token = await _signup_and_token(client, "b@test.com")
    aid = await _run_assess(client)
    save = await client.post(
        "/api/retrofits",
        json={"assessmentId": aid, "label": "Lake cabin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    rid = save.json()["id"]

    detail = await client.get(f"/api/retrofits/{rid}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200
    data = detail.json()
    assert data["id"] == rid
    assert "assessment" in data
    assert "technologies" in data["assessment"]


@pytest.mark.asyncio
async def test_delete_retrofit(client: AsyncClient):
    token = await _signup_and_token(client, "c@test.com")
    aid = await _run_assess(client)
    save = await client.post(
        "/api/retrofits",
        json={"assessmentId": aid},
        headers={"Authorization": f"Bearer {token}"},
    )
    rid = save.json()["id"]

    del_resp = await client.delete(f"/api/retrofits/{rid}", headers={"Authorization": f"Bearer {token}"})
    assert del_resp.status_code == 200
    assert del_resp.json()["ok"] is True

    get_resp = await client.get(f"/api/retrofits/{rid}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_retrofit_scoped_to_owner(client: AsyncClient):
    token_a = await _signup_and_token(client, "d@test.com")
    token_b = await _signup_and_token(client, "e@test.com")
    aid = await _run_assess(client)

    save = await client.post(
        "/api/retrofits",
        json={"assessmentId": aid, "label": "Owned by A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    rid = save.json()["id"]

    # User B cannot access user A's retrofit
    resp = await client.get(f"/api/retrofits/{rid}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_retrofits_require_auth(client: AsyncClient):
    resp = await client.get("/api/retrofits")
    assert resp.status_code in (401, 403)
