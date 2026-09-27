"""
gTTS-backed TTS adapter for livekit-agents.
Used as fallback when OPENAI_API_KEY is not configured.
Streams gTTS-generated MP3 audio to LiveKit via the TTS plugin interface.
"""

from __future__ import annotations

import asyncio
import io
from typing import Optional, AsyncIterable

from livekit.agents import tts
from livekit.agents.tts import SynthesizedAudio, SynthesizeStream

from core.voice.voice import synthesize_answer, prepare_text_for_speech
from core.logger import get_logger

logger = get_logger("recallai.voice.tts_adapter")


class GTTSSynthesizeStream(SynthesizeStream):
    def __init__(self, tts_instance: "GTTSAdapter", text: str, language: str) -> None:
        super().__init__(tts_instance)
        self._text = text
        self._language = language

    async def _run(self) -> None:
        loop = asyncio.get_event_loop()
        audio_bytes = await loop.run_in_executor(
            None, synthesize_answer, self._text, self._language
        )
        if not audio_bytes:
            logger.warning("GTTSAdapter: no audio produced for text=%r", self._text[:60])
            return

        # gTTS produces MP3; wrap in SynthesizedAudio for livekit-agents
        self._event_ch.send_nowait(
            SynthesizedAudio(
                request_id="gtts",
                segment_id="gtts-0",
                audio=tts.AudioFrame.create(
                    data=audio_bytes,
                    sample_rate=24000,
                    num_channels=1,
                ),
            )
        )


class GTTSAdapter(tts.TTS):
    """
    Minimal livekit-agents TTS plugin backed by the existing gTTS synthesize_answer.
    Falls back gracefully if gTTS is unavailable.
    """

    def __init__(self, language: str = "english") -> None:
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=24000,
            num_channels=1,
        )
        self._language = language

    def synthesize(self, text: str) -> "GTTSSynthesizeStream":
        clean_text = prepare_text_for_speech(text, max_chars=500)
        return GTTSSynthesizeStream(self, clean_text or text, self._language)
