"""
Maps API contract inputs → engine inputs, and engine outputs → camelCase API responses.
This is the snake_case ↔ camelCase boundary.
"""
from __future__ import annotations
import uuid
import math
from typing import Any, Optional

from renewable_retrofit import resource, solar, wind as wind_mod, hydro_geo, economics, marketplace
from renewable_retrofit.model import AssessmentInputs, run_assessment


# ── Input translation ──────────────────────────────────────────────────────────

_ROOF_TO_PV_KW = {"small": 5.0, "medium": 8.0, "large": 12.0}
_ROOF_TO_WIND_KW = {"small": 5.0, "medium": 10.0, "large": 15.0}
_ROOF_TO_BATTERY_KWH = {"small": 10.0, "medium": 13.5, "large": 20.0}
_ROOF_TO_GSHP_KW = {"small": 7.0, "medium": 10.5, "large": 14.0}

_MONTHLY_BILL_TO_KWH = {
    "under_100": 600,
    "100_200": 1200,
    "200_300": 1800,
    "over_300": 2600,
}

_HEATING_INCUMBENT = {
    "gas": "gas",
    "electric": "electric",
    "oil": "oil",
    "heat_pump": "heat_pump",
    "not_sure": "gas",
}


def build_engine_inputs(req: dict, allow_network: bool = True) -> AssessmentInputs:
    size = req.get("roofOrLotSize", "medium")
    features = req.get("siteFeatures", [])
    goals = req.get("goals", [])

    include_wind = "windy" in features or "open_land" in features
    include_gshp = True  # always model geothermal for comparison
    opts = req.get("options", {}) or {}
    tax_year = opts.get("taxYear") or 2026
    electricity_price = opts.get("electricityPrice")  # may be None
    currency = opts.get("currency", "USD")

    return AssessmentInputs(
        lat=req.get("lat"),
        lon=req.get("lon"),
        address=req.get("address", ""),
        allow_network=allow_network,
        pv_kw=_ROOF_TO_PV_KW.get(size, 8.0),
        battery_kwh=_ROOF_TO_BATTERY_KWH.get(size) if ("backup_power" in goals or "all" in goals) else None,
        wind_kw=_ROOF_TO_WIND_KW.get(size) if include_wind else None,
        gshp_kw_thermal=_ROOF_TO_GSHP_KW.get(size) if include_gshp else None,
        tax_year=tax_year,
        electricity_price=electricity_price,
    )


# ── Output serialization ───────────────────────────────────────────────────────

def serialize_assessment(result: dict, req: dict, assessment_id: str) -> dict:
    site: resource.Site = result["site"]
    techs = result["technologies"]
    ranking = result["ranking"]
    ctx: economics.IncentiveContext = result["incentive_context"]
    opts = req.get("options", {}) or {}
    currency = opts.get("currency", "CAD" if _is_canada(site) else "USD")

    tech_list = _serialize_technologies(techs, result["electricity_price"])
    # Sort by npv descending (recommended first)
    tech_list.sort(key=lambda t: (t["recommended"] is False, -(t["npv25yr"] or -999999)))

    ranking_out = [
        {
            "type": r["technology"],
            "npv25yr": r["npv"],
            "paybackYears": r["payback"],
        }
        for r in ranking
    ]

    # Find lead recommended tech for payback curve
    lead = next((t for t in tech_list if t["recommended"] and t["paybackYears"]), None)
    if not lead:
        lead = next((t for t in tech_list if t["recommended"]), None)

    return {
        "assessmentId": assessment_id,
        "currency": currency,
        "site": _serialize_site(site),
        "electricityPrice": result["electricity_price"],
        "priceSource": result["price_source"],
        "technologies": tech_list,
        "ranking": ranking_out,
        "incentiveSummary": {
            "taxYear": ctx.tax_year,
            "federalCreditRate": ctx.federal_credit_rate,
            "note": result["fed_note"],
            "moreInfoUrl": "https://www.dsireusa.org/",
        },
        "charts": _make_charts(site, lead),
        "disclaimer": "These results are an estimate for planning. They are not a quote or financial advice.",
    }


