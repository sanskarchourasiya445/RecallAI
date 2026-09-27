"""
Global Search Router for RecallAI API.
Provides workspace-level search across meeting transcripts, decisions, action items, and open dilemmas.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from core.logger import get_logger
from core.session_store import MeetingSessionStore
from api.dependencies import get_session_store
from core.retrieval.workspace_rag import search_workspace
from api.schemas.search import GlobalSearchResponse, SearchResultItem

logger = get_logger("gistly.api.search")
router = APIRouter(prefix="/search", tags=["Global Search"])


@router.get(
    "",
    response_model=GlobalSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Global Workspace Search",
    description="Searches across meeting transcripts, decisions, action items, and open questions across the entire workspace.",
)
def search_global(
    q: Optional[str] = Query(None, description="Search query string or keywords"),
    limit: int = Query(15, ge=1, le=50, description="Maximum number of search results to return"),
    session_id: Optional[str] = Query(None, description="Optional meeting session ID filter"),
    store: MeetingSessionStore = Depends(get_session_store),
) -> GlobalSearchResponse:
    if not q or not q.strip():
        return GlobalSearchResponse(query="", total=0, results=[])

    raw_results = search_workspace(
        query=q,
        store=store,
        limit=limit,
        session_filter=session_id,
    )

    items = [
        SearchResultItem(
            session_id=r["session_id"],
            meeting_title=r["meeting_title"],
            source_type=r["source_type"],
            timestamp=r["timestamp"],
            start_seconds=r["start_seconds"],
            end_seconds=r["end_seconds"],
            snippet=r["snippet"],
            match_type=r["match_type"],
            relevance_score=r["relevance_score"],
            evidence_id=r.get("evidence_id"),
            chunk_index=r.get("chunk_index"),
        )
        for r in raw_results
    ]

    return GlobalSearchResponse(
        query=q.strip(),
        total=len(items),
        results=items,
    )
