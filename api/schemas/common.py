"""
Common Pydantic Schemas for RecallAI REST API.
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized API error envelope."""
    error: str = Field(..., description="Human-readable error description")
    status_code: int = Field(..., description="HTTP status code")
    detail: Optional[Any] = Field(None, description="Optional error metadata or validation breakdown")


class HealthResponse(BaseModel):
    """Health and runtime diagnostic status response."""
    status: str = Field(..., description="Service operational status (Healthy/Degraded)")
    service: str = Field("recallai-api", description="API Service Name")
    version: str = Field("1.0.0", description="API Service Version")
    llm_provider: str = Field(..., description="Active LLM provider setting")
    embedding_provider: str = Field(..., description="Active Embedding provider setting")
    chromadb_available: bool = Field(True, description="ChromaDB directory accessibility")
    apis: Dict[str, Any] = Field(default_factory=dict, description="Redacted external API configurations")
    runtime: Dict[str, Any] = Field(default_factory=dict, description="Python, platform, and acceleration details")
