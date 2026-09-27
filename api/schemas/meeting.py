"""
Meeting Ingestion, Processing, and Detail Schemas for RecallAI API.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class YouTubeIngestRequest(BaseModel):
    """YouTube URL ingestion request."""
    url: str = Field(..., description="Valid YouTube video or audio URL")


class MeetingProcessRequest(BaseModel):
    """Meeting transcription and analysis processing request."""
    language: str = Field("english", description="Audio language: english or hinglish/hindi")


class MeetingIngestResponse(BaseModel):
    """Response returned upon staging meeting audio/video."""
    session_id: str
    source: str
    source_type: str = Field("upload", description="Source category: youtube or upload")
    status: str = Field("staged", description="Ingestion stage status")
    message: str


class MeetingProcessResponse(BaseModel):
    """Response returned upon completion of full meeting intelligence pipeline."""
    session_id: str
    title: str
    status: str = Field("completed", description="Processing lifecycle state")
    transcript_available: bool
    summary_available: bool
    indexed: bool
    action_items_count: int
    decisions_count: int
    open_questions_count: int


class MeetingDetailResponse(BaseModel):
    """Full meeting intelligence metadata and state representation."""
    session_id: str
    title: str
    transcript: str
    summary: str
    status: str
    segments_count: int = 0
    is_demo: bool = False
    created_at: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = "upload"
    duration: Optional[str] = "42 min"
    participants_count: Optional[int] = 12
    segments: Optional[List[Any]] = None


class MeetingListItemResponse(BaseModel):
    """Summary item for meetings list."""
    session_id: str
    title: str
    status: str = Field("completed", description="Lifecycle status")
    created_at: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = "upload"
    duration: Optional[str] = "42 min"
    participants_count: Optional[int] = 12
    summary_preview: Optional[str] = None
    decisions_count: int = 0
    actions_count: int = 0
    open_questions_count: int = 0
    is_demo: bool = False

