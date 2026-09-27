"""
Email Operations Tool for Phase 8.
Supports drafting and sending emails derived from meeting actions.
- draft_email: Safe operation (no confirmation needed)
- send_email: Consequential external operation (requires explicit confirmation gate)
"""

import time
import uuid
import re
from typing import Dict, List, Optional, Any
from core.actions.models import ToolResult

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


class EmailTool:
    """Session-isolated email adapter for drafting and sending emails."""

    def __init__(self):
        # session_id -> {draft_id -> draft_dict}
        self._drafts: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # session_id -> {message_id -> message_dict}
        self._sent: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def is_valid_email(self, email: str) -> bool:
        """Validate email format using standard RFC pattern."""
        if not email or not isinstance(email, str):
            return False
        return bool(EMAIL_REGEX.match(email.strip()))

    def draft_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        source_session_id: str,
        source_evidence_ids: Optional[List[str]] = None,
        source_timestamp: Optional[str] = None,
    ) -> ToolResult:
        """Create an email draft. Safe operation, no confirmation required."""
        # 1. Validation
        if not recipient or not str(recipient).strip():
            return ToolResult(
                success=False,
                tool_name="draft_email",
                error_code="MISSING_RECIPIENT",
                message="Recipient email address is required.",
            )

        if not self.is_valid_email(recipient):
            return ToolResult(
                success=False,
                tool_name="draft_email",
                error_code="INVALID_EMAIL",
                message=f"Invalid email address '{recipient}'. Must be in format user@example.com.",
            )

        if not subject or not str(subject).strip():
            return ToolResult(
                success=False,
                tool_name="draft_email",
                error_code="VALIDATION_ERROR",
                message="Email subject is required.",
            )

        if not body or not str(body).strip():
            return ToolResult(
                success=False,
                tool_name="draft_email",
                error_code="VALIDATION_ERROR",
                message="Email body is required.",
            )

        if not source_session_id or not str(source_session_id).strip():
            return ToolResult(
                success=False,
                tool_name="draft_email",
                error_code="MISSING_SESSION",
                message="source_session_id is required for drafting email.",
            )

        draft_id = f"draft_{uuid.uuid4().hex[:6]}"
        now = time.time()
        clean_evidence_ids = [str(e) for e in (source_evidence_ids or [])]

        draft_record = {
            "draft_id": draft_id,
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "status": "draft",
            "source_session_id": source_session_id,
            "source_evidence_ids": clean_evidence_ids,
            "source_timestamp": source_timestamp,
            "created_at": now,
            "created_by": "recallai",
        }

        if source_session_id not in self._drafts:
            self._drafts[source_session_id] = {}

        self._drafts[source_session_id][draft_id] = draft_record

        return ToolResult(
            success=True,
            tool_name="draft_email",
            resource_id=draft_id,
            message=f"Email draft created for '{recipient}'.",
            metadata=draft_record,
            source_session_id=source_session_id,
            source_evidence_ids=clean_evidence_ids,
            source_timestamp=source_timestamp,
        )

    def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        source_session_id: str,
        draft_id: Optional[str] = None,
        source_evidence_ids: Optional[List[str]] = None,
        source_timestamp: Optional[str] = None,
    ) -> ToolResult:
        """Send an email. Consequential operation requiring prior confirmation."""
        # 1. Validation
        if not recipient or not self.is_valid_email(recipient):
            return ToolResult(
                success=False,
                tool_name="send_email",
                error_code="INVALID_EMAIL",
                message=f"Cannot send email: invalid or missing recipient '{recipient}'.",
            )

        if not subject or not str(subject).strip():
            return ToolResult(
                success=False,
                tool_name="send_email",
                error_code="VALIDATION_ERROR",
                message="Email subject is required.",
            )

        if not body or not str(body).strip():
            return ToolResult(
                success=False,
                tool_name="send_email",
                error_code="VALIDATION_ERROR",
                message="Email body is required.",
            )

        if not source_session_id or not str(source_session_id).strip():
            return ToolResult(
                success=False,
                tool_name="send_email",
                error_code="MISSING_SESSION",
                message="source_session_id is required.",
            )

        message_id = f"msg_{uuid.uuid4().hex[:6]}"
        now = time.time()
        clean_evidence_ids = [str(e) for e in (source_evidence_ids or [])]

        sent_record = {
            "message_id": message_id,
            "draft_id": draft_id,
            "recipient": recipient.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "status": "sent",
            "source_session_id": source_session_id,
            "source_evidence_ids": clean_evidence_ids,
            "source_timestamp": source_timestamp,
            "sent_at": now,
            "created_by": "recallai",
        }

        if source_session_id not in self._sent:
            self._sent[source_session_id] = {}

        self._sent[source_session_id][message_id] = sent_record

        # If a draft existed, update its status
        if draft_id and source_session_id in self._drafts and draft_id in self._drafts[source_session_id]:
            self._drafts[source_session_id][draft_id]["status"] = "sent"

        return ToolResult(
            success=True,
            tool_name="send_email",
            resource_id=message_id,
            message=f"Email sent successfully to '{recipient.strip()}'.",
            metadata=sent_record,
            source_session_id=source_session_id,
            source_evidence_ids=clean_evidence_ids,
            source_timestamp=source_timestamp,
        )

    def list_drafts(self, session_id: str) -> ToolResult:
        """List email drafts for a session."""
        session_drafts = list(self._drafts.get(session_id, {}).values())
        return ToolResult(
            success=True,
            tool_name="list_drafts",
            message=f"Retrieved {len(session_drafts)} draft(s).",
            metadata={"drafts": session_drafts, "total_count": len(session_drafts)},
            source_session_id=session_id,
        )

    def list_sent_emails(self, session_id: str) -> ToolResult:
        """List sent emails for a session."""
        session_sent = list(self._sent.get(session_id, {}).values())
        return ToolResult(
            success=True,
            tool_name="list_sent_emails",
            message=f"Retrieved {len(session_sent)} sent email(s).",
            metadata={"sent_emails": session_sent, "total_count": len(session_sent)},
            source_session_id=session_id,
        )

    def clear_session(self, session_id: str):
        """Cleanly remove email data for a session."""
        if session_id in self._drafts:
            del self._drafts[session_id]
        if session_id in self._sent:
            del self._sent[session_id]
