"""GET /api/marketplace/{technology}"""
from fastapi import APIRouter, HTTPException
from renewable_retrofit.marketplace import get_marketplace, _BENCHMARKS

router = APIRouter()

_VALID = set(_BENCHMARKS.keys())


@router.get("/marketplace/{technology}")
async def marketplace(technology: str):
    if technology not in _VALID:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Unknown technology: {technology}", "field": "technology"}},
        )
    return get_marketplace(technology)
