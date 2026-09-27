"""
Persistent Workspace Memory Layer for RecallAI.
Aggregates and tracks structured intelligence across all meetings in the workspace:
- Decisions with meeting provenance & rationale
- Action items with owners, deadlines, and status
- Open questions & dilemmas requiring resolution
- Topics & team entities with cross-meeting citation traceability
Strictly explainable and grounded in meeting evidence.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from core.logger import get_logger

logger = get_logger("gistly.workspace_memory")


@dataclass
class WorkspaceDecision:
    decision_id: str
    session_id: str
    meeting_title: str
    decision: str
    rationale: Optional[str] = None
    evidence: Optional[str] = None
    timestamp: Optional[str] = None
    status: str = "Confirmed"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkspaceActionItem:
    action_id: str
    session_id: str
    meeting_title: str
    task: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: Optional[str] = "Medium"
    status: str = "Open"
    evidence: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkspaceOpenQuestion:
    question_id: str
    session_id: str
    meeting_title: str
    question: str
    context: Optional[str] = None
    evidence: Optional[str] = None
    timestamp: Optional[str] = None
    status: str = "Unresolved"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class WorkspaceEntityMention:
    name: str
    entity_type: str  # "person" | "technology" | "topic"
    mention_count: int
    session_ids: List[str] = field(default_factory=list)
    meeting_titles: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def clean_plain_text(val: Optional[str]) -> Optional[str]:
    """Strip any raw HTML tags, escape artifacts, and excessive whitespace."""
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    s = re.sub(r"<[^>]+>", " ", s)
    s = " ".join(s.split())
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    return s or None


class WorkspaceMemory:
    """
    Persistent in-memory workspace intelligence index.
    Aggregates verifiable structured intelligence across all meetings in the workspace.
    """

    KNOWN_TECH_TOPICS = [
        "PostgreSQL", "MySQL", "PgBouncer", "Kubernetes", "Docker", "Redis",
        "Memcached", "AWS", "FastAPI", "React 19", "React", "CloudFront",
        "CI/CD", "Ingress", "Analytics", "Migration",
    ]

    KNOWN_TEAM_PEOPLE = [
        "Rahul", "Sarah", "Michael", "Alex", "Priya", "David",
    ]

    def __init__(self):
        self._decisions: List[WorkspaceDecision] = []
        self._action_items: List[WorkspaceActionItem] = []
        self._open_questions: List[WorkspaceOpenQuestion] = []
        self._entities: Dict[str, WorkspaceEntityMention] = {}
        self._last_synced_session_ids: set = set()

    def sync_from_session_store(self, store: Any):
        """
        Synchronize and index structured intelligence from all loaded meetings in store.
        Maintains idempotent, deduplicated records with exact meeting provenance.
        """
        session_ids = store.list_sessions()
        for sid in session_ids:
            session_data = store.get_session(sid)
            if not session_data or sid in self._last_synced_session_ids:
                continue

            meeting_title = clean_plain_text(session_data.get("title")) or f"Meeting {sid}"

            # 1. Index Decisions
            raw_decisions = session_data.get("key_decisions_structured", [])
            for idx, d in enumerate(raw_decisions):
                dec_text = clean_plain_text(getattr(d, "decision", None) or (d.get("decision") if isinstance(d, dict) else str(d)))
                rationale = clean_plain_text(getattr(d, "rationale", None) or (d.get("rationale") if isinstance(d, dict) else None))
                evidence = clean_plain_text(getattr(d, "evidence", None) or (d.get("evidence") if isinstance(d, dict) else None))
                ts = clean_plain_text(getattr(d, "start_time", None) or (d.get("start_time") if isinstance(d, dict) else None))
                status = clean_plain_text(getattr(d, "status", None) or (d.get("status") if isinstance(d, dict) else "Confirmed"))

                if dec_text:
                    self._decisions.append(
                        WorkspaceDecision(
                            decision_id=f"dec_{sid}_{idx+1}",
                            session_id=sid,
                            meeting_title=meeting_title,
                            decision=dec_text,
                            rationale=rationale,
                            evidence=evidence,
                            timestamp=ts,
                            status=status or "Confirmed",
                        )
                    )

            # 2. Index Action Items
            raw_actions = session_data.get("action_items_structured", [])
            for idx, a in enumerate(raw_actions):
                task = clean_plain_text(getattr(a, "task", None) or (a.get("task") if isinstance(a, dict) else str(a)))
                owner = clean_plain_text(getattr(a, "owner", None) or (a.get("owner") if isinstance(a, dict) else None))
                deadline = clean_plain_text(getattr(a, "deadline", None) or (a.get("deadline") if isinstance(a, dict) else None))
                priority = clean_plain_text(getattr(a, "priority", None) or (a.get("priority") if isinstance(a, dict) else "Medium"))
                evidence = clean_plain_text(getattr(a, "evidence", None) or (a.get("evidence") if isinstance(a, dict) else None))
                ts = clean_plain_text(getattr(a, "start_time", None) or (a.get("start_time") if isinstance(a, dict) else None))
                status = clean_plain_text(getattr(a, "status", None) or (a.get("status") if isinstance(a, dict) else "Open"))

                if task:
                    self._action_items.append(
                        WorkspaceActionItem(
                            action_id=f"act_{sid}_{idx+1}",
                            session_id=sid,
                            meeting_title=meeting_title,
                            task=task,
                            owner=owner,
                            deadline=deadline,
                            priority=priority or "Medium",
                            status=status or "Open",
                            evidence=evidence,
                            timestamp=ts,
                        )
                    )

            # 3. Index Open Questions
            raw_questions = session_data.get("open_questions_structured", [])
            for idx, q in enumerate(raw_questions):
                q_text = clean_plain_text(getattr(q, "question", None) or (q.get("question") if isinstance(q, dict) else str(q)))
                context = clean_plain_text(getattr(q, "context", None) or (q.get("context") if isinstance(q, dict) else None))
                evidence = clean_plain_text(getattr(q, "evidence", None) or (q.get("evidence") if isinstance(q, dict) else None))
                ts = clean_plain_text(getattr(q, "start_time", None) or (q.get("start_time") if isinstance(q, dict) else None))
                status = clean_plain_text(getattr(q, "status", None) or (q.get("status") if isinstance(q, dict) else "Unresolved"))

                if q_text:
                    self._open_questions.append(
                        WorkspaceOpenQuestion(
                            question_id=f"q_{sid}_{idx+1}",
                            session_id=sid,
                            meeting_title=meeting_title,
                            question=q_text,
                            context=context,
                            evidence=evidence,
                            timestamp=ts,
                            status=status or "Unresolved",
                        )
                    )

            # 4. Extract and track entity mentions from transcript & metadata
            transcript_text = session_data.get("transcript", "")
            all_text = f"{meeting_title} {transcript_text}"

            for person in self.KNOWN_TEAM_PEOPLE:
                pattern = rf"\b{re.escape(person)}\b"
                matches = len(re.findall(pattern, all_text, re.IGNORECASE))
                if matches > 0:
                    ent = self._entities.setdefault(
                        person,
                        WorkspaceEntityMention(name=person, entity_type="person", mention_count=0),
                    )
                    ent.mention_count += matches
                    if sid not in ent.session_ids:
                        ent.session_ids.append(sid)
                        ent.meeting_titles.append(meeting_title)

            for tech in self.KNOWN_TECH_TOPICS:
                pattern = rf"\b{re.escape(tech)}\b"
                matches = len(re.findall(pattern, all_text, re.IGNORECASE))
                if matches > 0:
                    ent = self._entities.setdefault(
                        tech,
                        WorkspaceEntityMention(name=tech, entity_type="technology", mention_count=0),
                    )
                    ent.mention_count += matches
                    if sid not in ent.session_ids:
                        ent.session_ids.append(sid)
                        ent.meeting_titles.append(meeting_title)

            self._last_synced_session_ids.add(sid)

    def get_overview(self) -> Dict[str, Any]:
        """Return high-level workspace intelligence summary."""
        people = [
            e.name for e in sorted(self._entities.values(), key=lambda x: x.mention_count, reverse=True)
            if e.entity_type == "person"
        ]
        topics = [
            e.name for e in sorted(self._entities.values(), key=lambda x: x.mention_count, reverse=True)
            if e.entity_type == "technology"
        ]
        return {
            "total_meetings_synced": len(self._last_synced_session_ids),
            "total_meetings": len(self._last_synced_session_ids),
            "total_decisions": len(self._decisions),
            "total_action_items": len(self._action_items),
            "total_open_questions": len(self._open_questions),
            "tracked_people": people,
            "tracked_topics": topics,
            "key_entities": [e.to_dict() for e in sorted(self._entities.values(), key=lambda x: x.mention_count, reverse=True)[:8]],
        }

    def get_decisions(self, filter_query: Optional[str] = None) -> List[WorkspaceDecision]:
        if not filter_query:
            return list(self._decisions)
        q_lower = filter_query.lower()
        return [
            d for d in self._decisions
            if q_lower in d.decision.lower() or (d.rationale and q_lower in d.rationale.lower())
        ]

    def get_action_items(
        self,
        owner: Optional[str] = None,
        filter_query: Optional[str] = None,
    ) -> List[WorkspaceActionItem]:
        results = list(self._action_items)
        if owner:
            results = [a for a in results if a.owner and a.owner.lower() == owner.lower()]
        if filter_query:
            q_lower = filter_query.lower()
            results = [a for a in results if q_lower in a.task.lower()]
        return results

    def get_open_questions(self, filter_query: Optional[str] = None) -> List[WorkspaceOpenQuestion]:
        if not filter_query:
            return list(self._open_questions)
        q_lower = filter_query.lower()
        return [
            q for q in self._open_questions
            if q_lower in q.question.lower() or (q.context and q_lower in q.context.lower())
        ]

    def get_entities(self) -> List[WorkspaceEntityMention]:
        return list(self._entities.values())

    def query_intelligence(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search structured decisions, actions, and dilemmas across all meetings.
        Returns matching items tagged with match_type and source meeting attribution.
        """
        if not query or not query.strip():
            return []

        q_terms = [t for t in re.findall(r"\w+", query.lower()) if len(t) > 2]
        if not q_terms:
            return []

        matches = []

        # 1. Search Decisions
        for d in self._decisions:
            text_to_search = f"{d.decision} {d.rationale or ''} {d.meeting_title}".lower()
            matched_terms = sum(1 for term in q_terms if term in text_to_search)
            if matched_terms > 0:
                score = matched_terms / len(q_terms)
                matches.append({
                    "match_type": "decision",
                    "session_id": d.session_id,
                    "meeting_title": d.meeting_title,
                    "title": d.decision,
                    "snippet": d.rationale or d.decision,
                    "evidence": d.evidence,
                    "timestamp": d.timestamp or "00:00:00",
                    "score": round(score, 3),
                    "raw_item": d.to_dict(),
                })

        # 2. Search Action Items
        for a in self._action_items:
            text_to_search = f"{a.task} {a.owner or ''} {a.meeting_title}".lower()
            matched_terms = sum(1 for term in q_terms if term in text_to_search)
            if matched_terms > 0:
                score = matched_terms / len(q_terms)
                matches.append({
                    "match_type": "action_item",
                    "session_id": a.session_id,
                    "meeting_title": a.meeting_title,
                    "title": a.task,
                    "snippet": f"Owner: {a.owner or 'Unassigned'} | Due: {a.deadline or 'TBD'} — {a.task}",
                    "evidence": a.evidence,
                    "timestamp": a.timestamp or "00:00:00",
                    "score": round(score, 3),
                    "raw_item": a.to_dict(),
                })

        # 3. Search Open Questions
        for q in self._open_questions:
            text_to_search = f"{q.question} {q.context or ''} {q.meeting_title}".lower()
            matched_terms = sum(1 for term in q_terms if term in text_to_search)
            if matched_terms > 0:
                score = matched_terms / len(q_terms)
                matches.append({
                    "match_type": "open_question",
                    "session_id": q.session_id,
                    "meeting_title": q.meeting_title,
                    "title": q.question,
                    "snippet": q.context or q.question,
                    "evidence": q.evidence,
                    "timestamp": q.timestamp or "00:00:00",
                    "score": round(score, 3),
                    "raw_item": q.to_dict(),
                })

        # Sort by relevance score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]


# Global singleton instance
DEFAULT_WORKSPACE_MEMORY = WorkspaceMemory()
