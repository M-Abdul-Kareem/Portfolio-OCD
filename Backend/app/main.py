"""
Portfolio Backend API
======================
A small CMS-style backend for Muhammad Abdul Kareem's portfolio site.

Run locally with:
    uvicorn app.main:app --reload

Interactive API docs (auto-generated):
    http://127.0.0.1:8000/docs
"""
import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import engine, Base
from .routers import (
    auth_router,
    hero_router,
    about_router,
    skills_router,
    experience_router,
    projects_router,
    contact_info_router,
    contact_messages_router,
)

logger = logging.getLogger("uvicorn.error")

# Create all tables on startup if they don't already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Portfolio API",
    description="Backend API powering Muhammad Abdul Kareem's dynamic portfolio site.",
    version="1.0.0",
)

# CORS: allows the portfolio frontend (served from a different origin,
# e.g. a Live Server port or a different domain) to call this API from
# the browser. Restrict allow_origins to your real domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Adds baseline security headers to every response — flagged by
    browser dev tools / security audits as missing otherwise.
    x-content-type-options stops browsers from "MIME-sniffing" a
    response into a different type than what the server declared,
    which is a real (if minor) hardening step for any API.
    """
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catches any error that isn't already handled (e.g. a database
    schema mismatch, a bug in a route). Without this, an unhandled
    500 can skip past CORSMiddleware's response headers entirely,
    which makes the browser misreport a totally unrelated backend
    bug as a "CORS policy" error — very confusing to debug blind.

    This guarantees the browser always gets a clean JSON error
    response with proper CORS headers, so the real problem shows
    up clearly in the browser console instead of a red herring.
    """
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin", "*")},
    )


# Serve uploaded files (e.g. the About section photo) at /static/...
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth_router.router)
app.include_router(hero_router.router)
app.include_router(about_router.router)
app.include_router(skills_router.router)
app.include_router(experience_router.router)
app.include_router(projects_router.router)
app.include_router(contact_info_router.router)
app.include_router(contact_messages_router.router)


@app.get("/", tags=["Health"])
def root():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Portfolio API is running. Visit /docs for documentation."}
