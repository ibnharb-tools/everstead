"""GET /api/marketplace/{technology}"""
from fastapi import APIRouter, HTTPException
from renewable_retrofit.marketplace import CATALOG, price_capex
from api.adapter import _buy_at

router = APIRouter()

# Map API contract tech names → CATALOG keys
_API_TO_CATALOG = {
    "solar_pv": "solar_pv",
    "battery": "battery",
    "wind": "wind_small",
    "micro_hydro": "micro_hydro",
    "geothermal": "geothermal_gshp",
    "solar_thermal": "solar_thermal",
}

_VALID = set(_API_TO_CATALOG.keys())


@router.get("/marketplace/{technology}")
async def marketplace(technology: str):
    if technology not in _VALID:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Unknown technology: {technology}", "field": "technology"}},
        )
    catalog_key = _API_TO_CATALOG[technology]
    entry = CATALOG[catalog_key]
    band = entry["cost"]
    return {
        "technology": technology,
        "costBand": {
            "low": band.low,
            "typical": band.typical,
            "high": band.high,
            "unit": band.unit,
            "note": band.note,
        },
        "buyAt": _buy_at(entry["marketplaces"]),
        "benchmarkBasis": "NREL benchmarks ~2023-2024 $",
    }
