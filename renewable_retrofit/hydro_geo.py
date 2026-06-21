"""
hydro_geo.py
============
Step 5: Micro-hydro power and Step 6: Ground-source (geothermal) heat pump.

MICRO-HYDRO
-----------
Hydraulic power:        P = rho * g * Q * H_net * eta
  rho = 1000 kg/m^3, g = 9.81 m/s^2, Q = flow [m^3/s], H_net = net head [m],
  eta = overall efficiency (turbine x generator x penstock), 0.5-0.85 typical.
Annual energy:          E = P * 8760 * availability
Head and flow are intensely site-specific (you need a stream on or near the
property), so they are user inputs. Resources:
  * US DOE micro-hydro guide: https://www.energy.gov/energysaver/microhydropower-systems
  * USGS StreamStats (flow estimates): https://streamstats.usgs.gov/

GROUND-SOURCE HEAT PUMP (GSHP)
------------------------------
This DISPLACES heating/cooling energy rather than generating electricity.
Building load via degree-days (ASHRAE):
  Q_heat_annual [kWh] = (UA * HDD * 24) / 1000           UA [W/K], HDD in K*day
  Q_cool_annual [kWh] = (UA * CDD * 24) / 1000
Electricity to run the GSHP:
  E_gshp = Q_thermal / COP        (COP_heat ~ 3.5-5.0, COP_cool/EER high)
Savings vs an incumbent system are computed in economics.py from delivered-heat
cost differences. Vertical bore length rule of thumb (Kavanaugh & Rafferty):
  ~ 60-110 m of bore per ton (3.5 kW) of capacity depending on ground conductivity.
References:
  * ASHRAE Handbook -- HVAC Applications, Geothermal Energy chapter.
  * Kavanaugh & Rafferty, *Geothermal Heating and Cooling* (ASHRAE, 2014).
  * US DOE: https://www.energy.gov/energysaver/geothermal-heat-pumps
"""
from __future__ import annotations

from dataclasses import dataclass
from .resource import Site, DAYS_IN_MONTH

RHO_WATER = 1000.0
G = 9.81


# --------------------------------------------------------------------------- #
#  Micro-hydro
# --------------------------------------------------------------------------- #
@dataclass
class HydroResult:
    rated_power_kw: float
    annual_kwh: float
    capacity_factor: float
    net_head_m: float
    flow_m3s: float


def simulate_hydro(net_head_m: float, flow_lps: float, efficiency: float = 0.55,
                   availability: float = 0.90) -> HydroResult:
    """net_head_m: usable head after penstock losses. flow_lps: design flow in L/s."""
    q = flow_lps / 1000.0  # L/s -> m^3/s
    p_w = RHO_WATER * G * q * net_head_m * efficiency
    p_kw = p_w / 1000.0
    annual = p_kw * 8760.0 * availability
    return HydroResult(
        rated_power_kw=round(p_kw, 3),
        annual_kwh=round(annual, 1),
        capacity_factor=round(availability, 3),
        net_head_m=net_head_m,
        flow_m3s=round(q, 4),
    )


# --------------------------------------------------------------------------- #
#  Degree-days from monthly normals
# --------------------------------------------------------------------------- #
def degree_days(site: Site, base_heat_c: float = 18.0, base_cool_c: float = 18.0):
    """Approximate annual HDD / CDD (K*day) from monthly mean temperatures."""
    hdd = sum(max(0.0, base_heat_c - t) * d
              for t, d in zip(site.temp_air_c, DAYS_IN_MONTH))
    cdd = sum(max(0.0, t - base_cool_c) * d
              for t, d in zip(site.temp_air_c, DAYS_IN_MONTH))
    return round(hdd, 1), round(cdd, 1)


# --------------------------------------------------------------------------- #
#  Ground-source heat pump
# --------------------------------------------------------------------------- #
@dataclass
class GSHPConfig:
    ua_w_per_k: float = 250.0        # whole-house heat-loss coefficient (W/K)
    cop_heat: float = 4.0            # seasonal heating COP (ground-source)
    cop_cool: float = 5.0            # seasonal cooling COP
    base_heat_c: float = 18.0
    base_cool_c: float = 21.0
    capacity_kw_thermal: float = 10.5  # ~3 tons


@dataclass
class GSHPResult:
    heat_demand_kwh: float
    cool_demand_kwh: float
    elec_for_heat_kwh: float
    elec_for_cool_kwh: float
    total_gshp_elec_kwh: float
    bore_length_m: float
    hdd: float
    cdd: float
    config: GSHPConfig


def simulate_gshp(site: Site, cfg: GSHPConfig | None = None) -> GSHPResult:
    cfg = cfg or GSHPConfig()
    hdd, cdd = degree_days(site, cfg.base_heat_c, cfg.base_cool_c)

    heat_kwh = cfg.ua_w_per_k * hdd * 24.0 / 1000.0
    cool_kwh = cfg.ua_w_per_k * cdd * 24.0 / 1000.0
    e_heat = heat_kwh / cfg.cop_heat
    e_cool = cool_kwh / cfg.cop_cool

    # Vertical bore length: ~ 24 m of bore per kW_thermal (mid-range conductivity).
    bore = cfg.capacity_kw_thermal * 24.0

    return GSHPResult(
        heat_demand_kwh=round(heat_kwh, 1),
        cool_demand_kwh=round(cool_kwh, 1),
        elec_for_heat_kwh=round(e_heat, 1),
        elec_for_cool_kwh=round(e_cool, 1),
        total_gshp_elec_kwh=round(e_heat + e_cool, 1),
        bore_length_m=round(bore, 1),
        hdd=hdd, cdd=cdd, config=cfg,
    )


if __name__ == "__main__":
    from .resource import from_coordinates, fetch_climate
    s = fetch_climate(from_coordinates(44.98, -93.27, "Minneapolis", 254),
                      allow_network=False)
    g = simulate_gshp(s)
    print("GSHP heat demand", g.heat_demand_kwh, "kWh | elec", g.total_gshp_elec_kwh,
          "kWh | bore", g.bore_length_m, "m | HDD", g.hdd)
    h = simulate_hydro(net_head_m=12.0, flow_lps=20.0)
    print("Hydro 12 m / 20 L/s ->", h.rated_power_kw, "kW,", h.annual_kwh, "kWh/yr")
