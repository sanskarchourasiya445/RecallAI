"""
Meeting Intelligence Structured Output Schemas for RecallAI API.
Directly reuses core ActionItem, DecisionItem, and OpenQuestionItem models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from core.intelligence.extractor import ActionItem, DecisionItem, OpenQuestionItem


class SummaryResponse(BaseModel):
    """Executive summary response for a meeting session."""
    session_id: str
    title: str
    summary: str


class ActionItemsResponse(BaseModel):
    """Structured action items extracted with ownership and deadlines."""
    session_id: str
    action_items: List[ActionItem] = Field(default_factory=list)
    total: int


class DecisionsResponse(BaseModel):
    """Confirmed decisions agreed upon during the meeting."""
    session_id: str
    key_decisions: List[DecisionItem] = Field(default_factory=list)
    total: int


class OpenQuestionsResponse(BaseModel):
    """Unresolved dilemmas and open questions left pending."""
    session_id: str
    open_questions: List[OpenQuestionItem] = Field(default_factory=list)
    total: int
