import logging
import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import text

from app.api_keys.router import router as api_keys_router
from app.auth.router import router as auth_router
from app.blog_digest.router import router as blog_digest_router
from app.database import async_engine, async_session_factory
from app.exceptions import (
    AuthenticationError,
    JiraApiError,
    JiraNotConnectedError,
)
from app.external.router import router as external_router
from app.jira.router import router as jira_router
from app.jira.service import (
    JiraAPIError as _LegacyJiraAPIError,
    JiraNotConnectedError as _LegacyJiraNotConnectedError,
)
from app.blog_digest.scheduler import start_scheduler, stop_scheduler
from app.rate_limit import limiter

logger = logging.getLogger("identityhub")

# Alembic must run from the directory containing alembic.ini
_BACKEND_ROOT = Path(__file__).resolve().parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Running Alembic migrations …")
    env = {**os.environ, "PYTHONPATH": str(_BACKEND_ROOT)}
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env=env,
    )
    if result.returncode != 0:
        logger.error("Alembic migration failed:\n%s", result.stderr)
        raise RuntimeError(f"Alembic migration failed: {result.stderr}")
    logger.info("Alembic migrations completed successfully.")

    start_scheduler()

    yield

    stop_scheduler()
    await async_engine.dispose()
    logger.info("Database engine disposed.")


app = FastAPI(
    title="IdentityHub API",
    description="NHI finding management platform with Jira integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


def _rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Try again later.",
            "code": "RATE_LIMITED",
        },
    )


def _sanitize_errors(errors: list[dict]) -> list[dict]:
    """Ensure Pydantic error dicts are JSON-serializable (ctx may contain exceptions)."""
    safe = []
    for err in errors:
        e = {k: v for k, v in err.items() if k != "ctx"}
        if "ctx" in err:
            e["ctx"] = {k: str(v) for k, v in err["ctx"].items()}
        safe.append(e)
    return safe


def _validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": _sanitize_errors(exc.errors()),
            "code": "VALIDATION_ERROR",
        },
    )


def _request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "detail": _sanitize_errors(exc.errors()),
            "code": "VALIDATION_ERROR",
        },
    )


def _http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    code = (exc.headers or {}).get("X-Error-Code", "ERROR")
    body: dict = {"detail": exc.detail, "code": code}
    return JSONResponse(status_code=exc.status_code, content=body)


def _authentication_error(request: Request, exc: AuthenticationError) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "detail": str(exc) or "Not authenticated",
            "code": "NOT_AUTHENTICATED",
        },
    )


def _jira_not_connected(
    request: Request, exc: JiraNotConnectedError | _LegacyJiraNotConnectedError
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "detail": "Jira not connected",
            "code": "JIRA_NOT_CONNECTED",
        },
    )


def _jira_api_error(
    request: Request, exc: JiraApiError | _LegacyJiraAPIError
) -> JSONResponse:
    return JSONResponse(
        status_code=502,
        content={
            "detail": f"Jira API error: {exc}",
            "code": "JIRA_API_ERROR",
        },
    )


def _unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR",
        },
    )


app.add_exception_handler(HTTPException, _http_exception)
app.add_exception_handler(RequestValidationError, _request_validation_error)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded)
app.add_exception_handler(ValidationError, _validation_error)
app.add_exception_handler(AuthenticationError, _authentication_error)
app.add_exception_handler(JiraNotConnectedError, _jira_not_connected)
app.add_exception_handler(_LegacyJiraNotConnectedError, _jira_not_connected)
app.add_exception_handler(JiraApiError, _jira_api_error)
app.add_exception_handler(_LegacyJiraAPIError, _jira_api_error)
app.add_exception_handler(Exception, _unhandled_exception)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(jira_router)
app.include_router(external_router)
app.include_router(blog_digest_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Service health check — verifies the API is up and the database is reachable."""
    async with async_session_factory() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "healthy", "version": "1.0.0", "database": "connected"}
