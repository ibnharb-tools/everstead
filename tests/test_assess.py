"""Tests for POST /api/assess."""
import pytest
from httpx import AsyncClient

ASSESS_PAYLOAD = {
    "address": "123 Main St, Winnipeg, MB, Canada",
    "lat": 49.8951,
    "lon": -97.1384,
    "propertyType": "house",
    "floors": 2,
    "roofOrLotSize": "medium",
    "siteFeatures": ["open_land", "windy"],
    "monthlyBill": "100_200",
    "heatingType": "gas",
    "goals": ["lower_bill", "backup_power"],
    "options": {"taxYear": 2026, "electricityPrice": None, "currency": "CAD"},
}


@pytest.mark.asyncio
async def test_assess_returns_200(client: AsyncClient):
    resp = await client.post("/api/assess", json=ASSESS_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert data["assessmentId"].startswith("asmt_")
    assert "site" in data
    assert "technologies" in data
    assert "ranking" in data
    assert "charts" in data
    assert "incentiveSummary" in data
    assert data["disclaimer"]


@pytest.mark.asyncio
async def test_assess_site_fields(client: AsyncClient):
    resp = await client.post("/api/assess", json=ASSESS_PAYLOAD)
    site = resp.json()["site"]
    for field in ("resolvedAddress", "lat", "lon", "elevationM", "annualSunlightKwhM2",
                  "meanTempC", "averageWindSpeedMs", "groundTempC", "dataSource", "dataNote"):
        assert field in site, f"Missing site field: {field}"


@pytest.mark.asyncio
async def test_assess_technology_consistency(client: AsyncClient):
    resp = await client.post("/api/assess", json=ASSESS_PAYLOAD)
    data = resp.json()
    for tech in data["technologies"]:
        inc = tech["incentives"]
        assert inc["total"] == inc["federal"] + inc["state"] + inc["rebates"], \
            f"incentives.total mismatch in {tech['type']}"
        assert tech["netCapex"] == tech["grossCapex"] - inc["total"], \
            f"netCapex mismatch in {tech['type']}"


@pytest.mark.asyncio
async def test_assess_charts(client: AsyncClient):
    resp = await client.post("/api/assess", json=ASSESS_PAYLOAD)
    charts = resp.json()["charts"]
    assert len(charts["monthlySunlightKwhM2"]) == 12
    assert "paybackCurve" in charts
    assert "years" in charts["paybackCurve"]


@pytest.mark.asyncio
async def test_assess_2026_federal_credit_zero(client: AsyncClient):
    resp = await client.post("/api/assess", json=ASSESS_PAYLOAD)
    data = resp.json()
    assert data["incentiveSummary"]["federalCreditRate"] == 0
    for tech in data["technologies"]:
        assert tech["incentives"]["federal"] == 0


@pytest.mark.asyncio
async def test_assess_2025_federal_credit_thirty(client: AsyncClient):
    payload = dict(ASSESS_PAYLOAD)
    payload["options"] = {"taxYear": 2025, "currency": "CAD"}
    resp = await client.post("/api/assess", json=payload)
    data = resp.json()
    assert data["incentiveSummary"]["federalCreditRate"] == 0.30
    solar = next(t for t in data["technologies"] if t["type"] == "solar_pv")
    assert solar["incentives"]["federal"] > 0


@pytest.mark.asyncio
async def test_assess_missing_location(client: AsyncClient):
    payload = {k: v for k, v in ASSESS_PAYLOAD.items() if k not in ("address", "lat", "lon")}
    resp = await client.post("/api/assess", json=payload)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_assess_coordinates_only(client: AsyncClient):
    payload = {**ASSESS_PAYLOAD}
    del payload["address"]
    resp = await client.post("/api/assess", json=payload)
    assert resp.status_code == 200
