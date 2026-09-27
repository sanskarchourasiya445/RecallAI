"""
Workspace-Level Intelligence & Cross-Meeting Chat Schemas for RecallAI API.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkspaceChatRequest(BaseModel):
    """Conversational question or inquiry across all meetings in workspace."""
    message: str = Field(..., min_length=1, description="Question across meetings")
    top_k: int = Field(6, ge=1, le=20, description="Max evidence chunks across workspace")
    session_filter: Optional[str] = Field(None, description="Optional meeting filter")


class WorkspaceCitationItem(BaseModel):
    """Grounded cross-meeting citation preserving meeting provenance and timestamp."""
    evidence_id: str = Field(..., description="Citation identifier token (e.g. E1)")
    session_id: str = Field(..., description="Source meeting session ID")
    meeting_title: str = Field(..., description="Human-readable title of the source meeting")
    time_range: str = Field(..., description="Human-readable time range")
    start_seconds: float = Field(..., description="Start offset in seconds for jump navigation")
    citation_label: str = Field(..., description="Formatted label e.g. [E1 · Sprint Planning · 00:55]")
    snippet: str = Field(..., description="Snippet of the verified evidence")
    score: Optional[float] = Field(None, description="Similarity score or distance")


class WorkspaceChatResponse(BaseModel):
    """Context-aware cross-meeting synthesis grounded in multi-meeting evidence."""
    answer: str
    citations: List[WorkspaceCitationItem] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_query: str
    refused: bool = False


class WorkspaceMemoryResponse(BaseModel):
    """Aggregated persistent workspace memory."""
    overview: Dict[str, Any]
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    action_items: List[Dict[str, Any]] = Field(default_factory=list)
    open_questions: List[Dict[str, Any]] = Field(default_factory=list)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
