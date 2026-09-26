"""
Chat and RAG Conversation Router.
Connects directly to the compiled LangGraph assistant workflow.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status

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

    # Record turn in session memory if it was a conversational question or clarification
    if intent in ("question", "clarify"):
        ev_ids = [c.evidence_id for c in citations]
        memory.add_turn(
            user_message=request.message,
            assistant_message=raw_answer,
            evidence_ids=ev_ids,
            resolved_query=resolved_q,
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
