"""
Workspace Intelligence & Cross-Meeting Chat Router for RecallAI.
Provides:
- POST /api/v1/workspace/chat: Cross-meeting Q&A with meeting citations
- POST /api/v1/workspace/chat/stream: SSE progressive streaming
- GET  /api/v1/workspace/memory: Aggregated persistent memory and entity registry
"""

import json
import asyncio
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse

from core.logger import get_logger
from core.session_store import MeetingSessionStore
from api.dependencies import get_session_store
from core.retrieval.workspace_rag import run_workspace_assistant
from core.memory.workspace_memory import DEFAULT_WORKSPACE_MEMORY
from api.schemas.workspace import (
    WorkspaceChatRequest,
    WorkspaceChatResponse,
    WorkspaceCitationItem,
    WorkspaceMemoryResponse,
)

logger = get_logger("recallai.api.workspace")
router = APIRouter(prefix="/workspace", tags=["Workspace Intelligence"])


@router.post(
    "/chat",
    response_model=WorkspaceChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Cross-Meeting Conversation Intelligence",
    description="Asks questions across all meetings in the workspace, synthesizing answers with meeting-attributed citations.",
)
def chat_workspace(
    request: WorkspaceChatRequest,
    store: MeetingSessionStore = Depends(get_session_store),
) -> WorkspaceChatResponse:
    res = run_workspace_assistant(
        query=request.message,
        store=store,
        top_k=request.top_k,
    )

    citations = [
        WorkspaceCitationItem(
            evidence_id=c["evidence_id"],
            session_id=c["session_id"],
            meeting_title=c["meeting_title"],
            time_range=c["time_range"],
            start_seconds=c["start_seconds"],
            citation_label=c["citation_label"],
            snippet=c["snippet"],
            score=c.get("score"),
        )
        for c in res.get("citations", [])
    ]

    return WorkspaceChatResponse(
        answer=res.get("answer", ""),
        citations=citations,
        sources=res.get("sources", []),
        resolved_query=res.get("resolved_query", request.message),
        refused=res.get("refused", False),
    )


@router.post(
    "/chat/stream",
    summary="Streaming Cross-Meeting Intelligence via SSE",
    description="Streams workspace-level answer tokens and citations in real time via Server-Sent Events.",
)
async def chat_workspace_stream(
    request: WorkspaceChatRequest,
    store: MeetingSessionStore = Depends(get_session_store),
):
    async def event_generator():
        try:
            res = await asyncio.to_thread(
                run_workspace_assistant,
                query=request.message,
                store=store,
                top_k=request.top_k,
            )

            citations = [
                {
                    "evidence_id": c["evidence_id"],
                    "session_id": c["session_id"],
                    "meeting_title": c["meeting_title"],
                    "time_range": c["time_range"],
                    "start_seconds": c["start_seconds"],
                    "citation_label": c["citation_label"],
                    "snippet": c["snippet"],
                    "score": c.get("score"),
                }
                for c in res.get("citations", [])
            ]

            meta = {
                "citations": citations,
                "sources": res.get("sources", []),
                "resolved_query": res.get("resolved_query", request.message),
                "refused": res.get("refused", False),
            }
            yield f"event: metadata\ndata: {json.dumps(meta)}\n\n"

            raw_answer = res.get("answer", "")
            words = raw_answer.split(" ")
            for i, word in enumerate(words):
                delta = word if i == 0 else " " + word
                yield f"event: token\ndata: {json.dumps({'delta': delta})}\n\n"
                await asyncio.sleep(0.015)

            done_payload = {
                "answer": raw_answer,
                "citations": citations,
                "sources": res.get("sources", []),
                "resolved_query": res.get("resolved_query", request.message),
                "refused": res.get("refused", False),
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            logger.exception("Error during workspace chat streaming: %s", e)
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/memory",
    response_model=WorkspaceMemoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Persistent Workspace Memory",
    description="Returns aggregated intelligence across all meetings: decisions, action items, unresolved dilemmas, and key entities.",
)
def get_workspace_memory(
    store: MeetingSessionStore = Depends(get_session_store),
) -> WorkspaceMemoryResponse:
    # Ensure memory is synced with current session store
    DEFAULT_WORKSPACE_MEMORY.sync_from_session_store(store)

    overview = DEFAULT_WORKSPACE_MEMORY.get_overview()
    decisions = [d.to_dict() for d in DEFAULT_WORKSPACE_MEMORY.get_decisions()]
    actions = [a.to_dict() for a in DEFAULT_WORKSPACE_MEMORY.get_action_items()]
    questions = [q.to_dict() for q in DEFAULT_WORKSPACE_MEMORY.get_open_questions()]
    entities = [e.to_dict() for e in DEFAULT_WORKSPACE_MEMORY.get_entities()]

    return WorkspaceMemoryResponse(
        overview=overview,
        decisions=decisions,
        action_items=actions,
        open_questions=questions,
        entities=entities,
    )
