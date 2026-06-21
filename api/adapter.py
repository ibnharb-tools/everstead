"""
Maps API contract inputs → engine inputs, and engine outputs → camelCase API responses.
This is the snake_case ↔ camelCase boundary.

Engine output keys (snake_case) → API contract keys (camelCase).
"""
from __future__ import annotations
from typing import Optional

from renewable_retrofit.model import AssessmentInputs
from renewable_retrofit.resource import DAYS_IN_MONTH

# ── Input translation ──────────────────────────────────────────────────────────

_ROOF_TO_PV_KW = {"small": 5.0, "medium": 8.0, "large": 12.0}
_ROOF_TO_WIND_KW = {"small": 5.0, "medium": 10.0, "large": 15.0}
_ROOF_TO_BATTERY_KWH = {"small": 10.0, "medium": 13.5, "large": 20.0}
_ROOF_TO_GSHP_KW = {"small": 7.0, "medium": 10.5, "large": 14.0}

# URL → {name, url} mapping for buy_at links
_URL_NAMES = {
    "https://www.energysage.com/": {"name": "EnergySage", "url": "https://www.energysage.com/"},
    "https://signaturesolar.com/": {"name": "Signature Solar", "url": "https://signaturesolar.com/"},
    "https://unboundsolar.com/": {"name": "Unbound Solar", "url": "https://unboundsolar.com/"},
    "https://www.cedgreentech.com/": {"name": "CED Greentech", "url": "https://www.cedgreentech.com/"},
    "https://bergey.com/": {"name": "Bergey Windpower", "url": "https://bergey.com/"},
    "https://www.primuswindpower.com/": {"name": "Primus WindPower", "url": "https://www.primuswindpower.com/"},
    "https://www.energy.gov/energysaver/microhydropower-systems": {"name": "DOE Micro-Hydro Guide", "url": "https://www.energy.gov/energysaver/microhydropower-systems"},
    "https://www.waterfurnace.com/": {"name": "WaterFurnace", "url": "https://www.waterfurnace.com/"},
    "https://www.climatemaster.com/": {"name": "ClimateMaster", "url": "https://www.climatemaster.com/"},
}


def _buy_at(urls: list[str]) -> list[dict]:
    return [_URL_NAMES.get(u, {"name": u, "url": u}) for u in urls]


def build_engine_inputs(req: dict, allow_network: bool = True) -> AssessmentInputs:
    size = req.get("roofOrLotSize", "medium")
    features = req.get("siteFeatures") or []
    goals = req.get("goals") or []
    opts = req.get("options") or {}

    include_wind = "windy" in features or "open_land" in features
    include_battery = "backup_power" in goals or "all" in goals
    tax_year = opts.get("taxYear") or 2026
    electricity_price = opts.get("electricityPrice") or 0.15

    lat = req.get("lat")
    lon = req.get("lon")
    # Prefer explicit coordinates over address to avoid geocoding when offline.
    address = "" if (lat is not None and lon is not None) else (req.get("address") or "")

    return AssessmentInputs(
        lat=lat,
        lon=lon,
        address=address,
        allow_network=allow_network,
        eval_solar=True,
        eval_wind=include_wind,
        eval_hydro="stream" in features,
        eval_geothermal=True,
        pv_kw=_ROOF_TO_PV_KW.get(size, 8.0),
        battery_kwh=_ROOF_TO_BATTERY_KWH.get(size, 13.5) if include_battery else 0.0,
        wind_kw=_ROOF_TO_WIND_KW.get(size, 10.0),
        gshp_kw_thermal=_ROOF_TO_GSHP_KW.get(size, 10.5),
        tax_year=tax_year,
        electricity_price=electricity_price,
    )


# ── Output serialization ───────────────────────────────────────────────────────

def serialize_assessment(result: dict, req: dict, assessment_id: str,
                         user_provided_price: bool = False) -> dict:
    site_summary = result["site"]
    techs = result["technologies"]
    ranking = result["ranking"]
    monthly_climate = result["monthly_climate"]
    opts = req.get("options") or {}
    currency = opts.get("currency") or (_guess_currency(site_summary))

    tech_list = _serialize_technologies(techs)
    # Sort: recommended first, then by NPV descending
    tech_list.sort(key=lambda t: (not t["recommended"], -(t["npv25yr"] or -999999)))

    ranking_out = [
        {"type": _engine_tech_to_api(r["technology"]), "npv25yr": r["npv"], "paybackYears": r["payback_years"]}
        for r in ranking
    ]

    # Lead recommended tech for payback curve
    lead = next((t for t in tech_list if t["recommended"] and t.get("netCapex") and t.get("yearlySavings")), None)
    if not lead:
        lead = next((t for t in tech_list if t["recommended"]), None)

    # Determine federal credit rate from first tech with real capex
    fed_rate = 0.0
    for _t in tech_list:
        gross = _t.get("grossCapex")
        if gross and gross > 0:
            fed_rate = round(_t["incentives"]["federal"] / gross, 2)
            break

    # Tax year context
    tax_year = opts.get("taxYear") or 2026
    if tax_year <= 2025:
        fed_rate = 0.30
        fed_note = ("The federal residential clean energy credit is 30% for systems "
                    "placed in service in 2025 or earlier.")
    else:
        fed_rate = 0.0
        fed_note = ("The federal residential clean energy credit is 0 for systems placed "
                    "in service after 2025. Local and utility rebates may still apply. "
                    "Confirm details with a local expert.")

    electricity_price = opts.get("electricityPrice")
    price_source = "user_provided" if electricity_price else "regional_default"
    if not electricity_price:
        electricity_price = 0.15

    return {
        "assessmentId": assessment_id,
        "currency": currency,
        "site": _serialize_site(site_summary),
        "electricityPrice": electricity_price,
        "priceSource": price_source,
        "technologies": tech_list,
        "ranking": ranking_out,
        "incentiveSummary": {
            "taxYear": tax_year,
            "federalCreditRate": fed_rate,
            "note": fed_note,
            "moreInfoUrl": "https://www.dsireusa.org/",
        },
        "charts": _make_charts(monthly_climate, lead),
        "disclaimer": "These results are an estimate for planning. They are not a quote or financial advice.",
    }


