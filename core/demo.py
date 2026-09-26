"""
Demo Meeting Module for Jitsly / Gistly.
Provides instant, zero-API-key offline demonstration capabilities.
Allows evaluators, recruiters, and developers to explore the full
Meeting Intelligence Workspace, action item registers, decisions,
open dilemmas, and RAG Q&A without external credentials or costs.
"""

from typing import Dict, Any, List, Optional
from core.retrieval import parse_transcript_segments, RetrievedEvidence
from core.retrieval import build_vector_store, load_vector_store
from core.intelligence import ActionItem, DecisionItem, OpenQuestionItem

DEMO_SESSION_ID = "demo_backend_migration"
DEMO_TITLE = "Backend Platform Migration & Cloud Infrastructure Sync"
DEMO_SOURCE = "fixture_demo_backend_migration.wav"

DEMO_TRANSCRIPT = """00:00:00 - 00:00:25
Alex: Good morning team. Today we are reviewing our backend infrastructure migration, finalizing database architecture, and reviewing container orchestration. Let's make sure we come out with clear ownership.

00:00:25 - 00:00:55
Alex: By the way, Sarah, did you get a chance to go skiing in Tahoe over the weekend?
Sarah: Yes, the snow was fantastic! But let's dive into the architecture before we get distracted.

00:00:55 - 00:01:40
Sarah: Let's start with our primary database. After extensive benchmarking comparing MySQL 8 and PostgreSQL 16 under high concurrency, our team decided to migrate our primary transactional database from MySQL to PostgreSQL. The write performance and JSON indexing in Postgres outperformed MySQL by nearly 40%.

00:01:40 - 00:02:15
Michael: That's confirmed then. For connection management, we also agreed to deploy PgBouncer as a sidecar proxy configured with a pool size of 50 connections per replica to prevent connection starvation during peak traffic.

00:02:15 - 00:02:45
David: Should we consider using Redis for session caching instead of our current Memcached cluster?
Sarah: I think Redis might have advantages for pub/sub, but right now Memcached is completely stable and our memory footprint is low. Let's table Redis for Q4 and keep Memcached as-is for now.

00:02:45 - 00:03:25
Michael: Someone proposed hiring an external contractor firm to handle the entire database cutover over a weekend. We evaluated their proposal, but we decided against it because our in-house team needs deep familiarity with the failover playbooks.

00:03:25 - 00:04:00
Alex: Understood. Let's assign tasks. Rahul, can you take ownership of the database migration?
Rahul: Yes, I will prepare and distribute the complete PostgreSQL migration plan by Friday at 5 PM.

00:04:00 - 00:04:35
Sarah: On the Kubernetes side, we decided to upgrade our production clusters to Kubernetes version 1.30. I will upgrade the staging cluster to v1.30 by next Tuesday to validate our ingress controllers.

00:04:35 - 00:05:10
David: We also noticed the CI/CD pipeline was failing intermittently on pull requests this morning. Why was that happening?
Michael: That was due to a full Docker layer cache volume on the runner. I cleared the orphaned builder cache and increased the runner disk quota 30 minutes ago, so the CI builds are completely green now.

00:05:10 - 00:05:45
Alex: Glad that's resolved. Now, what about our primary AWS deployment region? We evaluated eu-west-1 and us-east-1, but our compliance team hasn't finalized the EU data residency requirements yet. So no final AWS region was selected during this meeting.

00:05:45 - 00:06:20
Rahul: That brings up another open dilemma: who will own long-term database operations and on-call rotations after the cutover? The platform team or the application engineering team? We need to resolve this ownership question with leadership before cutover.

00:06:20 - 00:06:50
Sarah: One last item: someone needs to update the database indexing scripts for the new schema changes, but we don't have an owner assigned for that yet. Let's find an owner in tomorrow's standup.
Alex: Agreed. Thanks everyone, meeting adjourned."""

DEMO_SUMMARY = (
    "The engineering architecture sync focused on the backend platform and database migration strategy. "
    "The team confirmed migrating the primary transactional database from MySQL 8 to PostgreSQL 16 following "
    "40% throughput improvements in concurrency benchmarks. PgBouncer was selected as a sidecar proxy with a "
    "50-connection pool limit per replica. A proposal to hire external cutover contractors was evaluated and rejected "
    "in favor of in-house operational ownership, while Redis session caching was tabled for Q4 in favor of Memcached. "
    "Production clusters will upgrade to Kubernetes v1.30. Key action items were assigned to Rahul (migration plan) "
    "and Sarah (staging cluster upgrade), while schema indexing scripts remain unassigned. Open dilemmas include "
    "compliance finalization for AWS region selection and post-cutover operational on-call ownership."
)

DEMO_ACTION_ITEMS: List[Dict[str, Any]] = [
    {
        "task": "Prepare and distribute complete PostgreSQL migration plan",
        "owner": "Rahul",
        "deadline": "Friday at 5 PM",
        "priority": "High",
        "status": "Open",
        "evidence": "Rahul: Yes, I will prepare and distribute the complete PostgreSQL migration plan by Friday at 5 PM.",
        "start_time": "00:03:25",
        "end_time": "00:04:00",
    },
    {
        "task": "Upgrade staging cluster to Kubernetes version 1.30 to validate ingress controllers",
        "owner": "Sarah",
        "deadline": "Next Tuesday",
        "priority": "Medium",
        "status": "Open",
        "evidence": "Sarah: I will upgrade the staging cluster to v1.30 by next Tuesday to validate our ingress controllers.",
        "start_time": "00:04:00",
        "end_time": "00:04:35",
    },
    {
        "task": "Update database indexing scripts for new schema changes",
        "owner": None,
        "deadline": None,
        "priority": "Medium",
        "status": "Open",
        "evidence": "Sarah: One last item: someone needs to update the database indexing scripts for the new schema changes, but we don't have an owner assigned for that yet.",
        "start_time": "00:06:20",
        "end_time": "00:06:50",
    }
]

