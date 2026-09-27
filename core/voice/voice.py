import io
import os
import re
import tempfile
from typing import Optional, Union, BinaryIO
from pydub import AudioSegment
from core.transcription.transcriber import (
    transcribe_chunk_whisper,
    _send_to_sarvam,
    get_sarvam_api_key,
    clean_transcript,
)

# Optional gTTS import with graceful fallback
try:
    from gtts import gTTS
    _GTTS_AVAILABLE = True
except ImportError:
    _GTTS_AVAILABLE = False


def prepare_text_for_speech(text: str, max_chars: int = 400) -> str:
    """
    Sanitize and prepare grounded LLM text answer for natural text-to-speech.
    - Strips citation markers such as [E1], [E2], [Evidence E1], [Chunk 0].
    - Strips markdown formatting (bold, italic, code blocks, headers, bullet points).
    - Strips XML/HTML delimiters.
    - If answer is very long, extracts first few complete sentences deterministically
      to keep speech natural and concise without altering factual meaning.
    """
    if not text or not text.strip():
        return ""

    cleaned = text.strip()

    # 1. Strip evidence and chunk citation patterns: [E1], [E2 · title · 01:23], [Evidence E1], [Chunk 3], etc.
    cleaned = re.sub(r"\[(?:Evidence\s+)?E\d+[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[(?:Chunk\s+)?#?\d+[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[\d{2}:\d{2}(?::\d{2})?\s*[-–—]\s*\d{2}:\d{2}(?::\d{2})?\]", "", cleaned)

    # 2. Strip XML/HTML tags
    cleaned = re.sub(r"<[^>]+>", "", cleaned)

    # 3. Strip markdown syntax
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)  # Bold
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)      # Italic
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)        # Inline code
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)  # Headers
    cleaned = re.sub(r"^\s*[-*•]\s+", "", cleaned, flags=re.MULTILINE)  # Bullets
    cleaned = re.sub(r"^\s*\d+\.\s+", "", cleaned, flags=re.MULTILINE)  # Numbered lists

    # 4. Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # 5. Length bounding for natural spoken answers
    if len(cleaned) > max_chars:
        # Split into sentences deterministically
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        selected_sentences = []
        current_len = 0
        for s in sentences:
            if current_len + len(s) <= max_chars or not selected_sentences:
                selected_sentences.append(s)
                current_len += len(s)
            else:
                break
        cleaned = " ".join(selected_sentences).strip()

    return cleaned


def synthesize_answer(text: str, language: str = "english") -> Optional[bytes]:
    """
    Synthesize an answer string into spoken MP3 audio bytes using gTTS.
    - Sanitizes text to remove citations and raw metadata.
    - Fails gracefully if TTS engine or network is unavailable, returning None.
    - Does not raise unhandled exceptions to callers.
    """
    if not _GTTS_AVAILABLE:
        print("[Voice] Warning: gTTS is not installed. TTS synthesis unavailable.")
        return None

    spoken_text = prepare_text_for_speech(text)
    if not spoken_text:
        return None

    lang_lower = language.lower()
    if lang_lower in ["hindi", "hi"]:
        lang_code = "hi"
    else:
        lang_code = "en"

    try:
        fp = io.BytesIO()
        tts = gTTS(text=spoken_text, lang=lang_code, slow=False)
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.getvalue()
        if audio_bytes and len(audio_bytes) > 0:
            return audio_bytes
        return None
    except Exception as exc:
        print(f"[Voice] Warning: TTS synthesis failed gracefully ({exc}). Returning None.")
        return None


def transcribe_voice_input(
    audio_source: Union[str, bytes, io.BytesIO, BinaryIO],
    language: str = "english",
) -> str:
    """
    Transcribe a short voice question from audio file path, raw bytes, or file-like buffer.
    - Standardizes audio to 16kHz mono PCM WAV via pydub.
    - Reuses existing Whisper / Sarvam transcription infrastructure.
    - Cleans the transcript via clean_transcript.
    - Strictly cleans up all temporary audio files in a finally block.
    """
    temp_in_path = None
    temp_wav_path = None

    try:
        # Step 1: Read audio into a temporary input file
        if isinstance(audio_source, str):
            if not os.path.exists(audio_source):
                raise FileNotFoundError(f"Audio file not found: {audio_source}")
            temp_in_path = audio_source
            is_external_file = True
        else:
            is_external_file = False
            # Read bytes from buffer or raw bytes
            if isinstance(audio_source, (bytes, bytearray)):
                raw_bytes = bytes(audio_source)
            elif hasattr(audio_source, "read"):
                if hasattr(audio_source, "seek"):
                    audio_source.seek(0)
                raw_bytes = audio_source.read()
            else:
                raise ValueError("Unsupported audio source type.")

            if not raw_bytes or len(raw_bytes) < 100:
                raise ValueError("Voice recording is empty or unreadable.")

            with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as f_in:
                f_in.write(raw_bytes)
                temp_in_path = f_in.name

        # Step 2: Validate and standardize audio using pydub
        try:
            seg = AudioSegment.from_file(temp_in_path)
        except Exception as exc:
            raise ValueError(f"Could not decode audio recording: {exc}")

        if len(seg) < 200:  # < 0.2 seconds
            raise ValueError("Voice recording is too short. Please speak clearly.")

        # Standardize to 16kHz mono PCM WAV
        seg = seg.set_channels(1).set_frame_rate(16000).set_sample_width(2)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f_wav:
            temp_wav_path = f_wav.name

        seg.export(temp_wav_path, format="wav")

        # Step 3: Transcribe using Whisper or Sarvam
        lang_lower = language.lower()
        if lang_lower in ["hindi", "hinglish"] and get_sarvam_api_key():
            print(f"[Voice] Transcribing short voice input with Sarvam STT ({language})...")
            raw_text = _send_to_sarvam(temp_wav_path)
        else:
            print(f"[Voice] Transcribing short voice input with Whisper ({language})...")
            raw_text = transcribe_chunk_whisper(temp_wav_path, language=language)

        cleaned_text = clean_transcript(raw_text)
        return cleaned_text

    finally:
        # Step 4: Strict cleanup of temporary files
        if temp_in_path and not (isinstance(audio_source, str) and is_external_file):
            if os.path.exists(temp_in_path):
                try:
                    os.remove(temp_in_path)
                except OSError:
                    pass

        if temp_wav_path and os.path.exists(temp_wav_path):
            try:
                os.remove(temp_wav_path)
            except OSError:
                pass


def transcribe_voice_input_safe(
    audio_source: Union[str, bytes, io.BytesIO, BinaryIO],
    language: str = "english",
) -> dict:
    """
    Safe wrapper around transcribe_voice_input that catches exceptions and returns:
    {
        "text": str,
        "error": Optional[str],
    }
    """
    try:
        text = transcribe_voice_input(audio_source, language=language)
        if not text or not text.strip():
            return {
                "text": "",
                "error": "Could not understand the recording. Please speak clearly and try again.",
            }
        return {
            "text": text.strip(),
            "error": None,
        }
    except Exception as exc:
        err_msg = str(exc)
        if "empty" in err_msg.lower() or "too short" in err_msg.lower():
            display_err = "Recording was too short or empty. Please try speaking again."
        elif "decode" in err_msg.lower() or "unreadable" in err_msg.lower():
            display_err = "Could not decode audio recording. Please verify your microphone."
        else:
            display_err = f"Voice transcription failed: {err_msg}"
        return {
            "text": "",
            "error": display_err,
        }