def _serialize_site(site: resource.Site) -> dict:
    return {
        "resolvedAddress": site.address,
        "lat": site.lat,
        "lon": site.lon,
        "elevationM": site.elevation_m,
        "annualSunlightKwhM2": site.annual_ghi_kwh_m2,
        "meanTempC": site.mean_temp_c,
        "averageWindSpeedMs": site.wind_speed_10m_ms,
        "groundTempC": site.ground_temp_c,
        "dataSource": site.data_source,
        "dataNote": site.data_note,
    }


def _serialize_technologies(techs: dict, elec_price: float) -> list[dict]:
    out = []

    if "solar_pv" in techs:
        t = techs["solar_pv"]
        e: economics.EconResult = t["economics"]
        pv: solar.PVResult = t["pv"]
        out.append({
            "type": "solar_pv",
            "displayName": "Solar panels",
            "recommended": e.npv > 0 or e.simple_payback_years is not None,
            "systemSizeKw": pv.__class__.__name__ and _get_pv_kw(pv),
            "annualKwh": pv.annual_ac_kwh,
            "specificYieldKwhPerKw": pv.specific_yield_kwh_kw,
            "capacityFactor": pv.capacity_factor,
            "grossCapex": e.gross_capex,
            "incentives": e.incentives,
            "netCapex": e.net_capex,
            "yearlySavings": e.yearly_savings,
            "paybackYears": e.simple_payback_years,
            "lcoePerKwh": e.lcoe_per_kwh,
            "npv25yr": e.npv,
            "irr": e.irr,
            "reason": _reason_solar(pv, e),
            "buyAt": t["buy_at"],
        })

    if "battery" in techs:
        t = techs["battery"]
        e = t["economics"]
        out.append({
            "type": "battery",
            "displayName": "Battery storage",
            "recommended": True,  # always useful if included
            "systemSizeKwh": t["system_kwh"],
            "annualKwh": None,
            "grossCapex": e.gross_capex,
            "incentives": e.incentives,
            "netCapex": e.net_capex,
            "yearlySavings": e.yearly_savings,
            "paybackYears": None,
            "lcoePerKwh": None,
            "npv25yr": e.npv,
            "irr": None,
            "reason": "Pairs with solar to keep the lights on during outages, which is one of your goals.",
            "buyAt": t["buy_at"],
        })

    if "wind" in techs:
        t = techs["wind"]
        e = t["economics"]
        w: wind_mod.WindResult = t["wind"]
        wind_kw = t.get("rated_kw", round(e.gross_capex / 6750, 1))
        recommended = w.mean_hub_height_wind_ms >= 5.0 and e.npv > 0
        out.append({
            "type": "wind",
            "displayName": "Wind",
            "recommended": recommended,
            "systemSizeKw": wind_kw,
            "annualKwh": w.annual_kwh,
            "capacityFactor": w.capacity_factor,
            "meanHubHeightWindMs": w.mean_hub_height_wind_ms,
            "grossCapex": e.gross_capex,
            "incentives": e.incentives,
            "netCapex": e.net_capex,
            "yearlySavings": e.yearly_savings,
            "paybackYears": e.simple_payback_years,
            "lcoePerKwh": e.lcoe_per_kwh,
            "npv25yr": e.npv,
            "irr": e.irr,
            "reason": _reason_wind(w, e),
            "buyAt": t["buy_at"],
        })

    if "geothermal" in techs:
        t = techs["geothermal"]
        e = t["economics"]
        g: hydro_geo.GSHPResult = t["gshp"]
        out.append({
            "type": "geothermal",
            "displayName": "Geothermal",
            "recommended": e.npv > 0,
            "systemSizeKwThermal": g.system_size_kw_thermal,
            "annualKwh": None,
            "heatDemandKwh": g.heat_demand_kwh,
            "coolDemandKwh": g.cool_demand_kwh,
            "boreLengthM": g.bore_length_m,
            "grossCapex": e.gross_capex,
            "incentives": e.incentives,
            "netCapex": e.net_capex,
            "annualHeatingSavings": round(e.yearly_savings * 0.65),
            "annualCoolingSavings": round(e.yearly_savings * 0.35),
            "yearlySavings": e.yearly_savings,
            "paybackYears": e.simple_payback_years,
            "lcoePerKwh": None,
            "npv25yr": e.npv,
            "irr": None,
            "reason": _reason_geo(g, e),
            "buyAt": t["buy_at"],
        })

    if "micro_hydro" in techs:
        t = techs["micro_hydro"]
        e = t["economics"]
        h: hydro_geo.HydroResult = t["hydro"]
        out.append({
            "type": "micro_hydro",
            "displayName": "Micro-hydro",
            "recommended": e.npv > 0,
            "systemSizeKw": h.power_kw,
            "annualKwh": h.annual_kwh,
            "grossCapex": e.gross_capex,
            "incentives": e.incentives,
            "netCapex": e.net_capex,
            "yearlySavings": e.yearly_savings,
            "paybackYears": e.simple_payback_years,
            "lcoePerKwh": e.lcoe_per_kwh,
            "npv25yr": e.npv,
            "irr": e.irr,
            "reason": "A stream-fed micro-hydro system can provide continuous renewable power.",
            "buyAt": t["buy_at"],
        })

    return out


