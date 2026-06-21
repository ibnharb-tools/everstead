"""
Step 4: Small/residential wind — Weibull + turbine power curve.
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from .resource import Site


@dataclass
class TurbineSpec:
    rated_kw: float = 10.0
    rotor_diameter_m: float = 7.0
    hub_height_m: float = 37.0
    cut_in_ms: float = 3.0
    rated_ms: float = 12.0
    cut_out_ms: float = 25.0
    cp_realized: float = 0.35          # realistic Cp accounting for losses


@dataclass
class WindResult:
    annual_kwh: float
    capacity_factor: float
    mean_hub_height_wind_ms: float
    hub_height_m: float


def simulate_wind(site: Site, spec: TurbineSpec | None = None) -> WindResult:
    if spec is None:
        spec = TurbineSpec()

    # Hub-height wind speed via power-law shear
    if site.wind_speed_10m_ms > 0 and site.wind_speed_50m_ms > 0:
        alpha = math.log(site.wind_speed_50m_ms / max(site.wind_speed_10m_ms, 0.01)) / math.log(50 / 10)
    else:
        alpha = 0.143
    v_hub = site.wind_speed_10m_ms * (spec.hub_height_m / 10) ** alpha

    # Weibull with k=2 (Rayleigh)
    k = 2.0
    c = v_hub / math.gamma(1 + 1 / k)

    swept_area = math.pi * (spec.rotor_diameter_m / 2) ** 2
    rho = site.air_density_kg_m3

    # Numerical integration over Weibull distribution
    dv = 0.5
    aep = 0.0
    v = dv / 2
    while v < spec.cut_out_ms + dv:
        f = (k / c) * (v / c) ** (k - 1) * math.exp(-((v / c) ** k))
        p = _turbine_power(v, spec, swept_area, rho)
        aep += f * p * dv
        v += dv
    annual_kwh = round(aep * 8760, 0)
    cf = round(annual_kwh / (spec.rated_kw * 8760), 3)
    return WindResult(
        annual_kwh=annual_kwh,
        capacity_factor=cf,
        mean_hub_height_wind_ms=round(v_hub, 2),
        hub_height_m=spec.hub_height_m,
    )


def _turbine_power(v: float, spec: TurbineSpec, area: float, rho: float) -> float:
    if v < spec.cut_in_ms or v >= spec.cut_out_ms:
        return 0.0
    if v >= spec.rated_ms:
        return spec.rated_kw
    # Cubic interpolation between cut-in and rated
    p_aero = 0.5 * rho * area * v ** 3 * spec.cp_realized / 1000  # kW
    return min(p_aero, spec.rated_kw)
