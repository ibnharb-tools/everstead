"""
Step 9: Orchestrator — run_assessment.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from . import resource, solar, wind, hydro_geo, economics, marketplace


@dataclass
class AssessmentInputs:
    lat: Optional[float] = None
    lon: Optional[float] = None
    address: str = ""
    allow_network: bool = True

    pv_kw: float = 8.0
    battery_kwh: Optional[float] = None
    wind_kw: Optional[float] = None
    gshp_kw_thermal: Optional[float] = None
    hydro_head_m: Optional[float] = None
    hydro_flow_lps: Optional[float] = None

    tax_year: int = 2026
    country: str = "US"
    electricity_price: Optional[float] = None
    export_price: float = 0.07
    upfront_rebates: float = 0.0
    state_credit_fraction: float = 0.0


def run_assessment(inputs: AssessmentInputs) -> dict:
    # 1. Resolve site
    if inputs.lat is None or inputs.lon is None:
        if not inputs.address:
            raise ValueError("Either lat/lon or address must be provided")
        lat, lon, resolved = resource.geocode(inputs.address)
        elevation = resource.get_elevation(lat, lon)
        site = resource.Site(lat=lat, lon=lon, address=resolved, elevation_m=elevation)
    else:
        site = resource.Site(
            lat=inputs.lat, lon=inputs.lon, address=inputs.address, elevation_m=0.0
        )

    site = resource.fetch_climate(site, allow_network=inputs.allow_network)

    electricity_price = inputs.electricity_price or _regional_default_price(site)
    price_source = "user_provided" if inputs.electricity_price else "regional_default"

    ctx = economics.IncentiveContext(
        tax_year=inputs.tax_year,
        country=inputs.country,
        upfront_rebates=inputs.upfront_rebates,
        state_credit_fraction=inputs.state_credit_fraction,
    )
    cfg = economics.EconConfig(
        electricity_price_per_kwh=electricity_price,
        export_price_per_kwh=inputs.export_price,
    )

    technologies = {}

    # Solar PV
    pv_cfg = solar.PVConfig(dc_capacity_kw=inputs.pv_kw)
    pv_res = solar.simulate_pv(site, pv_cfg)
    capex_pv = marketplace.price_capex("solar_pv", inputs.pv_kw)["gross_capex"]
    econ_pv = economics.evaluate(capex_pv, pv_res.annual_ac_kwh, inputs.pv_kw, ctx, cfg)
    technologies["solar_pv"] = {
        "pv": pv_res,
        "economics": econ_pv,
        "buy_at": marketplace._BENCHMARKS["solar_pv"]["buy_at"],
        "annual_kwh": pv_res.annual_ac_kwh,
        "heat_demand_kwh": None,
    }

    # Battery
    if inputs.battery_kwh:
        capex_bat = marketplace.price_capex("battery", inputs.battery_kwh)["gross_capex"]
        # Battery savings: assume 15% bill reduction from time-of-use arbitrage
        bat_savings = pv_res.annual_ac_kwh * electricity_price * 0.15
        econ_bat = economics.evaluate(capex_bat, 0, inputs.battery_kwh, ctx, cfg,
                                      yearly_savings_override=bat_savings)
        technologies["battery"] = {
            "economics": econ_bat,
            "buy_at": marketplace._BENCHMARKS["battery"]["buy_at"],
            "annual_kwh": None,
            "heat_demand_kwh": None,
            "system_kwh": inputs.battery_kwh,
        }

    # Wind
    if inputs.wind_kw:
        turbine = wind.TurbineSpec(rated_kw=inputs.wind_kw)
        wind_res = wind.simulate_wind(site, turbine)
        capex_wind = marketplace.price_capex("wind", inputs.wind_kw)["gross_capex"]
        econ_wind = economics.evaluate(capex_wind, wind_res.annual_kwh, inputs.wind_kw, ctx, cfg)
        technologies["wind"] = {
            "wind": wind_res,
            "economics": econ_wind,
            "buy_at": marketplace._BENCHMARKS["wind"]["buy_at"],
            "annual_kwh": wind_res.annual_kwh,
            "heat_demand_kwh": None,
            "rated_kw": inputs.wind_kw,
        }

    # Geothermal GSHP
    if inputs.gshp_kw_thermal:
        gshp_cfg = hydro_geo.GSHPConfig(kw_thermal=inputs.gshp_kw_thermal)
        gshp_res = hydro_geo.simulate_gshp(site, gshp_cfg)
        capex_geo = marketplace.price_capex("geothermal", inputs.gshp_kw_thermal)["gross_capex"]
        # Savings: replacing gas/electric heat at electricity price with COP advantage
        incumbent_cost = (gshp_res.heat_demand_kwh + gshp_res.cool_demand_kwh) * electricity_price
        gshp_elec_cost = gshp_res.annual_kwh_electric * electricity_price
        geo_savings = max(0, incumbent_cost - gshp_elec_cost)
        econ_geo = economics.evaluate(capex_geo, 0, inputs.gshp_kw_thermal, ctx, cfg,
                                      yearly_savings_override=geo_savings)
        technologies["geothermal"] = {
            "gshp": gshp_res,
            "economics": econ_geo,
            "buy_at": marketplace._BENCHMARKS["geothermal"]["buy_at"],
            "annual_kwh": None,
            "heat_demand_kwh": gshp_res.heat_demand_kwh,
        }

    # Micro-hydro
    if inputs.hydro_head_m and inputs.hydro_flow_lps:
        hydro_res = hydro_geo.simulate_hydro(inputs.hydro_head_m, inputs.hydro_flow_lps)
        capex_hydro = marketplace.price_capex("micro_hydro", hydro_res.power_kw)["gross_capex"]
        econ_hydro = economics.evaluate(capex_hydro, hydro_res.annual_kwh, hydro_res.power_kw, ctx, cfg)
        technologies["micro_hydro"] = {
            "hydro": hydro_res,
            "economics": econ_hydro,
            "buy_at": marketplace._BENCHMARKS["micro_hydro"]["buy_at"],
            "annual_kwh": hydro_res.annual_kwh,
            "heat_demand_kwh": None,
        }

    ranking = sorted(
        [{"technology": k, "npv": v["economics"].npv, "payback": v["economics"].simple_payback_years}
         for k, v in technologies.items()],
        key=lambda x: x["npv"],
        reverse=True,
    )

    fed_note = (
        "The federal residential clean energy credit is 30% for systems placed in service in 2025 or earlier."
        if ctx.tax_year <= 2025
        else "The federal residential clean energy credit is 0 for systems placed in service after 2025. "
             "Local and utility rebates may still apply. Confirm details with a local expert."
    )

    return {
        "site": site,
        "technologies": technologies,
        "ranking": ranking,
        "electricity_price": electricity_price,
        "price_source": price_source,
        "incentive_context": ctx,
        "fed_note": fed_note,
        "monthly_ghi": site.monthly_ghi_kwh_m2,
    }


def _regional_default_price(site: resource.Site) -> float:
    """Rough regional default electricity price in USD."""
    lat, lon = site.lat, site.lon
    # Canada
    if lon < -50 and lat > 42:
        return 0.11  # CAD-ish blend
    # US west coast
    if lon < -110 and lat > 30:
        return 0.22
    # US northeast
    if lon > -80 and lat > 40:
        return 0.22
    # US average
    if -130 < lon < -60 and 24 < lat < 50:
        return 0.15
    return 0.13
