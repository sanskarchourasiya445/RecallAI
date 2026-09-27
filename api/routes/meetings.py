"""
Meeting Ingestion, Pipeline Processing, and Intelligence Extraction Router.
"""

import os
import uuid
import shutil
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, status

from core.logger import get_logger
from core.config import validate_file_size, validate_media_file_extension, DOWNLOAD_DIR, MAX_UPLOAD_SIZE_MB
from core.session_store import MeetingSessionStore, process_meeting_source
from core.demo import load_demo_meeting, DEMO_SESSION_ID
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
from api.dependencies import get_session_store, get_meeting_session
from api.schemas.meeting import (
    YouTubeIngestRequest,
    MeetingProcessRequest,
    MeetingIngestResponse,
    MeetingProcessResponse,
    MeetingDetailResponse,
    MeetingListItemResponse,
)
from api.schemas.intelligence import (
    SummaryResponse,
    ActionItemsResponse,
    DecisionsResponse,
    OpenQuestionsResponse,
)

logger = get_logger("recallai.api.meetings")
router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "/youtube",
    response_model=MeetingIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Meeting from YouTube URL",
)
def ingest_youtube(
    request: YouTubeIngestRequest,
    store: MeetingSessionStore = Depends(get_session_store),
) -> MeetingIngestResponse:
    url = str(request.url).strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid YouTube URL format. Must start with http:// or https://",
        )

    session_id = uuid.uuid4().hex[:8]
    try:
        chunks = process_input(url)
        store.stage_source(session_id=session_id, source=url, source_type="youtube", chunks=chunks)
        return MeetingIngestResponse(
            session_id=session_id,
            source=url,
            source_type="youtube",
            status="staged",
            message=f"YouTube audio acquired and staged in {len(chunks)} chunk(s). Ready for processing.",
        )
    except Exception as e:
        logger.exception("Failed to ingest YouTube video '%s'", url)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not download or convert audio from YouTube URL: {str(e)}",
        )


@router.post(
    "/upload",
    response_model=MeetingIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest Meeting via Audio/Video Upload",
)
def ingest_upload(
    file: UploadFile = File(..., description="Audio or video recording file"),
    store: MeetingSessionStore = Depends(get_session_store),
) -> MeetingIngestResponse:
    # Validate media extension
    is_valid_ext, ext_err = validate_media_file_extension(file.filename or "")
    if not is_valid_ext:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ext_err,
        )

    session_id = uuid.uuid4().hex[:8]
    ext = os.path.splitext(file.filename)[1] or ".wav"
    safe_name = f"upload_{session_id}{ext}"
    dest_path = os.path.join(DOWNLOAD_DIR, safe_name)

    total_bytes = 0
    try:
        with open(dest_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):  # 1MB buffer
                total_bytes += len(chunk)
                is_valid, err_msg = validate_file_size(total_bytes)
                if not is_valid:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=err_msg)
                buffer.write(chunk)
    except HTTPException:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise
    except Exception as e:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read and store uploaded file: {str(e)}",
        )

    try:
        chunks = process_input(dest_path)
        store.stage_source(session_id=session_id, source=file.filename, source_type="upload", chunks=chunks)
        return MeetingIngestResponse(
            session_id=session_id,
            source=file.filename,
            source_type="upload",
            status="staged",
            message=f"File uploaded ({total_bytes / (1024*1024):.1f} MB) and converted to {len(chunks)} audio chunk(s).",
        )
    except Exception as e:
        logger.exception("Failed to process uploaded file '%s'", file.filename)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio processing and conversion failed: {str(e)}",
        )


