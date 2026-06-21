"""POST /api/assess"""
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.config import get_settings
from api.db.session import get_db
from api.db.models import AssessmentCache
from api.adapter import build_engine_inputs, serialize_assessment
from renewable_retrofit.model import run_assessment

router = APIRouter()


class AssessOptions(BaseModel):
    taxYear: Optional[int] = None
    electricityPrice: Optional[float] = None
    currency: Optional[str] = None


class AssessRequest(BaseModel):
    address: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    propertyType: str = "house"
    floors: int = 1
    roofOrLotSize: str = "medium"
    siteFeatures: list[str] = Field(default_factory=list)
    monthlyBill: str = "100_200"
    heatingType: str = "not_sure"
    goals: list[str] = Field(default_factory=list)
    options: Optional[AssessOptions] = None


def _err(code: str, message: str, field: Optional[str] = None, status: int = 400):
    raise HTTPException(status_code=status, detail={"error": {"code": code, "message": message, "field": field}})


@router.post("/assess")
async def assess(body: AssessRequest, db: AsyncSession = Depends(get_db)):
    # Validate: must have address or coordinates
    if not body.address and (body.lat is None or body.lon is None):
        _err("VALIDATION_ERROR", "Provide an address or lat/lon coordinates.", "address")

    # Validate enums
    valid_property = {"house", "townhouse", "farm", "cabin", "other"}
    if body.propertyType not in valid_property:
        _err("VALIDATION_ERROR", f"propertyType must be one of: {', '.join(sorted(valid_property))}.", "propertyType")

    valid_size = {"small", "medium", "large"}
    if body.roofOrLotSize not in valid_size:
        _err("VALIDATION_ERROR", "roofOrLotSize must be small, medium, or large.", "roofOrLotSize")

    valid_bill = {"under_100", "100_200", "200_300", "over_300"}
    if body.monthlyBill not in valid_bill:
        _err("VALIDATION_ERROR", "monthlyBill must be one of: under_100, 100_200, 200_300, over_300.", "monthlyBill")

    settings = get_settings()
    req_dict = body.model_dump()
    if body.options:
        req_dict["options"] = body.options.model_dump()

    try:
        engine_inputs = build_engine_inputs(req_dict, allow_network=settings.allow_network)
        result = run_assessment(engine_inputs)
    except ValueError as exc:
        msg = str(exc)
        if "Address not found" in msg or "geocode" in msg.lower():
            _err("INVALID_ADDRESS", "We could not find that address. Try adding a city and country.", "address", 422)
        _err("VALIDATION_ERROR", msg, status=400)
    except RuntimeError as exc:
        msg = str(exc)
        if "LOCATION_DATA_UNAVAILABLE" in msg:
            _err("LOCATION_DATA_UNAVAILABLE", "Climate data is not available for this location.", None, 422)
        _err("SERVER_ERROR", "An unexpected error occurred. Please try again.", status=500)
    except Exception as exc:
        _err("SERVER_ERROR", "An unexpected error occurred. Please try again.", status=500)

    assessment_id = f"asmt_{uuid.uuid4().hex[:8]}"
    out = serialize_assessment(result, req_dict, assessment_id)

    # Cache the result so it can be saved later
    cache_row = AssessmentCache(
        id=assessment_id,
        assessment_json=json.dumps(out),
        created_at=datetime.now(timezone.utc),
    )
    db.add(cache_row)
    await db.commit()

    return out
