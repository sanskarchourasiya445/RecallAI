"""
Voice interaction package for RecallAI.
Provides:
  - Voice input transcription (STT via Whisper / Sarvam)
  - Synthesized spoken answer audio (TTS via gTTS)
  - LiveKit/Pipecat pipeline adapter (Phase 6)
"""

from core.voice.voice import (
    transcribe_voice_input,
    transcribe_voice_input_safe,
    synthesize_answer,
    prepare_text_for_speech,
)

__all__ = [
    "transcribe_voice_input",
    "transcribe_voice_input_safe",
    "synthesize_answer",
    "prepare_text_for_speech",
]
