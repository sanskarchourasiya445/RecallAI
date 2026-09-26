"""
Controlled Actions and Safety Confirmation Gate Router.
Enforces strict human-in-the-loop confirmation policies for consequential tools.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.logger import get_logger
from core.actions.tool_registry import ToolRegistry
from core.actions.models import ToolResult
from api.dependencies import get_tool_registry
from api.schemas.actions import (
    ActionExecutionRequest,
    ActionExecutionResponse,
    ActionConfirmRequest,
    ActionRejectRequest,
    PendingActionItem,
    PendingActionsResponse,
)

logger = get_logger("gistly.api.actions")
router = APIRouter(prefix="/actions", tags=["Actions & MCP"])


@router.get(
    "/tools",
    status_code=status.HTTP_200_OK,
    summary="List Registered MCP Action Tools",
    description="Returns JSON Schema specifications and risk levels for all available tools.",
)
def list_tools(
    registry: ToolRegistry = Depends(get_tool_registry),
) -> List[Dict[str, Any]]:
    return registry.list_tools()


@router.post(
    "",
    response_model=ActionExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute Controlled Action Tool",
    description="Executes a tool by name. If the action is consequential (e.g. send_email), it is automatically staged in the Confirmation Gate.",
)
def execute_action(
    request: ActionExecutionRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ActionExecutionResponse:
    tool_def = registry.get_tool(request.action)
    if not tool_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action tool '{request.action}' is not registered in the system.",
        )

    # Inject session_id if omitted in arguments
    args = dict(request.parameters)
    if "session_id" not in args and "source_session_id" not in args:
        args["source_session_id"] = request.session_id

    # Execute with confirmation gate enforcement
    t_res: ToolResult = registry.execute_tool(request.action, args)

    is_pending = bool(
        getattr(t_res, "pending_action_id", None)
        or (t_res.metadata and t_res.metadata.get("status") == "pending_confirmation")
    )
    act_id = getattr(t_res, "pending_action_id", None) or (t_res.metadata or {}).get("action_id")

    return ActionExecutionResponse(
        success=t_res.success,
        tool_name=t_res.tool_name,
        message=t_res.message,
        resource_id=t_res.resource_id,
        requires_confirmation=is_pending,
        pending_action_id=act_id,
        metadata=t_res.metadata,
    )


@router.get(
    "/pending",
    response_model=PendingActionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List Pending Consequential Action Confirmations",
)
def get_pending_actions(
    session_id: Optional[str] = Query(None, description="Filter pending actions by meeting session ID"),
    registry: ToolRegistry = Depends(get_tool_registry),
) -> PendingActionsResponse:
    pending_list = registry.confirmation_mgr.get_pending_actions(session_id)
    items = [
        PendingActionItem(
            action_id=p.action_id,
            session_id=p.session_id,
            tool_name=p.tool_name,
            risk_level=p.risk_level,
            preview_summary=p.preview_summary,
            expires_at=p.expires_at,
        )
        for p in pending_list
    ]
    return PendingActionsResponse(session_id=session_id, pending_actions=items)


@router.post(
    "/{action_id}/confirm",
    response_model=ActionExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm and Execute Staged Consequential Action",
    description="Explicit human approval gate. Strictly validates that action belongs to session.",
)
def confirm_action(
    action_id: str,
    request: ActionConfirmRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ActionExecutionResponse:
    res = registry.confirm_action(action_id, session_id=request.session_id)
    if not res.success:
        err_code = getattr(res, "error_code", "CONFIRMATION_FAILED")
        if err_code == "NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.message)

    return ActionExecutionResponse(
        success=res.success,
        tool_name=res.tool_name,
        message=res.message,
        resource_id=res.resource_id,
        requires_confirmation=False,
        metadata=res.metadata,
    )


@router.post(
    "/{action_id}/reject",
    response_model=ActionExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject Staged Consequential Action",
)
def reject_action(
    action_id: str,
    request: ActionRejectRequest,
    registry: ToolRegistry = Depends(get_tool_registry),
) -> ActionExecutionResponse:
    res = registry.reject_action(action_id, session_id=request.session_id, reason=request.reason)
    if not res.success:
        err_code = getattr(res, "error_code", "REJECTION_FAILED")
        if err_code == "NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=res.message)

    return ActionExecutionResponse(
        success=res.success,
        tool_name=res.tool_name,
        message=res.message,
        resource_id=res.resource_id,
        requires_confirmation=False,
        metadata=res.metadata,
    )
