"""
Comprehensive End-to-End Verification Test for Phase 5:
- Workspace Intelligence
- Global Cross-Meeting Search
- Cross-Meeting RAG with Grounded Citations
- SSE Streaming Cross-Meeting Assistant
- Persistent Workspace Memory
"""

import sys
import json
import urllib.request
import urllib.parse
import pytest

BASE_URL = "http://127.0.0.1:8000"


def setup_module():
    """Skip E2E tests if the backend server is not running."""
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/v1/health")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status != 200:
                pytest.skip("Backend server not healthy", allow_module_level=True)
    except Exception:
        pytest.skip(
            f"Backend server not running at {BASE_URL} (E2E tests require running server)",
            allow_module_level=True,
        )


def test_meetings_loaded():
    print("\n[1/5] Testing Meeting Discovery across Workspace...")
    req = urllib.request.Request(f"{BASE_URL}/api/v1/meetings")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode())
        print(f" -> Found {len(data)} meetings in workspace:")
        for m in data:
            print(f"    - [{m['session_id']}] {m['title']} ({m['source_type']})")
        assert len(data) >= 2, "Expected at least 2 demo meetings loaded"
    print(" -> PASS: Meetings loaded with full provenance.")


def test_global_search():
    print("\n[2/5] Testing Global Workspace Search (/api/v1/search)...")
    q = urllib.parse.quote("PostgreSQL")
    req = urllib.request.Request(f"{BASE_URL}/api/v1/search?q={q}&limit=10")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode())
        print(f" -> Found {data['total']} results across meetings for 'PostgreSQL':")
        session_ids = set()
        for r in data["results"][:4]:
            session_ids.add(r["session_id"])
            print(f"    * [{r['evidence_id']}] {r['meeting_title']} ({r['timestamp']}): {r['snippet'][:70]}... (Relevance: {r['relevance_score']}, Type: {r['match_type']})")
        assert data["total"] > 0, "Expected search results"
        print(f" -> Results span sessions: {session_ids}")
    print(" -> PASS: Global search retrieves cross-meeting results with metadata.")


def test_workspace_chat():
    print("\n[3/5] Testing Cross-Meeting Q&A (/api/v1/workspace/chat)...")
    payload = json.dumps({
        "message": "What decisions were made about PostgreSQL and database architecture across all meetings?",
        "top_k": 6,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/workspace/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode())
        print(" -> Response Answer:")
        print(f"    {data['answer'][:250]}...")
        print(f" -> Structured Citations ({len(data.get('citations', []))}):")
        for c in data.get("citations", []):
            print(f"    - {c['citation_label']} (Session: {c['session_id']}, Time: {c['time_range']})")
        assert len(data.get("citations", [])) > 0, "Expected citations"
        assert not data.get("refused", True), "Expected not refused"
    print(" -> PASS: Cross-meeting assistant synthesizes evidence with [E# · Title · MM:SS] citations.")


def test_workspace_streaming():
    print("\n[4/5] Testing Cross-Meeting SSE Streaming (/api/v1/workspace/chat/stream)...")
    payload = json.dumps({
        "message": "What open dilemmas exist across our meetings?",
        "top_k": 4,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/workspace/chat/stream",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        stream_text = resp.read().decode("utf-8")
        assert "event: metadata" in stream_text, "Missing metadata event"
        assert "event: token" in stream_text, "Missing token event"
        assert "event: done" in stream_text, "Missing done event"
        print(f" -> Successfully received SSE stream ({len(stream_text)} bytes).")
    print(" -> PASS: Real SSE stream delivers progressive tokens and metadata.")


def test_workspace_memory():
    print("\n[5/5] Testing Persistent Workspace Memory (/api/v1/workspace/memory)...")
    req = urllib.request.Request(f"{BASE_URL}/api/v1/workspace/memory")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200, got {resp.status}"
        data = json.loads(resp.read().decode())
        overview = data["overview"]
        print(f" -> Workspace Overview: {overview}")
        print(f"    - Decisions: {len(data['decisions'])}")
        print(f"    - Action Items: {len(data['action_items'])}")
        print(f"    - Open Questions: {len(data['open_questions'])}")
        print(f"    - Tracked People: {overview['tracked_people']}")
        print(f"    - Tracked Topics: {overview['tracked_topics']}")
        assert overview["total_decisions"] >= 4, "Expected decisions"
        assert overview["total_action_items"] >= 3, "Expected action items"
        assert overview["total_open_questions"] >= 2, "Expected open questions"
    print(" -> PASS: Persistent Workspace Memory aggregates and organizes intelligence.")


if __name__ == "__main__":
    print("=" * 60)
    print("RECALLAI PHASE 5 END-TO-END VERIFICATION")
    print("=" * 60)
    try:
        test_meetings_loaded()
        test_global_search()
        test_workspace_chat()
        test_workspace_streaming()
        test_workspace_memory()
        print("\n" + "=" * 60)
        print("ALL 5 PHASE 5 VERIFICATION SUITES PASSED SUCCESSFULLY!")
        print("=" * 60)
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
