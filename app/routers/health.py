import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field


router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


class DebugActionResponse(BaseModel):
    status: str = Field(..., examples=["ok"])
    message: str = Field(..., examples=["debug action reached"])
    method: str = Field(..., examples=["POST"])
    body_length: int = Field(..., alias="bodyLength", examples=[17])


@router.get("/health", summary="Health check", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/debug-action",
    operation_id="debugActionConnectivity",
    summary="Debug Custom GPT Action connectivity",
    response_model=DebugActionResponse,
    openapi_extra={"x-openai-isConsequential": False},
)
async def debug_action_connectivity(request: Request) -> DebugActionResponse:
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
        },
    )
    return DebugActionResponse(
        status="ok",
        message="debug action reached",
        method=request.method,
        bodyLength=len(body),
    )
