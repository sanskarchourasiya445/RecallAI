"""
Controlled Action and Confirmation Schemas for RecallAI API.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ActionExecutionRequest(BaseModel):
    """Direct controlled action invocation request."""
    session_id: str = Field(..., description="Target meeting session ID")
    action: str = Field(..., description="Action tool identifier (e.g. create_task, send_email)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific argument payload")


class ActionExecutionResponse(BaseModel):
    """Result of controlled tool invocation or confirmation requirement."""
    success: bool
    tool_name: str
    message: str
    resource_id: Optional[str] = None
    requires_confirmation: bool = False
    pending_action_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionConfirmRequest(BaseModel):
    """Request body for approving a staged consequential action."""
    session_id: str = Field(..., description="Target meeting session ID ensuring isolation")


class ActionRejectRequest(BaseModel):
    """Request body for rejecting/canceling a staged consequential action."""
    session_id: str = Field(..., description="Target meeting session ID ensuring isolation")
    reason: Optional[str] = Field("User declined", description="Rejection rationale")


class PendingActionItem(BaseModel):
    """Staged consequential action awaiting user approval."""
    action_id: str
    session_id: str
    tool_name: str
    risk_level: str
    preview_summary: str
    expires_at: float


class PendingActionsResponse(BaseModel):
    """List of all staged pending actions."""
    session_id: Optional[str] = None
    pending_actions: List[PendingActionItem] = Field(default_factory=list)