def _serialize_site(s: dict) -> dict:
    ds = s.get("data_source", "")
    if "NASA POWER" in ds:
        data_note = "Based on long term climate averages for your location."
    elif "OFFLINE" in ds or "offline" in ds:
        data_note = "Synthetic climate estimate used — live data unavailable."
    else:
        data_note = ds

    return {
        "resolvedAddress": s.get("label", ""),
        "lat": s.get("latitude"),
        "lon": s.get("longitude"),
        "elevationM": s.get("elevation_m"),
        "annualSunlightKwhM2": s.get("annual_GHI_kWh_m2"),
        "meanTempC": s.get("mean_air_temp_C"),
        "averageWindSpeedMs": s.get("mean_wind_10m_ms"),
        "groundTempC": s.get("ground_temp_C"),
        "dataSource": "NASA POWER" if "NASA POWER" in ds else ds,
        "dataNote": data_note,
    }


def _engine_tech_to_api(key: str) -> str:
    return {"hydro": "micro_hydro"}.get(key, key)


def _serialize_technologies(techs: dict) -> list[dict]:
    out = []

    if "solar_pv" in techs:
        t = techs["solar_pv"]
        e = t["economics"]
        inc = _map_incentives(e["incentives"])
        battery_kwh = t.get("battery_kwh")
        recommended = (e["npv"] or 0) > -5000  # recommend unless deeply negative
        out.append({
            "type": "solar_pv",
            "displayName": "Solar panels" + (" + battery" if battery_kwh else ""),
            "recommended": recommended,
            "systemSizeKw": t.get("pv_kw", 8.0),
            "annualKwh": t.get("annual_kwh"),
            "specificYieldKwhPerKw": t.get("specific_yield_kwh_kw"),
            "capacityFactor": t.get("capacity_factor"),
            "grossCapex": e["gross_capex"],
            "incentives": inc,
            "netCapex": e["net_capex"],
            "yearlySavings": e["year1_savings"],
            "paybackYears": e["simple_payback_years"],
            "lcoePerKwh": e["lcoe_per_kwh"],
            "npv25yr": e["npv"],
            "irr": round(e["irr_percent"] / 100, 4) if e["irr_percent"] is not None else None,
            "reason": _reason_solar(t),
            "buyAt": _buy_at(t.get("buy_at", [])),
        })
        # If battery bundled into solar, add it as a separate entry
        if battery_kwh:
            out.append({
                "type": "battery",
                "displayName": "Battery storage",
                "recommended": True,
                "systemSizeKwh": battery_kwh,
                "annualKwh": None,
                "grossCapex": None,   # bundled with solar above
                "incentives": {"federal": 0, "state": 0, "rebates": 0, "total": 0},
                "netCapex": None,
                "yearlySavings": None,
                "paybackYears": None,
                "lcoePerKwh": None,
                "npv25yr": None,
                "irr": None,
                "reason": "Pairs with solar to keep the lights on during outages, which is one of your goals.",
                "buyAt": _buy_at(["https://www.energysage.com/", "https://signaturesolar.com/"]),
            })

    if "wind" in techs:
        t = techs["wind"]
        e = t["economics"]
        inc = _map_incentives(e["incentives"])
        v_hub = t.get("mean_hubheight_ms", 0)
        recommended = v_hub >= 5.0 and (e["npv"] or 0) > 0
        out.append({
            "type": "wind",
            "displayName": "Wind",
            "recommended": recommended,
            "systemSizeKw": t.get("wind_kw", 10.0),
            "annualKwh": t.get("annual_kwh"),
            "capacityFactor": t.get("capacity_factor"),
            "meanHubHeightWindMs": v_hub,
            "grossCapex": e["gross_capex"],
            "incentives": inc,
            "netCapex": e["net_capex"],
            "yearlySavings": e["year1_savings"],
            "paybackYears": e["simple_payback_years"],
            "lcoePerKwh": e["lcoe_per_kwh"],
            "npv25yr": e["npv"],
            "irr": round(e["irr_percent"] / 100, 4) if e["irr_percent"] is not None else None,
            "reason": _reason_wind(t),
            "buyAt": _buy_at(t.get("buy_at", [])),
        })

    if "geothermal" in techs:
        t = techs["geothermal"]
        e = t["economics"]
        inc = _map_incentives(e["incentives"])
        recommended = (e["npv"] or 0) > 0
        heat_sav = t.get("annual_heating_savings_dollar", 0) or 0
        cool_sav = t.get("annual_cooling_savings_dollar", 0) or 0
        out.append({
            "type": "geothermal",
            "displayName": "Geothermal",
            "recommended": recommended,
            "systemSizeKwThermal": t.get("gshp_kw_thermal", 10.5),
            "annualKwh": None,
            "heatDemandKwh": t.get("heat_demand_kwh"),
            "coolDemandKwh": t.get("cool_demand_kwh"),
            "boreLengthM": t.get("bore_length_m"),
            "grossCapex": e["gross_capex"],
            "incentives": inc,
            "netCapex": e["net_capex"],
            "annualHeatingSavings": round(heat_sav),
            "annualCoolingSavings": round(cool_sav),
            "yearlySavings": e["year1_savings"],
            "paybackYears": e["simple_payback_years"],
            "lcoePerKwh": None,
            "npv25yr": e["npv"],
            "irr": None,
            "reason": _reason_geo(t, e),
            "buyAt": _buy_at(t.get("buy_at", [])),
        })

    if "hydro" in techs:
        t = techs["hydro"]
        e = t["economics"]
        inc = _map_incentives(e["incentives"])
        out.append({
            "type": "micro_hydro",
            "displayName": "Micro-hydro",
            "recommended": (e["npv"] or 0) > 0,
            "systemSizeKw": t.get("rated_power_kw"),
            "annualKwh": t.get("annual_kwh"),
            "grossCapex": e["gross_capex"],
            "incentives": inc,
            "netCapex": e["net_capex"],
            "yearlySavings": e["year1_savings"],
            "paybackYears": e["simple_payback_years"],
            "lcoePerKwh": e["lcoe_per_kwh"],
            "npv25yr": e["npv"],
            "irr": round(e["irr_percent"] / 100, 4) if e["irr_percent"] is not None else None,
            "reason": "A stream-fed micro-hydro system can provide continuous renewable power.",
            "buyAt": _buy_at(t.get("buy_at", [])),
        })

    return out


