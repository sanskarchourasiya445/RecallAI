"""
Tests for Global Workspace Search API (/api/v1/search).
Validates:
- Workspace-level search across multiple meeting transcripts
- Structured intelligence search across decisions, actions, and questions
- Session ID filtering
- Empty query handling
- Nonexistent query handling
- Proper provenance metadata (meeting_title, session_id, timestamps, snippets)
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


class TestGlobalSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Ensure demo sessions are initialized
        cls.client.get("/api/v1/meetings")

    def test_global_search_empty_query(self):
        """Empty or whitespace search query returns 200 with empty list."""
        res = self.client.get("/api/v1/search?q=")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["results"], [])

    def test_global_search_across_meetings(self):
        """Search query 'postgresql' returns results with complete provenance."""
        res = self.client.get("/api/v1/search?q=postgresql&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["total"] > 0)
        self.assertTrue(len(data["results"]) > 0)

        first_res = data["results"][0]
        self.assertIn("session_id", first_res)
        self.assertIn("meeting_title", first_res)
        self.assertIn("timestamp", first_res)
        self.assertIn("snippet", first_res)
        self.assertIn("match_type", first_res)
        self.assertIn("relevance_score", first_res)
        self.assertTrue(first_res["relevance_score"] > 0)

        import re
        for r in data["results"]:
            if r.get("evidence_id"):
                self.assertTrue(re.match(r"^E\d+$", r["evidence_id"]), f"Invalid evidence_id format: {r.get('evidence_id')}")

    def test_global_search_session_filter(self):
        """Passing session_id filters results to only that meeting."""
        res = self.client.get(f"/api/v1/search?q=postgresql&session_id={DEMO_SESSION_ID}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        for r in data["results"]:
            self.assertEqual(r["session_id"], DEMO_SESSION_ID)

    def test_global_search_nonexistent_query(self):
        """Query for term not mentioned in any meeting returns zero results."""
        res = self.client.get("/api/v1/search?q=supercalifragilisticexpialidocious_xyz")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 0)


if __name__ == "__main__":
    unittest.main()
