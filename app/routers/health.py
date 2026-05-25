import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


class DebugActionRequest(BaseModel):
    ping: str = Field(default="ping", examples=["ping"])


class DebugActionResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    message: str = Field(..., examples=["debug action reached"])
    received_ping: str = Field(..., examples=["ping"])


@router.get(
    "/health",
    summary="Health check",
    response_model=HealthResponse,
    include_in_schema=False,
)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/debug-action",
    operation_id="debugActionConnectivity",
    summary="Debug Custom GPT Action connectivity",
    response_model=DebugActionResponse,
    openapi_extra={"x-openai-isConsequential": False},
)
async def debug_action_connectivity(
    payload: DebugActionRequest,
    request: Request,
) -> DebugActionResponse:
    body = await request.body()
    logger.warning(
        "Debug action endpoint reached.",
        extra={
            "event": "debug_action_reached",
            "http": {
                "method": request.method,
                "path": request.url.path,
                "status_code": 200,
            },
            "client_host": request.client.host if request.client else None,
            "content_type": request.headers.get("content-type"),
            "user_agent": request.headers.get("user-agent"),
            "body_length": len(body),
            "body_preview": body[:500].decode("utf-8", errors="replace"),
            "ping": payload.ping,
        },
    )
    return DebugActionResponse(
        status="ok",
        message="debug action reached",
        received_ping=payload.ping,
    )
