"""
cli.py
======
Command-line entry point.

Examples
--------
  # By coordinates, live NASA POWER data:
  python -m renewable_retrofit.cli --lat 33.45 --lon -112.07 --pv-kw 8 \
         --price 0.15 --tax-year 2026

  # By address (needs internet for geocoding):
  python -m renewable_retrofit.cli --address "1600 Amphitheatre Pkwy, Mountain View, CA"

  # Offline demo (uses synthetic climatology fallback):
  python -m renewable_retrofit.cli --lat 49.90 --lon -97.14 --offline
"""
from __future__ import annotations

import argparse
import json

from .model import AssessmentInputs, run_assessment


def main(argv=None):
    p = argparse.ArgumentParser(description="Home renewable-energy retrofit model")
    loc = p.add_mutually_exclusive_group(required=True)
    loc.add_argument("--address", type=str, help="Street address to geocode")
    loc.add_argument("--lat", type=float, help="Latitude (use with --lon)")
    p.add_argument("--lon", type=float, help="Longitude")
    p.add_argument("--offline", action="store_true",
                   help="Skip network; use synthetic climatology fallback")

    p.add_argument("--pv-kw", type=float, default=6.0)
    p.add_argument("--battery-kwh", type=float, default=0.0)
    p.add_argument("--wind-kw", type=float, default=10.0)
    p.add_argument("--gshp-kw", type=float, default=10.5)
    p.add_argument("--hydro-head", type=float, default=0.0, help="net head (m)")
    p.add_argument("--hydro-flow", type=float, default=0.0, help="flow (L/s)")

    p.add_argument("--no-solar", action="store_true")
    p.add_argument("--no-wind", action="store_true")
    p.add_argument("--no-geo", action="store_true")

    p.add_argument("--tax-year", type=int, default=2026)
    p.add_argument("--country", type=str, default="US")
    p.add_argument("--financing", type=str, default="owned",
                   choices=["owned", "loan", "lease_ppa"])
    p.add_argument("--price", type=float, default=0.16, help="$/kWh retail")
    p.add_argument("--export-price", type=float, default=0.06)
    p.add_argument("--rebates", type=float, default=0.0, help="upfront $ rebates")
    p.add_argument("--state-credit", type=float, default=0.0,
                   help="state credit fraction, e.g. 0.25")
    p.add_argument("--cost-level", type=str, default="typical",
                   choices=["low", "typical", "high"])
    p.add_argument("--json", action="store_true", help="emit full JSON")
    args = p.parse_args(argv)

    if args.lat is not None and args.lon is None:
        p.error("--lat requires --lon")

    inp = AssessmentInputs(
        address=args.address, lat=args.lat, lon=args.lon,
        allow_network=not args.offline,
        eval_solar=not args.no_solar, eval_wind=not args.no_wind,
        eval_geothermal=not args.no_geo,
        eval_hydro=(args.hydro_head > 0 and args.hydro_flow > 0),
        pv_kw=args.pv_kw, battery_kwh=args.battery_kwh, wind_kw=args.wind_kw,
        gshp_kw_thermal=args.gshp_kw, hydro_head_m=args.hydro_head,
        hydro_flow_lps=args.hydro_flow, tax_year=args.tax_year,
        country=args.country, financing=args.financing,
        electricity_price=args.price, export_price=args.export_price,
        upfront_rebates=args.rebates, state_credit_fraction=args.state_credit,
        cost_level=args.cost_level,
    )
    report = run_assessment(inp)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    s = report["site"]
    print(f"\n=== SITE: {s['label']} ===")
    print(f"  {s['latitude']:.4f}, {s['longitude']:.4f} | elev {s['elevation_m']} m"
          f" | GHI {s['annual_GHI_kWh_m2']} kWh/m2/yr | mean T {s['mean_air_temp_C']} C")
    print(f"  Data: {s['data_source']}")

    print("\n=== TECHNOLOGY RESULTS ===")
    for t, v in report["technologies"].items():
        e = v["economics"]
        kwh = v.get("annual_kwh", v.get("heat_demand_kwh", 0))
        lcoe = e.get("lcoe_per_kwh")
        lcoe_s = f"${lcoe}/kWh" if lcoe is not None else "n/a (thermal)"
        print(f"\n  [{t.upper()}]")
        print(f"    Energy:    {kwh:,.0f} kWh/yr")
        print(f"    Gross capex: ${e['gross_capex']:,.0f}  ->  net ${e['net_capex']:,.0f}")
        print(f"    Incentives:  {e['incentives']['total_incentives']:,.0f} "
              f"(fed {e['incentives']['federal_credit']:,.0f}, "
              f"state {e['incentives']['state_credit']:,.0f}, "
              f"rebate {e['incentives']['upfront_rebates']:,.0f})")
        print(f"    Year-1 savings: ${e['year1_savings']:,.0f}"
              if e['year1_savings'] is not None else "    Year-1 savings: n/a")
        print(f"    Payback: {e['simple_payback_years']} yr | LCOE {lcoe_s} | "
              f"NPV ${e['npv']:,.0f} | IRR {e['irr_percent']}%")
        print(f"    Buy/compare: {', '.join(v['buy_at'][:3])}")

    print("\n=== RANKING (by 25-yr NPV) ===")
    for i, r in enumerate(report["ranking"], 1):
        print(f"  {i}. {r['technology']:12s}  NPV ${r['npv']:>11,.0f}  "
              f"payback {r['payback_years']} yr")

    print(f"\nNOTE: {report['incentive_note_2026']}")


if __name__ == "__main__":
    main()
