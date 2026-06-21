"""
resource.py
===========
Step 1-2 of the methodology: turn an address or (lat, lon) into a site object,
then pull the long-term climate normals that every downstream physics module needs.

Data sources (all free, global, real):
  * Geocoding ............ OpenStreetMap Nominatim   https://nominatim.org/release-docs/latest/api/Search/
  * Elevation ............ Open-Elevation            https://open-elevation.com/
  * Solar / wind / temp .. NASA POWER (RE community) https://power.larc.nasa.gov/docs/services/api/

NASA POWER climatology endpoint returns 22-yr solar / 30-yr meteorology monthly
normals for ANY land or ocean point on Earth, no API key required. Parameters used:
  ALLSKY_SFC_SW_DWN  Global horizontal irradiance (kWh/m^2/day)  -> solar
  CLRSKY_SFC_SW_DWN  Clear-sky GHI (kWh/m^2/day)                 -> clearness/QC
  T2M                Air temperature at 2 m (degC)               -> PV temp, HDD/CDD, ground temp
  WS10M / WS50M      Wind speed at 10 m / 50 m (m/s)             -> wind, hub-height shear
  PS                 Surface pressure (kPa)                      -> air density

If the network is unavailable the module falls back to a documented Kt-based
synthetic climatology so the whole pipeline still runs (clearly flagged in output).
"""
from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Optional

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DAYS_IN_MONTH = [31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/climatology/point"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_ELEV_URL = "https://api.open-elevation.com/api/v1/lookup"

_HTTP_TIMEOUT = 20


# --------------------------------------------------------------------------- #
#  Site container
# --------------------------------------------------------------------------- #
@dataclass
class Site:
    latitude: float
    longitude: float
    elevation_m: float = 0.0
    label: str = ""
    timezone_guess: str = ""

    # 12-element monthly climate normals (filled by fetch_climate)
    ghi_kwh_m2_day: list = field(default_factory=list)   # global horiz irradiance
    clearsky_kwh_m2_day: list = field(default_factory=list)
    temp_air_c: list = field(default_factory=list)
    wind_10m_ms: list = field(default_factory=list)
    wind_50m_ms: list = field(default_factory=list)
    pressure_kpa: list = field(default_factory=list)
    data_source: str = ""

    # -- convenience aggregates -------------------------------------------- #
    @property
    def annual_ghi_kwh_m2(self) -> float:
        """Annual global horizontal irradiation (kWh/m^2/yr)."""
        return sum(g * d for g, d in zip(self.ghi_kwh_m2_day, DAYS_IN_MONTH))

    @property
    def mean_air_temp_c(self) -> float:
        return sum(self.temp_air_c) / 12 if self.temp_air_c else float("nan")

    @property
    def ground_temp_c(self) -> float:
        """Undisturbed deep-ground temperature ~ annual mean air temperature.
        (ASHRAE; Kavanaugh & Rafferty, *Geothermal Heating and Cooling*, 2014.)"""
        return self.mean_air_temp_c

    def air_density(self, month_index: Optional[int] = None) -> float:
        """Air density rho = P/(R_specific * T)  [kg/m^3], R_dry = 287.05 J/kg/K."""
        if month_index is None:
            p_kpa = sum(self.pressure_kpa) / 12
            t_c = self.mean_air_temp_c
        else:
            p_kpa = self.pressure_kpa[month_index]
            t_c = self.temp_air_c[month_index]
        return (p_kpa * 1000.0) / (287.05 * (t_c + 273.15))

    def summary(self) -> dict:
        return {
            "label": self.label,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "elevation_m": round(self.elevation_m, 1),
            "annual_GHI_kWh_m2": round(self.annual_ghi_kwh_m2, 1),
            "mean_air_temp_C": round(self.mean_air_temp_c, 1),
            "mean_wind_10m_ms": round(sum(self.wind_10m_ms) / 12, 2) if self.wind_10m_ms else None,
            "ground_temp_C": round(self.ground_temp_c, 1),
            "data_source": self.data_source,
        }


# --------------------------------------------------------------------------- #
#  Geocoding
# --------------------------------------------------------------------------- #
def _http_get_json(url: str, params: dict, headers: Optional[dict] = None) -> dict:
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{qs}", headers=headers or {})
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(address: str) -> Site:
    """Address string -> Site (lat/lon/elevation). Uses OSM Nominatim (free)."""
    data = _http_get_json(
        NOMINATIM_URL,
        {"q": address, "format": "json", "limit": 1},
        headers={"User-Agent": "renewable-retrofit-model/1.0"},
    )
    if not data:
        raise ValueError(f"Could not geocode address: {address!r}")
    lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
    site = Site(latitude=lat, longitude=lon, label=data[0].get("display_name", address))
    site.elevation_m = _fetch_elevation(lat, lon)
    return site


def from_coordinates(lat: float, lon: float, label: str = "",
                     elevation_m: Optional[float] = None) -> Site:
    site = Site(latitude=lat, longitude=lon, label=label or f"{lat:.4f}, {lon:.4f}")
    site.elevation_m = elevation_m if elevation_m is not None else _fetch_elevation(lat, lon)
    return site


def _fetch_elevation(lat: float, lon: float) -> float:
    try:
        d = _http_get_json(OPEN_ELEV_URL, {"locations": f"{lat},{lon}"})
        return float(d["results"][0]["elevation"])
    except Exception:
        return 0.0


# --------------------------------------------------------------------------- #
#  Climate normals
# --------------------------------------------------------------------------- #
def fetch_climate(site: Site, allow_network: bool = True) -> Site:
    """Populate site monthly normals from NASA POWER; fall back if offline."""
    params = {
        "parameters": "ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN,T2M,WS10M,WS50M,PS",
        "community": "RE",
        "longitude": f"{site.longitude:.4f}",
        "latitude": f"{site.latitude:.4f}",
        "format": "JSON",
    }
    if allow_network:
        try:
            d = _http_get_json(NASA_POWER_URL, params)
            p = d["properties"]["parameter"]
            site.ghi_kwh_m2_day = [p["ALLSKY_SFC_SW_DWN"][m] for m in MONTHS]
            site.clearsky_kwh_m2_day = [p["CLRSKY_SFC_SW_DWN"][m] for m in MONTHS]
            site.temp_air_c = [p["T2M"][m] for m in MONTHS]
            site.wind_10m_ms = [p["WS10M"][m] for m in MONTHS]
            site.wind_50m_ms = [p["WS50M"][m] for m in MONTHS]
            site.pressure_kpa = [p["PS"][m] for m in MONTHS]
            site.data_source = "NASA POWER climatology (live)"
            return site
        except Exception as exc:  # noqa: BLE001
            site.data_source = f"OFFLINE fallback ({type(exc).__name__})"
    else:
        site.data_source = "OFFLINE fallback (network disabled)"

    _fill_fallback(site)
    return site


def _fill_fallback(site: Site) -> None:
    """Physically-grounded synthetic climatology when NASA POWER is unreachable.

    Builds monthly extraterrestrial irradiation H0 from astronomy, applies a
    latitude-based clearness index Kt, and a sinusoidal temperature model. This
    is a stand-in for testing/offline use ONLY -- live NASA POWER data should be
    used for any real assessment.
    """
    lat = math.radians(site.latitude)
    g_sc = 1361.0  # solar constant W/m^2
    kt = max(0.45, 0.62 - 0.0016 * abs(site.latitude))  # rough global clearness
    ghi, clr = [], []
    for n_doy in [17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]:
        decl = math.radians(23.45 * math.sin(math.radians(360 * (284 + n_doy) / 365)))
        ws = math.acos(max(-1.0, min(1.0, -math.tan(lat) * math.tan(decl))))
        d_corr = 1 + 0.033 * math.cos(math.radians(360 * n_doy / 365))
        h0 = (24 / math.pi) * g_sc * d_corr * (
            math.cos(lat) * math.cos(decl) * math.sin(ws)
            + ws * math.sin(lat) * math.sin(decl)
        ) / 1000.0  # kWh/m^2/day (extraterrestrial)
        h0 = max(0.0, h0)
        ghi.append(round(kt * h0, 2))
        clr.append(round(0.78 * h0, 2))
    site.ghi_kwh_m2_day = ghi
    site.clearsky_kwh_m2_day = clr

    t_mean = 26.0 - 0.004 * site.latitude ** 2   # ~26C equator -> cooler poleward
    amp = 0.32 * abs(site.latitude)              # seasonal swing grows poleward
    phase = 0 if site.latitude >= 0 else math.pi
    site.temp_air_c = [round(t_mean - amp * math.cos(2 * math.pi * (m) / 12 + phase), 1)
                       for m in range(12)]
    site.wind_10m_ms = [4.0] * 12
    site.wind_50m_ms = [5.4] * 12
    site.pressure_kpa = [round(101.325 * math.exp(-site.elevation_m / 8434.0), 2)] * 12


if __name__ == "__main__":
    s = from_coordinates(49.8951, -97.1384, "Winnipeg, MB", elevation_m=232)
    fetch_climate(s, allow_network=False)
    print(json.dumps(s.summary(), indent=2))
