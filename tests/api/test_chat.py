"""
Test Chat & RAG API Endpoints via LangGraph Assistant Workflow.
Validates:
- Grounded query answering with citations and evidence
- Ungrounded question refusal
- Follow-up query pronoun resolution via session conversation memory
- 404 on invalid session ID
- 422 on validation errors
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from api.main import app
from api.dependencies import DEFAULT_MEMORY_MANAGER
from core.demo import DEMO_SESSION_ID


class TestChatEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Ensure demo meeting is initialized and memory is fresh for isolation
        self.client.post("/api/v1/meetings/demo")
        DEFAULT_MEMORY_MANAGER.reset_session(DEMO_SESSION_ID)

    def test_chat_grounded_answer(self):
        """Verify POST /api/v1/chat returns grounded response with citations."""
        response = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "Which database was selected for the migration?",
                "top_k": 4,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertIn("answer", data)
        self.assertFalse(data.get("refused", True))
        self.assertTrue(len(data.get("citations", [])) > 0)
        self.assertEqual(data["citations"][0]["evidence_id"], "E1")

    def test_chat_ungrounded_refusal(self):
        """Verify unmentioned facts return a refusal response."""
        response = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "What is the marketing advertising budget for Q4?",
                "top_k": 4,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        ans = data.get("answer", "").lower()
        self.assertTrue(
            "could not find this information" in ans or data.get("refused", False),
            f"Expected refusal for ungrounded topic, got: {data.get('answer')}",
        )

    def test_chat_conversational_pronoun_followup(self):
        """Verify multi-turn follow-up rewrites pronouns using memory."""
        # Turn 1
        res1 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "What database did the team choose?",
            },
        )
        self.assertEqual(res1.status_code, 200)

        # Turn 2: Follow-up using pronoun 'it'
        res2 = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "Who is responsible for it?",
            },
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        resolved = data2.get("resolved_query", "").lower()
        self.assertNotEqual(resolved, "who is responsible for it?")
        self.assertIn("responsible for the", resolved)

    def test_chat_session_not_found(self):
        """Verify 404 is returned when querying unknown session."""
        response = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": "nonexistent_session_0000",
                "message": "What happened?",
            },
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("not found", data.get("error", "").lower())

    def test_chat_validation_error(self):
        """Verify 422 is returned when query message is empty."""
        response = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "",
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_chat_history_retrieval_and_clearing(self):
        """Verify GET /api/v1/chat/history and DELETE /api/v1/chat/history."""
        # 1. Ask a question to generate a turn
        res = self.client.post(
            "/api/v1/chat",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "What database was chosen?",
            },
        )
        self.assertEqual(res.status_code, 200)

        # 2. Get history
        hist_res = self.client.get(f"/api/v1/chat/history?session_id={DEMO_SESSION_ID}")
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.json()
        self.assertEqual(hist_data.get("session_id"), DEMO_SESSION_ID)
        self.assertTrue(len(hist_data.get("turns", [])) >= 1)
        first_turn = hist_data["turns"][0]
        self.assertEqual(first_turn["user_message"], "What database was chosen?")
        self.assertIsNotNone(first_turn["timestamp"])

        # 3. Clear history
        del_res = self.client.delete(f"/api/v1/chat/history?session_id={DEMO_SESSION_ID}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json().get("cleared"))

        # 4. Verify history is empty
        hist_res2 = self.client.get(f"/api/v1/chat/history?session_id={DEMO_SESSION_ID}")
        self.assertEqual(hist_res2.status_code, 200)
        self.assertEqual(len(hist_res2.json().get("turns", [])), 0)

    def test_chat_streaming(self):
        """Verify POST /api/v1/chat/stream streams SSE events (metadata, tokens, done)."""
        response = self.client.post(
            "/api/v1/chat/stream",
            json={
                "session_id": DEMO_SESSION_ID,
                "message": "Which database was selected?",
            },
        )
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertIn("event: metadata", content)
        self.assertIn("event: token", content)
        self.assertIn("event: done", content)


if __name__ == "__main__":
    unittest.main()

