"""Saved retrofit routes (all require auth)."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.db.session import get_db
from api.db.models import User, Retrofit, AssessmentCache
from api.auth import current_user

router = APIRouter(prefix="/retrofits")


def _err(code: str, message: str, field: Optional[str] = None, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message, "field": field}})


def _retrofit_summary(r: Retrofit) -> dict:
    data = json.loads(r.assessment_json)
    techs = data.get("technologies", [])
    top = next((t for t in techs if t.get("recommended")), techs[0] if techs else {})
    return {
        "id": r.id,
        "label": r.label,
        "resolvedAddress": data.get("site", {}).get("resolvedAddress", ""),
        "createdAt": r.created_at.isoformat(),
        "topRecommendation": top.get("type"),
        "topRecommendationName": top.get("displayName"),
        "estimatedYearlySavings": top.get("yearlySavings"),
        "currency": data.get("currency"),
    }


class SaveBody(BaseModel):
    # Frontend sends full assessment dict + label
    assessment: Optional[dict] = None
    # Legacy: save by cached assessmentId
    assessmentId: Optional[str] = None
    label: Optional[str] = None


@router.get("")
async def list_retrofits(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Retrofit).where(Retrofit.user_id == user.id).order_by(Retrofit.created_at.desc()))
    rows = result.scalars().all()
    return {"retrofits": [_retrofit_summary(r) for r in rows]}


@router.get("/{retrofit_id}")
async def get_retrofit(retrofit_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Retrofit).where(Retrofit.id == retrofit_id, Retrofit.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if not row:
        _err("NOT_FOUND", "Retrofit not found.", status_code=404)
    return {
        "id": row.id,
        "label": row.label,
        "createdAt": row.created_at.isoformat(),
        "assessment": json.loads(row.assessment_json),
    }


@router.post("", status_code=201)
async def save_retrofit(body: SaveBody, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    # Resolve the assessment JSON
    if body.assessment and "technologies" in body.assessment:
        assessment_json = json.dumps(body.assessment)
    elif body.assessmentId:
        cache_result = await db.execute(select(AssessmentCache).where(AssessmentCache.id == body.assessmentId))
        cached = cache_result.scalar_one_or_none()
        if not cached:
            _err("NOT_FOUND", "Assessment not found. Run a new assessment first.", status_code=404)
        assessment_json = cached.assessment_json
    else:
        _err("VALIDATION_ERROR", "Provide an assessment or assessmentId.", status_code=400)

    label = (body.label or "My home").strip()
    now = datetime.now(timezone.utc)
    row = Retrofit(
        id=f"rtf_{uuid.uuid4().hex[:8]}",
        user_id=user.id,
        label=label,
        assessment_json=assessment_json,
        created_at=now,
    )
    db.add(row)
    await db.commit()
    return {"id": row.id, "label": row.label, "createdAt": row.created_at.isoformat()}


@router.delete("/{retrofit_id}")
async def delete_retrofit(retrofit_id: str, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Retrofit).where(Retrofit.id == retrofit_id, Retrofit.user_id == user.id)
    )
    row = result.scalar_one_or_none()
    if not row:
        _err("NOT_FOUND", "Retrofit not found.", status_code=404)
    await db.delete(row)
    await db.commit()
    return {"ok": True}
