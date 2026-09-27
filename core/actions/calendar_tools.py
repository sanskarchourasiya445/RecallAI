"""
Calendar Event Tool for Phase 8.
Supports creating and listing calendar events with strict date/time validation,
participant checks, and evidence provenance.
Requires explicit confirmation before execution.
"""

import time
import uuid
import re
from typing import Dict, List, Optional, Any
from core.actions.models import ToolResult


class CalendarTool:
    """Session-isolated calendar adapter."""

    def __init__(self):
        # session_id -> {event_id -> event_dict}
        self._events: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def validate_datetime_string(self, dt_str: str) -> bool:
        """
        Validate that a datetime string contains at least a date and time specification.
        Accepts formats like:
        - '2026-10-15 14:00'
        - '2026-10-15T14:00:00'
        - 'October 15, 2026 2:00 PM'
        - 'Friday 5:00 PM'
        Rejects ambiguous relative strings without time like 'next week', 'sometime soon'.
        """
        if not dt_str or not str(dt_str).strip():
            return False
        raw = str(dt_str).strip().lower()
        if raw in ("next week", "later", "soon", "tomorrow", "next monday", "tbd", "unspecified"):
            return False
        # Must have at least a date indicator and a time or explicit hour
        has_time_indicator = any(x in raw for x in (":", "am", "pm", "00"))
        has_date_indicator = bool(re.search(r"\d{4}-\d{2}-\d{2}|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}/\d{1,2}|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", raw))
        return has_time_indicator and has_date_indicator

    def create_calendar_event(
        self,
        title: str,
        start_time: str,
        end_time: str,
        participants: List[str],
        description: Optional[str] = None,
        source_session_id: str = None,
        source_evidence_ids: Optional[List[str]] = None,
        source_timestamp: Optional[str] = None,
    ) -> ToolResult:
        """Create a scheduled calendar event after parameter validation."""
        # 1. Validation
        if not title or not str(title).strip():
            return ToolResult(
                success=False,
                tool_name="create_calendar_event",
                error_code="VALIDATION_ERROR",
                message="Event title is required and cannot be empty.",
            )

        if not source_session_id or not str(source_session_id).strip():
            return ToolResult(
                success=False,
                tool_name="create_calendar_event",
                error_code="MISSING_SESSION",
                message="source_session_id is required for event creation.",
            )

        if not self.validate_datetime_string(start_time):
            return ToolResult(
                success=False,
                tool_name="create_calendar_event",
                error_code="MISSING_DATE_TIME",
                message=f"Invalid or ambiguous start_time '{start_time}'. Please provide an explicit date and time (e.g. '2026-10-15 15:00' or 'Friday 5:00 PM').",
            )

        if not self.validate_datetime_string(end_time):
            return ToolResult(
                success=False,
                tool_name="create_calendar_event",
                error_code="MISSING_DATE_TIME",
                message=f"Invalid or ambiguous end_time '{end_time}'. Please provide an explicit date and time (e.g. '2026-10-15 16:00' or 'Friday 6:00 PM').",
            )

        if not participants or not isinstance(participants, list) or len(participants) == 0:
            return ToolResult(
                success=False,
                tool_name="create_calendar_event",
                error_code="MISSING_PARTICIPANTS",
                message="At least one participant is required to create a calendar event.",
            )

        clean_evidence_ids = [str(e) for e in (source_evidence_ids or [])]
        clean_participants = [str(p).strip() for p in participants if str(p).strip()]

        # 2. Creation
        event_id = f"event_{uuid.uuid4().hex[:6]}"
        now = time.time()

        event_record = {
            "event_id": event_id,
            "title": title.strip(),
            "description": description.strip() if description else "",
            "start_time": start_time.strip(),
            "end_time": end_time.strip(),
            "participants": clean_participants,
            "source_session_id": source_session_id,
            "source_evidence_ids": clean_evidence_ids,
            "source_timestamp": source_timestamp,
            "created_at": now,
            "created_by": "recallai",
        }

        if source_session_id not in self._events:
            self._events[source_session_id] = {}

        self._events[source_session_id][event_id] = event_record

        return ToolResult(
            success=True,
            tool_name="create_calendar_event",
            resource_id=event_id,
            message=f"Calendar event '{title.strip()}' scheduled from {start_time} to {end_time}.",
            metadata=event_record,
            source_session_id=source_session_id,
            source_evidence_ids=clean_evidence_ids,
            source_timestamp=source_timestamp,
        )

    def list_calendar_events(
        self,
        session_id: str,
        date: Optional[str] = None,
    ) -> ToolResult:
        """List calendar events for a specific meeting session with optional date filtering."""
        if not session_id or not str(session_id).strip():
            return ToolResult(
                success=False,
                tool_name="list_calendar_events",
                error_code="MISSING_SESSION",
                message="session_id is required to list calendar events.",
            )

        session_events = list(self._events.get(session_id, {}).values())

        if date:
            d_clean = date.strip().lower()
            session_events = [e for e in session_events if d_clean in e.get("start_time", "").lower()]

        return ToolResult(
            success=True,
            tool_name="list_calendar_events",
            message=f"Retrieved {len(session_events)} calendar event(s) for session '{session_id}'.",
            metadata={"events": session_events, "total_count": len(session_events)},
            source_session_id=session_id,
        )

    def get_event(self, session_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single event record by ID within a session."""
        return self._events.get(session_id, {}).get(event_id)

    def clear_session(self, session_id: str):
        """Cleanly remove calendar events for a session."""
        if session_id in self._events:
            del self._events[session_id]