def _map_incentives(inc: dict) -> dict:
    """Map engine incentive dict → API contract incentive shape."""
    federal = round(inc.get("federal_credit", 0))
    state = round(inc.get("state_credit", 0))
    rebates = round(inc.get("upfront_rebates", 0))
    total = federal + state + rebates
    return {"federal": federal, "state": state, "rebates": rebates, "total": total}


def _make_charts(monthly_climate: dict, lead: Optional[dict]) -> dict:
    ghi_daily = monthly_climate.get("ghi_kwh_m2_day", [0] * 12)
    monthly_totals = [round(g * d, 1) for g, d in zip(ghi_daily, DAYS_IN_MONTH)]

    if lead and lead.get("netCapex") and lead.get("yearlySavings"):
        net = lead["netCapex"]
        savings = lead["yearlySavings"]
        years = [0, 1, 2, 3, 4, 5, 10, 15, 20, 25]
        cash = [-net] + [round(-net + savings * y) for y in years[1:]]
        payback_curve = {"years": years, "cumulativeCashFlow": cash}
    else:
        payback_curve = {"years": [], "cumulativeCashFlow": []}

    return {"monthlySunlightKwhM2": monthly_totals, "paybackCurve": payback_curve}


def _reason_solar(t: dict) -> str:
    cf = t.get("capacity_factor", 0)
    if cf >= 0.18:
        return "Excellent year-round sunlight makes solar the strongest fit for this location."
    if cf >= 0.13:
        return "Your roof gets steady sunlight through the year, which makes solar the strongest fit."
    return "Moderate sunlight makes solar viable; payback depends on local electricity prices."


def _reason_wind(t: dict) -> str:
    v = t.get("mean_hubheight_ms", 0)
    npv = t.get("economics", {}).get("npv", 0) or 0
    if v >= 6.0 and npv > 0:
        return "Strong average wind speeds make a turbine a solid complement to solar here."
    if v >= 5.0:
        return "There is usable wind here, but the upfront cost is high for the power it would make."
    return "Wind speeds are below the cost-effective threshold for residential turbines."


def _reason_geo(t: dict, e: dict) -> str:
    if (e.get("npv") or 0) > 0:
        return "Ground temperatures are stable here and can cut heating and cooling costs significantly."
    return "Works well technically, but with current local energy prices the savings are modest."


def _guess_currency(site_summary: dict) -> str:
    lat = site_summary.get("latitude", 0)
    lon = site_summary.get("longitude", 0)
    # Canada: roughly lon < -50, lat > 42, lon > -141
    if lon is not None and lat is not None and lon < -50 and lat > 42 and lon > -141:
        return "CAD"
    return "USD"
