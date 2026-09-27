"""
Core package for RecallAI.
Modular AI Meeting & Video Intelligence Assistant.

Subpackages:
- ingestion: Audio & video input processing, normalization, and chunking
- transcription: Speech-to-text with Whisper (English/multilingual) and Sarvam AI (Hindi/Hinglish)
- intelligence: Structured extraction (action items, decisions, open questions) and summarization
- retrieval: ChromaDB vector storage, semantic search, evidence provenance, and grounded RAG
- memory: Multi-turn conversational memory with pronoun and entity resolution
- voice: Voice interaction (speech-to-text questions and text-to-speech answers)
- actions: Controlled external actions, safety confirmation gate, and MCP tools
"""

from core.config import (
    DOWNLOAD_DIR,
    MAX_UPLOAD_SIZE_MB,
    MAX_AUDIO_DURATION_MINUTES,
    MAX_TRANSCRIPT_CHARS,
    get_system_health,
)
from core.logger import get_logger
from core.llm_provider import get_llm
from core.workflow import create_meeting_workflow, run_assistant_workflow

__all__ = [
    "DOWNLOAD_DIR",
    "MAX_UPLOAD_SIZE_MB",
    "MAX_AUDIO_DURATION_MINUTES",
    "MAX_TRANSCRIPT_CHARS",
    "get_system_health",
    "get_logger",
    "get_llm",
    "create_meeting_workflow",
    "run_assistant_workflow",
]
