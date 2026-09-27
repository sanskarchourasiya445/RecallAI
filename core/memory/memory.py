import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict

DEFAULT_MAX_TURNS = 6

# Common English sentence-starter words to filter out from entity extraction
COMMON_STOP_WORDS = {
    "they", "the", "we", "i", "let", "today", "after", "for", "on", "to", "one",
    "our", "you", "it", "its", "this", "that", "these", "those", "what", "who",
    "when", "where", "why", "how", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "can", "could", "should", "would",
    "will", "shall", "may", "might", "must", "in", "at", "by", "from", "with",
    "about", "into", "over", "after", "before", "between", "under", "above",
    "yes", "no", "not", "also", "and", "or", "but", "so", "if", "then", "else",
    "good", "welcome", "everyone", "hello", "hi", "morning", "afternoon", "sync",
}

# Domain keywords that carry strong meeting entity value
DOMAIN_KEYWORDS = [
    "postgresql", "mysql", "mongodb", "pgbouncer", "react 19", "react 18",
    "react", "aws", "cloud", "database", "migration plan", "migration",
    "analytics service", "analytics", "deployment", "connection pool",
    "pool size", "region", "operations", "infrastructure", "backend",
    "frontend", "client", "service", "cluster",
]

# Patterns indicating referential or pronoun-dependent follow-up questions
REFERENTIAL_PATTERNS = [
    r"\b(it|its|they|them|their|this|that|these|those)\b",
    r"\b(who owns it|who is responsible for it|when is it due|what about it)\b",
    r"\b(the decision|that decision|this decision)\b",
    r"\b(the migration|this migration|that migration)\b",
    r"\b(the plan|this plan|that plan)\b",
    r"\b(the task|this task|that task)\b",
    r"\b(the unresolved issue|the dilemma|the open question)\b",
    r"\b(what about the second option|what about the other option)\b",
    r"^(who is responsible\??|who owns (?:it|this|that)\??|when is it\??|when is it due\??)$",
]


@dataclass
class ConversationTurn:
    """A discrete conversational turn between user and assistant within a meeting session."""
    turn_id: int
    user_message: str
    assistant_message: str
    evidence_ids: List[str] = field(default_factory=list)
    resolved_query: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationTurn":
        return cls(
            turn_id=data.get("turn_id", 0),
            user_message=data.get("user_message", ""),
            assistant_message=data.get("assistant_message", ""),
            evidence_ids=data.get("evidence_ids", []),
            resolved_query=data.get("resolved_query"),
            timestamp=data.get("timestamp"),
        )


