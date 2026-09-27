"""
Cross-Meeting RAG, Global Search, and Workspace Retrieval Engine for RecallAI.
Orchestrates:
1. Workspace-wide similarity search across multiple meeting Chroma collections
2. Structured intelligence query across decisions, actions, and dilemmas
3. Multi-meeting evidence ranking and provenance assembly
4. Grounded cross-meeting conversational question answering with [E1 · Meeting Title · MM:SS] citations
"""

import os
import re
from typing import List, Dict, Any, Optional
from core.logger import get_logger
from core.session_store import MeetingSessionStore, DEFAULT_SESSION_STORE
from core.retrieval.provenance import (
    RetrievedEvidence,
    format_seconds,
    format_time_range,
    parse_timestamp,
)
from core.memory.workspace_memory import DEFAULT_WORKSPACE_MEMORY, WorkspaceMemory

logger = get_logger("recallai.workspace_rag")

STOP_WORDS = {
    "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "can", "could", "should", "would", "will", "shall",
    "this", "that", "these", "those", "our", "your", "their", "its", "my",
    "we", "you", "they", "it", "he", "she", "me", "him", "her", "us", "them",
    "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "now", "tell", "show", "give", "find", "search", "discuss", "discussed",
    "decide", "decided", "decision", "decisions", "meeting", "meetings", "across",
}


