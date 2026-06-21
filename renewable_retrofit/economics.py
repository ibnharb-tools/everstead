"""
economics.py
============
Step 7: Cost, incentives, and savings.

IMPORTANT 2026 U.S. POLICY UPDATE
---------------------------------
The federal Residential Clean Energy Credit (IRC Section 25D) -- the 30% credit
for homeowner-OWNED solar, wind, geothermal and battery -- was terminated for
property *placed in service after December 31, 2025* by the One Big Beautiful
Bill Act (OBBBA, P.L. 119-21). For a cash/loan purchase completed in 2026 or
later the federal residential credit is therefore $0. Nuances this model encodes:
  * `tax_year <= 2025`            -> 30% federal credit available (legacy).
  * `tax_year >= 2026` + owned    -> 0% federal credit.
  * `financing == "lease_ppa"`    -> the third-party owner may still claim the
                                     commercial credit (Sec. 48E); some of that
                                     value is typically passed through as lower
                                     lease payments (modeled as `ppa_passthrough`).
  * Non-U.S. sites                -> federal credit not applicable; use local.
Always confirm with current IRS guidance / a tax professional. Sources:
  * IRS Residential Clean Energy Credit: https://www.irs.gov/credits-deductions/residential-clean-energy-credit
  * CRS, expiration & carryforward: https://www.congress.gov/crs-product/IN12611
State / utility incentives (the part that still matters in 2026):
  * DSIRE database: https://www.dsireusa.org/

FINANCE FORMULAS
----------------
Capital recovery factor:  CRF = i(1+i)^n / ((1+i)^n - 1)
LCOE:                     LCOE = (CRF * Capex_net + O&M_annual) / E_annual
Simple payback:           SPB = Capex_net / Annual_savings_year1
NPV:                      NPV = -Capex_net + sum_t (Savings_t - O&M_t)/(1+r)^t
   with PV degradation, electricity-price escalation, and inverter replacement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------- #
#  Incentive logic
# --------------------------------------------------------------------------- #
@dataclass
class IncentiveContext:
    country: str = "US"
    tax_year: int = 2026
    financing: str = "owned"          # "owned" | "loan" | "lease_ppa"
    state_credit_fraction: float = 0.0  # e.g. NY 25% (capped) -> set fraction
    state_credit_cap: float = 1e12
    upfront_rebates: float = 0.0      # utility/state $ that reduce basis up front
    ppa_passthrough: float = 0.0      # $ value passed through in a lease/PPA


def federal_residential_credit(capex_after_rebates: float,
                               ctx: IncentiveContext) -> float:
    """Federal Sec. 25D credit. 30% through 2025; $0 for 2026+ owned systems."""
    if ctx.country != "US":
        return 0.0
    if ctx.financing == "lease_ppa":
        # Homeowner doesn't claim 25D; benefit arrives via passthrough instead.
        return 0.0
    if ctx.tax_year <= 2025:
        return 0.30 * capex_after_rebates
    return 0.0  # OBBBA: terminated for property placed in service after 2025


def total_incentives(capex_gross: float, ctx: IncentiveContext) -> dict:
    after_rebates = max(0.0, capex_gross - ctx.upfront_rebates)
    fed = federal_residential_credit(after_rebates, ctx)
    state = min(ctx.state_credit_fraction * after_rebates, ctx.state_credit_cap)
    passthrough = ctx.ppa_passthrough if ctx.financing == "lease_ppa" else 0.0
    total = ctx.upfront_rebates + fed + state + passthrough
    return {
        "upfront_rebates": round(ctx.upfront_rebates, 2),
        "federal_credit": round(fed, 2),
        "state_credit": round(state, 2),
        "lease_passthrough": round(passthrough, 2),
        "total_incentives": round(total, 2),
        "net_capex": round(capex_gross - total, 2),
    }


# --------------------------------------------------------------------------- #
#  Project economics
# --------------------------------------------------------------------------- #
@dataclass
class EconConfig:
    electricity_price_per_kwh: float = 0.16
    export_price_per_kwh: float = 0.06   # net-metering / feed-in for surplus
    self_consumption_fraction: float = 0.6  # share of generation used on-site
    price_escalation: float = 0.025      # annual utility price growth
    discount_rate: float = 0.05
    analysis_years: int = 25
    pv_degradation: float = 0.005        # annual yield loss for PV
    om_per_kw_year: float = 18.0         # O&M $/kW-yr
    inverter_replace_year: int = 13
    inverter_replace_cost_per_kw: float = 150.0


@dataclass
class EconResult:
    gross_capex: float
    incentives: dict
    net_capex: float
    year1_savings: float
    simple_payback_years: Optional[float]
    lcoe_per_kwh: float
    npv: float
    irr_percent: Optional[float]
    annual_cashflows: list = field(default_factory=list)


def _crf(i: float, n: int) -> float:
    if i == 0:
        return 1.0 / n
    return i * (1 + i) ** n / ((1 + i) ** n - 1)


def annual_energy_value(gen_kwh: float, cfg: EconConfig, year: int) -> float:
    """$ value of one year of generation, splitting self-use vs export, escalated."""
    esc = (1 + cfg.price_escalation) ** (year - 1)
    self_kwh = gen_kwh * cfg.self_consumption_fraction
    exp_kwh = gen_kwh * (1 - cfg.self_consumption_fraction)
    return (self_kwh * cfg.electricity_price_per_kwh
            + exp_kwh * cfg.export_price_per_kwh) * esc


def _irr(cashflows, lo=-0.9, hi=1.0, tol=1e-6):
    """Bisection IRR; returns None if no sign change."""
    def npv(r):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(cashflows))
    if npv(lo) * npv(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        v = npv(mid)
        if abs(v) < tol:
            return mid
        if npv(lo) * v < 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def evaluate(gross_capex: float, annual_generation_kwh: float,
             capacity_kw: float, ctx: IncentiveContext,
             cfg: EconConfig | None = None,
             extra_annual_savings: float = 0.0) -> EconResult:
    """Full techno-economic evaluation for one technology (or a bundle).

    extra_annual_savings: e.g. GSHP heating-fuel displacement not captured by
    `annual_generation_kwh` (which is electricity generation).
    """
    cfg = cfg or EconConfig()
    inc = total_incentives(gross_capex, ctx)
    net = inc["net_capex"]

    om = cfg.om_per_kw_year * capacity_kw
    cashflows = [-net]
    year1 = None
    for yr in range(1, cfg.analysis_years + 1):
        gen = annual_generation_kwh * (1 - cfg.pv_degradation) ** (yr - 1)
        value = annual_energy_value(gen, cfg, yr) + extra_annual_savings * \
            (1 + cfg.price_escalation) ** (yr - 1)
        cash = value - om
        if yr == cfg.inverter_replace_year:
            cash -= cfg.inverter_replace_cost_per_kw * capacity_kw
        if yr == 1:
            year1 = value - om
        cashflows.append(cash)

    # Discounted NPV.
    npv = sum(cf / (1 + cfg.discount_rate) ** t for t, cf in enumerate(cashflows))

    # LCOE over lifetime energy.
    crf = _crf(cfg.discount_rate, cfg.analysis_years)
    life_energy = sum(annual_generation_kwh * (1 - cfg.pv_degradation) ** (y - 1)
                      for y in range(1, cfg.analysis_years + 1))
    avg_energy = life_energy / cfg.analysis_years if cfg.analysis_years else 0
    lcoe = ((crf * net + om) / avg_energy) if avg_energy > 0 else None

    # Simple payback against year-1 net savings.
    spb = (net / year1) if (year1 and year1 > 0) else None
    irr = _irr(cashflows)

    return EconResult(
        gross_capex=round(gross_capex, 2),
        incentives=inc,
        net_capex=round(net, 2),
        year1_savings=round(year1, 2) if year1 is not None else None,
        simple_payback_years=round(spb, 1) if spb else None,
        lcoe_per_kwh=round(lcoe, 4) if lcoe is not None else None,
        npv=round(npv, 2),
        irr_percent=round(irr * 100, 2) if irr is not None else None,
        annual_cashflows=[round(c, 2) for c in cashflows],
    )


if __name__ == "__main__":
    # 6 kW PV, $2.80/W gross, Phoenix-ish 10,000 kWh/yr.
    capex = 6.0 * 1000 * 2.80
    print("--- 2025 (legacy 30% federal) ---")
    print(evaluate(capex, 10000, 6.0,
                   IncentiveContext(tax_year=2025), EconConfig()).incentives)
    print("--- 2026 (federal expired) ---")
    r = evaluate(capex, 10000, 6.0, IncentiveContext(tax_year=2026), EconConfig())
    print(r.incentives)
    print("net capex", r.net_capex, "| payback", r.simple_payback_years,
          "yr | LCOE", r.lcoe_per_kwh, "| NPV", r.npv, "| IRR", r.irr_percent, "%")
