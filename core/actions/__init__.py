"""
Phase 8 Controlled External Actions & MCP Tools Package.
Exports:
- ToolResult, PendingAction, ActionExecution
- TaskTool, CalendarTool, EmailTool
- ConfirmationManager
- ToolDefinition, ToolRegistry, DEFAULT_TOOL_REGISTRY
- ActionResolver, ResolutionResult
"""

from core.actions.models import ToolResult, PendingAction, ActionExecution
from core.actions.task_tools import TaskTool
from core.actions.calendar_tools import CalendarTool
from core.actions.email_tools import EmailTool
from core.actions.confirmation import ConfirmationManager
from core.actions.tool_registry import ToolDefinition, ToolRegistry, DEFAULT_TOOL_REGISTRY
from core.actions.action_resolver import ActionResolver, ResolutionResult

__all__ = [
    "ToolResult",
    "PendingAction",
    "ActionExecution",
    "TaskTool",
    "CalendarTool",
    "EmailTool",
    "ConfirmationManager",
    "ToolDefinition",
    "ToolRegistry",
    "DEFAULT_TOOL_REGISTRY",
    "ActionResolver",
    "ResolutionResult",
]
