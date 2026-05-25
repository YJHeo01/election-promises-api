import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.observability import (
    configure_logging,
    get_logger,
    reset_request_id,
    set_request_id,
)
from app.routers import answer_context, health, privacy


_MAX_REQUEST_ID_LENGTH = 128
settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    description=(
        "Custom GPT Action backend that returns structured, source-backed "
        "election promise context without generating final answer text."
    ),
    version="0.1.0",
    servers=[{"url": settings.public_base_url.rstrip("/")}],
)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    body = await request.body()
    logger.warning(
        "HTTP request validation failed.",
        extra={
            "event": "http_request_validation_failed",
            "http": {
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
            },
            "client_host": request.client.host if request.client else None,
            "validation_errors": exc.errors(),
            "request_body": body.decode("utf-8", errors="replace"),
        },
    )
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):  # noqa: ANN001
    request_id = _request_id_from_header(request)
    token = set_request_id(request_id)
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        logger.exception(
            "HTTP request failed.",
            extra={
                "event": "http_request_failed",
                "http": {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                },
                "duration_ms": round(duration_ms, 2),
                "client_host": request.client.host if request.client else None,
            },
        )
        reset_request_id(token)
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    response.headers["X-Request-ID"] = request_id
    log_level = logging.WARNING if response.status_code >= 500 else logging.INFO
    logger.log(
        log_level,
        "HTTP request completed.",
        extra={
            "event": "http_request_completed",
            "http": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
            },
            "response_content_length": response.headers.get("content-length"),
            "duration_ms": round(duration_ms, 2),
            "client_host": request.client.host if request.client else None,
        },
    )
    reset_request_id(token)
    return response


def _request_id_from_header(request: Request) -> str:
    request_id = (request.headers.get("X-Request-ID") or "").strip()
    if request_id:
        return request_id[:_MAX_REQUEST_ID_LENGTH]
    return uuid4().hex


app.include_router(health.router)
app.include_router(privacy.router)
app.include_router(answer_context.router)
