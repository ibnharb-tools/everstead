"""Authentication routes."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.db.session import get_db
from api.db.models import User
from api.auth import hash_password, verify_password, create_token, current_user

router = APIRouter(prefix="/auth")


def _err(code: str, message: str, field: Optional[str] = None, status_code: int = 400):
    raise HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message, "field": field}})


def _user_out(user: User) -> dict:
    return {"id": user.id, "name": user.name, "email": user.email}


def _auth_response(user: User) -> dict:
    return {"token": create_token(user.id), "user": _user_out(user)}


class SignupBody(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class OAuthBody(BaseModel):
    provider: str
    credential: str


class ForgotPasswordBody(BaseModel):
    email: EmailStr


@router.post("/signup", status_code=201)
async def signup(body: SignupBody, db: AsyncSession = Depends(get_db)):
    if not body.name.strip():
        _err("VALIDATION_ERROR", "Name is required.", "name")
    if len(body.password) < 8:
        _err("VALIDATION_ERROR", "Password must be at least 8 characters.", "password")

    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        _err("EMAIL_IN_USE", "An account with that email already exists.", "email", 409)

    user = User(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        name=body.name.strip(),
        email=body.email,
        password_hash=hash_password(body.password),
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    return _auth_response(user)


@router.post("/login")
async def login(body: LoginBody, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        _err("INVALID_CREDENTIALS", "Incorrect email or password.", None, 401)
    return _auth_response(user)


@router.post("/oauth")
async def oauth(body: OAuthBody):
    raise HTTPException(
        status_code=501,
        detail={"error": {"code": "NOT_IMPLEMENTED", "message": "OAuth sign-in is coming soon.", "field": None}},
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordBody):
    # Always return the same response regardless of whether the email exists
    return {"ok": True, "message": "If that email exists, we sent reset instructions."}


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return {"user": _user_out(user)}
