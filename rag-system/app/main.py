from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.documents import router as documents_router
from app.api.routes.health import router as health_router
from app.api.routes.qa import router as qa_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.security import (
    AUTH_COOKIE_MAX_AGE,
    AUTH_COOKIE_NAME,
    is_passcode_enabled,
    is_valid_passcode_shape,
    make_auth_token,
    verify_auth_token,
)

settings = get_settings()
setup_logging(settings.log_level)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def passcode_gate(request: Request, call_next):
    passcode = settings.app_passcode.strip()
    path = request.url.path

    if not is_passcode_enabled(passcode):
        return await call_next(request)

    allowed_paths = {"/login", "/auth/unlock", "/health", "/favicon.ico"}
    allowed_prefixes = ("/static/",)
    if path in allowed_paths or path.startswith(allowed_prefixes):
        return await call_next(request)

    if verify_auth_token(request.cookies.get(AUTH_COOKIE_NAME), passcode):
        return await call_next(request)

    if path.startswith(("/documents", "/qa")) or path in {"/docs", "/openapi.json", "/redoc"}:
        return JSONResponse(
            status_code=401,
            content={"detail": "Enter the 4-digit passcode to use Document Companion."},
        )

    return RedirectResponse(url="/login", status_code=303)

app.include_router(health_router)
app.include_router(documents_router)
app.include_router(qa_router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/login")
def login() -> FileResponse:
    return FileResponse(STATIC_DIR / "login.html")


@app.post("/auth/unlock")
async def unlock(request: Request) -> JSONResponse:
    passcode = settings.app_passcode.strip()
    if not is_passcode_enabled(passcode):
        return JSONResponse({"unlocked": True})

    payload = await request.json()
    submitted = str(payload.get("passcode", "")).strip()

    if not is_valid_passcode_shape(passcode):
        return JSONResponse(
            status_code=500,
            content={"detail": "APP_PASSCODE must be exactly 4 digits."},
        )

    if not hmac_compare(submitted, passcode):
        return JSONResponse(
            status_code=401,
            content={"detail": "That passcode did not work. Please try again."},
        )

    response = JSONResponse({"unlocked": True})
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=make_auth_token(passcode),
        max_age=AUTH_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/auth/lock")
def lock() -> JSONResponse:
    response = JSONResponse({"locked": True})
    response.delete_cookie(key=AUTH_COOKIE_NAME, samesite="lax")
    return response


@app.get("/")
def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


def hmac_compare(left: str, right: str) -> bool:
    import hmac

    return hmac.compare_digest(left, right)
