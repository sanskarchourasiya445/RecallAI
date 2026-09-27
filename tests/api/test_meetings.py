"""
Test Meeting Management & Intelligence API Endpoints.
Validates:
- Loading offline demo meeting via POST /api/v1/meetings/demo
- Retrieval of meeting details, summaries, action items, decisions, and open dilemmas
- Ingestion error handling for invalid sources
- 404 responses for nonexistent sessions
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from api.main import app
from core.demo import DEMO_SESSION_ID


class TestMeetingEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_load_demo_meeting(self):
        """Verify POST /api/v1/meetings/demo initializes the offline demo meeting."""
        response = self.client.post("/api/v1/meetings/demo")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertIn("Backend Platform Migration", data.get("title", ""))
        self.assertTrue(len(data.get("transcript", "")) > 100)

    def test_get_meeting_details(self):
        """Verify GET /api/v1/meetings/{session_id} returns workspace metadata."""
        # Ensure demo is loaded
        self.client.post("/api/v1/meetings/demo")

        response = self.client.get(f"/api/v1/meetings/{DEMO_SESSION_ID}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertEqual(data.get("status"), "completed")
        self.assertTrue(data.get("segments_count", 0) > 0)

    def test_get_meeting_summary(self):
        """Verify GET /api/v1/meetings/{session_id}/summary returns executive summary."""
        response = self.client.get(f"/api/v1/meetings/{DEMO_SESSION_ID}/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertIn("PostgreSQL", data.get("summary", ""))

    def test_get_meeting_action_items(self):
        """Verify GET /api/v1/meetings/{session_id}/actions returns structured tasks."""
        response = self.client.get(f"/api/v1/meetings/{DEMO_SESSION_ID}/actions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertTrue(data.get("total", 0) >= 3)
        tasks = [item["task"] for item in data.get("action_items", [])]
        self.assertTrue(any("PostgreSQL" in t for t in tasks))

    def test_get_meeting_decisions(self):
        """Verify GET /api/v1/meetings/{session_id}/decisions returns confirmed decisions."""
        response = self.client.get(f"/api/v1/meetings/{DEMO_SESSION_ID}/decisions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertTrue(data.get("total", 0) >= 4)
        decisions = [item["decision"] for item in data.get("key_decisions", [])]
        self.assertTrue(any("PostgreSQL" in d for d in decisions))

    def test_get_meeting_open_questions(self):
        """Verify GET /api/v1/meetings/{session_id}/open-questions returns unresolved items."""
        response = self.client.get(f"/api/v1/meetings/{DEMO_SESSION_ID}/open-questions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("session_id"), DEMO_SESSION_ID)
        self.assertTrue(data.get("total", 0) >= 2)
        questions = [item["question"] for item in data.get("open_questions", [])]
        self.assertTrue(any("AWS" in q or "on-call" in q.lower() for q in questions))

    def test_meeting_not_found(self):
        """Verify 404 is returned for nonexistent meeting session."""
        response = self.client.get("/api/v1/meetings/non_existent_session_9999")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("not found", data.get("error", "").lower())

    def test_invalid_youtube_url(self):
        """Verify 400 is returned for invalid YouTube URL format."""
        response = self.client.post("/api/v1/meetings/youtube", json={"url": "not-a-valid-url"})
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Invalid YouTube URL", data.get("error", ""))

    def test_list_meetings(self):
        """Verify GET /api/v1/meetings returns a list of sessions including demo."""
        response = self.client.get("/api/v1/meetings")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) >= 1)
        demo_item = next((item for item in data if item["session_id"] == DEMO_SESSION_ID), None)
        self.assertIsNotNone(demo_item)
        self.assertEqual(demo_item["status"], "completed")


if __name__ == "__main__":
    unittest.main()
