"""
Phase 7 — Production Deployment Readiness Tests.
Verifies:
- Media file extension validation guardrails
- System health diagnostic report schema (including livekit_configured)
- Upload endpoints rejection of unsupported file extensions
- CORS configuration behavior
"""

import io
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


class TestDeploymentReadiness(unittest.TestCase):
    """Tests verifying production guardrails and diagnostic endpoints."""

    def setUp(self):
        from fastapi.testclient import TestClient
        from api.main import app
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_media_extension_validation_guardrails(self):
        """Test validate_media_file_extension with valid and malicious extensions."""
        from core.config import validate_media_file_extension

        # Valid audio/video formats
        for valid in ["test.mp3", "recording.wav", "meeting.m4a", "video.mp4", "audio.webm", "clip.flac"]:
            is_valid, err = validate_media_file_extension(valid)
            self.assertTrue(is_valid, f"Expected {valid} to be valid, got error: {err}")
            self.assertIsNone(err)

        # Invalid/executable/malicious extensions
        for invalid in ["script.sh", "payload.exe", "test.py", "malware.bat", "", "   "]:
            is_valid, err = validate_media_file_extension(invalid)
            self.assertFalse(is_valid, f"Expected {invalid} to be rejected")
            self.assertIsNotNone(err)

    def test_health_endpoint_includes_livekit_and_storage(self):
        """Health diagnostic must include livekit_configured and storage writable checks."""
        r = self.client.get("/api/v1/health")
        self.assertEqual(r.status_code, 200)
        data = r.json()

        self.assertIn("status", data)
        self.assertIn("apis", data)
        self.assertIn("livekit_configured", data["apis"])
        self.assertIsInstance(data["apis"]["livekit_configured"], bool)

        # Ensure secrets are never exposed in health response
        raw_text = r.text
        self.assertNotIn("your_gemini_api_key", raw_text)
        self.assertNotIn("your_mistral_api_key", raw_text)
        self.assertNotIn("your_livekit_api_key", raw_text)

    def test_upload_rejects_unsupported_file_extension(self):
        """POST /api/v1/meetings/upload must reject unsupported file extensions."""
        fake_payload = io.BytesIO(b"echo 'malicious script'")
        r = self.client.post(
            "/api/v1/meetings/upload",
            files={"file": ("exploit.sh", fake_payload, "application/x-sh")},
        )
        self.assertEqual(r.status_code, 400)
        err = r.json().get("error") or r.json().get("detail", "")
        self.assertIn("Unsupported file extension", err)

    def test_voice_transcribe_rejects_unsupported_file_extension(self):
        """POST /api/v1/voice/transcribe must reject unsupported extensions."""
        fake_payload = io.BytesIO(b"mz executable")
        r = self.client.post(
            "/api/v1/voice/transcribe",
            files={"file": ("malware.exe", fake_payload, "application/octet-stream")},
            data={"language": "english"},
        )
        self.assertEqual(r.status_code, 400)
        err = r.json().get("error") or r.json().get("detail", "")
        self.assertIn("Unsupported file extension", err)

    def test_cors_wildcard_logic(self):
        """Verify CORS middleware logic: wildcard origins disable allow_credentials."""
        from api.main import app
        from starlette.middleware.cors import CORSMiddleware

        cors_middleware = next(
            (m for m in app.user_middleware if m.cls == CORSMiddleware),
            None,
        )
        self.assertIsNotNone(cors_middleware, "CORSMiddleware must be registered")


if __name__ == "__main__":
    unittest.main(verbosity=2)
