"""
Chat and RAG Conversation Schemas for Gistly API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat message request against an active meeting session."""
    session_id: str = Field(..., description="Unique meeting session identifier")
    message: str = Field(..., min_length=1, description="User question or action instruction")
    top_k: int = Field(4, ge=1, le=20, description="Number of evidence chunks to retrieve")


class CitationItem(BaseModel):
    """Grounded evidence citation."""
    evidence_id: str = Field(..., description="Evidence citation token (e.g. E1, E2)")
    time_range: str = Field(..., description="Human-readable timestamp range")
    chunk_index: int = Field(..., description="Zero-indexed chunk identifier")
    source: str = Field(..., description="Source transcript or audio origin")
    score: Optional[float] = Field(None, description="Retrieval similarity distance or score")


class EvidenceItem(BaseModel):
    """Raw verified evidence passage supporting the response."""
    evidence_id: str
    text: str
    time_range: str
    start_seconds: float
    end_seconds: float
    chunk_index: int


class ChatResponse(BaseModel):
    """Context-aware grounded chat response driven by LangGraph assistant workflow."""
    session_id: str
    answer: str
    citations: List[CitationItem] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    resolved_query: str
    intent: str = Field("question", description="Detected intent: question | action | clarify")
    refused: bool = Field(False, description="True if answer was refused due to missing/ungrounded evidence")
    requires_confirmation: bool = Field(False, description="True if action is consequential and staged")
    pending_action_id: Optional[str] = Field(None, description="ID of pending action if confirmation required")


class ChatTurnItem(BaseModel):
    """A conversational turn in session memory."""
    turn_id: int
    user_message: str
    assistant_message: str
    evidence_ids: List[str] = Field(default_factory=list)
    resolved_query: Optional[str] = None
    timestamp: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """Full conversational memory history for a meeting session."""
    session_id: str
    turns: List[ChatTurnItem] = Field(default_factory=list)