def _get_pv_kw(pv: solar.PVResult) -> float:
    # Reverse from specific yield: annual_kwh / specific_yield = kW
    if pv.specific_yield_kwh_kw and pv.specific_yield_kwh_kw > 0:
        return round(pv.annual_ac_kwh / pv.specific_yield_kwh_kw, 1)
    return 8.0


def _make_charts(site: resource.Site, lead: Optional[dict]) -> dict:
    monthly = [round(v, 1) for v in site.monthly_ghi_kwh_m2]

    if lead and lead.get("netCapex") and lead.get("yearlySavings"):
        net = lead["netCapex"]
        savings = lead["yearlySavings"]
        years = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25]
        cash = [-net] + [round(-net + savings * y) for y in years[1:]]
        payback_curve = {"years": years, "cumulativeCashFlow": cash}
    else:
        payback_curve = {"years": [], "cumulativeCashFlow": []}

    return {
        "monthlySunlightKwhM2": monthly,
        "paybackCurve": payback_curve,
    }


def _reason_solar(pv: solar.PVResult, e: economics.EconResult) -> str:
    if pv.capacity_factor >= 0.18:
        return "Excellent year-round sunlight makes solar the strongest fit for this location."
    if pv.capacity_factor >= 0.13:
        return "Your roof gets steady sunlight through the year, which makes solar the strongest fit."
    return "Moderate sunlight makes solar viable; payback depends on local electricity prices."


def _reason_wind(w: wind_mod.WindResult, e: economics.EconResult) -> str:
    if w.mean_hub_height_wind_ms >= 6.0 and e.npv > 0:
        return "Strong average wind speeds make a turbine a solid complement to solar here."
    if w.mean_hub_height_wind_ms >= 5.0:
        return "There is usable wind here, but the upfront cost is high for the power it would make."
    return "Wind speeds are below the cost-effective threshold for residential turbines."


def _reason_geo(g: hydro_geo.GSHPResult, e: economics.EconResult) -> str:
    if e.npv > 0:
        return "Ground temperatures are stable here and can cut heating and cooling costs significantly."
    return "Works well technically, but with current local energy prices the savings are modest."


def _is_canada(site: resource.Site) -> bool:
    return site.lon < -50 and site.lat > 42 and site.lon > -141
