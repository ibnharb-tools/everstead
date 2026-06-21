"""
Step 5-6: Micro-hydro and ground-source heat pump (GSHP).
"""
from __future__ import annotations
import math
from dataclasses import dataclass

from .resource import Site


# ── Micro-hydro ────────────────────────────────────────────────────────────────

@dataclass
class HydroResult:
    annual_kwh: float
    power_kw: float


def simulate_hydro(net_head_m: float, flow_lps: float, efficiency: float = 0.7) -> HydroResult:
    flow_m3s = flow_lps / 1000
    power_kw = 1000 * 9.81 * flow_m3s * net_head_m * efficiency / 1000
    annual_kwh = round(power_kw * 8760 * 0.90, 0)  # 90% availability
    return HydroResult(annual_kwh=annual_kwh, power_kw=round(power_kw, 2))


# ── Geothermal GSHP ────────────────────────────────────────────────────────────

@dataclass
class GSHPConfig:
    kw_thermal: float = 10.5
    cop_heat: float = 4.0
    cop_cool: float = 5.0
    ua_factor: float = 100.0           # building UA in W/°C
    base_temp_c: float = 18.0
    bore_m_per_kw: float = 24.0        # vertical bore rule of thumb


@dataclass
class GSHPResult:
    heat_demand_kwh: float
    cool_demand_kwh: float
    bore_length_m: float
    system_size_kw_thermal: float
    annual_kwh_electric: float


def simulate_gshp(site: Site, cfg: GSHPConfig | None = None) -> GSHPResult:
    if cfg is None:
        cfg = GSHPConfig()

    _days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    hdd = sum(max(0, cfg.base_temp_c - t) * d for t, d in zip(site.monthly_temp_c, _days))
    cdd = sum(max(0, t - cfg.base_temp_c) * d for t, d in zip(site.monthly_temp_c, _days))

    heat_kwh = cfg.ua_factor * hdd * 24 / 1000
    cool_kwh = cfg.ua_factor * cdd * 24 / 1000
    elec_kwh = heat_kwh / cfg.cop_heat + cool_kwh / cfg.cop_cool

    bore_len = round(cfg.kw_thermal * cfg.bore_m_per_kw, 0)
    return GSHPResult(
        heat_demand_kwh=round(heat_kwh, 0),
        cool_demand_kwh=round(cool_kwh, 0),
        bore_length_m=bore_len,
        system_size_kw_thermal=cfg.kw_thermal,
        annual_kwh_electric=round(elec_kwh, 0),
    )
