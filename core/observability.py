"""
Lightweight Observability & Tracing Module for RecallAI.
Integrates optional Langfuse tracing for:
- LLM generation traces
- Retrieval traces & relevance scores
- Latency & token monitoring
- Evaluation run visibility

Guaranteed non-breaking: if LANGFUSE_ENABLED is false or keys are absent,
all functions no-op gracefully with zero overhead and zero network traffic.
"""

import os
from typing import Optional, List, Dict, Any
from core.config import (
    LANGFUSE_ENABLED,
    LANGFUSE_PUBLIC_KEY,
    LANGFUSE_SECRET_KEY,
    LANGFUSE_HOST,
)


def is_langfuse_enabled() -> bool:
    """Return whether Langfuse tracing is active and configured."""
    enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("1", "true", "yes")
    pub_key = os.getenv("LANGFUSE_PUBLIC_KEY") or LANGFUSE_PUBLIC_KEY
    sec_key = os.getenv("LANGFUSE_SECRET_KEY") or LANGFUSE_SECRET_KEY
    return bool(enabled and pub_key and sec_key)


def get_langfuse_callback(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[Any]:
    """
    Instantiate and return a LangChain/LangGraph compatible Langfuse CallbackHandler.
    Returns None if tracing is disabled or initialization fails.
    """
    if not is_langfuse_enabled():
        return None

    pub_key = os.getenv("LANGFUSE_PUBLIC_KEY") or LANGFUSE_PUBLIC_KEY
    sec_key = os.getenv("LANGFUSE_SECRET_KEY") or LANGFUSE_SECRET_KEY
    host = os.getenv("LANGFUSE_HOST") or LANGFUSE_HOST or "https://cloud.langfuse.com"

    try:
        from langfuse.langchain import CallbackHandler
        return CallbackHandler(
            public_key=pub_key,
            secret_key=sec_key,
            host=host,
            session_id=session_id,
            user_id=user_id,
            tags=tags or ["recallai"],
        )
    except Exception as e:
        print(f"[Observability] Warning: Failed to initialize Langfuse callback: {e}")
        return None


def get_langfuse_callbacks(
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> List[Any]:
    """Return list of active Langfuse callbacks (or empty list if disabled)."""
    cb = get_langfuse_callback(session_id=session_id, user_id=user_id, tags=tags)
    return [cb] if cb is not None else []
