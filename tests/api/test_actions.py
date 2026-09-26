"""
Test Controlled Actions & Safety Confirmation Gate API Endpoints.
Validates:
- Tool listing
- Direct execution for low-risk actions (create_task)
- Staging and confirmation requirement for high-impact actions (send_email)
- Explicit user confirmation gate execution
- Cross-session security isolation enforcement
- Action rejection
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from api.main import app
from core.actions.tool_registry import DEFAULT_TOOL_REGISTRY


class TestActionEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.session_id = "test_api_actions_sess"
        DEFAULT_TOOL_REGISTRY.clear_session(self.session_id)

    def test_list_tools(self):
        """Verify GET /api/v1/actions/tools returns registered tool schemas."""
        response = self.client.get("/api/v1/actions/tools")
        self.assertEqual(response.status_code, 200)
        tools = response.json()
        self.assertTrue(len(tools) >= 6)
        names = [t["name"] for t in tools]
        self.assertIn("create_task", names)
        self.assertIn("create_calendar_event", names)
        self.assertIn("draft_email", names)
        self.assertIn("send_email", names)

    def test_execute_low_risk_action(self):
        """Verify create_task executes directly without requiring confirmation."""
        response = self.client.post(
            "/api/v1/actions",
            json={
                "session_id": self.session_id,
                "action": "create_task",
                "parameters": {
                    "title": "Upgrade Ingress Controller",
                    "owner": "Sarah",
                    "deadline": "Next Tuesday",
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertFalse(data.get("requires_confirmation"))
        self.assertIsNotNone(data.get("resource_id"))

    def test_consequential_action_confirmation_lifecycle(self):
        """
        Verify consequential send_email triggers confirmation gate,
        stages pending action, and executes only upon explicit approval.
        """
        # Step 1: Attempt to send email
        send_req = self.client.post(
            "/api/v1/actions",
            json={
                "session_id": self.session_id,
                "action": "send_email",
                "parameters": {
                    "recipient": "lead@company.com",
                    "subject": "Platform Cutover Plan",
                    "body": "Postgres cutover scheduled for weekend.",
                },
            },
        )
        self.assertEqual(send_req.status_code, 200)
        send_data = send_req.json()
        self.assertTrue(send_data.get("requires_confirmation"))
        action_id = send_data.get("pending_action_id")
        self.assertIsNotNone(action_id)

        # Step 2: Check pending actions endpoint
        pending_req = self.client.get(f"/api/v1/actions/pending?session_id={self.session_id}")
        self.assertEqual(pending_req.status_code, 200)
        pending_list = pending_req.json().get("pending_actions", [])
        self.assertEqual(len(pending_list), 1)
        self.assertEqual(pending_list[0]["action_id"], action_id)

        # Step 3: Cross-Session security violation attempt (Session B tries to confirm Session A action)
        evil_req = self.client.post(
            f"/api/v1/actions/{action_id}/confirm",
            json={"session_id": "other_attacker_session"},
        )
        self.assertEqual(evil_req.status_code, 400)
        self.assertIn("access denied", evil_req.json().get("error", "").lower())

        # Step 4: Legitimate user confirmation from source session
        confirm_req = self.client.post(
            f"/api/v1/actions/{action_id}/confirm",
            json={"session_id": self.session_id},
        )
        self.assertEqual(confirm_req.status_code, 200)
        confirm_data = confirm_req.json()
        self.assertTrue(confirm_data.get("success"))
        self.assertIn("sent successfully", confirm_data.get("message", "").lower())

    def test_action_rejection(self):
        """Verify user can cancel a staged action."""
        # Stage action
        send_req = self.client.post(
            "/api/v1/actions",
            json={
                "session_id": self.session_id,
                "action": "send_email",
                "parameters": {
                    "recipient": "cancel@company.com",
                    "subject": "Cancel Me",
                    "body": "Test cancel",
                },
            },
        )
        action_id = send_req.json().get("pending_action_id")

        # Reject action
        reject_req = self.client.post(
            f"/api/v1/actions/{action_id}/reject",
            json={"session_id": self.session_id, "reason": "User changed mind"},
        )
        self.assertEqual(reject_req.status_code, 200)
        msg = reject_req.json().get("message", "").lower()
        self.assertTrue(any(w in msg for w in ("cancel", "reject")))


if __name__ == "__main__":
    unittest.main()
