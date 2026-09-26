"""
Core Data Models for Phase 8 MCP & Controlled External Actions.
Defines:
- ToolResult: Structured output from tool operations
- ActionExecution: Audit trail records connecting actions to meeting provenance
- PendingAction: Staged proposals waiting for user confirmation
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Structured response returned by every tool invocation."""
    success: bool
    tool_name: str
    resource_id: Optional[str] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = None
    source_session_id: Optional[str] = None
    source_evidence_ids: List[str] = Field(default_factory=list)
    source_timestamp: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class ActionExecution(BaseModel):
    """Audit log entry capturing tool invocation history and evidence backing."""
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    session_id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    status: str = "success"  # success, failed, rejected, pending_confirmation
    source_evidence_ids: List[str] = Field(default_factory=list)
    source_timestamp: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    created_by: str = "jitsly"

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


class PendingAction(BaseModel):
    """A staged consequential action awaiting explicit user confirmation."""
    action_id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    session_id: str
    tool_name: str
    arguments: Dict[str, Any]
    risk_level: str = "medium"  # low, medium, high
    preview_summary: str
    source_evidence_ids: List[str] = Field(default_factory=list)
    source_timestamp: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    expires_at: float = Field(default_factory=lambda: time.time() + 900.0)  # 15 minutes TTL
    status: str = "pending"  # pending, confirmed, rejected, expired

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
