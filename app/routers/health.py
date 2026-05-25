import logging

from fastapi import APIRouter, Request


router = APIRouter(tags=["system"])
logger = logging.getLogger(__name__)


@router.get("/health", summary="Health check")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.post(
    "/debug-action",
    operation_id="debugActionConnectivity",
    summary="Debug Custom GPT Action connectivity",
)
async def debug_action_connectivity(request: Request) -> dict[str, str | int]:
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
    return {
        "status": "ok",
        "message": "debug action reached",
        "method": request.method,
        "bodyLength": len(body),
    }
