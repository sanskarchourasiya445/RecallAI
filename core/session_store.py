"""
Central In-Memory Meeting Session Store for RecallAI.
Manages meeting workspaces, staged media sources, and pipeline processing state.
Framework-agnostic: shared across FastAPI, frontend clients, and CLI pipelines.
"""

import os
import uuid
import threading
from typing import Dict, Any, Optional, List

from core.logger import get_logger
from core.demo import (
    load_demo_meeting,
    DEMO_SESSION_ID,
    load_demo_meeting_2,
    DEMO_SESSION_ID_2,
    load_all_demo_meetings,
)
from utils.audio_processor import process_input, cleanup_temp_files
from core.transcription import transcribe_all_with_segments
from core.intelligence import (
    summarize,
    generate_title,
    extract_meeting_intelligence,
    format_action_items,
    format_key_decisions,
    format_open_questions,
)
from core.retrieval import build_vector_store, build_rag_chain

logger = get_logger("recallai.session_store")


class MeetingSessionStore:
    """Thread-safe storage for meeting intelligence workspaces and staged inputs."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._staged_sources: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def stage_source(
        self,
        session_id: str,
        source: str,
        source_type: str = "upload",
        chunks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Stage an ingested audio/video source awaiting transcription/processing."""
        with self._lock:
            info = {
                "session_id": session_id,
                "source": source,
                "source_type": source_type,
                "chunks": chunks or [],
                "status": "staged",
            }
            self._staged_sources[session_id] = info
            return info

    def get_staged_source(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve staged source metadata for a session."""
        with self._lock:
            return self._staged_sources.get(session_id)

    def save_session(self, session_id: str, data: Dict[str, Any]):
        """Persist or update a completed meeting session workspace."""
        with self._lock:
            data["session_id"] = session_id
            self._sessions[session_id] = data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a meeting session by ID.
        Auto-loads and caches demo meeting if DEMO_SESSION_ID is requested.
        """
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]

            if session_id == DEMO_SESSION_ID:
                logger.info("Auto-loading demo meeting session '%s'...", session_id)
                demo_data = load_demo_meeting()
                self._sessions[session_id] = demo_data
                return demo_data

            if session_id == DEMO_SESSION_ID_2:
                logger.info("Auto-loading demo meeting session 2 '%s'...", session_id)
                demo_data = load_demo_meeting_2()
                self._sessions[session_id] = demo_data
                return demo_data

            return None

    def list_sessions(self) -> List[str]:
        """Return list of all registered session IDs. Auto-loads demo meetings if empty."""
        with self._lock:
            if not self._sessions:
                demo1 = load_demo_meeting()
                self._sessions[DEMO_SESSION_ID] = demo1
                demo2 = load_demo_meeting_2()
                self._sessions[DEMO_SESSION_ID_2] = demo2
            return list(self._sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        """Remove a session from memory."""
        with self._lock:
            removed = self._sessions.pop(session_id, None) is not None
            self._staged_sources.pop(session_id, None)
            return removed

    def clear(self):
        """Clear all stored sessions."""
        with self._lock:
            self._sessions.clear()
            self._staged_sources.clear()


# Default singleton instance
DEFAULT_SESSION_STORE = MeetingSessionStore()


def process_meeting_source(
    source: str,
    language: str = "english",
    session_id: Optional[str] = None,
    store: Optional[MeetingSessionStore] = None,
) -> Dict[str, Any]:
    """
    Execute full end-to-end meeting processing pipeline:
    Audio Acquisition → Transcription → Title & Summary → Intelligence Extraction → Vector Indexing.
    Saves the resulting workspace into the session store.
    """
    sid = session_id or uuid.uuid4().hex[:8]
    session_store = store or DEFAULT_SESSION_STORE

    logger.info("Processing meeting session '%s' from source: %s (lang: %s)", sid, source, language)

    # 1. Audio Acquisition & Standardization
    chunks = process_input(source)
    try:
        # 2. Multilingual Speech-to-Text
        transcript, segments = transcribe_all_with_segments(chunks, language)
    finally:
        cleanup_temp_files(chunks)

    if not transcript or not transcript.strip():
        raise ValueError(f"Transcription for session '{sid}' yielded no audible speech or text. Pipeline halted.")

    # 3. Title Generation with fallback
    try:
        title = generate_title(transcript)
    except Exception as e:
        logger.warning("Title generation fallback triggered: %s", e)
        title = "Untitled Meeting"

    # 4. Executive Summarization with fallback
    try:
        summary = summarize(transcript)
    except Exception as e:
        logger.warning("Summarization fallback triggered: %s", e)
        summary = f"Summary generation unavailable: {e}"

    # 5. Structured Meeting Intelligence Extraction
    try:
        intel = extract_meeting_intelligence(transcript)
        action_items_structured = intel.get("action_items", [])
        decisions_structured = intel.get("key_decisions", [])
        questions_structured = intel.get("open_questions", [])
        action_item_text = format_action_items(action_items_structured)
        decisions_text = format_key_decisions(decisions_structured)
        questions_text = format_open_questions(questions_structured)
    except Exception as e:
        logger.warning("Intelligence extraction fallback triggered: %s", e)
        action_items_structured = []
        decisions_structured = []
        questions_structured = []
        action_item_text = "Action item extraction unavailable."
        decisions_text = "Key decisions extraction unavailable."
        questions_text = "Open questions extraction unavailable."

    # 6. ChromaDB Vector Store & LCEL RAG Chain Indexing
    vector_store = None
    rag_chain = None
    try:
        vector_store = build_vector_store(transcript, session_id=sid, source=source, segments=segments)
        rag_chain = build_rag_chain(transcript, session_id=sid, source=source, segments=segments)
    except Exception as e:
        logger.warning("RAG indexing failed for session '%s': %s", sid, e)

    session_data = {
        "session_id": sid,
        "title": title,
        "source": source,
        "transcript": transcript,
        "segments": segments,
        "summary": summary,
        "action_items": action_item_text,
        "key_decisions": decisions_text,
        "open_questions": questions_text,
        "action_items_structured": action_items_structured,
        "key_decisions_structured": decisions_structured,
        "open_questions_structured": questions_structured,
        "vector_store": vector_store,
        "rag_chain": rag_chain,
        "status": "completed",
    }

    session_store.save_session(sid, session_data)
    return session_data
