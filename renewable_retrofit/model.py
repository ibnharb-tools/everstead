"""
model.py
========
Step 9: Orchestrator. Runs the full home-retrofit assessment end-to-end:
  address/coords -> resource data -> per-technology yield -> capex from
  marketplace benchmarks -> incentives + economics -> ranked recommendation.

Returns a single nested dict you can print, JSON-dump, or feed to a UI.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from . import resource, solar, wind, hydro_geo, economics, marketplace


@dataclass
class AssessmentInputs:
    # Location: provide ONE of address or (lat, lon)
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    allow_network: bool = True

    # Which technologies to evaluate
    eval_solar: bool = True
    eval_wind: bool = True
    eval_hydro: bool = False           # needs head+flow inputs below
    eval_geothermal: bool = True

    # System sizes
    pv_kw: float = 6.0
    battery_kwh: float = 0.0
    wind_kw: float = 10.0
    gshp_kw_thermal: float = 10.5

    # Hydro site inputs (only if eval_hydro)
    hydro_head_m: float = 0.0
    hydro_flow_lps: float = 0.0

    # Economics / incentives
    tax_year: int = 2026
    country: str = "US"
    financing: str = "owned"
    electricity_price: float = 0.16
    export_price: float = 0.06
    upfront_rebates: float = 0.0
    state_credit_fraction: float = 0.0
    cost_level: str = "typical"        # low | typical | high

    # Baseline systems the GSHP would replace (for fuel/efficiency savings)
    incumbent_heat_cop: float = 0.95   # 0.95 ~ gas furnace efficiency-equivalent
    incumbent_heat_fuel_price_per_kwh: float = 0.06  # delivered-heat $/kWh_thermal
    incumbent_cool_cop: float = 3.5    # standard AC (~SEER 12-14) seasonal COP


def _resolve_site(inp: AssessmentInputs) -> resource.Site:
    if inp.address:
        try:
            site = resource.geocode(inp.address)
        except Exception:
            raise ValueError("Geocoding failed (offline?). Pass lat/lon instead.")
    elif inp.lat is not None and inp.lon is not None:
        site = resource.from_coordinates(inp.lat, inp.lon)
    else:
        raise ValueError("Provide either address or (lat, lon).")
    resource.fetch_climate(site, allow_network=inp.allow_network)
    return site


def run_assessment(inp: AssessmentInputs) -> dict:
    site = _resolve_site(inp)
    ctx = economics.IncentiveContext(
        country=inp.country, tax_year=inp.tax_year, financing=inp.financing,
        upfront_rebates=inp.upfront_rebates,
        state_credit_fraction=inp.state_credit_fraction,
    )
    econ_cfg = economics.EconConfig(
        electricity_price_per_kwh=inp.electricity_price,
        export_price_per_kwh=inp.export_price,
    )

    report = {"site": site.summary(), "monthly_climate": {
        "ghi_kwh_m2_day": site.ghi_kwh_m2_day,
        "temp_air_c": site.temp_air_c,
        "wind_10m_ms": site.wind_10m_ms,
    }, "technologies": {}, "ranking": []}

    rankable = []

    # ---- Solar PV -------------------------------------------------------- #
    if inp.eval_solar:
        pv = solar.simulate_pv(site, solar.PVConfig(dc_capacity_kw=inp.pv_kw))
        capex = marketplace.price_capex("solar_pv", inp.pv_kw, inp.cost_level)
        if inp.battery_kwh > 0:
            bcap = marketplace.price_capex("battery", inp.battery_kwh, inp.cost_level)
            capex["gross_capex"] += bcap["gross_capex"]
        e = economics.evaluate(capex["gross_capex"], pv.annual_ac_kwh,
                               inp.pv_kw, ctx, econ_cfg)
        report["technologies"]["solar_pv"] = {
            "annual_kwh": pv.annual_ac_kwh,
            "specific_yield_kwh_kw": pv.specific_yield_kwh_kw,
            "performance_ratio": pv.performance_ratio,
            "capacity_factor": pv.capacity_factor,
            "tilt_deg": pv.tilt_deg, "azimuth_deg": pv.azimuth_deg,
            "gross_capex": capex["gross_capex"], "economics": _econ_dict(e),
            "buy_at": capex["marketplaces"],
            "pv_kw": inp.pv_kw,
            "battery_kwh": inp.battery_kwh if inp.battery_kwh > 0 else None,
        }
        rankable.append(("solar_pv", pv.annual_ac_kwh, e.npv, e.simple_payback_years))

    # ---- Wind ------------------------------------------------------------ #
    if inp.eval_wind:
        wr = wind.simulate_wind(site, wind.TurbineSpec(rated_power_kw=inp.wind_kw))
        capex = marketplace.price_capex("wind_small", inp.wind_kw, inp.cost_level)
        e = economics.evaluate(capex["gross_capex"], wr.annual_kwh,
                               inp.wind_kw, ctx, econ_cfg)
        report["technologies"]["wind"] = {
            "annual_kwh": wr.annual_kwh, "capacity_factor": wr.capacity_factor,
            "mean_hubheight_ms": wr.mean_hubheight_ms,
            "weibull_k": wr.weibull_k, "weibull_c": wr.weibull_c,
            "viability": wind.viability_note(wr),
            "gross_capex": capex["gross_capex"], "economics": _econ_dict(e),
            "buy_at": capex["marketplaces"],
            "wind_kw": inp.wind_kw,
        }
        rankable.append(("wind", wr.annual_kwh, e.npv, e.simple_payback_years))

    # ---- Hydro ----------------------------------------------------------- #
    if inp.eval_hydro and inp.hydro_head_m > 0 and inp.hydro_flow_lps > 0:
        hy = hydro_geo.simulate_hydro(inp.hydro_head_m, inp.hydro_flow_lps)
        capex = marketplace.price_capex("micro_hydro", hy.rated_power_kw, inp.cost_level)
        e = economics.evaluate(capex["gross_capex"], hy.annual_kwh,
                               hy.rated_power_kw, ctx, econ_cfg)
        report["technologies"]["hydro"] = {
            "rated_power_kw": hy.rated_power_kw, "annual_kwh": hy.annual_kwh,
            "gross_capex": capex["gross_capex"], "economics": _econ_dict(e),
            "buy_at": capex["marketplaces"],
        }
        rankable.append(("hydro", hy.annual_kwh, e.npv, e.simple_payback_years))

    # ---- Geothermal heat pump ------------------------------------------- #
    if inp.eval_geothermal:
        gc = hydro_geo.GSHPConfig(capacity_kw_thermal=inp.gshp_kw_thermal)
        g = hydro_geo.simulate_gshp(site, gc)
        capex = marketplace.price_capex("geothermal_gshp", inp.gshp_kw_thermal,
                                        inp.cost_level)
        # Heating savings: incumbent delivered-heat cost minus GSHP electricity cost.
        incumbent_heat_cost = (g.heat_demand_kwh / inp.incumbent_heat_cop) * \
            inp.incumbent_heat_fuel_price_per_kwh
        gshp_heat_elec_cost = g.elec_for_heat_kwh * inp.electricity_price
        heat_savings = incumbent_heat_cost - gshp_heat_elec_cost
        # Cooling savings: efficiency gain vs a standard AC (both electric).
        incumbent_cool_elec = g.cool_demand_kwh / inp.incumbent_cool_cop
        cool_savings = (incumbent_cool_elec - g.elec_for_cool_kwh) * inp.electricity_price
        annual_heat_savings = heat_savings + cool_savings
        e = economics.evaluate(capex["gross_capex"], 0.0, inp.gshp_kw_thermal,
                               ctx, econ_cfg, extra_annual_savings=annual_heat_savings)
        report["technologies"]["geothermal"] = {
            "heat_demand_kwh": g.heat_demand_kwh,
            "cool_demand_kwh": g.cool_demand_kwh,
            "gshp_electricity_kwh": g.total_gshp_elec_kwh,
            "bore_length_m": g.bore_length_m,
            "annual_heating_savings_dollar": round(heat_savings, 2),
            "annual_cooling_savings_dollar": round(cool_savings, 2),
            "gross_capex": capex["gross_capex"], "economics": _econ_dict(e),
            "buy_at": capex["marketplaces"],
            "gshp_kw_thermal": inp.gshp_kw_thermal,
        }
        rankable.append(("geothermal", g.heat_demand_kwh, e.npv, e.simple_payback_years))

    # ---- Ranking (by NPV) ------------------------------------------------ #
    rankable.sort(key=lambda r: (r[2] if r[2] is not None else -1e12), reverse=True)
    report["ranking"] = [
        {"technology": t, "annual_kwh_or_thermal": round(kwh, 1),
         "npv": npv, "payback_years": pb}
        for (t, kwh, npv, pb) in rankable
    ]
    report["incentive_note_2026"] = (
        "US federal residential credit (IRC 25D) is $0 for systems placed in "
        "service after 2025 (OBBBA). State/utility incentives via DSIRE and "
        "lease/PPA passthrough may still apply. Verify with a tax professional."
    )
    return report


def _econ_dict(e: economics.EconResult) -> dict:
    return {
        "gross_capex": e.gross_capex, "net_capex": e.net_capex,
        "incentives": e.incentives, "year1_savings": e.year1_savings,
        "simple_payback_years": e.simple_payback_years,
        "lcoe_per_kwh": e.lcoe_per_kwh, "npv": e.npv, "irr_percent": e.irr_percent,
    }


if __name__ == "__main__":
    inp = AssessmentInputs(lat=49.8951, lon=-97.1384, allow_network=False,
                           pv_kw=6.0, wind_kw=10.0, tax_year=2026,
                           electricity_price=0.106)
    print(json.dumps(run_assessment(inp), indent=2))
