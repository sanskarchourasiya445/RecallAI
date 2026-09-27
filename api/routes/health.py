"""
System Health and Runtime Diagnostics Router.
"""

from fastapi import APIRouter, status
from core.config import get_system_health
from api.schemas.common import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health and Component Readiness",
    description="Returns diagnostic health information including LLM provider, embedding configuration, and storage hygiene. Never exposes secrets.",
)
def get_health() -> HealthResponse:
    health_data = get_system_health()
    is_healthy = health_data.get("status") == "Healthy"
    status_text = "ok" if is_healthy else "degraded"

    return HealthResponse(
        status=status_text,
        service="recallai-api",
        version="1.0.0",
        llm_provider=health_data["apis"].get("llm_provider", "auto"),
        embedding_provider=health_data["apis"].get("embedding_provider", "local"),
        chromadb_available=health_data["storage"].get("chroma_writable", True),
        apis=health_data.get("apis", {}),
        runtime=health_data.get("runtime", {}),
    )
