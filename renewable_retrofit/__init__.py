"""
renewable_retrofit
==================
A reference, physics-based toolkit for modeling a home renewable-energy retrofit
(solar PV, small wind, micro-hydro, ground-source geothermal) anywhere on Earth
from an address or coordinate, with marketplace cost benchmarks and 2026-correct
incentive/economics analysis.

Quick start
-----------
    from renewable_retrofit.model import AssessmentInputs, run_assessment
    report = run_assessment(AssessmentInputs(lat=33.45, lon=-112.07, pv_kw=8))

Or via the CLI:
    python -m renewable_retrofit.cli --lat 33.45 --lon -112.07 --pv-kw 8
"""
from . import resource, solar, wind, hydro_geo, economics, marketplace, model  # noqa

__all__ = ["resource", "solar", "wind", "hydro_geo",
           "economics", "marketplace", "model"]
__version__ = "1.0.0"
