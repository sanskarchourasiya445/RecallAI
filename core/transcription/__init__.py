"""
Transcription module for RecallAI.
Integrates Whisper (local/GPU multilingual transcription) and Sarvam AI (specialized Hindi/Hinglish transcription).
"""

from core.transcription.transcriber import (
    transcribe_all,
    transcribe_all_with_segments,
    transcribe_chunk_whisper,
    transcribe_chunk_sarvam,
    clean_transcript,
    load_model,
    get_whisper_model,
    get_sarvam_api_key,
    get_sarvam_model,
)

__all__ = [
    "transcribe_all",
    "transcribe_all_with_segments",
    "transcribe_chunk_whisper",
    "transcribe_chunk_sarvam",
    "clean_transcript",
    "load_model",
    "get_whisper_model",
    "get_sarvam_api_key",
    "get_sarvam_model",
]
