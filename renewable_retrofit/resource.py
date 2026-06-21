"""
Step 1-2: Geocoding, elevation, and NASA POWER climate normals.
"""
from __future__ import annotations
import math
import urllib.request
import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Site:
    lat: float
    lon: float
    address: str
    elevation_m: float = 0.0
    # climate fields filled by fetch_climate
    monthly_ghi_kwh_m2: list[float] = field(default_factory=lambda: [0.0] * 12)
    annual_ghi_kwh_m2: float = 0.0
    monthly_temp_c: list[float] = field(default_factory=lambda: [0.0] * 12)
    mean_temp_c: float = 0.0
    wind_speed_10m_ms: float = 0.0
    wind_speed_50m_ms: float = 0.0
    pressure_kpa: float = 101.325
    air_density_kg_m3: float = 1.225
    ground_temp_c: float = 10.0
    data_source: str = "offline_synthetic"
    data_note: str = ""


def geocode(address: str) -> tuple[float, float, str]:
    """Returns (lat, lon, resolved_address). Raises ValueError if not found."""
    url = (
        "https://nominatim.openstreetmap.org/search"
        f"?q={urllib.parse.quote(address)}&format=json&limit=1&addressdetails=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Everstead/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        results = json.loads(resp.read())
    if not results:
        raise ValueError(f"Address not found: {address!r}")
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"]


def get_elevation(lat: float, lon: float) -> float:
    """Fetch elevation in metres from Open-Elevation."""
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    req = urllib.request.Request(url, headers={"User-Agent": "Everstead/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    return float(data["results"][0]["elevation"])


def from_coordinates(lat: float, lon: float, address: str = "", elevation_m: float = 0.0) -> Site:
    return Site(lat=lat, lon=lon, address=address, elevation_m=elevation_m)


def fetch_climate(site: Site, allow_network: bool = True) -> Site:
    """
    Fetch NASA POWER monthly climatologies and compute derived fields.
    Falls back to synthetic offline data if network is unavailable or disabled.
    Raises RuntimeError with "LOCATION_DATA_UNAVAILABLE" message on hard failure.
    """
    if allow_network:
        try:
            _fetch_nasa_power(site)
            return site
        except Exception as exc:
            raise RuntimeError(f"LOCATION_DATA_UNAVAILABLE: {exc}") from exc
    _synthetic_climate(site)
    return site


def _fetch_nasa_power(site: Site) -> None:
    params = "ALLSKY_SFC_SW_DWN,T2M,WS10M,WS50M,PS"
    url = (
        "https://power.larc.nasa.gov/api/temporal/climatology/point"
        f"?parameters={params}&community=RE&longitude={site.lon}&latitude={site.lat}"
        "&format=JSON&start=2001&end=2022"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Everstead/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())

    props = data["properties"]["parameter"]
    # GHI: kWh/m²/day → multiply by days-in-month
    _days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    ghi_daily = [props["ALLSKY_SFC_SW_DWN"][str(m)] for m in range(1, 13)]
    site.monthly_ghi_kwh_m2 = [round(g * d, 1) for g, d in zip(ghi_daily, _days)]
    site.annual_ghi_kwh_m2 = round(sum(site.monthly_ghi_kwh_m2), 0)
    site.monthly_temp_c = [round(props["T2M"][str(m)], 1) for m in range(1, 13)]
    site.mean_temp_c = round(sum(site.monthly_temp_c) / 12, 1)
    site.wind_speed_10m_ms = round(
        sum(props["WS10M"][str(m)] for m in range(1, 13)) / 12, 2
    )
    site.wind_speed_50m_ms = round(
        sum(props["WS50M"][str(m)] for m in range(1, 13)) / 12, 2
    )
    site.pressure_kpa = round(
        sum(props["PS"][str(m)] for m in range(1, 13)) / 12, 2
    )
    site.air_density_kg_m3 = round(
        site.pressure_kpa * 1000 / (287.05 * (site.mean_temp_c + 273.15)), 3
    )
    site.ground_temp_c = site.mean_temp_c  # ASHRAE approximation
    site.data_source = "NASA POWER"
    site.data_note = "Based on long term climate averages for your location."


def _synthetic_climate(site: Site) -> None:
    """Synthetic climatology for offline/testing use."""
    lat = site.lat
    # Rough insolation based on latitude
    base_ghi = max(3.0, 5.5 - abs(lat - 25) * 0.05)
    _days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    season = [0.5, 0.65, 0.85, 1.05, 1.25, 1.35, 1.35, 1.2, 1.0, 0.75, 0.55, 0.45]
    if lat < 0:  # southern hemisphere flip
        season = season[6:] + season[:6]
    site.monthly_ghi_kwh_m2 = [round(base_ghi * s * d, 1) for s, d in zip(season, _days)]
    site.annual_ghi_kwh_m2 = round(sum(site.monthly_ghi_kwh_m2), 0)
    temp_base = max(-5.0, 25.0 - abs(lat - 25) * 0.6)
    temp_amp = max(2.0, abs(lat) * 0.3)
    site.monthly_temp_c = [
        round(temp_base + temp_amp * math.sin(math.pi * (m - 1) / 6 - math.pi / 2), 1)
        for m in range(1, 13)
    ]
    if lat < 0:
        site.monthly_temp_c = site.monthly_temp_c[6:] + site.monthly_temp_c[:6]
    site.mean_temp_c = round(sum(site.monthly_temp_c) / 12, 1)
    site.wind_speed_10m_ms = 4.5
    site.wind_speed_50m_ms = 6.0
    site.pressure_kpa = max(85.0, 101.325 * math.exp(-site.elevation_m / 8500))
    site.air_density_kg_m3 = round(
        site.pressure_kpa * 1000 / (287.05 * (site.mean_temp_c + 273.15)), 3
    )
    site.ground_temp_c = site.mean_temp_c
    site.data_source = "offline_synthetic"
    site.data_note = "Synthetic climate estimate — offline mode."


# lazy import to avoid top-level failure when urllib.parse not imported
import urllib.parse