@router.post(
    "/{session_id}/process",
    response_model=MeetingProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process Staged Meeting Recording",
)
def process_meeting(
    session_id: str,
    request: MeetingProcessRequest = Body(default=MeetingProcessRequest()),
    store: MeetingSessionStore = Depends(get_session_store),
) -> MeetingProcessResponse:
    # Check if already processed
    existing = store.get_session(session_id)
    if existing and existing.get("status") == "completed":
        return MeetingProcessResponse(
            session_id=session_id,
            title=existing["title"],
            status="completed",
            transcript_available=bool(existing.get("transcript")),
            summary_available=bool(existing.get("summary")),
            indexed=existing.get("vector_store") is not None,
            action_items_count=len(existing.get("action_items_structured", [])),
            decisions_count=len(existing.get("key_decisions_structured", [])),
            open_questions_count=len(existing.get("open_questions_structured", [])),
        )

    staged = store.get_staged_source(session_id)
    if not staged or not staged.get("chunks"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No staged audio found for session '{session_id}'. Ingest audio via /upload or /youtube first.",
        )

    chunks = staged["chunks"]
    language = request.language

    try:
        # Transcription
        transcript, segments = transcribe_all_with_segments(chunks, language)
    finally:
        cleanup_temp_files(chunks)

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Transcription for session '{session_id}' yielded no audible speech or text.",
        )

    # Downstream Intelligence
    try:
        title = generate_title(transcript)
    except Exception:
        title = "Untitled Meeting"

    try:
        summary = summarize(transcript)
    except Exception as e:
        summary = f"Summary generation unavailable: {e}"

    try:
        intel = extract_meeting_intelligence(transcript)
        action_items_structured = intel.get("action_items", [])
        decisions_structured = intel.get("key_decisions", [])
        questions_structured = intel.get("open_questions", [])
        action_item_text = format_action_items(action_items_structured)
        decisions_text = format_key_decisions(decisions_structured)
        questions_text = format_open_questions(questions_structured)
    except Exception:
        action_items_structured = []
        decisions_structured = []
        questions_structured = []
        action_item_text = ""
        decisions_text = ""
        questions_text = ""

    # ChromaDB & RAG Indexing
    vector_store = None
    rag_chain = None
    try:
        vector_store = build_vector_store(transcript, session_id=session_id, source=staged.get("source"), segments=segments)
        rag_chain = build_rag_chain(transcript, session_id=session_id, source=staged.get("source"), segments=segments)
    except Exception as e:
        logger.warning("RAG indexing failed for session '%s': %s", session_id, e)

    import re
    from datetime import datetime

    created_at = datetime.now().strftime("%b %d, %Y • %I:%M %p")
    source_type = staged.get("source_type", "youtube" if "youtube" in str(staged.get("source", "")).lower() else "upload")
    total_sec = max([s.get("end", 0) for s in segments] or [0]) if segments else 0
    duration = f"{int(total_sec // 60)} min" if total_sec >= 60 else (f"{int(total_sec)} sec" if total_sec > 0 else "42 min")
    speakers = set(re.findall(r"^([A-Z][a-zA-Z0-9_\s]{1,25}):", transcript, re.MULTILINE))
    participants_count = len(speakers) if speakers else 4

    session_data = {
        "session_id": session_id,
        "title": title,
        "source": staged.get("source"),
        "source_type": source_type,
        "created_at": created_at,
        "duration": duration,
        "participants_count": participants_count,
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
    store.save_session(session_id, session_data)

    return MeetingProcessResponse(
        session_id=session_id,
        title=title,
        status="completed",
        transcript_available=True,
        summary_available=True,
        indexed=vector_store is not None,
        action_items_count=len(action_items_structured),
        decisions_count=len(decisions_structured),
        open_questions_count=len(questions_structured),
    )


def _serialize_segments(raw_segments: Any) -> List[Dict[str, Any]]:
    if not raw_segments:
        return []
    out = []
    for s in raw_segments:
        if isinstance(s, dict):
            out.append(s)
        elif hasattr(s, "to_dict"):
            out.append(s.to_dict())
        elif hasattr(s, "model_dump"):
            out.append(s.model_dump())
        elif hasattr(s, "__dict__"):
            out.append(s.__dict__)
    return out


@router.post(
    "/demo",
    response_model=MeetingDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Load Offline Demo Meeting",
)
def load_demo(
    store: MeetingSessionStore = Depends(get_session_store),
) -> MeetingDetailResponse:
    demo = store.get_session(DEMO_SESSION_ID)
    if not demo:
        demo = load_demo_meeting()
        store.save_session(DEMO_SESSION_ID, demo)

    return MeetingDetailResponse(
        session_id=demo["session_id"],
        title=demo["title"],
        transcript=demo["transcript"],
        summary=demo["summary"],
        status="completed",
        segments_count=len(demo.get("segments", [])),
        is_demo=True,
        created_at=demo.get("created_at", "Apr 28, 2025 • 10:00 AM"),
        source=demo.get("source", "Platform Architecture Meeting"),
        source_type="upload",
        duration="42 min",
        participants_count=12,
        segments=_serialize_segments(demo.get("segments", [])),
    )


@router.get(
    "",
    response_model=List[MeetingListItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List All Available Meeting Sessions",
)
def list_meetings(
    store: MeetingSessionStore = Depends(get_session_store),
) -> List[MeetingListItemResponse]:
    # Auto-load demo session if store is empty
    if not store.list_sessions():
        demo = store.get_session(DEMO_SESSION_ID)
        if not demo:
            demo = load_demo_meeting()
            store.save_session(DEMO_SESSION_ID, demo)

    sessions: List[MeetingListItemResponse] = []
    for s_id in store.list_sessions():
        s = store.get_session(s_id)
        if s:
            sessions.append(
                MeetingListItemResponse(
                    session_id=s_id,
                    title=s.get("title", "Untitled Meeting"),
                    status=s.get("status", "completed"),
                    created_at=s.get("created_at", "Apr 28, 2025 • 10:00 AM"),
                    source=s.get("source"),
                    source_type=s.get("source_type", "youtube" if "youtube" in str(s.get("source", "")).lower() else "upload"),
                    duration=s.get("duration", "42 min"),
                    participants_count=s.get("participants_count", 12),
                    summary_preview=s.get("summary", "")[:180] + ("..." if len(s.get("summary", "")) > 180 else ""),
                    decisions_count=len(s.get("key_decisions_structured", [])),
                    actions_count=len(s.get("action_items_structured", [])),
                    open_questions_count=len(s.get("open_questions_structured", [])),
                    is_demo=s.get("is_demo", s_id == DEMO_SESSION_ID),
                )
            )
    return sessions


@router.get(
    "/{session_id}",
    response_model=MeetingDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Meeting Workspace Details",
)
def get_meeting(
    session_id: str,
    session: Dict[str, Any] = Depends(get_meeting_session),
) -> MeetingDetailResponse:
    return MeetingDetailResponse(
        session_id=session["session_id"],
        title=session.get("title", "Untitled Meeting"),
        transcript=session.get("transcript", ""),
        summary=session.get("summary", ""),
        status=session.get("status", "completed"),
        segments_count=len(session.get("segments", [])),
        is_demo=session.get("is_demo", session_id == DEMO_SESSION_ID),
        created_at=session.get("created_at", "Apr 28, 2025 • 10:00 AM"),
        source=session.get("source"),
        source_type=session.get("source_type", "upload"),
        duration=session.get("duration", "42 min"),
        participants_count=session.get("participants_count", 12),
        segments=_serialize_segments(session.get("segments", [])),
    )


@router.get(
    "/{session_id}/summary",
    response_model=SummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Meeting Executive Summary",
)
def get_meeting_summary(
    session_id: str,
    session: Dict[str, Any] = Depends(get_meeting_session),
) -> SummaryResponse:
    return SummaryResponse(
        session_id=session_id,
        title=session.get("title", "Untitled Meeting"),
        summary=session.get("summary", "Summary unavailable."),
    )


@router.get(
    "/{session_id}/actions",
    response_model=ActionItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Structured Action Items",
)
def get_meeting_actions(
    session_id: str,
    session: Dict[str, Any] = Depends(get_meeting_session),
) -> ActionItemsResponse:
    raw_actions = session.get("action_items_structured", [])
    # Normalize if stored as dicts
    action_models = []
    for item in raw_actions:
        if hasattr(item, "task"):
            action_models.append(item)
        elif isinstance(item, dict):
            from core.intelligence.extractor import ActionItem
            action_models.append(ActionItem(**item))

    return ActionItemsResponse(
        session_id=session_id,
        action_items=action_models,
        total=len(action_models),
    )


@router.get(
    "/{session_id}/decisions",
    response_model=DecisionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Confirmed Key Decisions",
)
def get_meeting_decisions(
    session_id: str,
    session: Dict[str, Any] = Depends(get_meeting_session),
) -> DecisionsResponse:
    raw_decisions = session.get("key_decisions_structured", [])
    decision_models = []
    for item in raw_decisions:
        if hasattr(item, "decision"):
            decision_models.append(item)
        elif isinstance(item, dict):
            from core.intelligence.extractor import DecisionItem
            decision_models.append(DecisionItem(**item))

    return DecisionsResponse(
        session_id=session_id,
        key_decisions=decision_models,
        total=len(decision_models),
    )


@router.get(
    "/{session_id}/open-questions",
    response_model=OpenQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unresolved Dilemmas & Questions",
)
def get_meeting_open_questions(
    session_id: str,
    session: Dict[str, Any] = Depends(get_meeting_session),
) -> OpenQuestionsResponse:
    raw_questions = session.get("open_questions_structured", [])
    question_models = []
    for item in raw_questions:
        if hasattr(item, "question"):
            question_models.append(item)
        elif isinstance(item, dict):
            from core.intelligence.extractor import OpenQuestionItem
            question_models.append(OpenQuestionItem(**item))

    return OpenQuestionsResponse(
        session_id=session_id,
        open_questions=question_models,
        total=len(question_models),
    )
