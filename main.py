"""Everstead API — FastAPI entry point."""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.db.session import init_db, create_tables
from api.routers import assess, auth, retrofits, marketplace


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db(settings.database_url)
    await create_tables()
    yield


app = FastAPI(title="Everstead API", version="1.0.0", lifespan=lifespan)

# CORS
settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(assess.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(retrofits.router, prefix="/api")
app.include_router(marketplace.router, prefix="/api")


@app.get("/health")
async def health():
    return {"ok": True}
