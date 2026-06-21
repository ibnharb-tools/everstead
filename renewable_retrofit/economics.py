"""
Step 7: LCOE, payback, NPV, IRR, incentives.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class IncentiveContext:
    tax_year: int = 2026
    country: str = "US"
    upfront_rebates: float = 0.0
    state_credit_fraction: float = 0.0

    @property
    def federal_credit_rate(self) -> float:
        if self.country.upper() == "US" and self.tax_year <= 2025:
            return 0.30
        return 0.0


@dataclass
class EconConfig:
    electricity_price_per_kwh: float = 0.13
    export_price_per_kwh: float = 0.07
    self_consumption_fraction: float = 0.75
    discount_rate: float = 0.04
    escalation_rate: float = 0.02
    pv_degradation_rate: float = 0.005
    project_life_years: int = 25
    om_annual_per_kw: float = 20.0      # $/kW/yr O&M
    inverter_replacement_year: int = 12
    inverter_replacement_cost: float = 1500.0


@dataclass
class EconResult:
    incentives: dict
    federal_credit_rate: float
    gross_capex: float
    net_capex: float
    yearly_savings: float
    simple_payback_years: Optional[float]
    lcoe_per_kwh: Optional[float]
    npv: float
    irr: Optional[float]
    irr_percent: Optional[float]


def total_incentives(gross_capex: float, ctx: IncentiveContext) -> dict:
    fed = round(gross_capex * ctx.federal_credit_rate)
    state = round(gross_capex * ctx.state_credit_fraction)
    rebates = round(ctx.upfront_rebates)
    total = fed + state + rebates
    return {"federal": fed, "state": state, "rebates": rebates, "total": total}


def evaluate(
    gross_capex: float,
    annual_kwh: float,
    system_kw: float,
    ctx: IncentiveContext,
    cfg: EconConfig,
    yearly_savings_override: Optional[float] = None,
) -> EconResult:
    inc = total_incentives(gross_capex, ctx)
    net = gross_capex - inc["total"]

    if yearly_savings_override is not None:
        yr1_savings = yearly_savings_override
    else:
        # Self-consumption at retail; surplus at export rate
        yr1_savings = annual_kwh * (
            cfg.self_consumption_fraction * cfg.electricity_price_per_kwh
            + (1 - cfg.self_consumption_fraction) * cfg.export_price_per_kwh
        )
    yr1_savings = round(yr1_savings)

    om_annual = cfg.om_annual_per_kw * system_kw

    # LCOE
    if annual_kwh > 0:
        i = cfg.discount_rate
        n = cfg.project_life_years
        crf = i * (1 + i) ** n / ((1 + i) ** n - 1)
        lcoe = round((crf * net + om_annual) / annual_kwh, 4)
    else:
        lcoe = None

    # Simple payback
    if yr1_savings > 0:
        payback = round(net / yr1_savings, 1)
    else:
        payback = None

    # NPV over project life
    npv = -net
    savings_t = yr1_savings
    for t in range(1, cfg.project_life_years + 1):
        annual_om = om_annual
        if t == cfg.inverter_replacement_year:
            annual_om += cfg.inverter_replacement_cost
        net_cash = savings_t - annual_om
        npv += net_cash / (1 + cfg.discount_rate) ** t
        savings_t *= (1 + cfg.escalation_rate) * (1 - cfg.pv_degradation_rate)
    npv = round(npv)

    # IRR — bisection
    irr = _irr(net, yr1_savings, om_annual, cfg)
    irr_pct = round(irr * 100, 1) if irr is not None else None

    return EconResult(
        incentives=inc,
        federal_credit_rate=ctx.federal_credit_rate,
        gross_capex=gross_capex,
        net_capex=round(net),
        yearly_savings=yr1_savings,
        simple_payback_years=payback,
        lcoe_per_kwh=lcoe,
        npv=npv,
        irr=irr,
        irr_percent=irr_pct,
    )


def _irr(net_capex: float, yr1_savings: float, om_annual: float, cfg: EconConfig) -> Optional[float]:
    def _npv_at_r(r: float) -> float:
        v = -net_capex
        s = yr1_savings
        for t in range(1, cfg.project_life_years + 1):
            om = om_annual + (cfg.inverter_replacement_cost if t == cfg.inverter_replacement_year else 0)
            v += (s - om) / (1 + r) ** t
            s *= (1 + cfg.escalation_rate) * (1 - cfg.pv_degradation_rate)
        return v

    if _npv_at_r(0.0) <= 0:
        return None  # project never pays back

    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _npv_at_r(mid) > 0:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 4)
