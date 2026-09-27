"""
Tests for Workspace Intelligence API (/api/v1/workspace).
Validates:
- Cross-meeting conversational Q&A
- Multi-meeting citation attribution [E1 · Meeting Title · MM:SS]
- Workspace SSE streaming
- Persistent workspace memory retrieval (decisions, actions, dilemmas, entities)
- Refusal on unmentioned topics
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from api.main import app
from core.demo import DEMO_SESSION_ID, DEMO_SESSION_ID_2


class TestWorkspaceIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Ensure demo sessions are initialized
        cls.client.get("/api/v1/meetings")

    def test_workspace_memory_retrieval(self):
        """GET /api/v1/workspace/memory returns aggregated decisions, actions, and dilemmas."""
        res = self.client.get("/api/v1/workspace/memory")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("overview", data)
        self.assertIn("decisions", data)
        self.assertIn("action_items", data)
        self.assertIn("open_questions", data)
        self.assertIn("entities", data)

        self.assertTrue(len(data["decisions"]) >= 4)
        self.assertTrue(len(data["action_items"]) >= 3)
        self.assertTrue(len(data["open_questions"]) >= 2)

        import re
        html_tag_pattern = re.compile(r"<[^>]+>")
        for dec in data["decisions"]:
            self.assertFalse(html_tag_pattern.search(dec.get("decision", "")))
            if dec.get("evidence"):
                self.assertFalse(html_tag_pattern.search(dec["evidence"]))
        for act in data["action_items"]:
            self.assertFalse(html_tag_pattern.search(act.get("task", "")))
        for q in data["open_questions"]:
            self.assertFalse(html_tag_pattern.search(q.get("question", "")))

    def test_workspace_chat_cross_meeting(self):
        """POST /api/v1/workspace/chat synthesizes evidence across meetings with citations."""
        res = self.client.post(
            "/api/v1/workspace/chat",
            json={
                "message": "What decisions were made about PostgreSQL and database architecture across all meetings?",
                "top_k": 6,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("answer", data)
        self.assertFalse(data.get("refused", True))
        self.assertTrue(len(data.get("citations", [])) > 0)

        # Verify citation format and provenance
        first_cit = data["citations"][0]
        self.assertIn("evidence_id", first_cit)
        self.assertIn("session_id", first_cit)
        self.assertIn("meeting_title", first_cit)
        self.assertIn("time_range", first_cit)
        self.assertIn("citation_label", first_cit)
        self.assertTrue(first_cit["citation_label"].startswith("[E1 · "))

    def test_workspace_chat_streaming(self):
        """POST /api/v1/workspace/chat/stream streams SSE events across meetings."""
        res = self.client.post(
            "/api/v1/workspace/chat/stream",
            json={
                "message": "What decisions were made about databases?",
                "top_k": 4,
            },
        )
        self.assertEqual(res.status_code, 200)
        text = res.text
        self.assertIn("event: metadata", text)
        self.assertIn("event: token", text)
        self.assertIn("event: done", text)

    def test_workspace_chat_unmentioned_refusal(self):
        """Queries about unmentioned topics return safe refusal."""
        res = self.client.post(
            "/api/v1/workspace/chat",
            json={
                "message": "What is our corporate real estate lease termination policy?",
                "top_k": 4,
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue("could not find" in data["answer"].lower() or data.get("refused", False))
        self.assertTrue(data.get("refused", False))


if __name__ == "__main__":
    unittest.main()