def find_evidence_id_for_timestamp(session_data: Optional[Dict[str, Any]], start_sec: float) -> str:
    """Find the corresponding E# evidence id for a timestamp in the session transcript."""
    if not session_data:
        return "E1"
    raw_transcript = session_data.get("transcript", "")
    if not raw_transcript:
        return "E1"
    blocks = [b.strip() for b in raw_transcript.split("\n\n") if b.strip()]
    for idx, block in enumerate(blocks):
        lines = block.split("\n")
        if lines and ":" in lines[0] and ("-" in lines[0] or "-->" in lines[0]):
            time_part = lines[0].split("-")[0].strip()
            block_start = parse_timestamp(time_part)
            time_end_part = lines[0].split("-")[1].strip() if "-" in lines[0] else ""
            block_end = parse_timestamp(time_end_part) if time_end_part else block_start + 45.0
            if block_start <= start_sec <= block_end:
                return f"E{idx + 1}"
    approx_idx = max(1, int(start_sec // 45) + 1)
    return f"E{approx_idx}"


def search_workspace(
    query: str,
    store: Optional[MeetingSessionStore] = None,
    limit: int = 15,
    session_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Execute unified global search across all meetings in the workspace:
    - Vector semantic search across transcript chunks in each meeting's vector store
    - Structured intelligence search across decisions, action items, and open dilemmas
    - Merges, scores, and ranks results with complete meeting and timestamp provenance.
    """
    if not query or not query.strip():
        return []

    clean_q = query.strip()
    session_store = store or DEFAULT_SESSION_STORE

    # Ensure store has sessions loaded
    active_sids = session_store.list_sessions()
    if not active_sids:
        return []

    # Sync workspace memory with all loaded sessions
    DEFAULT_WORKSPACE_MEMORY.sync_from_session_store(session_store)

    target_sids = [session_filter] if session_filter and session_filter in active_sids else active_sids

    all_results: List[Dict[str, Any]] = []
    seen_snippets = set()

    # 1. Search Vector Stores for each target meeting
    for sid in target_sids:
        session_data = session_store.get_session(sid)
        if not session_data:
            continue

        vs = session_data.get("vector_store")
        meeting_title = session_data.get("title", f"Meeting {sid}")
        source_type = session_data.get("source_type", "upload")

        if vs:
            try:
                # Retrieve top 4 per meeting for global search
                hits = vs.similarity_search_with_score(clean_q, k=4)
                content_words = [w.lower() for w in re.findall(r"\w+", clean_q) if len(w) >= 3 and w.lower() not in STOP_WORDS]
                for doc, score in hits:
                    text = doc.page_content.strip()
                    if not text or text == "No transcript content available for this session.":
                        continue

                    # Mathematical noise cutoff: vector distance >= 1.65 is unrelated
                    if float(score) >= 1.65:
                        continue

                    # Exact token set matching
                    text_tokens = set(re.findall(r"\w+", text.lower()))
                    matched_content_words = [w for w in content_words if w in text_tokens]
                    has_keyword_match = bool(matched_content_words)

                    # Marginal distance check: if score >= 1.35, require token match
                    if float(score) >= 1.35 and not has_keyword_match:
                        continue

                    # Deduplication key
                    snippet_key = f"{sid}_{text[:60]}"
                    if snippet_key in seen_snippets:
                        continue
                    seen_snippets.add(snippet_key)

                    start_sec = float(doc.metadata.get("start_seconds", 0.0))
                    end_sec = float(doc.metadata.get("end_seconds", 0.0))
                    time_range = doc.metadata.get("time_range") or format_time_range(start_sec, end_sec)
                    chunk_idx = int(doc.metadata.get("chunk_index", 0))

                    # Normalize distance into relevance score (0.0 to 1.0)
                    relevance = max(0.05, min(0.99, round(1.0 / (1.0 + float(score)), 3)))
                    if has_keyword_match:
                        relevance = min(0.98, round(relevance + 0.15, 3))

                    all_results.append({
                        "session_id": sid,
                        "meeting_title": meeting_title,
                        "source_type": source_type,
                        "timestamp": time_range,
                        "start_seconds": start_sec,
                        "end_seconds": end_sec,
                        "snippet": text,
                        "match_type": "transcript",
                        "relevance_score": relevance,
                        "evidence_id": f"E{chunk_idx + 1}",
                        "chunk_index": chunk_idx,
                    })
            except Exception as e:
                logger.warning("Vector search failed on meeting '%s': %s", sid, e)

    # 2. Search Structured Intelligence (Decisions, Action Items, Dilemmas)
    structured_matches = DEFAULT_WORKSPACE_MEMORY.query_intelligence(clean_q, limit=limit)
    for sm in structured_matches:
        sid = sm["session_id"]
        if session_filter and sid != session_filter:
            continue

        snippet_text = sm.get("snippet") or sm.get("title")
        snippet_key = f"{sid}_{snippet_text[:60]}"
        if snippet_key in seen_snippets:
            continue
        seen_snippets.add(snippet_key)

        ts_str = sm.get("timestamp") or "00:00:00"
        start_sec = parse_timestamp(ts_str)
        session_data = session_store.get_session(sid)
        ev_id = find_evidence_id_for_timestamp(session_data, start_sec)

        all_results.append({
            "session_id": sid,
            "meeting_title": sm["meeting_title"],
            "source_type": "intelligence",
            "timestamp": ts_str,
            "start_seconds": start_sec,
            "end_seconds": start_sec + 30.0,
            "snippet": f"[{sm['match_type'].replace('_', ' ').title()}] {snippet_text}",
            "match_type": sm["match_type"],
            "relevance_score": round(min(0.98, sm["score"] + 0.1), 3),
            "evidence_id": ev_id,
            "chunk_index": 0,
        })

    # Sort all results by relevance score descending
    all_results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return all_results[:limit]


def retrieve_cross_meeting_evidence(
    query: str,
    store: Optional[MeetingSessionStore] = None,
    top_k: int = 6,
    session_filter: Optional[str] = None,
) -> List[RetrievedEvidence]:
    """
    Retrieve top-k evidence passages across all loaded meeting vector stores.
    Deduplicates across meetings and returns verified RetrievedEvidence objects
    enriched with meeting title and session ID.
    """
    if not query or not query.strip():
        return []

    clean_q = query.strip()
    session_store = store or DEFAULT_SESSION_STORE
    active_sids = session_store.list_sessions()
    if not active_sids:
        return []

    target_sids = [session_filter] if session_filter and session_filter in active_sids else active_sids

    candidates = []
    for sid in target_sids:
        session_data = session_store.get_session(sid)
        if not session_data:
            continue
        vs = session_data.get("vector_store")
        title = session_data.get("title", f"Meeting {sid}")
        source = session_data.get("source", "meeting_transcript")
        source_type = session_data.get("source_type", "upload")

        if vs:
            try:
                hits = vs.similarity_search_with_score(clean_q, k=max(3, top_k // len(target_sids) + 2))
                content_words = [w.lower() for w in re.findall(r"\w+", clean_q) if len(w) >= 3 and w.lower() not in STOP_WORDS]
                for doc, score in hits:
                    text = doc.page_content.strip()
                    if not text or text == "No transcript content available for this session.":
                        continue

                    # Mathematical noise cutoff: vector distance >= 1.65 is unrelated
                    if float(score) >= 1.65:
                        continue

                    text_tokens = set(re.findall(r"\w+", text.lower()))
                    matched_content_words = [w for w in content_words if w in text_tokens]
                    has_keyword_match = bool(matched_content_words)

                    # Marginal distance check: if score >= 1.35, require token match
                    if float(score) >= 1.35 and not has_keyword_match:
                        continue

                    candidates.append((doc, float(score), sid, title, source, source_type))
            except Exception as e:
                logger.warning("Retrieval failed for session '%s': %s", sid, e)

    # Sort candidates by L2 distance (ascending: lower distance is better)
    candidates.sort(key=lambda x: x[1])

    evidence_list: List[RetrievedEvidence] = []
    seen_texts = set()
    e_idx = 1

    for doc, score, sid, title, source, source_type in candidates:
        text = doc.page_content.strip()
        if text in seen_texts:
            continue
        seen_texts.add(text)

        chunk_idx = int(doc.metadata.get("chunk_index", 0))
        start_sec = float(doc.metadata.get("start_seconds", 0.0))
        end_sec = float(doc.metadata.get("end_seconds", 0.0))
        time_range = doc.metadata.get("time_range") or format_time_range(start_sec, end_sec)

        ev = RetrievedEvidence(
            evidence_id=f"E{e_idx}",
            chunk_index=chunk_idx,
            text=text,
            time_range=time_range,
            start_time=format_seconds(start_sec),
            end_time=format_seconds(end_sec),
            start_seconds=start_sec,
            end_seconds=end_sec,
            source=source,
            source_type=source_type,
            session_id=sid,
            score=score,
            meeting_title=title,
        )
        evidence_list.append(ev)
        e_idx += 1
        if len(evidence_list) >= top_k:
            break

    return evidence_list


def run_workspace_assistant(
    query: str,
    store: Optional[MeetingSessionStore] = None,
    top_k: int = 6,
) -> Dict[str, Any]:
    """
    Execute cross-meeting conversation intelligence workflow:
    1. Retrieve top multi-meeting evidence
    2. Format cross-meeting grounded context
    3. Generate grounded answer with [E1 · Meeting Title · MM:SS] citations
    """
    clean_q = query.strip()
    session_store = store or DEFAULT_SESSION_STORE
    evidence = retrieve_cross_meeting_evidence(clean_q, store=session_store, top_k=top_k)

    if not evidence:
        return {
            "answer": "I could not find relevant discussions or decisions about this across your workspace meetings.",
            "citations": [],
            "evidence": [],
            "resolved_query": clean_q,
            "sources": [],
            "refused": True,
        }

    # Format structured citations
    citations = []
    unique_sources = {}
    for idx, ev in enumerate(evidence):
        start_formatted = format_seconds(ev.start_seconds)
        # Clean leading 00: if 00:01:23 -> 01:23
        start_short = start_formatted[3:] if start_formatted.startswith("00:") else start_formatted
        c_label = f"[{ev.evidence_id} · {ev.meeting_title} · {start_short}]"

        citations.append({
            "evidence_id": ev.evidence_id,
            "session_id": ev.session_id,
            "meeting_title": ev.meeting_title or "Meeting",
            "time_range": ev.time_range,
            "start_seconds": ev.start_seconds,
            "citation_label": c_label,
            "snippet": ev.text[:120] + "...",
            "score": ev.score,
        })

        if ev.session_id not in unique_sources:
            unique_sources[ev.session_id] = {
                "session_id": ev.session_id,
                "title": ev.meeting_title,
                "source": ev.source,
            }

    # Attempt live LLM invocation if configured
    answer = None
    from core.llm_provider import is_llm_configured
    if is_llm_configured():
        try:
            from core.llm_provider import get_llm
            from langchain_core.prompts import ChatPromptTemplate
            llm = get_llm(temperature=0.1)

            context_parts = []
            for ev in evidence:
                context_parts.append(
                    f"[{ev.evidence_id}] Meeting: \"{ev.meeting_title}\" | Time: {ev.time_range}\n{ev.text}"
                )
            context_block = "\n\n".join(context_parts)

            prompt = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are the RecallAI Workspace Intelligence Assistant. Answer the user's question across multiple meetings "
                    "strictly based on the provided cross-meeting evidence below.\n"
                    "Citing Rule: For every factual statement, reference the evidence token [E1], [E2] and specify which meeting made the decision.\n"
                    "If the answer cannot be found in the context, state: 'I could not find this information in the workspace meetings.'\n\n"
                    f"Workspace Context:\n{context_block}",
                ),
                ("human", "{query}"),
            ])

            chain = prompt | llm
            res = chain.invoke({"query": clean_q})
            answer = getattr(res, "content", str(res)).strip()
        except Exception as e:
            logger.warning("Workspace LLM invocation error: %s", e)
            answer = None

    # Deterministic grounded fallback synthesis
    if not answer:
        # Group by meeting for clean synthesis
        meetings_map: Dict[str, List[RetrievedEvidence]] = {}
        for ev in evidence:
            meetings_map.setdefault(ev.meeting_title or "Meeting", []).append(ev)

        answer_sections = []
        for m_title, ev_items in meetings_map.items():
            first_ev = ev_items[0]
            start_short = format_seconds(first_ev.start_seconds)
            if start_short.startswith("00:"):
                start_short = start_short[3:]
            citation_tag = f"[{first_ev.evidence_id} · {m_title} · {start_short}]"
            cleaned_excerpt = first_ev.text.replace("\n", " ").strip()
            answer_sections.append(
                f"**In {m_title}** {citation_tag}:\n\"{cleaned_excerpt}\""
            )

        answer = (
            "Here is what was discussed and decided across your workspace meetings:\n\n"
            + "\n\n".join(answer_sections)
            + "\n\n*(Note: LLM API key not configured; showing grounded multi-meeting retrieval synthesis.)*"
        )

    refused = bool("could not find" in answer.lower())
    return {
        "answer": answer,
        "citations": citations,
        "evidence": [ev.to_dict() for ev in evidence],
        "resolved_query": clean_q,
        "sources": list(unique_sources.values()),
        "refused": refused,
    }
