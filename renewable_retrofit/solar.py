"""
solar.py
========
Step 3: Solar PV energy yield via the NREL PVWatts(R) v5 model chain, implemented
with pvlib-python (Sandia/PVSC reference library, https://pvlib-python.readthedocs.io).

Method (representative-day-per-month, Duffie & Beckman, *Solar Engineering of
Thermal Processes*, 4th ed.):
  1. For the mid-month day, compute sun position hour-by-hour (pvlib.solarposition).
  2. Build clear-sky GHI (Ineichen) and scale it so the day's total equals the
     NASA POWER monthly-mean GHI -> realistic hourly GHI shape.
  3. Decompose GHI -> DNI + DHI with the Erbs model (pvlib.irradiance.erbs).
  4. Transpose to the tilted plane-of-array with Hay-Davies
     (pvlib.irradiance.get_total_irradiance).
  5. Cell temperature from the PVWatts thermal model (pvlib.temperature.pvsyst...
     -> here Sandia/Faiman), then DC power (pvlib.pvsystem.pvwatts_dc),
     inverter clip (pvlib.inverter.pvwatts), and a system-loss derate.
  6. Sum the representative day and scale by days-in-month -> monthly & annual kWh.

Core PVWatts equations
----------------------
  P_dc  = (G_poa / 1000) * P_dc0 * (1 + gamma_pdc * (T_cell - 25))
  T_cell= T_air + (G_poa / 800) * (NOCT - 20)              [NOCT cell-temp model]
  P_ac  = min(P_dc * eta_inv, P_ac0)                       [inverter clipping]
  E     = P_ac * dt  -> integrate
NREL PVWatts technical reference: https://www.nrel.gov/docs/fy14osti/62641.pdf
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np
import pandas as pd

import pvlib
from pvlib import solarposition, irradiance, location as pvloc

from .resource import Site, DAYS_IN_MONTH

# Representative ("mean radiation") day-of-year for each month (Klein 1977)
REP_DOY = [17, 47, 75, 105, 135, 162, 198, 228, 258, 288, 318, 344]


@dataclass
class PVConfig:
    dc_capacity_kw: float = 6.0       # nameplate DC (kW)
    tilt_deg: float | None = None     # None -> use |latitude| (rule of thumb)
    azimuth_deg: float | None = None  # None -> 180 (south) / 0 (north) auto
    gamma_pdc: float = -0.0040        # power temp-coeff (1/degC), c-Si typical
    noct_c: float = 45.0              # nominal operating cell temp
    dc_ac_ratio: float = 1.15         # array-to-inverter sizing ratio
    inv_efficiency: float = 0.96      # nominal inverter efficiency
    system_losses: float = 0.14       # PVWatts default soiling+wiring+mismatch+...
    albedo: float = 0.20
    bifacial: bool = False


@dataclass
class PVResult:
    annual_ac_kwh: float
    monthly_ac_kwh: list
    specific_yield_kwh_kw: float      # annual kWh per kW DC (kWh/kWp)
    performance_ratio: float
    capacity_factor: float
    tilt_deg: float
    azimuth_deg: float
    config: PVConfig


def _auto_tilt_azimuth(site: Site, cfg: PVConfig):
    tilt = cfg.tilt_deg if cfg.tilt_deg is not None else min(60.0, abs(site.latitude))
    if cfg.azimuth_deg is not None:
        az = cfg.azimuth_deg
    else:
        az = 180.0 if site.latitude >= 0 else 0.0  # face the equator
    return tilt, az


def simulate_pv(site: Site, cfg: PVConfig | None = None) -> PVResult:
    cfg = cfg or PVConfig()
    tilt, az = _auto_tilt_azimuth(site, cfg)
    loc = pvloc.Location(site.latitude, site.longitude,
                         altitude=max(0.0, site.elevation_m))

    p_dc0_w = cfg.dc_capacity_kw * 1000.0
    p_ac0_w = p_dc0_w / cfg.dc_ac_ratio
    monthly_kwh = []
    poa_annual_wh = 0.0  # plane-of-array insolation accumulator (Wh/m^2/yr)

    for m in range(12):
        doy = REP_DOY[m]
        # Hourly timeline for the representative day (UTC-naive local solar time).
        times = pd.date_range("2025-01-01", periods=24, freq="1h") \
            + pd.Timedelta(days=doy - 1)
        solpos = solarposition.get_solarposition(times, site.latitude,
                                                  site.longitude,
                                                  altitude=max(0.0, site.elevation_m))
        # Clear-sky shape (Ineichen w/ default Linke turbidity).
        cs = loc.get_clearsky(times, model="ineichen", solar_position=solpos)
        cs_ghi = cs["ghi"].to_numpy()
        cs_sum = cs_ghi.sum()  # Wh/m^2 for the day (1-h steps)

        target_kwh = site.ghi_kwh_m2_day[m] * 1000.0  # Wh/m^2/day from NASA POWER
        scale = (target_kwh / cs_sum) if cs_sum > 1e-6 else 0.0
        ghi = np.clip(cs_ghi * scale, 0, None)

        # Erbs decomposition GHI -> DNI, DHI.
        zenith = solpos["zenith"].to_numpy()
        ghi_series = pd.Series(ghi, index=times)
        erbs = irradiance.erbs(ghi_series, solpos["zenith"], times)
        dni = erbs["dni"].to_numpy()
        dhi = erbs["dhi"].to_numpy()

        dni_extra = irradiance.get_extra_radiation(times).to_numpy()
        poa = irradiance.get_total_irradiance(
            surface_tilt=tilt, surface_azimuth=az,
            solar_zenith=zenith, solar_azimuth=solpos["azimuth"].to_numpy(),
            dni=dni, ghi=ghi, dhi=dhi,
            dni_extra=dni_extra, albedo=cfg.albedo, model="haydavies",
        )["poa_global"]
        poa = np.nan_to_num(poa, nan=0.0)
        poa_annual_wh += float(poa.sum()) * DAYS_IN_MONTH[m]

        # Cell temperature (NOCT model) and PVWatts DC.
        t_cell = site.temp_air_c[m] + (poa / 800.0) * (cfg.noct_c - 20.0)
        p_dc = pvlib.pvsystem.pvwatts_dc(poa, t_cell, p_dc0_w,
                                         cfg.gamma_pdc, temp_ref=25.0)
        # Inverter: nominal efficiency + AC clipping.
        p_ac = np.minimum(p_dc * cfg.inv_efficiency, p_ac0_w)
        p_ac = np.clip(p_ac, 0, None) * (1.0 - cfg.system_losses)

        day_kwh = p_ac.sum() / 1000.0  # 1-h steps -> Wh -> kWh
        monthly_kwh.append(day_kwh * DAYS_IN_MONTH[m])

    annual = float(sum(monthly_kwh))
    specific = annual / cfg.dc_capacity_kw if cfg.dc_capacity_kw else 0.0
    poa_annual_kwh_m2 = poa_annual_wh / 1000.0
    # PR = actual AC energy / ideal energy (P_dc0 * POA / G_stc), G_stc = 1 kW/m^2
    pr = (annual / (cfg.dc_capacity_kw * poa_annual_kwh_m2)
          if poa_annual_kwh_m2 else 0.0)
    cf = annual / (cfg.dc_capacity_kw * 8760.0) if cfg.dc_capacity_kw else 0.0

    return PVResult(
        annual_ac_kwh=round(annual, 1),
        monthly_ac_kwh=[round(x, 1) for x in monthly_kwh],
        specific_yield_kwh_kw=round(specific, 1),
        performance_ratio=round(pr, 3),
        capacity_factor=round(cf, 3),
        tilt_deg=round(tilt, 1),
        azimuth_deg=round(az, 1),
        config=cfg,
    )


def optimal_tilt(site: Site, cfg: PVConfig | None = None,
                 lo: int = 0, hi: int = 65, step: int = 5):
    """Brute-force the fixed tilt that maximizes annual yield."""
    cfg = cfg or PVConfig()
    best = (None, -1.0)
    for t in range(lo, hi + 1, step):
        c = PVConfig(**{**cfg.__dict__, "tilt_deg": float(t)})
        e = simulate_pv(site, c).annual_ac_kwh
        if e > best[1]:
            best = (t, e)
    return {"optimal_tilt_deg": best[0], "annual_ac_kwh": round(best[1], 1)}


if __name__ == "__main__":
    from .resource import from_coordinates, fetch_climate
    s = fetch_climate(from_coordinates(33.45, -112.07, "Phoenix, AZ", 331),
                      allow_network=False)
    r = simulate_pv(s, PVConfig(dc_capacity_kw=6.0))
    print("Phoenix 6 kW  ->", r.annual_ac_kwh, "kWh/yr,",
          r.specific_yield_kwh_kw, "kWh/kWp, CF", r.capacity_factor)
