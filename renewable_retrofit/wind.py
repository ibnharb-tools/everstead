"""
wind.py
=======
Step 4: Small/residential wind turbine energy yield.

Physics
-------
Power in the wind through swept area A:      P = 0.5 * rho * A * v^3
Extractable (Betz limit Cp_max = 16/27 = 0.593):  P_e = 0.5 * rho * A * v^3 * Cp
Hub-height wind from a reference height (power law / Hellmann):
        v(h) = v_ref * (h / h_ref) ^ alpha          alpha ~ 0.143 open terrain
Long-term energy uses the Weibull wind-speed distribution:
        f(v) = (k/c) (v/c)^(k-1) exp(-(v/c)^k)
        AEP = 8760 * sum_v f(v) * P_turbine(v) * dv
with the turbine's real power curve (cut-in -> rated -> cut-out).

References:
  * Manwell, McGowan & Rogers, *Wind Energy Explained*, 2nd ed. (Wiley).
  * IEC 61400-2 (small wind turbines).
  * Global Wind Atlas (resource maps): https://globalwindatlas.info/
  * NREL Wind Resource data: https://www.nrel.gov/gis/wind.html
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .resource import Site

BETZ = 16.0 / 27.0  # 0.5926


@dataclass
class TurbineSpec:
    """A small wind turbine power curve (piecewise). Defaults ~ Bergey Excel 10."""
    name: str = "generic 10 kW"
    rated_power_kw: float = 10.0
    rotor_diameter_m: float = 7.0
    cut_in_ms: float = 2.5
    rated_ms: float = 11.0
    cut_out_ms: float = 25.0
    cp: float = 0.35                 # realized power coefficient below rated
    hub_height_m: float = 24.0

    @property
    def swept_area_m2(self) -> float:
        return math.pi * (self.rotor_diameter_m / 2.0) ** 2

    def power_kw(self, v: float, rho: float = 1.225) -> float:
        """Electrical power [kW] at hub-height wind speed v [m/s]."""
        if v < self.cut_in_ms or v >= self.cut_out_ms:
            return 0.0
        if v >= self.rated_ms:
            return self.rated_power_kw
        # Cubic ramp from cut-in to rated, capped at aerodynamic limit.
        p_aero = 0.5 * rho * self.swept_area_m2 * v ** 3 * self.cp / 1000.0
        return min(p_aero, self.rated_power_kw)


@dataclass
class WindResult:
    annual_kwh: float
    capacity_factor: float
    mean_hubheight_ms: float
    weibull_k: float
    weibull_c: float
    turbine: TurbineSpec


def _weibull_params(v_mean: float, k: float = 2.0):
    """Scale c from mean speed & shape k:  v_mean = c * Gamma(1 + 1/k)."""
    c = v_mean / math.gamma(1.0 + 1.0 / k)
    return k, c


def _shear_to_hub(v_ref: float, h_ref: float, h_hub: float,
                  alpha: float = 0.143) -> float:
    return v_ref * (h_hub / h_ref) ** alpha


def simulate_wind(site: Site, turbine: TurbineSpec | None = None,
                  shear_alpha: float = 0.143, weibull_k: float = 2.0) -> WindResult:
    turbine = turbine or TurbineSpec()
    rho = site.air_density()

    # Use the higher NASA POWER anchor (50 m) when available for a better shear fit.
    v10 = sum(site.wind_10m_ms) / 12 if site.wind_10m_ms else 4.0
    if site.wind_50m_ms and sum(site.wind_50m_ms) > 0:
        v50 = sum(site.wind_50m_ms) / 12
        # Fit alpha from the 10 m / 50 m pair, then project to hub height.
        if v10 > 0 and v50 > 0:
            shear_alpha = math.log(v50 / v10) / math.log(50.0 / 10.0)
        v_hub = _shear_to_hub(v50, 50.0, turbine.hub_height_m, shear_alpha)
    else:
        v_hub = _shear_to_hub(v10, 10.0, turbine.hub_height_m, shear_alpha)

    k, c = _weibull_params(v_hub, weibull_k)

    # Numerically integrate AEP = 8760 * sum f(v) P(v) dv.
    vs = np.arange(0.0, turbine.cut_out_ms + 1.0, 0.25)
    dv = 0.25
    f = (k / c) * (vs / c) ** (k - 1) * np.exp(-((vs / c) ** k))
    p = np.array([turbine.power_kw(v, rho) for v in vs])
    annual_kwh = float(8760.0 * np.sum(f * p * dv))
    cf = annual_kwh / (turbine.rated_power_kw * 8760.0) if turbine.rated_power_kw else 0.0

    return WindResult(
        annual_kwh=round(annual_kwh, 1),
        capacity_factor=round(cf, 3),
        mean_hubheight_ms=round(v_hub, 2),
        weibull_k=round(k, 2),
        weibull_c=round(c, 2),
        turbine=turbine,
    )


def viability_note(result: WindResult) -> str:
    v = result.mean_hubheight_ms
    if v < 4.0:
        return ("Marginal: mean hub-height wind < 4 m/s. Residential wind is "
                "rarely cost-effective below ~5 m/s (NREL small-wind guidance).")
    if v < 5.5:
        return "Borderline: 4-5.5 m/s. Worth it only with good siting & incentives."
    return "Favorable: >5.5 m/s mean. Wind can be a meaningful contributor."


if __name__ == "__main__":
    from .resource import from_coordinates, fetch_climate
    s = fetch_climate(from_coordinates(41.25, -101.0, "W. Nebraska", 1000),
                      allow_network=False)
    # bump fallback wind to a windy-plains value for demonstration
    s.wind_10m_ms = [6.5] * 12
    s.wind_50m_ms = [8.2] * 12
    r = simulate_wind(s)
    print(r.turbine.name, "->", r.annual_kwh, "kWh/yr, CF", r.capacity_factor,
          "| v_hub", r.mean_hubheight_ms, "m/s")
    print(viability_note(r))