DEMO_KEY_DECISIONS: List[Dict[str, Any]] = [
    {
        "decision": "Migrate primary transactional database from MySQL to PostgreSQL 16",
        "rationale": "Write performance and JSON indexing outperformed MySQL by nearly 40% under high concurrency benchmarking.",
        "status": "Confirmed",
        "evidence": "Sarah: Let's start with our primary database. After extensive benchmarking comparing MySQL 8 and PostgreSQL 16 under high concurrency, our team decided to migrate our primary transactional database from MySQL to PostgreSQL.",
        "start_time": "00:00:55",
        "end_time": "00:01:40",
    },
    {
        "decision": "Deploy PgBouncer as a sidecar proxy with 50 connections per replica",
        "rationale": "Prevents connection starvation during peak query traffic.",
        "status": "Confirmed",
        "evidence": "Michael: For connection management, we also agreed to deploy PgBouncer as a sidecar proxy configured with a pool size of 50 connections per replica.",
        "start_time": "00:01:40",
        "end_time": "00:02:15",
    },
    {
        "decision": "Reject external contractor firm for weekend database cutover",
        "rationale": "In-house engineering team needs deep operational familiarity with failover playbooks.",
        "status": "Confirmed",
        "evidence": "Michael: Someone proposed hiring an external contractor firm... we decided against it because our in-house team needs deep familiarity with the failover playbooks.",
        "start_time": "00:02:45",
        "end_time": "00:03:25",
    },
    {
        "decision": "Upgrade production clusters to Kubernetes version 1.30",
        "rationale": "Standardization on latest validated Kubernetes release.",
        "status": "Confirmed",
        "evidence": "Sarah: On the Kubernetes side, we decided to upgrade our production clusters to Kubernetes version 1.30.",
        "start_time": "00:04:00",
        "end_time": "00:04:35",
    }
]

DEMO_OPEN_QUESTIONS: List[Dict[str, Any]] = [
    {
        "question": "Which primary AWS deployment region (eu-west-1 vs us-east-1) will be selected for EU data residency compliance?",
        "context": "Compliance team has not finalized EU data residency requirements.",
        "status": "Unresolved",
        "evidence": "Alex: We evaluated eu-west-1 and us-east-1, but our compliance team hasn't finalized the EU data residency requirements yet. So no final AWS region was selected during this meeting.",
        "start_time": "00:05:10",
        "end_time": "00:05:45",
    },
    {
        "question": "Who will own long-term database operations and on-call rotations after the cutover (platform team or application engineering team)?",
        "context": "Needs executive alignment before the scheduled cutover weekend.",
        "status": "Unresolved",
        "evidence": "Rahul: That brings up another open dilemma: who will own long-term database operations and on-call rotations after the cutover? The platform team or the application engineering team?",
        "start_time": "00:05:45",
        "end_time": "00:06:20",
    }
]


def load_demo_meeting() -> Dict[str, Any]:
    """
    Load the pre-analyzed demo meeting into a complete state dictionary.
    Builds or retrieves the local Chroma vector store collection.
    """
    segments = parse_transcript_segments(DEMO_TRANSCRIPT)

    # Convert dictionaries to Pydantic models for structured compatibility
    action_items_models = [ActionItem(**item) for item in DEMO_ACTION_ITEMS]
    decisions_models = [DecisionItem(**item) for item in DEMO_KEY_DECISIONS]
    questions_models = [OpenQuestionItem(**item) for item in DEMO_OPEN_QUESTIONS]

    # Build or load vector store locally on CPU
    collection_name = f"meeting_{DEMO_SESSION_ID}"
    try:
        vector_store = load_vector_store(collection_name)
        # Verify collection has documents
        if vector_store._collection.count() == 0:
            vector_store = build_vector_store(
                transcript=DEMO_TRANSCRIPT,
                session_id=DEMO_SESSION_ID,
                source=DEMO_SOURCE,
                segments=segments,
            )
    except Exception:
        vector_store = build_vector_store(
            transcript=DEMO_TRANSCRIPT,
            session_id=DEMO_SESSION_ID,
            source=DEMO_SOURCE,
            segments=segments,
        )

    # Format human-readable text representations
    from core.intelligence import format_action_items, format_key_decisions, format_open_questions
    action_items_str = format_action_items(action_items_models)
    decisions_str = format_key_decisions(decisions_models)
    questions_str = format_open_questions(questions_models)

    return {
        "session_id": DEMO_SESSION_ID,
        "title": DEMO_TITLE,
        "transcript": DEMO_TRANSCRIPT,
        "segments": segments,
        "summary": DEMO_SUMMARY,
        "action_items": action_items_str,
        "key_decisions": decisions_str,
        "open_questions": questions_str,
        "action_items_structured": action_items_models,
        "key_decisions_structured": decisions_models,
        "open_questions_structured": questions_models,
        "vector_store": vector_store,
        "rag_chain": None,  # Will use live chain if key set, else grounded fallback
        "is_demo": True,
    }
