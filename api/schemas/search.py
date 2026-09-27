"""
Global Workspace Search Schemas for RecallAI API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """An individual search match across meeting transcripts and structured intelligence."""
    session_id: str = Field(..., description="Unique meeting session ID")
    meeting_title: str = Field(..., description="Human-readable title of the meeting")
    source_type: str = Field(..., description="Origin source type: upload | youtube | intelligence")
    timestamp: str = Field(..., description="Formatted timestamp or time range")
    start_seconds: float = Field(0.0, description="Start offset in seconds for player alignment")
    end_seconds: float = Field(0.0, description="End offset in seconds")
    snippet: str = Field(..., description="Matching transcript or intelligence passage")
    match_type: str = Field("transcript", description="Match origin: transcript | decision | action_item | open_question")
    relevance_score: float = Field(..., description="Normalized similarity or relevance score (0.0 to 1.0)")
    evidence_id: Optional[str] = Field(None, description="Evidence token identifier (e.g. E1)")
    chunk_index: Optional[int] = Field(None, description="Index of the chunk in vector store")


class GlobalSearchResponse(BaseModel):
    """Response payload for global workspace search queries."""
    query: str
    total: int
    results: List[SearchResultItem] = Field(default_factory=list)