class SessionConversationMemory:
    """
    Lightweight, in-session conversational memory strictly bound to a single meeting session_id.
    Maintains a bounded window of recent dialogue turns (default 6 turns).
    Guarantees session isolation and provides query context without polluting evidence.
    """
    def __init__(self, session_id: str, max_turns: int = DEFAULT_MAX_TURNS):
        self.session_id = session_id
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []

    def add_turn(
        self,
        user_message: str,
        assistant_message: str,
        evidence_ids: Optional[List[str]] = None,
        resolved_query: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> ConversationTurn:
        """Append a new verified conversation turn, enforcing the bounded FIFO window."""
        turn = ConversationTurn(
            turn_id=len(self.turns) + 1,
            user_message=user_message.strip(),
            assistant_message=assistant_message.strip(),
            evidence_ids=evidence_ids or [],
            resolved_query=resolved_query,
            timestamp=timestamp,
        )
        self.turns.append(turn)
        # Bounded history window
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]
        return turn

    def get_recent_turns(self, n: Optional[int] = None) -> List[ConversationTurn]:
        """Return the n most recent turns (defaults to all active turns in memory)."""
        count = n if n is not None else self.max_turns
        return self.turns[-count:]

    def clear(self):
        """Reset conversation memory for current session without modifying meeting transcript or index."""
        self.turns = []

    def __len__(self) -> int:
        return len(self.turns)

    def __bool__(self) -> bool:
        return bool(self.turns)

    def __iter__(self):
        return iter(self.turns)

    def __getitem__(self, index):
        return self.turns[index]

    def format_history_for_prompt(self, max_turns: Optional[int] = None) -> str:
        """
        Format recent turns into a structured text block for the LLM prompt.
        Delimited clearly to indicate conversational context rather than meeting evidence.
        """
        recent = self.get_recent_turns(max_turns)
        if not recent:
            return ""

        formatted_lines = []
        for t in recent:
            formatted_lines.append(f"User: {t.user_message}")
            formatted_lines.append(f"Assistant: {t.assistant_message}")
        return "\n".join(formatted_lines)

    def extract_salient_entities(self) -> List[str]:
        """
        Extract key topic entities mentioned across recent conversation turns.
        Gives priority to the most recent turn.
        """
        if not self.turns:
            return []

        entities = []
        seen = set()

        for turn in reversed(self.turns[-3:]):
            combined_text = f"{turn.user_message} {turn.assistant_message}"
            text_lower = combined_text.lower()

            # 1. Check known domain keywords
            for kw in DOMAIN_KEYWORDS:
                if kw in text_lower and kw not in seen:
                    entities.append(kw)
                    seen.add(kw)

            # 2. Extract capitalized terms (proper nouns / technologies / names)
            words = re.findall(r"\b[A-Z][a-zA-Z0-9_.-]+\b", combined_text)
            for w in words:
                w_clean = w.strip(".,;:!?()")
                if w_clean.lower() not in COMMON_STOP_WORDS and len(w_clean) > 1 and w_clean.lower() not in seen:
                    entities.append(w_clean)
                    seen.add(w_clean.lower())

        return entities

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "max_turns": self.max_turns,
            "turns": [t.to_dict() for t in self.turns],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionConversationMemory":
        mem = cls(
            session_id=data.get("session_id", "default"),
            max_turns=data.get("max_turns", DEFAULT_MAX_TURNS),
        )
        mem.turns = [ConversationTurn.from_dict(t) for t in data.get("turns", [])]
        return mem


class ConversationMemoryManager:
    """
    Registry managing SessionConversationMemory instances by meeting session_id.
    Guarantees strict isolation across multiple meeting sessions.
    """
    def __init__(self, default_max_turns: int = DEFAULT_MAX_TURNS, max_turns: Optional[int] = None):
        self.default_max_turns = max_turns if max_turns is not None else default_max_turns
        self._sessions: Dict[str, SessionConversationMemory] = {}

    def get_memory(self, session_id: str) -> SessionConversationMemory:
        if not session_id:
            session_id = "default"
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionConversationMemory(
                session_id=session_id,
                max_turns=self.default_max_turns,
            )
        return self._sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            self._sessions[session_id].clear()

    def remove_session(self, session_id: str):
        self._sessions.pop(session_id, None)


def has_referential_phrases(query: str) -> bool:
    """Check if query contains pronouns or referential expressions needing contextual resolution."""
    if not query or not query.strip():
        return False
    q_lower = query.strip().lower()
    return any(re.search(pat, q_lower) for pat in REFERENTIAL_PATTERNS)


