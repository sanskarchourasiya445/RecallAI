"""
Chat and RAG Conversation Router.
Connects directly to the compiled LangGraph assistant workflow.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from core.logger import get_logger
from core.workflow import run_assistant_workflow
from core.session_store import MeetingSessionStore
from core.actions.tool_registry import ToolRegistry
from core.memory import ConversationMemoryManager
from api.dependencies import (
    get_session_store,
    get_tool_registry,
    get_memory_manager,
    get_meeting_session,
)
from api.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationItem,
    EvidenceItem,
    ChatTurnItem,
    ChatHistoryResponse,
)

logger = get_logger("gistly.api.chat")
router = APIRouter(prefix="/chat", tags=["Chat & RAG"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Context-Aware Chat with Meeting via LangGraph",
    description="Executes a conversational inquiry or action request through the LangGraph workflow, adhering strictly to meeting transcript citations.",
)
def chat_with_meeting(
    request: ChatRequest,
    store: MeetingSessionStore = Depends(get_session_store),
    registry: ToolRegistry = Depends(get_tool_registry),
    memory_mgr: ConversationMemoryManager = Depends(get_memory_manager),
) -> ChatResponse:
    # Verify session existence
    session = store.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting session '{request.session_id}' not found. Please ingest or process the meeting first.",
        )

    # Multi-turn conversational memory isolated by session ID
    memory = memory_mgr.get_memory(request.session_id)
    history_turns = memory.get_recent_turns()

    vs = session.get("vector_store")
    rag_c = session.get("rag_chain")
    action_items = session.get("action_items_structured", [])

    # Route through LangGraph assistant workflow
    try:
        workflow_res = run_assistant_workflow(
            query=request.message,
            session_id=request.session_id,
            history=history_turns,
            vector_store=vs,
            rag_chain=rag_c,
            tool_registry=registry,
            action_items=action_items,
        )
    except Exception as e:
        logger.exception("LangGraph workflow error during chat query: '%s'", request.message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing meeting workflow: {str(e)}",
        )

    raw_answer = workflow_res.get("answer", "")
    raw_evidence = workflow_res.get("evidence", [])
    resolved_q = workflow_res.get("resolved_query", request.message)
    intent = workflow_res.get("intent", "question")

    # Detect ungrounded refusal
    is_refused = "could not find this information in the meeting transcript" in raw_answer.lower()

    # Format citations and evidence
    citations = [
        CitationItem(
            evidence_id=getattr(ev, "evidence_id", f"E{idx+1}"),
            time_range=getattr(ev, "time_range", "Not specified"),
            chunk_index=getattr(ev, "chunk_index", idx),
            source=getattr(ev, "source", "meeting_transcript"),
            score=getattr(ev, "score", None),
        )
        for idx, ev in enumerate(raw_evidence)
    ]

    evidence_items = [
        EvidenceItem(
            evidence_id=getattr(ev, "evidence_id", f"E{idx+1}"),
            text=getattr(ev, "text", ""),
            time_range=getattr(ev, "time_range", "Not specified"),
            start_seconds=getattr(ev, "start_seconds", 0.0),
            end_seconds=getattr(ev, "end_seconds", 0.0),
            chunk_index=getattr(ev, "chunk_index", idx),
        )
        for idx, ev in enumerate(raw_evidence)
    ]

    # Record turn in session memory if it was a conversational question, clarification, or action
    if intent in ("question", "clarify", "action"):
        ev_ids = [c.evidence_id for c in citations]
        memory.add_turn(
            user_message=request.message,
            assistant_message=raw_answer,
            evidence_ids=ev_ids,
            resolved_query=resolved_q,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    return ChatResponse(
        session_id=request.session_id,
        answer=raw_answer,
        citations=citations,
        evidence=evidence_items,
        resolved_query=resolved_q,
        intent=intent,
        refused=is_refused,
        requires_confirmation=workflow_res.get("requires_confirmation", False),
        pending_action_id=workflow_res.get("pending_action_id"),
    )


@router.get(
    "/history",
    response_model=ChatHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Session Chat History",
    description="Returns the multi-turn conversational history for the given session ID.",
)
def get_chat_history(
    session_id: str = Query(..., description="Target meeting session ID"),
    memory_mgr: ConversationMemoryManager = Depends(get_memory_manager),
    store: MeetingSessionStore = Depends(get_session_store),
) -> ChatHistoryResponse:
    # Verify session existence
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting session '{session_id}' not found.",
        )

    memory = memory_mgr.get_memory(session_id)
    turns = [
        ChatTurnItem(
            turn_id=t.turn_id,
            user_message=t.user_message,
            assistant_message=t.assistant_message,
            evidence_ids=t.evidence_ids,
            resolved_query=t.resolved_query,
            timestamp=t.timestamp,
        )
        for t in memory.turns
    ]
    return ChatHistoryResponse(session_id=session_id, turns=turns)


@router.delete(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Clear Session Chat History",
    description="Resets conversational memory turns for the specified session.",
)
def clear_chat_history(
    session_id: str = Query(..., description="Target meeting session ID"),
    memory_mgr: ConversationMemoryManager = Depends(get_memory_manager),
    store: MeetingSessionStore = Depends(get_session_store),
) -> Dict[str, Any]:
    session = store.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting session '{session_id}' not found.",
        )

    memory_mgr.reset_session(session_id)
    return {"session_id": session_id, "cleared": True}


@router.post(
    "/stream",
    summary="Streaming Context-Aware Chat via Server-Sent Events (SSE)",
    description="Progressively streams assistant response tokens and citations as real-time Server-Sent Events.",
)
async def chat_with_meeting_stream(
    request: ChatRequest,
    store: MeetingSessionStore = Depends(get_session_store),
    registry: ToolRegistry = Depends(get_tool_registry),
    memory_mgr: ConversationMemoryManager = Depends(get_memory_manager),
):
    session = store.get_session(request.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting session '{request.session_id}' not found. Please ingest or process the meeting first.",
        )

    memory = memory_mgr.get_memory(request.session_id)
    history_turns = memory.get_recent_turns()
    vs = session.get("vector_store")
    rag_c = session.get("rag_chain")
    action_items = session.get("action_items_structured", [])

    async def event_generator():
        try:
            workflow_res = await asyncio.to_thread(
                run_assistant_workflow,
                query=request.message,
                session_id=request.session_id,
                history=history_turns,
                vector_store=vs,
                rag_chain=rag_c,
                tool_registry=registry,
                action_items=action_items,
            )

            raw_answer = workflow_res.get("answer", "")
            raw_evidence = workflow_res.get("evidence", [])
            resolved_q = workflow_res.get("resolved_query", request.message)
            intent = workflow_res.get("intent", "question")
            is_refused = "could not find this information in the meeting transcript" in raw_answer.lower()

            citations = [
                {
                    "evidence_id": getattr(ev, "evidence_id", f"E{idx+1}"),
                    "time_range": getattr(ev, "time_range", "Not specified"),
                    "chunk_index": getattr(ev, "chunk_index", idx),
                    "source": getattr(ev, "source", "meeting_transcript"),
                    "score": getattr(ev, "score", None),
                }
                for idx, ev in enumerate(raw_evidence)
            ]

            evidence_items = [
                {
                    "evidence_id": getattr(ev, "evidence_id", f"E{idx+1}"),
                    "text": getattr(ev, "text", ""),
                    "time_range": getattr(ev, "time_range", "Not specified"),
                    "start_seconds": getattr(ev, "start_seconds", 0.0),
                    "end_seconds": getattr(ev, "end_seconds", 0.0),
                    "chunk_index": getattr(ev, "chunk_index", idx),
                }
                for idx, ev in enumerate(raw_evidence)
            ]

            # 1. Send metadata event (citations, intent, resolved query)
            meta_payload = {
                "citations": citations,
                "evidence": evidence_items,
                "resolved_query": resolved_q,
                "intent": intent,
                "refused": is_refused,
                "requires_confirmation": workflow_res.get("requires_confirmation", False),
                "pending_action_id": workflow_res.get("pending_action_id"),
            }
            yield f"event: metadata\ndata: {json.dumps(meta_payload)}\n\n"

            # 2. Progressively stream answer tokens
            words = raw_answer.split(" ")
            for i, word in enumerate(words):
                delta = word if i == 0 else " " + word
                yield f"event: token\ndata: {json.dumps({'delta': delta})}\n\n"
                await asyncio.sleep(0.015)

            # 3. Record turn in session memory
            if intent in ("question", "clarify", "action"):
                ev_ids = [c["evidence_id"] for c in citations]
                memory.add_turn(
                    user_message=request.message,
                    assistant_message=raw_answer,
                    evidence_ids=ev_ids,
                    resolved_query=resolved_q,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )

            # 4. Send done event
            done_payload = {
                "session_id": request.session_id,
                "answer": raw_answer,
                "citations": citations,
                "evidence": evidence_items,
                "resolved_query": resolved_q,
                "intent": intent,
                "refused": is_refused,
                "requires_confirmation": workflow_res.get("requires_confirmation", False),
                "pending_action_id": workflow_res.get("pending_action_id"),
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            logger.exception("Error in chat streaming: %s", e)
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

