"""
Central Tool Registry for Phase 8.
Defines MCP-compatible tool definitions, schemas, confirmation policies,
and unified invocation pipeline.
"""

from typing import Dict, List, Optional, Any, Callable
from pydantic import BaseModel, Field

from core.actions.models import ToolResult, PendingAction
from core.actions.task_tools import TaskTool
from core.actions.calendar_tools import CalendarTool
from core.actions.email_tools import EmailTool
from core.actions.confirmation import ConfirmationManager


class ToolDefinition(BaseModel):
    """Metadata and execution specification for an MCP-compatible tool."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    risk_level: str = "low"  # low, medium, high
    requires_confirmation: bool = False
    handler: Any = Field(exclude=True)  # callable


class ToolRegistry:
    """Registry coordinating task, calendar, email tools, confirmation gates, and schemas."""

    def __init__(
        self,
        task_tool: Optional[TaskTool] = None,
        calendar_tool: Optional[CalendarTool] = None,
        email_tool: Optional[EmailTool] = None,
        confirmation_manager: Optional[ConfirmationManager] = None,
    ):
        self.task_tool = task_tool or TaskTool()
        self.calendar_tool = calendar_tool or CalendarTool()
        self.email_tool = email_tool or EmailTool()
        self.confirmation_mgr = confirmation_manager or ConfirmationManager()

        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register the 6 core meeting action tools with standard JSON schemas."""

        # 1. create_task
        self.register_tool(
            ToolDefinition(
                name="create_task",
                description="Create an actionable task with owner, deadline, and meeting evidence provenance.",
                risk_level="low",
                requires_confirmation=False,
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Title or task description"},
                        "description": {"type": "string", "description": "Detailed background or notes"},
                        "owner": {"type": "string", "description": "Person assigned or null if unassigned"},
                        "deadline": {"type": "string", "description": "Explicit due date/timeframe or null"},
                        "source_session_id": {"type": "string", "description": "Active meeting session ID"},
                        "source_evidence_ids": {"type": "array", "items": {"type": "string"}, "description": "Evidence IDs e.g. ['E1']"},
                        "source_timestamp": {"type": "string", "description": "Transcript timestamp e.g. '00:01:40'"},
                    },
                    "required": ["title", "source_session_id"],
                },
                handler=lambda **kwargs: self.task_tool.create_task(**kwargs),
            )
        )

        # 2. list_tasks
        self.register_tool(
            ToolDefinition(
                name="list_tasks",
                description="List tasks created for a specific meeting session with optional filters.",
                risk_level="low",
                requires_confirmation=False,
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Meeting session ID"},
                        "owner": {"type": "string", "description": "Filter by assignee"},
                        "status": {"type": "string", "description": "Filter by status: Open, In Progress, Done"},
                    },
                    "required": ["session_id"],
                },
                handler=lambda **kwargs: self.task_tool.list_tasks(**kwargs),
            )
        )

        # 3. create_calendar_event
        self.register_tool(
            ToolDefinition(
                name="create_calendar_event",
                description="Schedule a calendar event. Consequential external action requiring confirmation.",
                risk_level="medium",
                requires_confirmation=True,
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Meeting or event title"},
                        "start_time": {"type": "string", "description": "Start datetime e.g. '2026-10-15 14:00'"},
                        "end_time": {"type": "string", "description": "End datetime e.g. '2026-10-15 15:00'"},
                        "participants": {"type": "array", "items": {"type": "string"}, "description": "List of attendees"},
                        "description": {"type": "string", "description": "Agenda or description"},
                        "source_session_id": {"type": "string", "description": "Meeting session ID"},
                        "source_evidence_ids": {"type": "array", "items": {"type": "string"}, "description": "Evidence IDs"},
                        "source_timestamp": {"type": "string", "description": "Transcript timestamp"},
                    },
                    "required": ["title", "start_time", "end_time", "participants", "source_session_id"],
                },
                handler=lambda **kwargs: self.calendar_tool.create_calendar_event(**kwargs),
            )
        )

        # 4. list_calendar_events
        self.register_tool(
            ToolDefinition(
                name="list_calendar_events",
                description="List scheduled calendar events for a meeting session.",
                risk_level="low",
                requires_confirmation=False,
                input_schema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Meeting session ID"},
                        "date": {"type": "string", "description": "Optional date filter e.g. '2026-10-15'"},
                    },
                    "required": ["session_id"],
                },
                handler=lambda **kwargs: self.calendar_tool.list_calendar_events(**kwargs),
            )
        )

        # 5. draft_email
        self.register_tool(
            ToolDefinition(
                name="draft_email",
                description="Draft an email for review. Safe operation, does not send.",
                risk_level="low",
                requires_confirmation=False,
                input_schema={
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email body content"},
                        "source_session_id": {"type": "string", "description": "Meeting session ID"},
                        "source_evidence_ids": {"type": "array", "items": {"type": "string"}, "description": "Evidence IDs"},
                        "source_timestamp": {"type": "string", "description": "Transcript timestamp"},
                    },
                    "required": ["recipient", "subject", "body", "source_session_id"],
                },
                handler=lambda **kwargs: self.email_tool.draft_email(**kwargs),
            )
        )

        # 6. send_email
        self.register_tool(
            ToolDefinition(
                name="send_email",
                description="Send an email to a recipient. Consequential action requiring explicit confirmation.",
                risk_level="high",
                requires_confirmation=True,
                input_schema={
                    "type": "object",
                    "properties": {
                        "recipient": {"type": "string", "description": "Recipient email address"},
                        "subject": {"type": "string", "description": "Email subject line"},
                        "body": {"type": "string", "description": "Email message body"},
                        "draft_id": {"type": "string", "description": "Optional draft ID if sending existing draft"},
                        "source_session_id": {"type": "string", "description": "Meeting session ID"},
                        "source_evidence_ids": {"type": "array", "items": {"type": "string"}, "description": "Evidence IDs"},
                        "source_timestamp": {"type": "string", "description": "Transcript timestamp"},
                    },
                    "required": ["recipient", "subject", "body", "source_session_id"],
                },
                handler=lambda **kwargs: self.email_tool.send_email(**kwargs),
            )
        )

    def register_tool(self, tool_def: ToolDefinition):
        """Register a new tool definition."""
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Lookup tool definition by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return MCP-standard list of tool specifications."""
        output = []
        for t in self._tools.values():
            output.append({
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema,
                "riskLevel": t.risk_level,
                "requiresConfirmation": t.requires_confirmation,
            })
        return output

    def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        bypass_confirmation: bool = False,
    ) -> ToolResult:
        """
        Execute a tool by name with arguments.
        Enforces Confirmation Gate for consequential actions.
        """
        if name not in self._tools:
            return ToolResult(
                success=False,
                tool_name=name,
                error_code="TOOL_NOT_FOUND",
                message=f"Tool '{name}' is not registered in the system.",
            )

        tool_def = self._tools[name]
        session_id = arguments.get("source_session_id") or arguments.get("session_id", "default")

        # Confirmation Gate Check
        if tool_def.requires_confirmation and not bypass_confirmation:
            preview = self._build_preview(name, arguments)
            staged = self.confirmation_mgr.stage_action(
                tool_name=name,
                arguments=arguments,
                session_id=session_id,
                preview_summary=preview,
                risk_level=tool_def.risk_level,
                source_evidence_ids=arguments.get("source_evidence_ids", []),
                source_timestamp=arguments.get("source_timestamp"),
            )
            return ToolResult(
                success=True,
                tool_name=name,
                message=f"Action '{name}' staged for user confirmation.",
                metadata={
                    "action_id": staged.action_id,
                    "status": "pending_confirmation",
                    "preview_summary": preview,
                    "risk_level": tool_def.risk_level,
                    "expires_at": staged.expires_at,
                },
                source_session_id=session_id,
                source_evidence_ids=staged.source_evidence_ids,
                source_timestamp=staged.source_timestamp,
            )

        # Direct execution
        try:
            res: ToolResult = tool_def.handler(**arguments)
            # Record execution in audit trail
            self.confirmation_mgr.record_execution(
                session_id=session_id,
                tool_name=name,
                arguments=arguments,
                result=res.to_dict(),
                status="success" if res.success else "failed",
                source_evidence_ids=arguments.get("source_evidence_ids", []),
                source_timestamp=arguments.get("source_timestamp"),
            )
            return res

        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=name,
                error_code="EXECUTION_ERROR",
                message=f"Tool execution failed: {str(e)}",
                source_session_id=session_id,
            )

    def confirm_action(self, action_id: str, session_id: str) -> ToolResult:
        """Delegate confirmation to ConfirmationManager."""
        return self.confirmation_mgr.confirm_action(
            action_id=action_id,
            session_id=session_id,
            tool_executor_fn=lambda name, args: self.execute_tool(name, args, bypass_confirmation=True),
        )

    def reject_action(self, action_id: str, session_id: str, reason: str = "User declined") -> ToolResult:
        """Delegate rejection to ConfirmationManager."""
        return self.confirmation_mgr.reject_action(action_id, session_id, reason)

    def _build_preview(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Generate human-readable action preview summary for the confirmation prompt."""
        ev = arguments.get("source_evidence_ids", [])
        ts = arguments.get("source_timestamp")
        src_note = f" (Evidence: {', '.join(ev)}, Time: {ts})" if ev or ts else ""

        if tool_name == "create_calendar_event":
            return (
                f"Schedule Event: '{arguments.get('title')}'\n"
                f"When: {arguments.get('start_time')} - {arguments.get('end_time')}\n"
                f"Participants: {', '.join(arguments.get('participants', []))}\n"
                f"Source: Meeting dialogue{src_note}"
            )
        elif tool_name == "send_email":
            return (
                f"Send Email to: {arguments.get('recipient')}\n"
                f"Subject: {arguments.get('subject')}\n"
                f"Body Preview: {str(arguments.get('body', ''))[:100]}...\n"
                f"Source: Meeting dialogue{src_note}"
            )
        return f"Execute '{tool_name}' with arguments: {arguments}"

    def clear_session(self, session_id: str):
        """Clean all data across tools for a session."""
        self.task_tool.clear_session(session_id)
        self.calendar_tool.clear_session(session_id)
        self.email_tool.clear_session(session_id)
        self.confirmation_mgr.clear_session(session_id)


# Global default registry instance
DEFAULT_TOOL_REGISTRY = ToolRegistry()
