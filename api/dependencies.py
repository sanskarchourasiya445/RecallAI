"""
FastAPI Dependencies for Gistly API.
Provides singleton dependency injection for:
- MeetingSessionStore
- ToolRegistry
- ConversationMemoryManager
"""

from typing import Dict, Any
from fastapi import HTTPException, status
from core.session_store import DEFAULT_SESSION_STORE, MeetingSessionStore
from core.actions.tool_registry import DEFAULT_TOOL_REGISTRY, ToolRegistry
from core.memory import ConversationMemoryManager

DEFAULT_MEMORY_MANAGER = ConversationMemoryManager()


def get_session_store() -> MeetingSessionStore:
    """Provide singleton MeetingSessionStore."""
    return DEFAULT_SESSION_STORE


def get_tool_registry() -> ToolRegistry:
    """Provide singleton ToolRegistry with Phase 8 action tools."""
    return DEFAULT_TOOL_REGISTRY


def get_memory_manager() -> ConversationMemoryManager:
    """Provide singleton ConversationMemoryManager for multi-turn session tracking."""
    return DEFAULT_MEMORY_MANAGER


def get_meeting_session(session_id: str) -> Dict[str, Any]:
    """Dependency looking up session by ID; raises 404 if absent."""
    session = DEFAULT_SESSION_STORE.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting session '{session_id}' not found. Please ingest or process the meeting first.",
        )
    return session
