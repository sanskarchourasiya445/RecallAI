"""
Tests for LangGraph Stateful Workflow Orchestration in RecallAI.
Validates:
- End-to-end StateGraph compilation and invocation
- Query understanding and intent detection (questions vs actions)
- Conversational pronoun resolution via memory
- Grounded RAG retrieval and citation extraction
- Ungrounded query refusal
- Tool execution (list_tasks, create_task)
- Consequential action confirmation safety gate (send_email)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.workflow import create_meeting_workflow, run_assistant_workflow, MeetingWorkflowState
from core.retrieval.provenance import RetrievedEvidence
from core.memory import ConversationTurn
from core.actions.tool_registry import ToolRegistry
from core.actions.models import ToolResult
from core.actions.confirmation import ConfirmationManager
from core.actions.action_resolver import ActionResolver
from core.intelligence.extractor import ActionItem


class MockRAGChain:
    def __init__(self, answer_text: str = "This is a grounded answer [E1]."):
        self.answer_text = answer_text

    def invoke(self, *args, **kwargs) -> str:
        return self.answer_text


class TestLangGraphWorkflow(unittest.TestCase):
    def setUp(self):
        # Create an isolated tool registry for tests
        self.registry = ToolRegistry(confirmation_manager=ConfirmationManager())
        self.session_id = "test_sess_workflow"

    def test_workflow_compilation(self):
        """Verify the StateGraph compiles cleanly without errors."""
        app = create_meeting_workflow(tool_registry=self.registry)
        self.assertIsNotNone(app)

    def test_question_intent_and_grounded_answer(self):
        """Verify question inquiries route to retrieval and grounded answer generation."""
        mock_chain = MockRAGChain("PostgreSQL was chosen as the database [E1].")
        mock_vs = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "We decided to migrate from MySQL to PostgreSQL."
        mock_doc.metadata = {
            "session_id": self.session_id,
            "chunk_index": 0,
            "time_range": "00:01:00 - 00:02:00",
            "start_time": "00:01:00",
            "end_time": "00:02:00",
            "source": "meeting_transcript",
        }
        mock_vs.similarity_search_with_score.return_value = [(mock_doc, 0.45)]

        res = run_assistant_workflow(
            query="Which database did we select?",
            session_id=self.session_id,
            vector_store=mock_vs,
            rag_chain=mock_chain,
            tool_registry=self.registry,
        )

        self.assertEqual(res["intent"], "question")
        self.assertIn("PostgreSQL was chosen", res["answer"])
        self.assertEqual(len(res["evidence"]), 1)
        self.assertEqual(res["evidence"][0].evidence_id, "E1")
        self.assertFalse(res["requires_confirmation"])

    def test_ungrounded_query_refusal(self):
        """Verify queries with no matching evidence return refusal response."""
        mock_vs = MagicMock()
        mock_vs.similarity_search_with_score.return_value = []

        res = run_assistant_workflow(
            query="What is the marketing budget?",
            session_id=self.session_id,
            vector_store=mock_vs,
            rag_chain=None,
            tool_registry=self.registry,
        )

        self.assertEqual(res["intent"], "question")
        self.assertIn("could not find this information", res["answer"].lower())
        self.assertEqual(len(res["evidence"]), 0)

    def test_conversational_pronoun_resolution(self):
        """Verify conversation history resolves follow-up pronouns."""
        history = [
            ConversationTurn(
                turn_id="t1",
                user_message="What database did we choose?",
                assistant_message="We chose PostgreSQL [E1].",
                evidence_ids=["E1"],
                resolved_query="What database did we choose?",
            )
        ]

        mock_chain = MockRAGChain("Rahul is the owner [E1].")
        mock_vs = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_content = "Rahul will handle PostgreSQL."
        mock_doc.metadata = {
            "session_id": self.session_id,
            "chunk_index": 0,
            "time_range": "00:02:00 - 00:03:00",
            "start_time": "00:02:00",
            "end_time": "00:03:00",
            "source": "meeting_transcript",
        }
        mock_vs.similarity_search_with_score.return_value = [(mock_doc, 0.3)]

        res = run_assistant_workflow(
            query="Who is responsible for it?",
            session_id=self.session_id,
            history=history,
            vector_store=mock_vs,
            rag_chain=mock_chain,
            tool_registry=self.registry,
        )

        self.assertIn("postgresql", res["resolved_query"].lower())
        self.assertIn("Rahul is the owner", res["answer"])

    def test_action_list_tasks(self):
        """Verify 'list tasks' query invokes list_tasks action cleanly."""
        res = run_assistant_workflow(
            query="Show tasks for this meeting",
            session_id=self.session_id,
            tool_registry=self.registry,
        )

        self.assertEqual(res["intent"], "action")
        self.assertIn("No tasks have been created", res["answer"])
        self.assertFalse(res["requires_confirmation"])

    def test_action_create_task_from_action_items(self):
        """Verify action item is converted and executed via create_task tool."""
        action_items = [
            ActionItem(
                task="Deploy PgBouncer cluster",
                owner="Sarah",
                deadline="Friday 5 PM",
                evidence="Sarah: I will deploy PgBouncer by Friday 5 PM.",
                timestamp="00:05:00",
            )
        ]

        res = run_assistant_workflow(
            query="create task for PgBouncer",
            session_id=self.session_id,
            tool_registry=self.registry,
            action_items=action_items,
        )

        self.assertEqual(res["intent"], "action")
        self.assertIn("Task Created Successfully", res["answer"])
        self.assertIn("Deploy PgBouncer cluster", res["answer"])
        self.assertIn("Sarah", res["answer"])

    def test_consequential_action_confirmation_gate(self):
        """Verify 'send email' triggers confirmation gate with pending action ID."""
        res = run_assistant_workflow(
            query="send email to team",
            session_id=self.session_id,
            tool_registry=self.registry,
        )

        self.assertEqual(res["intent"], "action")
        self.assertTrue(res["requires_confirmation"])
        self.assertIsNotNone(res["pending_action_id"])
        self.assertIn("requires your explicit confirmation", res["answer"])

        # Check that action is staged in ConfirmationManager
        pending_list = self.registry.confirmation_mgr.get_pending_actions(self.session_id)
        self.assertEqual(len(pending_list), 1)
        self.assertEqual(pending_list[0].action_id, res["pending_action_id"])


if __name__ == "__main__":
    unittest.main()
