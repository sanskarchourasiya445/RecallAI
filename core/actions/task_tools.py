"""
Task Management Tool for Phase 8.
Supports creating and listing tasks derived from meeting action items.
Maintains session isolation and evidence provenance.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from core.actions.models import ToolResult


class TaskTool:
    """Session-isolated task manager adapter."""

    def __init__(self):
        # session_id -> {task_id -> task_dict}
        self._tasks: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        owner: Optional[str] = None,
        deadline: Optional[str] = None,
        source_session_id: str = None,
        source_evidence_ids: Optional[List[str]] = None,
        source_timestamp: Optional[str] = None,
    ) -> ToolResult:
        """Create a new task with provenance linking back to meeting evidence."""
        # 1. Validation
        if not title or not str(title).strip():
            return ToolResult(
                success=False,
                tool_name="create_task",
                error_code="VALIDATION_ERROR",
                message="Task title is required and cannot be empty.",
            )

        if not source_session_id or not str(source_session_id).strip():
            return ToolResult(
                success=False,
                tool_name="create_task",
                error_code="MISSING_SESSION",
                message="source_session_id is required for task creation.",
            )

        clean_evidence_ids = [str(e) for e in (source_evidence_ids or [])]
        clean_owner = None if str(owner).lower() in ("none", "null", "not specified", "unassigned", "") else owner
        clean_deadline = None if str(deadline).lower() in ("none", "null", "not specified", "n/a", "") else deadline

        # 2. Resource creation
        task_id = f"task_{uuid.uuid4().hex[:6]}"
        now = time.time()

        task_record = {
            "task_id": task_id,
            "title": title.strip(),
            "description": description.strip() if description else "",
            "owner": clean_owner,
            "deadline": clean_deadline,
            "status": "Open",
            "source_session_id": source_session_id,
            "source_evidence_ids": clean_evidence_ids,
            "source_timestamp": source_timestamp,
            "created_at": now,
            "created_by": "recallai",
        }

        if source_session_id not in self._tasks:
            self._tasks[source_session_id] = {}

        self._tasks[source_session_id][task_id] = task_record

        return ToolResult(
            success=True,
            tool_name="create_task",
            resource_id=task_id,
            message=f"Task '{title.strip()}' created successfully.",
            metadata=task_record,
            source_session_id=source_session_id,
            source_evidence_ids=clean_evidence_ids,
            source_timestamp=source_timestamp,
        )

    def list_tasks(
        self,
        session_id: str,
        owner: Optional[str] = None,
        status: Optional[str] = None,
    ) -> ToolResult:
        """List tasks belonging to a specific meeting session with optional filters."""
        if not session_id or not str(session_id).strip():
            return ToolResult(
                success=False,
                tool_name="list_tasks",
                error_code="MISSING_SESSION",
                message="session_id is required to list tasks.",
            )

        session_tasks = list(self._tasks.get(session_id, {}).values())

        if owner:
            owner_lower = owner.strip().lower()
            session_tasks = [t for t in session_tasks if t.get("owner") and t["owner"].strip().lower() == owner_lower]

        if status:
            status_lower = status.strip().lower()
            session_tasks = [t for t in session_tasks if t.get("status") and t["status"].strip().lower() == status_lower]

        return ToolResult(
            success=True,
            tool_name="list_tasks",
            message=f"Retrieved {len(session_tasks)} task(s) for session '{session_id}'.",
            metadata={"tasks": session_tasks, "total_count": len(session_tasks)},
            source_session_id=session_id,
        )

    def get_task(self, session_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single task record by ID within a session."""
        return self._tasks.get(session_id, {}).get(task_id)

    def clear_session(self, session_id: str):
        """Cleanly remove tasks for a session."""
        if session_id in self._tasks:
            del self._tasks[session_id]
