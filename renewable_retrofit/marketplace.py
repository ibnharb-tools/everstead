"""
marketplace.py
==============
Step 8: Equipment marketplace + cost benchmarks.

Prices move constantly, so this module stores DATED, SOURCED cost *ranges* (not
live quotes) anchored to authoritative benchmarks, plus links to real
marketplaces where each item can be compared and purchased. Use `price_capex()`
to turn a system size into a gross-capex estimate, then feed that into
economics.evaluate(). For a binding number, always pull live quotes.

Authoritative cost references
  * NREL Annual Technology Baseline (ATB):           https://atb.nrel.gov/
  * NREL U.S. PV + Storage Cost Benchmark:           https://www.nrel.gov/solar/market-research-analysis/solar-installed-system-cost.html
  * NREL Distributed Wind / small wind:              https://www.nrel.gov/wind/distributed-wind.html
  * DOE Geothermal Heat Pump cost data:              https://www.energy.gov/energysaver/geothermal-heat-pumps

Comparison / purchase marketplaces (real)
  * Solar quotes & comparison ....... EnergySage      https://www.energysage.com/
  * DIY / wholesale solar+battery ... Signature Solar https://signaturesolar.com/
                                      Wholesale Solar / Unbound  https://unboundsolar.com/
                                      CED Greentech (distributor) https://www.cedgreentech.com/
  * Small wind turbines ............. Bergey          https://bergey.com/
                                      Primus WindPower https://www.primuswindpower.com/
  * Micro-hydro ..................... Canyon Hydro / Scott Hydro / Harris Hydro (search)
  * Geothermal heat pumps ........... WaterFurnace    https://www.waterfurnace.com/
                                      ClimateMaster   https://www.climatemaster.com/
  * Batteries ....................... Tesla Powerwall, Enphase, EG4 (via above retailers)
  * Find certified installers ....... NABCEP          https://www.nabcep.org/
"""
from __future__ import annotations

from dataclasses import dataclass

BENCHMARK_DATE = "NREL benchmarks ~2023-2024 $, escalate for current year"


@dataclass
class CostBand:
    low: float
    typical: float
    high: float
    unit: str
    note: str = ""


# Installed (turnkey) cost benchmarks. USD. Ranges reflect DIY-low to full-install-high.
CATALOG = {
    "solar_pv": {
        "unit_basis": "per_w_dc",
        "cost": CostBand(2.10, 2.90, 3.80, "$/W_dc",
                         "NREL 2023 residential benchmark ~$2.90/W turnkey; "
                         "DIY/wholesale modules alone ~$0.30-0.45/W."),
        "marketplaces": ["https://www.energysage.com/", "https://signaturesolar.com/",
                         "https://unboundsolar.com/", "https://www.cedgreentech.com/"],
    },
    "battery": {
        "unit_basis": "per_kwh",
        "cost": CostBand(800, 1100, 1500, "$/kWh",
                         "NREL 2023 benchmark ~$1,000-1,400/kWh installed; "
                         "must be >=3 kWh to have qualified for legacy 25D."),
        "marketplaces": ["https://www.energysage.com/", "https://signaturesolar.com/"],
    },
    "wind_small": {
        "unit_basis": "per_kw",
        "cost": CostBand(3500, 6000, 10000, "$/kW",
                         "Distributed/small wind installed cost is high per kW "
                         "(towers, permitting); 5-10 kW class typical."),
        "marketplaces": ["https://bergey.com/", "https://www.primuswindpower.com/"],
    },
    "micro_hydro": {
        "unit_basis": "per_kw",
        "cost": CostBand(2500, 5000, 12000, "$/kW",
                         "Highly site-specific (intake, penstock, civil works); "
                         "very low $/kWh where good head+flow exist."),
        "marketplaces": ["https://www.energy.gov/energysaver/microhydropower-systems"],
    },
    "geothermal_gshp": {
        "unit_basis": "per_kw_thermal",
        "cost": CostBand(1800, 2800, 4500, "$/kW_th",
                         "GSHP incl. ground loop ~$18k-$45k for a home (3-5 ton); "
                         "ground-loop drilling dominates cost."),
        "marketplaces": ["https://www.waterfurnace.com/",
                         "https://www.climatemaster.com/"],
    },
    "solar_thermal": {
        "unit_basis": "per_m2_collector",
        "cost": CostBand(600, 900, 1300, "$/m^2",
                         "Solar water heating; 2-4 collectors typical per home."),
        "marketplaces": ["https://www.energy.gov/energysaver/solar-water-heaters"],
    },
}


def price_capex(tech: str, size: float, level: str = "typical") -> dict:
    """Estimate gross installed capex.

    tech  : key in CATALOG
    size  : kW_dc (solar), kWh (battery), kW (wind/hydro), kW_thermal (gshp), m^2 (thermal)
    level : 'low' | 'typical' | 'high'
    """
    if tech not in CATALOG:
        raise KeyError(f"Unknown tech {tech!r}; options: {list(CATALOG)}")
    band = CATALOG[tech]["cost"]
    rate = {"low": band.low, "typical": band.typical, "high": band.high}[level]
    basis = CATALOG[tech]["unit_basis"]
    # Solar quoted per-W: convert kW -> W.
    multiplier = size * 1000.0 if basis == "per_w_dc" else size
    return {
        "tech": tech,
        "size": size,
        "rate": rate,
        "unit": band.unit,
        "gross_capex": round(rate * multiplier, 2),
        "note": band.note,
        "marketplaces": CATALOG[tech]["marketplaces"],
        "benchmark_basis": BENCHMARK_DATE,
    }


def catalog_table() -> list:
    rows = []
    for k, v in CATALOG.items():
        b = v["cost"]
        rows.append({
            "technology": k,
            "low": b.low, "typical": b.typical, "high": b.high, "unit": b.unit,
            "buy_at": ", ".join(v["marketplaces"][:2]),
        })
    return rows


if __name__ == "__main__":
    import json
    print(json.dumps(price_capex("solar_pv", 6.0), indent=2))
    print(json.dumps(price_capex("battery", 13.5, "typical"), indent=2))
    for r in catalog_table():
        print(r["technology"], r["low"], "-", r["high"], r["unit"])
