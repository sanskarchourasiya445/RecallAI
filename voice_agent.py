"""
RecallAI LiveKit Voice Agent — Phase 6
Runs as a separate process/entry point.
Orchestrates: Microphone → LiveKit → STT → RecallAI AI Pipeline → TTS → LiveKit

Architecture:
  LiveKit Room
      ↓ audio frames
  Silero VAD (turn detection)
      ↓ speech segments
  Deepgram/Whisper STT
      ↓ text
  RecallAI: run_assistant_workflow / run_workspace_assistant
      ↓ grounded answer
  gTTS / OpenAI TTS
      ↓ audio
  LiveKit (speak to user)

Context is preserved per-session: meeting_id routes to the correct
session store entry so RAG/memory is meeting-aware.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai as lk_openai, silero

from core.logger import get_logger
from core.session_store import DEFAULT_SESSION_STORE
from core.voice.pipeline import RecallAIPipelineAdapter

logger = get_logger("recallai.voice_agent")

# ---------------------------------------------------------------------------
# LiveKit entrypoint — called for each new voice room
# ---------------------------------------------------------------------------

async def entrypoint(ctx: JobContext) -> None:
    """
    Main entrypoint for each LiveKit voice session.
    Extracts meeting context from room metadata, then launches the pipeline.
    """
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Extract context from room metadata (set by frontend when creating token)
    room_meta: dict = {}
    try:
        import json
        room_meta = json.loads(ctx.room.metadata or "{}")
    except Exception:
        pass

    session_id: Optional[str] = room_meta.get("session_id")  # None = workspace mode
    language: str = room_meta.get("language", "english")

    logger.info(
        "Voice session started | room=%s session_id=%s language=%s",
        ctx.room.name, session_id, language,
    )

    # Build the Pipecat-compatible adapter that routes through RecallAI
    recall_llm = RecallAIPipelineAdapter(
        session_store=DEFAULT_SESSION_STORE,
        session_id=session_id,
        language=language,
    )

    # Prefer Deepgram for low-latency STT; fall back to Whisper if not configured
    deepgram_api_key = os.environ.get("DEEPGRAM_API_KEY")
    if deepgram_api_key:
        stt_plugin = deepgram.STT(api_key=deepgram_api_key)
    else:
        # Use livekit-agents built-in Whisper (local, no API key needed)
        from livekit.plugins import openai as lk_openai_stt
        stt_plugin = lk_openai_stt.STT.with_whisper()

    # Prefer OpenAI TTS for natural voice; fall back to gTTS-backed synthesis
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        tts_plugin = lk_openai.TTS(
            model="tts-1",
            voice=room_meta.get("voice", "nova"),
            api_key=openai_api_key,
        )
    else:
        from core.voice.tts_adapter import GTTSAdapter
        tts_plugin = GTTSAdapter(language=language)

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=stt_plugin,
        llm=recall_llm,
        tts=tts_plugin,
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=(
                "You are RecallAI, an intelligent voice assistant for meeting intelligence. "
                "Answer concisely and naturally for spoken voice — no markdown, no bullet lists, "
                "no citation brackets. Speak in clear complete sentences."
            ),
        ),
        interrupt_speech_duration=0.6,
        interrupt_min_words=2,
    )

    assistant.start(ctx.room)
    logger.info("RecallAI Voice Assistant started in room %s", ctx.room.name)

    # Greet the user with meeting context awareness
    if session_id:
        session = DEFAULT_SESSION_STORE.get_session(session_id)
        meeting_title = (session or {}).get("title", "your meeting")
        await assistant.say(
            f"Hi! I'm RecallAI. I can answer questions about {meeting_title}. What would you like to know?",
            allow_interruptions=True,
        )
    else:
        await assistant.say(
            "Hi! I'm RecallAI. I can answer questions across all your meetings. What would you like to explore?",
            allow_interruptions=True,
        )

    # Keep the session alive until the room is empty
    await asyncio.sleep(float("inf"))


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(entrypoint_fnc=entrypoint),
    )
