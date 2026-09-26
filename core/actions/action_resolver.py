"""
Action Intelligence Resolver for Phase 8.
Bridges Phase 6 Meeting Intelligence (ActionItems, Decisions) and Conversational
Intent with Phase 8 Tool Invocations.
- Resolves action items into structured tool arguments.
- Strictly guards against hallucination: asks user for missing fields rather than guessing.
"""

from typing import Dict, List, Optional, Any, Tuple
from pydantic import BaseModel, Field

from core.intelligence.extractor import ActionItem
from core.actions.models import ToolResult
from core.actions.tool_registry import ToolRegistry, DEFAULT_TOOL_REGISTRY


class ResolutionResult(BaseModel):
    """Output from the action resolver: either ready-to-execute tool call or request for missing info."""
    is_ready: bool
    tool_name: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
    resolved_action_item: Optional[Dict[str, Any]] = None


class ActionResolver:
    """Resolves meeting intelligence and user intent into validated tool calls."""

    def __init__(self, registry: ToolRegistry = None):
        self.registry = registry or DEFAULT_TOOL_REGISTRY

    def resolve_action_item_to_task(
        self,
        action_item: ActionItem,
        session_id: str,
        custom_notes: Optional[str] = None,
    ) -> ResolutionResult:
        """Convert a structured ActionItem into a create_task tool call."""
        if not action_item or not action_item.task:
            return ResolutionResult(
                is_ready=False,
                missing_fields=["task"],
                clarification_prompt="Cannot create task: action item description is empty.",
            )

        ev_ids = []
        if getattr(action_item, "evidence", None):
            ev_ids.append(action_item.evidence)

        args = {
            "title": action_item.task,
            "description": custom_notes or f"Created from meeting commitment: {action_item.task}",
            "owner": action_item.owner,
            "deadline": action_item.deadline,
            "source_session_id": session_id,
            "source_evidence_ids": ev_ids,
            "source_timestamp": getattr(action_item, "timestamp", None),
        }

        return ResolutionResult(
            is_ready=True,
            tool_name="create_task",
            arguments=args,
            resolved_action_item=action_item.model_dump() if hasattr(action_item, "model_dump") else dict(action_item),
        )

    def resolve_action_item_to_calendar(
        self,
        action_item: ActionItem,
        session_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        participants: Optional[List[str]] = None,
    ) -> ResolutionResult:
        """
        Convert an ActionItem into a create_calendar_event tool call.
        Strictly detects missing date/time/participants and refuses to invent them.
        """
        missing = []
        if not start_time:
            missing.append("start_time")
        if not end_time:
            missing.append("end_time")
        if not participants or len(participants) == 0:
            missing.append("participants")

        if missing:
            missing_str = ", ".join(missing).replace("_", " ")
            return ResolutionResult(
                is_ready=False,
                tool_name="create_calendar_event",
                missing_fields=missing,
                clarification_prompt=(
                    f"I can schedule a calendar event for '{action_item.task}', but I need missing details: {missing_str}."
                ),
            )

        ev_ids = []
        if getattr(action_item, "evidence", None):
            ev_ids.append(action_item.evidence)

        args = {
            "title": action_item.task,
            "start_time": start_time,
            "end_time": end_time,
            "participants": participants,
            "description": f"Follow-up meeting regarding: {action_item.task}",
            "source_session_id": session_id,
            "source_evidence_ids": ev_ids,
            "source_timestamp": getattr(action_item, "timestamp", None),
        }

        return ResolutionResult(
            is_ready=True,
            tool_name="create_calendar_event",
            arguments=args,
            resolved_action_item=action_item.model_dump() if hasattr(action_item, "model_dump") else dict(action_item),
        )

    def resolve_action_item_to_email(
        self,
        action_item: ActionItem,
        session_id: str,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        custom_body: Optional[str] = None,
    ) -> ResolutionResult:
        """
        Convert an ActionItem into a draft_email tool call.
        Guards against missing recipient email address.
        """
        if not recipient:
            owner_hint = f" for {action_item.owner}" if action_item.owner else ""
            return ResolutionResult(
                is_ready=False,
                tool_name="draft_email",
                missing_fields=["recipient"],
                clarification_prompt=f"What should the recipient email address be{owner_hint}?",
            )

        ev_ids = []
        if getattr(action_item, "evidence", None):
            ev_ids.append(action_item.evidence)

        subj = subject or f"Meeting Follow-up: {action_item.task}"
        body = custom_body or (
            f"Hi,\n\n"
            f"This is a follow-up regarding the action item agreed upon in our meeting:\n"
            f"• Task: {action_item.task}\n"
            f"• Owner: {action_item.owner or 'Unassigned'}\n"
            f"• Due Date: {action_item.deadline or 'Not specified'}\n\n"
            f"Please let us know if you need any assistance.\n\n"
            f"Best regards,\nJitsly Assistant"
        )

        args = {
            "recipient": recipient,
            "subject": subj,
            "body": body,
            "source_session_id": session_id,
            "source_evidence_ids": ev_ids,
            "source_timestamp": getattr(action_item, "timestamp", None),
        }

        return ResolutionResult(
            is_ready=True,
            tool_name="draft_email",
            arguments=args,
            resolved_action_item=action_item.model_dump() if hasattr(action_item, "model_dump") else dict(action_item),
        )

    def find_action_item_by_query(
        self,
        query: str,
        action_items: List[Any],
    ) -> Optional[ActionItem]:
        """Match an action item from session memory using natural language tokens."""
        if not action_items:
            return None

        q_lower = query.lower()

        # Check for numeric references: "first one", "#1", "action item 2"
        if "first" in q_lower or "#1" in q_lower or "item 1" in q_lower:
            return action_items[0] if len(action_items) > 0 else None
        if "second" in q_lower or "#2" in q_lower or "item 2" in q_lower:
            return action_items[1] if len(action_items) > 1 else None
        if "third" in q_lower or "#3" in q_lower or "item 3" in q_lower:
            return action_items[2] if len(action_items) > 2 else None

        # Check for owner name or task keyword matches
        for item in action_items:
            owner = getattr(item, "owner", None)
            task = getattr(item, "task", "")
            if owner and owner.lower() in q_lower:
                return item
            words = [w for w in task.lower().split() if len(w) > 3]
            if any(w in q_lower for w in words):
                return item

        # Default fallback to first if specifically asking about an action item
        return action_items[0] if action_items else None
