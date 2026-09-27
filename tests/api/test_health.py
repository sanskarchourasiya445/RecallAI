"""
Test Health & Diagnostics API Endpoints.
Validates:
- GET /api/v1/health returns 200 with expected schema
- Zero secret exposure
- GET / returns 200 with service metadata
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from api.main import app


class TestHealthEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Verify root endpoint returns API directory information."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("service"), "recallai-api")
        self.assertEqual(data.get("api_v1_prefix"), "/api/v1")
        self.assertEqual(data.get("docs_url"), "/docs")

    def test_health_endpoint_schema_and_status(self):
        """Verify GET /api/v1/health returns 200 with health metrics."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn(data.get("status"), ("ok", "degraded"))
        self.assertEqual(data.get("service"), "recallai-api")
        self.assertEqual(data.get("version"), "1.0.0")
        self.assertIn("llm_provider", data)
        self.assertIn("embedding_provider", data)
        self.assertIn("chromadb_available", data)

    def test_no_secrets_in_health_response(self):
        """Verify API keys and secrets are never leaked in plain text."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        content_str = response.text

        # Check against active environment secrets
        for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY", "SARVAM_API_KEY"):
            val = os.getenv(var)
            if val and len(val) > 8 and not val.startswith("mock-") and val != "your_gemini_api_key_here":
                self.assertNotIn(val, content_str, f"Secret {var} leaked in health output!")


if __name__ == "__main__":
    unittest.main()
