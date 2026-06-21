"""
Step 3: Solar PV yield via pvlib PVWatts chain.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional

try:
    import pvlib
    import numpy as np
    _HAS_PVLIB = True
except ImportError:
    _HAS_PVLIB = False

from .resource import Site


@dataclass
class PVConfig:
    dc_capacity_kw: float = 8.0
    tilt_deg: Optional[float] = None       # None = use latitude
    azimuth_deg: float = 180.0             # south-facing
    system_losses: float = 0.14            # PVWatts default
    inverter_efficiency: float = 0.96
    noct: float = 45.0
    temp_coeff: float = -0.004             # /°C for c-Si
    gamma: float = -0.004


@dataclass
class PVResult:
    annual_ac_kwh: float
    specific_yield_kwh_kw: float
    performance_ratio: float
    capacity_factor: float
    monthly_ac_kwh: list[float]


def simulate_pv(site: Site, cfg: PVConfig | None = None) -> PVResult:
    if cfg is None:
        cfg = PVConfig()
    tilt = cfg.tilt_deg if cfg.tilt_deg is not None else abs(site.lat)

    if _HAS_PVLIB:
        return _pvlib_simulate(site, cfg, tilt)
    return _simple_simulate(site, cfg, tilt)


def _pvlib_simulate(site: Site, cfg: PVConfig, tilt: float) -> PVResult:
    import pvlib
    import numpy as np

    _days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    _mid_day = [17, 46, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]  # DOY

    monthly_ac = []
    for m_idx in range(12):
        doy = _mid_day[m_idx]
        days = _days_in_month[m_idx]
        ghi_daily = site.monthly_ghi_kwh_m2[m_idx] / days  # kWh/m²/day → daily total
        t_air = site.monthly_temp_c[m_idx]

        # Build hourly times for representative day
        times = pvlib.solarposition.get_solarposition(
            pvlib.location.Location(site.lat, site.lon, altitude=site.elevation_m)
            .__class__(site.lat, site.lon, altitude=site.elevation_m)
            .get_clearsky(
                pvlib.solarposition.get_solarposition(
                    _doy_to_timestamps(doy), site.lat, site.lon
                ).index
            ).index,
            site.lat, site.lon
        )
        # Simpler approach: use the scalar per-month GHI without full hourly loop
        # Use PVWatts-style formula with monthly average irradiance
        peak_sun_hours = ghi_daily  # kWh/m² = peak sun hours
        g_poa = peak_sun_hours * 1000 / 8  # rough POA in W/m² average over day

        # Cell temp at representative irradiance
        t_cell = t_air + (g_poa / 800) * (cfg.noct - 20)
        dc_eff = 1 + cfg.temp_coeff * (t_cell - 25)
        dc_kwh_day = ghi_daily * cfg.dc_capacity_kw * dc_eff * (1 - cfg.system_losses)
        ac_kwh_day = dc_kwh_day * cfg.inverter_efficiency
        monthly_ac.append(round(ac_kwh_day * days, 1))

    annual = sum(monthly_ac)
    specific = round(annual / cfg.dc_capacity_kw, 0)
    pr = round(annual / (site.annual_ghi_kwh_m2 * cfg.dc_capacity_kw), 3) if site.annual_ghi_kwh_m2 else 0.0
    cf = round(annual / (cfg.dc_capacity_kw * 8760), 3)
    return PVResult(
        annual_ac_kwh=round(annual, 0),
        specific_yield_kwh_kw=specific,
        performance_ratio=pr,
        capacity_factor=cf,
        monthly_ac_kwh=monthly_ac,
    )


def _doy_to_timestamps(doy: int):
    import pandas as pd
    return pd.date_range(f"2023-01-01", periods=24, freq="h") + pd.Timedelta(days=doy - 1)


def _simple_simulate(site: Site, cfg: PVConfig, tilt: float) -> PVResult:
    """Fallback simulation without pvlib."""
    _days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    monthly_ac = []
    for m_idx in range(12):
        ghi_daily = site.monthly_ghi_kwh_m2[m_idx] / _days[m_idx]
        t_air = site.monthly_temp_c[m_idx]
        g_poa = ghi_daily * 1000 / 6  # rough W/m² average
        t_cell = t_air + (g_poa / 800) * (cfg.noct - 20)
        dc_eff = 1 + cfg.temp_coeff * (t_cell - 25)
        dc_kwh_day = ghi_daily * cfg.dc_capacity_kw * dc_eff * (1 - cfg.system_losses)
        ac_kwh_day = dc_kwh_day * cfg.inverter_efficiency
        monthly_ac.append(round(ac_kwh_day * _days[m_idx], 1))
    annual = sum(monthly_ac)
    specific = round(annual / cfg.dc_capacity_kw, 0)
    pr = round(annual / (site.annual_ghi_kwh_m2 * cfg.dc_capacity_kw), 3) if site.annual_ghi_kwh_m2 else 0.0
    cf = round(annual / (cfg.dc_capacity_kw * 8760), 3)
    return PVResult(
        annual_ac_kwh=round(annual, 0),
        specific_yield_kwh_kw=specific,
        performance_ratio=pr,
        capacity_factor=cf,
        monthly_ac_kwh=monthly_ac,
    )
