"""
Confirmation Gate & Audit Trail Manager for Phase 8.
Enforces the safety rule: Never blindly execute consequential external actions.
- Staged proposed actions require explicit user confirmation.
- Prevents cross-session action approval.
- Enforces TTL expiration (15 min) and duplicate execution protection.
- Maintains comprehensive audit history with evidence provenance.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from core.actions.models import ToolResult, PendingAction, ActionExecution


class ConfirmationManager:
    """Manages action proposals, confirmation gates, and audit trails."""

    def __init__(self, default_ttl_seconds: float = 900.0):
        # action_id -> PendingAction
        self._pending: Dict[str, PendingAction] = {}
        # execution_id -> ActionExecution
        self._audit_log: Dict[str, ActionExecution] = {}
        self.default_ttl = default_ttl_seconds

    def stage_action(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: str,
        preview_summary: str,
        risk_level: str = "medium",
        source_evidence_ids: Optional[List[str]] = None,
        source_timestamp: Optional[str] = None,
    ) -> PendingAction:
        """Stage a proposed action requiring user confirmation."""
        clean_evidence_ids = [str(e) for e in (source_evidence_ids or [])]
        action = PendingAction(
            session_id=session_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level,
            preview_summary=preview_summary,
            source_evidence_ids=clean_evidence_ids,
            source_timestamp=source_timestamp,
            created_at=time.time(),
            expires_at=time.time() + self.default_ttl,
            status="pending",
        )
        self._pending[action.action_id] = action

        # Record in audit trail as staged
        audit_entry = ActionExecution(
            execution_id=f"staged_{action.action_id}",
            session_id=session_id,
            tool_name=tool_name,
            arguments=arguments,
            result={"status": "pending_confirmation", "preview": preview_summary},
            status="pending_confirmation",
            source_evidence_ids=clean_evidence_ids,
            source_timestamp=source_timestamp,
            created_at=time.time(),
        )
        self._audit_log[audit_entry.execution_id] = audit_entry

        return action

    def record_execution(
        self,
        session_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        status: str = "success",
        source_evidence_ids: Optional[List[str]] = None,
        source_timestamp: Optional[str] = None,
    ) -> ActionExecution:
        """Record a completed tool execution directly into audit trail."""
        audit_entry = ActionExecution(
            session_id=session_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            status=status,
            source_evidence_ids=[str(e) for e in (source_evidence_ids or [])],
            source_timestamp=source_timestamp,
            created_at=time.time(),
        )
        self._audit_log[audit_entry.execution_id] = audit_entry
        return audit_entry


    def confirm_action(
        self,
        action_id: str,
        session_id: str,
        tool_executor_fn,
    ) -> ToolResult:
        """
        Confirm and execute a previously staged action.
        - Validates action existence
        - Validates active session matching (cross-session isolation guard)
        - Validates expiration
        - Prevents duplicate confirmation
        """
        if not action_id or action_id not in self._pending:
            return ToolResult(
                success=False,
                tool_name="confirm_action",
                error_code="NOT_FOUND",
                message=f"Action '{action_id}' not found or already purged.",
            )

        pending = self._pending[action_id]

        # 1. Session Isolation Guard
        if pending.session_id != session_id:
            return ToolResult(
                success=False,
                tool_name=pending.tool_name,
                error_code="SESSION_MISMATCH",
                message=f"Access denied: Action '{action_id}' belongs to session '{pending.session_id}', not active session '{session_id}'.",
                source_session_id=session_id,
            )

        # 2. Expiration Guard
        if pending.is_expired():
            pending.status = "expired"
            return ToolResult(
                success=False,
                tool_name=pending.tool_name,
                error_code="EXPIRED_ACTION",
                message=f"Action '{action_id}' has expired. Please re-propose the action.",
                source_session_id=session_id,
            )

        # 3. Duplicate Execution Guard
        if pending.status != "pending":
            return ToolResult(
                success=False,
                tool_name=pending.tool_name,
                error_code="ALREADY_PROCESSED",
                message=f"Action '{action_id}' has already been processed with status '{pending.status}'.",
                source_session_id=session_id,
            )

        # 4. Execute the tool
        pending.status = "confirmed"
        result: ToolResult = tool_executor_fn(pending.tool_name, pending.arguments)

        # 5. Log audit trail
        audit_entry = ActionExecution(
            session_id=session_id,
            tool_name=pending.tool_name,
            arguments=pending.arguments,
            result=result.to_dict(),
            status="success" if result.success else "failed",
            source_evidence_ids=pending.source_evidence_ids,
            source_timestamp=pending.source_timestamp,
            created_at=time.time(),
        )
        self._audit_log[audit_entry.execution_id] = audit_entry

        return result

    def reject_action(
        self,
        action_id: str,
        session_id: str,
        reason: str = "User declined",
    ) -> ToolResult:
        """Reject and cancel a pending action."""
        if not action_id or action_id not in self._pending:
            return ToolResult(
                success=False,
                tool_name="reject_action",
                error_code="NOT_FOUND",
                message=f"Action '{action_id}' not found.",
            )

        pending = self._pending[action_id]

        if pending.session_id != session_id:
            return ToolResult(
                success=False,
                tool_name=pending.tool_name,
                error_code="SESSION_MISMATCH",
                message=f"Access denied: Action belongs to different session.",
                source_session_id=session_id,
            )

        if pending.status != "pending":
            return ToolResult(
                success=False,
                tool_name=pending.tool_name,
                error_code="ALREADY_PROCESSED",
                message=f"Action '{action_id}' already has status '{pending.status}'.",
                source_session_id=session_id,
            )

        pending.status = "rejected"

        audit_entry = ActionExecution(
            session_id=session_id,
            tool_name=pending.tool_name,
            arguments=pending.arguments,
            result={"status": "rejected", "reason": reason},
            status="rejected",
            source_evidence_ids=pending.source_evidence_ids,
            source_timestamp=pending.source_timestamp,
            created_at=time.time(),
        )
        self._audit_log[audit_entry.execution_id] = audit_entry

        return ToolResult(
            success=True,
            tool_name=pending.tool_name,
            message=f"Action '{action_id}' was cancelled ({reason}).",
            metadata={"action_id": action_id, "status": "rejected"},
            source_session_id=session_id,
        )

    def get_pending_actions(self, session_id: Optional[str] = None) -> List[PendingAction]:
        """Get all active pending actions for a session, or all pending if session_id is None."""
        return [
            a for a in self._pending.values()
            if (session_id is None or a.session_id == session_id) and a.status == "pending" and not a.is_expired()
        ]

    def get_audit_history(self, session_id: Optional[str] = None) -> List[ActionExecution]:
        """Get execution history, optionally filtered by session."""
        if session_id:
            return [e for e in self._audit_log.values() if e.session_id == session_id]
        return list(self._audit_log.values())

    def explain_action(self, identifier: str) -> str:
        """
        Explain the provenance and reason for an action execution or resource.
        Answers: What did you do? Why did you do it? Which meeting evidence caused it?
        """
        # Search by execution_id, action_id, or resource_id in result
        matched_exec = None
        for entry in self._audit_log.values():
            if (
                entry.execution_id == identifier
                or identifier in entry.execution_id
                or entry.result.get("resource_id") == identifier
            ):
                matched_exec = entry
                break

        if not matched_exec:
            return f"No audit history found for identifier '{identifier}'."

        tool = matched_exec.tool_name
        args = matched_exec.arguments
        status = matched_exec.status
        ev_ids = matched_exec.source_evidence_ids or ["None recorded"]
        ts = matched_exec.source_timestamp or "Not specified"
        sid = matched_exec.session_id

        explanation = (
            f"Action Explanation:\n"
            f"• Tool: {tool}\n"
            f"• Status: {status}\n"
            f"• Session ID: {sid}\n"
            f"• Meeting Evidence: {', '.join(ev_ids)}\n"
            f"• Transcript Timestamp: {ts}\n"
            f"• Target Arguments: {args}\n"
            f"• Grounding Rationale: This action was derived directly from meeting intelligence extracted from dialogue at [{ts}] backed by evidence {ev_ids}."
        )
        return explanation

    def clear_session(self, session_id: str):
        """Purge pending actions and audit logs for a session."""
        self._pending = {k: v for k, v in self._pending.items() if v.session_id != session_id}
        self._audit_log = {k: v for k, v in self._audit_log.items() if v.session_id != session_id}
