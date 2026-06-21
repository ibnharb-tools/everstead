"""JWT auth helpers — stdlib implementation (no cryptography dep)."""
import base64
import hashlib
import hmac
import json
import time
from typing import Optional

import hashlib
import os as _os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import get_settings
from .db.session import get_db
from .db.models import User

_bearer = HTTPBearer()

_ITERATIONS = 260000


def hash_password(plain: str) -> str:
    salt = _os.urandom(16).hex()
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt}${dk.hex()}"


def verify_password(plain: str, hashed: str) -> bool:
    try:
        _, iters, salt, dk_hex = hashed.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), int(iters))
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def create_token(user_id: str) -> str:
    s = get_settings()
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    exp = int(time.time()) + s.jwt_expire_minutes * 60
    payload = _b64url(json.dumps({"sub": user_id, "exp": exp}).encode())
    msg = f"{header}.{payload}".encode()
    sig = _b64url(hmac.new(s.jwt_secret.encode(), msg, hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"


def _decode_token(token: str) -> str:
    s = get_settings()
    try:
        parts = token.split(".")
        assert len(parts) == 3
        header, payload_b64, sig = parts
        msg = f"{header}.{payload_b64}".encode()
        expected_sig = _b64url(hmac.new(s.jwt_secret.encode(), msg, hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected_sig):
            raise ValueError("bad signature")
        claims = json.loads(_b64url_decode(payload_b64))
        if claims["exp"] < time.time():
            raise ValueError("expired")
        return claims["sub"]
    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "Invalid or expired token.", "field": None}},
        )


async def current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = _decode_token(creds.credentials)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "UNAUTHORIZED", "message": "User not found.", "field": None}},
        )
    return user
