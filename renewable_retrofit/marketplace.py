"""
Step 8: Equipment cost benchmarks and vendor links.
"""
from __future__ import annotations

# Installed cost benchmarks (per unit as noted)
_BENCHMARKS = {
    "solar_pv": {
        "low_per_w": 2.10, "high_per_w": 3.80, "unit": "per_watt", "currency": "USD",
        "vendors": [
            {"name": "EnergySage", "url": "https://www.energysage.com/", "kind": "comparison"},
            {"name": "Signature Solar", "url": "https://signaturesolar.com/", "kind": "retailer"},
            {"name": "Unbound Solar", "url": "https://unboundsolar.com/", "kind": "retailer"},
            {"name": "CED Greentech", "url": "https://www.cedgreentech.com/", "kind": "distributor"},
        ],
        "buy_at": [
            {"name": "EnergySage", "url": "https://www.energysage.com/"},
            {"name": "Signature Solar", "url": "https://signaturesolar.com/"},
        ],
    },
    "battery": {
        "low_per_kwh": 800, "high_per_kwh": 1500, "unit": "per_kwh", "currency": "USD",
        "vendors": [
            {"name": "EnergySage", "url": "https://www.energysage.com/", "kind": "comparison"},
            {"name": "Signature Solar", "url": "https://signaturesolar.com/", "kind": "retailer"},
        ],
        "buy_at": [
            {"name": "Signature Solar", "url": "https://signaturesolar.com/"},
        ],
    },
    "wind": {
        "low_per_kw": 3500, "high_per_kw": 10000, "unit": "per_kw", "currency": "USD",
        "vendors": [
            {"name": "Bergey Windpower", "url": "https://bergey.com/", "kind": "manufacturer"},
            {"name": "Primus WindPower", "url": "https://www.primuswindpower.com/", "kind": "manufacturer"},
        ],
        "buy_at": [
            {"name": "Bergey Windpower", "url": "https://bergey.com/"},
        ],
    },
    "micro_hydro": {
        "low_per_kw": 2500, "high_per_kw": 12000, "unit": "per_kw", "currency": "USD",
        "vendors": [
            {"name": "Harris Hydro", "url": "https://www.harrishydro.com/", "kind": "retailer"},
        ],
        "buy_at": [
            {"name": "Harris Hydro", "url": "https://www.harrishydro.com/"},
        ],
    },
    "geothermal": {
        "low_per_kw_thermal": 1800, "high_per_kw_thermal": 4500, "unit": "per_kw_thermal", "currency": "USD",
        "vendors": [
            {"name": "WaterFurnace", "url": "https://www.waterfurnace.com/", "kind": "manufacturer"},
            {"name": "ClimateMaster", "url": "https://www.climatemaster.com/", "kind": "manufacturer"},
        ],
        "buy_at": [
            {"name": "WaterFurnace", "url": "https://www.waterfurnace.com/"},
        ],
    },
}

# Mid-range cost multipliers for capex calculation
_MIDPOINT = {
    "solar_pv": ("mid_per_w", lambda b: (b["low_per_w"] + b["high_per_w"]) / 2),
    "battery": ("mid_per_kwh", lambda b: (b["low_per_kwh"] + b["high_per_kwh"]) / 2),
    "wind": ("mid_per_kw", lambda b: (b["low_per_kw"] + b["high_per_kw"]) / 2),
    "micro_hydro": ("mid_per_kw", lambda b: (b["low_per_kw"] + b["high_per_kw"]) / 2),
    "geothermal": ("mid_per_kw_thermal", lambda b: (b["low_per_kw_thermal"] + b["high_per_kw_thermal"]) / 2),
}


def price_capex(tech: str, size: float) -> dict:
    """Return gross_capex for a given technology and size."""
    b = _BENCHMARKS[tech]
    _, mid_fn = _MIDPOINT[tech]
    mid = mid_fn(b)
    # Size units: solar_pv in kW→W, battery in kWh, wind/hydro in kW, geo in kW_thermal
    if tech == "solar_pv":
        gross = mid * size * 1000  # $/W × W
    else:
        gross = mid * size
    return {"gross_capex": round(gross)}


def catalog_table() -> dict:
    return _BENCHMARKS


def get_marketplace(tech: str) -> dict:
    b = _BENCHMARKS[tech]
    low_key = [k for k in b if k.startswith("low_")][0]
    high_key = [k for k in b if k.startswith("high_")][0]
    return {
        "technology": tech,
        "costBand": {"low": b[low_key], "high": b[high_key], "unit": b["unit"], "currency": b["currency"]},
        "vendors": b["vendors"],
        "note": "Cost bands are typical ranges, not live prices.",
    }