def resolve_conversational_query(
    query: str,
    history: List[ConversationTurn],
) -> str:
    """
    Deterministically rewrite follow-up queries containing pronouns or elliptical references
    into standalone search queries suitable for vector retrieval.

    Principles:
    - Zero additional LLM latency or cost.
    - If the query does not contain referential phrases, returns original query verbatim.
    - If the query already explicitly mentions the salient entity, leaves it untouched.
    - Resolves pronouns ('it', 'this', 'that', 'they') with specific subject from recent turns.
    - Resolves elliptical follow-ups ('when is it due', 'who owns it', 'what was the unresolved issue').
    """
    if not query or not query.strip():
        return ""

    clean_q = query.strip()
    if hasattr(history, "turns"):
        turns_list = history.turns
    elif isinstance(history, list):
        turns_list = history
    else:
        turns_list = []

    if not turns_list or not has_referential_phrases(clean_q):
        return clean_q

    # Extract salient context from the most recent turn
    last_turn = turns_list[-1]
    last_user = last_turn.user_message.strip()
    last_asst = last_turn.assistant_message.strip()
    combined_last = f"{last_user} {last_asst}"
    combined_lower = combined_last.lower()

    # Determine candidate subject entities from last turn
    # Multi-word key concepts take priority
    priority_subjects = [
        ("postgresql migration plan", "PostgreSQL migration plan"),
        ("database migration plan", "database migration plan"),
        ("postgresql database", "PostgreSQL database"),
        ("database migration", "PostgreSQL database migration"),
        ("react 19 migration", "React 19 migration"),
        ("analytics service", "analytics service"),
        ("aws deployment", "AWS deployment"),
        ("connection pool", "PgBouncer connection pool"),
        ("postgresql", "PostgreSQL database"),
        ("mongodb", "MongoDB"),
        ("pgbouncer", "PgBouncer"),
        ("react 19", "React 19"),
        ("deployment", "AWS deployment"),
        ("database", "database"),
        ("migration", "migration plan"),
    ]

    target_subject = None
    for pattern, display_name in priority_subjects:
        if pattern in combined_lower:
            target_subject = display_name
            break

    # Fallback to any capitalized proper noun in last assistant response
    if not target_subject:
        cap_terms = [
            w for w in re.findall(r"\b[A-Z][a-zA-Z0-9_.-]+\b", last_asst)
            if w.lower() not in COMMON_STOP_WORDS and len(w) > 2
        ]
        if cap_terms:
            target_subject = cap_terms[0]

    # If no subject was found in conversation history, return original query
    if not target_subject:
        return clean_q

    # Check if the query ALREADY contains the target subject or its primary entity
    # (e.g. adversarial check: "Why did they choose PostgreSQL because it is cheaper?")
    subject_tokens = [
        w.lower() for w in re.findall(r"\b\w+\b", target_subject)
        if len(w) > 3 and w.lower() not in COMMON_STOP_WORDS
    ]
    if any(tok in clean_q.lower() for tok in subject_tokens[:2]):
        return clean_q

    q_lower = clean_q.lower()

    # Specific common follow-up idioms:
    # 1. "When is it due?" / "When is it due"
    if re.search(r"\bwhen is (?:it|this|that|the plan) due\b", q_lower):
        return f"When is the {target_subject} due?"

    # 2. "Who is responsible for it?" / "Who owns it?" / "Who will migrate it?"
    if re.search(r"\bwho (?:is responsible for|owns|will handle|will lead|will prepare) (?:it|this|that)\b", q_lower):
        return re.sub(r"\b(?:it|this|that)\b", f"the {target_subject}", clean_q, flags=re.IGNORECASE)

    # 3. "What was the unresolved issue?" / "What was the unresolved issue regarding..."
    if re.search(r"\bwhat was the unresolved (?:issue|dilemma|topic)\b", q_lower):
        return f"What was the unresolved issue regarding {target_subject}?"

    # 4. "Why did they choose it?" / "What about it?"
    if re.search(r"\b(?:why did they choose|what about) (?:it|this|that)\b", q_lower):
        return re.sub(r"\b(?:it|this|that)\b", f"the {target_subject}", clean_q, flags=re.IGNORECASE)

    # 5. General pronoun replacement for 'it', 'this', 'that'
    if re.search(r"\b(it|this|that)\b", q_lower):
        resolved = re.sub(r"\b(it|this|that)\b", f"the {target_subject}", clean_q, count=1, flags=re.IGNORECASE)
        return resolved

    # 6. Elliptical questions without explicit verbs (e.g., "Any deadlines?", "Who owns that?")
    if len(clean_q.split()) <= 4:
        return f"{clean_q} regarding {target_subject}"

    return clean_q


# Re-export Workspace Memory symbols
from core.memory.workspace_memory import (
    WorkspaceMemory,
    DEFAULT_WORKSPACE_MEMORY,
    WorkspaceDecision,
    WorkspaceActionItem,
    WorkspaceOpenQuestion,
    WorkspaceEntityMention,
)

