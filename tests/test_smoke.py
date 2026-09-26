"""
Phase 9 Production Smoke Test Suite.
Validates:
- Import integrity of all core subsystems
- Configuration parsing, defaults, and health checks
- Resource limit guardrails (size, duration, transcript length)
- Secret masking and logger scrubbing
- Storage hygiene and temporary file garbage collection
- Demo mode fixture integrity and local vector store retrieval
- Action tools and safety confirmation gate
- MCP JSON-RPC protocol compliance
"""

import os
import sys
import time
import unittest

# Ensure project root is in sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

os.environ.setdefault("MISTRAL_API_KEY", "mock-mistral-key-for-smoke-test")


class TestProductionSmoke(unittest.TestCase):
    """Production readiness and smoke test suite for Jitsly / Gistly."""

    def test_01_core_module_imports(self):
        """Verify all core production modules import without syntax or circular dependency errors."""
        modules = [
            "core.config",
            "core.logger",
            "core.demo",
            "core.ingestion",
            "core.transcription",
            "core.transcription.transcriber",
            "core.intelligence",
            "core.intelligence.summarizer",
            "core.intelligence.extractor",
            "core.retrieval",
            "core.retrieval.vector_store",
            "core.retrieval.rag_engine",
            "core.retrieval.provenance",
            "core.memory",
            "core.memory.memory",
            "core.voice",
            "core.voice.voice",
            "core.actions",
            "core.actions.models",
            "core.actions.task_tools",
            "core.actions.calendar_tools",
            "core.actions.email_tools",
            "core.actions.confirmation",
            "core.actions.tool_registry",
            "core.actions.action_resolver",
            "core.llm_provider",
            "core.observability",
            "core.workflow",
            "mcp_server.server",
            "utils.audio_processor",
        ]
        for mod_name in modules:
            with self.subTest(module=mod_name):
                mod = __import__(mod_name, fromlist=["*"])
                self.assertIsNotNone(mod, f"Failed to import {mod_name}")

    def test_02_system_health_check(self):
        """Verify diagnostic health check returns complete report with expected schema."""
        from core.config import get_system_health

        health = get_system_health()
        self.assertIn("status", health)
        self.assertIn("runtime", health)
        self.assertIn("apis", health)
        self.assertIn("storage", health)
        self.assertIn("limits", health)

        # Runtime checks
        self.assertTrue(isinstance(health["runtime"]["python_version"], str))
        self.assertTrue(len(health["runtime"]["python_version"]) > 0)

        # Limits checks
        self.assertGreater(health["limits"]["max_upload_size_mb"], 0)
        self.assertGreater(health["limits"]["max_audio_duration_minutes"], 0)
        self.assertGreater(health["limits"]["max_transcript_chars"], 0)

    def test_03_resource_limit_guardrails(self):
        """Verify file size, audio duration, and transcript length guardrails."""
        from core.config import (
            validate_file_size,
            validate_audio_duration,
            validate_transcript_length,
            MAX_UPLOAD_SIZE_MB,
            MAX_AUDIO_DURATION_MINUTES,
            MAX_TRANSCRIPT_CHARS,
        )

        # File size validation
        ok_size, err_size = validate_file_size(10 * 1024 * 1024)  # 10 MB
        self.assertTrue(ok_size)
        self.assertIsNone(err_size)

        bad_size = (MAX_UPLOAD_SIZE_MB + 50) * 1024 * 1024
        ok_size, err_size = validate_file_size(bad_size)
        self.assertFalse(ok_size)
        self.assertIn("exceeds maximum allowed upload size", err_size)

        # Audio duration validation
        ok_dur, err_dur = validate_audio_duration(15 * 60)  # 15 mins
        self.assertTrue(ok_dur)
        self.assertIsNone(err_dur)

        bad_dur = (MAX_AUDIO_DURATION_MINUTES + 30) * 60
        ok_dur, err_dur = validate_audio_duration(bad_dur)
        self.assertFalse(ok_dur)
        self.assertIn("exceeds maximum limit", err_dur)

        # Transcript length validation
        ok_len, err_len = validate_transcript_length(5000)
        self.assertTrue(ok_len)
        self.assertIsNone(err_len)

        bad_len = MAX_TRANSCRIPT_CHARS + 50000
        ok_len, err_len = validate_transcript_length(bad_len)
        self.assertFalse(ok_len)
        self.assertIn("exceeds limit", err_len)

    def test_04_secret_masking_and_scrubbing(self):
        """Verify secrets are masked and stripped from logs."""
        from core.config import mask_secret
        from core.logger import SecretScrubbingFilter
        import logging

        # Test mask_secret
        self.assertEqual(mask_secret(None), "None")
        self.assertEqual(mask_secret(""), "None")
        self.assertEqual(mask_secret("short"), "***")
        masked = mask_secret("sk-mistral-super-secret-key-12345")
        self.assertTrue(masked.startswith("sk-m..."))
        self.assertTrue(masked.endswith("2345"))
        self.assertNotIn("super-secret", masked)

        # Test logger filter
        scrubber = SecretScrubbingFilter()
        rec = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Connected to api with key sk-abcdef1234567890 securely",
            args=(),
            exc_info=None,
        )
        scrubber.filter(rec)
        self.assertNotIn("sk-abcdef1234567890", rec.msg)
        self.assertIn("[REDACTED_KEY]", rec.msg)

    def test_05_storage_cleanup_hygiene(self):
        """Verify storage garbage collector removes expired temporary audio files."""
        from core.config import cleanup_old_temp_files, DOWNLOAD_DIR

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        dummy_file = os.path.join(DOWNLOAD_DIR, "smoke_test_old_file.tmp")
        with open(dummy_file, "w") as f:
            f.write("temporary chunk data")

        # Fake old modification time (3 hours ago)
        old_time = time.time() - (3 * 3600)
        os.utime(dummy_file, (old_time, old_time))

        deleted = cleanup_old_temp_files(max_age_hours=1.0)
        self.assertGreaterEqual(deleted, 1)
        self.assertFalse(os.path.exists(dummy_file))

    def test_06_demo_fixture_and_vector_retrieval(self):
        """Verify offline demo meeting loads correctly with full workspace and vector store."""
        from core.demo import load_demo_meeting, DEMO_TITLE

        demo_data = load_demo_meeting()
        self.assertEqual(demo_data["title"], DEMO_TITLE)
        self.assertGreater(len(demo_data["transcript"]), 100)
        self.assertGreater(len(demo_data["segments"]), 0)
        self.assertGreater(len(demo_data["summary"]), 50)

        # Verify structured intelligence items
        self.assertEqual(len(demo_data["action_items_structured"]), 3)
        self.assertEqual(len(demo_data["key_decisions_structured"]), 4)
        self.assertEqual(len(demo_data["open_questions_structured"]), 2)

        # Verify vector store retrieval
        vs = demo_data["vector_store"]
        self.assertIsNotNone(vs)
        results = vs.similarity_search("PostgreSQL database write performance", k=2)
        self.assertGreater(len(results), 0)
        top_meta = results[0].metadata
        self.assertIn("time_range", top_meta)
        self.assertEqual(top_meta["session_id"], "demo_backend_migration")

    def test_07_action_tools_and_safety_gate(self):
        """Verify action tool execution and high-risk confirmation gate."""
        from core.actions.tool_registry import DEFAULT_TOOL_REGISTRY

        sess_id = f"smoke_sess_{int(time.time())}"

        # Low-risk action: create_task
        task_res = DEFAULT_TOOL_REGISTRY.execute_tool("create_task", {
            "title": "Smoke Test Task",
            "owner": "Tester",
            "deadline": "Tomorrow",
            "source_session_id": sess_id,
        })
        self.assertTrue(task_res.success)
        self.assertIsNotNone(task_res.resource_id)

        # High-risk action: draft_email
        email_res = DEFAULT_TOOL_REGISTRY.execute_tool("draft_email", {
            "recipient": "tester@example.com",
            "subject": "Smoke Test Email",
            "body": "Smoke test body",
            "source_session_id": sess_id,
        })
        self.assertTrue(email_res.success)

        # High-risk gated action: send_email requires confirmation
        send_res = DEFAULT_TOOL_REGISTRY.execute_tool("send_email", {
            "recipient": "recipient@example.com",
            "subject": "Deploy Update",
            "body": "Deploy update body",
            "source_session_id": sess_id,
        })
        self.assertTrue(send_res.success)
        self.assertEqual(send_res.metadata.get("status"), "pending_confirmation")
        pending_id = send_res.metadata.get("action_id")
        self.assertIsNotNone(pending_id)

        # Confirm action
        conf_res = DEFAULT_TOOL_REGISTRY.confirm_action(pending_id, session_id=sess_id)
        self.assertTrue(conf_res.success)

    def test_08_mcp_json_rpc_server(self):
        """Verify MCP server JSON-RPC protocol handling."""
        from mcp_server.server import handle_json_rpc_message

        # Ping request
        ping_resp = handle_json_rpc_message({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertIsNotNone(ping_resp)
        self.assertEqual(ping_resp.get("id"), 1)
        self.assertIn("result", ping_resp)

        # List tools request
        tools_resp = handle_json_rpc_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        self.assertIsNotNone(tools_resp)
        self.assertEqual(tools_resp.get("id"), 2)
        self.assertIn("tools", tools_resp.get("result", {}))
        tool_names = [t["name"] for t in tools_resp["result"]["tools"]]
        self.assertIn("create_task", tool_names)
        self.assertIn("create_calendar_event", tool_names)
        self.assertIn("draft_email", tool_names)
        self.assertIn("send_email", tool_names)

    def test_09_langgraph_workflow_orchestration(self):
        """Verify LangGraph workflow compiles, routes intents, and triggers confirmation gate."""
        from core.workflow import create_meeting_workflow, run_assistant_workflow
        from core.actions.tool_registry import DEFAULT_TOOL_REGISTRY

        sess_id = f"smoke_wf_{int(time.time())}"
        app = create_meeting_workflow(tool_registry=DEFAULT_TOOL_REGISTRY)
        self.assertIsNotNone(app)

        # 1. Action intent routing (list_tasks)
        wf_res = run_assistant_workflow(
            query="Show tasks for this meeting",
            session_id=sess_id,
            tool_registry=DEFAULT_TOOL_REGISTRY,
        )
        self.assertEqual(wf_res["intent"], "action")
        self.assertFalse(wf_res["requires_confirmation"])

        # 2. Consequential action confirmation gate (send_email)
        email_res = run_assistant_workflow(
            query="send email to team",
            session_id=sess_id,
            tool_registry=DEFAULT_TOOL_REGISTRY,
        )
        self.assertEqual(email_res["intent"], "action")
        self.assertTrue(email_res["requires_confirmation"])
        self.assertIsNotNone(email_res["pending_action_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
