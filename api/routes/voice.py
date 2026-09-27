"""
Voice Interaction and Speech Processing Router.
Provides voice transcription and speech synthesis reusing core STT/TTS abstractions.
"""

import os
import uuid
import base64
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from core.logger import get_logger
from core.voice.voice import transcribe_voice_input_safe, synthesize_answer
from core.config import DOWNLOAD_DIR, validate_media_file_extension

logger = get_logger("gistly.api.voice")
router = APIRouter(prefix="/voice", tags=["Voice"])


class VoiceSynthesizeRequest(BaseModel):
    """Text-to-Speech synthesis request."""
    text: str = Field(..., min_length=1, description="Answer text to synthesize")
    language: str = Field("english", description="Target audio language: english or hinglish/hindi")


class VoiceTranscribeResponse(BaseModel):
    """Voice transcription result."""
    text: str
    language: str
    status: str = "success"


class VoiceSynthesizeResponse(BaseModel):
    """Spoken answer audio encoded in base64."""
    text: str
    language: str
    audio_base64: Optional[str] = None
    status: str = "success"


@router.post(
    "/transcribe",
    response_model=VoiceTranscribeResponse,
    status_code=status.HTTP_200_OK,
    summary="Transcribe Spoken Voice Query",
)
def transcribe_voice(
    file: UploadFile = File(..., description="Audio file recording of spoken question"),
    language: str = Form("english", description="Language: english or hinglish/hindi"),
) -> VoiceTranscribeResponse:
    # Validate extension if filename provided
    if file.filename:
        is_valid_ext, ext_err = validate_media_file_extension(file.filename)
        if not is_valid_ext:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ext_err,
            )

    ext = os.path.splitext(file.filename or "")[1] or ".wav"
    temp_name = f"voice_query_{uuid.uuid4().hex[:8]}{ext}"
    temp_path = os.path.join(DOWNLOAD_DIR, temp_name)

    try:
        with open(temp_path, "wb") as f:
            f.write(file.file.read())

        recognized_text = transcribe_voice_input_safe(temp_path, language=language)
        return VoiceTranscribeResponse(
            text=recognized_text,
            language=language,
            status="success",
        )
    except Exception as e:
        logger.exception("Voice transcription failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Voice transcription failed: {str(e)}",
        )
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@router.post(
    "/synthesize",
    response_model=VoiceSynthesizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize Spoken Answer (TTS)",
)
def synthesize_voice(
    request: VoiceSynthesizeRequest,
) -> VoiceSynthesizeResponse:
    try:
        audio_bytes = synthesize_answer(request.text, language=request.language)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else None
        return VoiceSynthesizeResponse(
            text=request.text,
            language=request.language,
            audio_base64=audio_b64,
            status="success" if audio_b64 else "unavailable",
        )
    except Exception as e:
        logger.warning("TTS synthesis error: %s", e)
        return VoiceSynthesizeResponse(
            text=request.text,
            language=request.language,
            audio_base64=None,
            status="error",
        )
