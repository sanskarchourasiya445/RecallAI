"""
LiveKit Token & Room Management API — Phase 6
Provides:
  POST /api/v1/voice/livekit/token   — issue a LiveKit access token for voice session
  POST /api/v1/voice/livekit/room    — create/ensure a voice room exists
  GET  /api/v1/voice/livekit/rooms   — list active voice rooms
  DELETE /api/v1/voice/livekit/room/{room_name} — close a voice room

Environment variables required (see .env.example):
  LIVEKIT_URL        — wss://your-project.livekit.cloud
  LIVEKIT_API_KEY    — your LiveKit API key
  LIVEKIT_API_SECRET — your LiveKit API secret
"""

import json
import os
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.logger import get_logger
from core.session_store import DEFAULT_SESSION_STORE

logger = get_logger("recallai.api.livekit")
router = APIRouter(prefix="/voice/livekit", tags=["Voice — LiveKit"])


def _get_livekit_config() -> tuple[str, str, str]:
    """Read and validate LiveKit credentials from environment."""
    url = os.environ.get("LIVEKIT_URL", "")
    api_key = os.environ.get("LIVEKIT_API_KEY", "")
    api_secret = os.environ.get("LIVEKIT_API_SECRET", "")
    if not all([url, api_key, api_secret]):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "LiveKit is not configured. Set LIVEKIT_URL, LIVEKIT_API_KEY, "
                "and LIVEKIT_API_SECRET in your environment."
            ),
        )
    return url, api_key, api_secret


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class VoiceTokenRequest(BaseModel):
    """Request a LiveKit access token for a voice session."""
    participant_name: str = Field(
        default_factory=lambda: f"user-{uuid.uuid4().hex[:6]}",
        description="Display name for the participant",
    )
    session_id: Optional[str] = Field(
        None,
        description="Meeting session ID. If omitted, voice uses workspace-level context.",
    )
    language: str = Field("english", description="Preferred language: english or hindi")
    room_name: Optional[str] = Field(
        None,
        description="Specific room name. Auto-generated if omitted.",
    )


class VoiceTokenResponse(BaseModel):
    """LiveKit access token and room details for the voice session."""
    token: str
    room_name: str
    livekit_url: str
    session_id: Optional[str] = None
    participant_name: str


class VoiceRoomInfo(BaseModel):
    """Minimal info about an active LiveKit room."""
    name: str
    num_participants: int
    metadata: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/token",
    response_model=VoiceTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue LiveKit Voice Access Token",
    description=(
        "Generates a short-lived LiveKit JWT for a participant joining a voice room. "
        "Room metadata encodes session_id so the voice agent uses the correct meeting context."
    ),
)
def issue_voice_token(request: VoiceTokenRequest) -> VoiceTokenResponse:
    livekit_url, api_key, api_secret = _get_livekit_config()

    # Validate session_id if provided
    if request.session_id:
        session = DEFAULT_SESSION_STORE.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meeting session '{request.session_id}' not found.",
            )

    # Generate a stable room name per session (or unique for workspace mode)
    room_name = request.room_name or (
        f"recallai-{request.session_id}" if request.session_id
        else f"recallai-workspace-{uuid.uuid4().hex[:8]}"
    )

    # Room metadata tells the voice agent which meeting to use
    room_metadata = json.dumps({
        "session_id": request.session_id,
        "language": request.language,
    })

    try:
        from livekit.api import AccessToken, VideoGrants

        token = (
            AccessToken(api_key, api_secret)
            .with_identity(request.participant_name)
            .with_name(request.participant_name)
            .with_grants(
                VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .with_metadata(room_metadata)
            .to_jwt()
        )
    except Exception as exc:
        logger.exception("Failed to generate LiveKit token: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate voice session token: {exc}",
        )

    logger.info(
        "Voice token issued | room=%s session_id=%s participant=%s",
        room_name, request.session_id, request.participant_name,
    )

    return VoiceTokenResponse(
        token=token,
        room_name=room_name,
        livekit_url=livekit_url,
        session_id=request.session_id,
        participant_name=request.participant_name,
    )


@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    summary="LiveKit Configuration Status",
)
def livekit_status() -> dict:
    """Returns whether LiveKit is configured (without exposing secrets)."""
    url = os.environ.get("LIVEKIT_URL", "")
    api_key = os.environ.get("LIVEKIT_API_KEY", "")
    api_secret = os.environ.get("LIVEKIT_API_SECRET", "")
    configured = bool(url and api_key and api_secret)
    return {
        "configured": configured,
        "livekit_url": url if configured else None,
        "message": (
            "LiveKit is configured and ready for voice sessions."
            if configured
            else (
                "LiveKit credentials not set. Voice features require LIVEKIT_URL, "
                "LIVEKIT_API_KEY, and LIVEKIT_API_SECRET."
            )
        ),
    }
