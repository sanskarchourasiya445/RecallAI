"""
RecallAI Pipeline Adapter — Phase 6
Bridges livekit-agents LLM interface with the existing RecallAI LangGraph workflow.

This is the critical integration point:
  STT text → RecallAIPipelineAdapter → run_assistant_workflow / run_workspace_assistant → answer text

Preserves:
  - Meeting-specific RAG (when session_id is set)
  - Workspace-level cross-meeting retrieval (when session_id is None)
  - Conversation memory (per voice session, isolated)
  - MCP action detection (surfaces confirmation intent in voice response)
  - Existing grounding and citation system (citations stripped for voice)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, AsyncIterable, Optional, List, MutableSet

from livekit.agents import APIConnectOptions
from livekit.agents import llm
from livekit.agents.llm import (
    ChatContext,
    ChatChunk,
    CompletionUsage,
    LLMStream,
    ChoiceDelta,
    Tool,
)

from core.logger import get_logger
from core.session_store import MeetingSessionStore
from core.workflow import run_assistant_workflow
from core.retrieval.workspace_rag import run_workspace_assistant
from core.memory import ConversationMemoryManager, ConversationTurn
from core.voice.voice import prepare_text_for_speech

logger = get_logger("recallai.voice.pipeline")

# Shared in-process memory manager for voice sessions
_VOICE_MEMORY_MANAGER = ConversationMemoryManager()


class RecallAILLMStream(LLMStream):
    """
    LLMStream implementation that delivers the RecallAI answer
    as a single streamed chunk (avoids unnecessary streaming complexity
    since the RecallAI pipeline is synchronous LangGraph).
    """

    def __init__(
        self,
        llm_instance: "RecallAIPipelineAdapter",
        answer: str,
        *,
        chat_ctx: ChatContext,
        tools: Optional[list[Tool]] = None,
        conn_options: Optional[APIConnectOptions] = None,
    ) -> None:
        super().__init__(
            llm_instance,
            chat_ctx=chat_ctx,
            tools=tools or [],
            conn_options=conn_options or APIConnectOptions(),
        )
        self._answer = answer

    async def _run(self) -> None:
        # Deliver the full answer chunk
        chunk = ChatChunk(
            id=str(uuid.uuid4()),
            delta=ChoiceDelta(
                role="assistant",
                content=self._answer,
            ),
        )
        self._event_ch.send_nowait(chunk)

        # Deliver completion chunk with token count usage
        tokens = len(self._answer.split())
        final_chunk = ChatChunk(
            id=str(uuid.uuid4()),
            delta=ChoiceDelta(role="assistant", content=""),
            usage=CompletionUsage(
                prompt_tokens=10,
                completion_tokens=tokens,
                total_tokens=10 + tokens,
            ),
        )
        self._event_ch.send_nowait(final_chunk)


class RecallAIPipelineAdapter(llm.LLM):
    """
    LLM adapter that routes voice queries through the existing RecallAI pipeline:
    - If session_id is set  → meeting-specific RAG + LangGraph workflow
    - If session_id is None → workspace cross-meeting RAG

    MCP confirmation requests are surfaced as natural language in the voice response.
    """

    def __init__(
        self,
        session_store: MeetingSessionStore,
        session_id: Optional[str] = None,
        language: str = "english",
    ) -> None:
        super().__init__()
        self._store = session_store
        self._session_id = session_id
        self._language = language
        # Unique voice-session memory key (isolates from text chat history)
        self._memory_key = f"voice_{session_id or 'workspace'}"

    @property
    def model(self) -> str:
        return "recallai-pipeline"

    @property
    def provider(self) -> str:
        return "recallai"

    def chat(
        self,
        *,
        chat_ctx: ChatContext,
        tools: Optional[list[Tool]] = None,
        conn_options: Optional[APIConnectOptions] = None,
        **kwargs: Any,
    ) -> LLMStream:
        # Extract the last user utterance
        user_text = ""
        for msg in reversed(chat_ctx.messages):
            if msg.role == "user" and msg.content:
                if isinstance(msg.content, str):
                    user_text = msg.content.strip()
                elif isinstance(msg.content, list):
                    user_text = " ".join(
                        p if isinstance(p, str) else getattr(p, "text", "") or ""
                        for p in msg.content
                    ).strip()
                if user_text:
                    break

        if not user_text:
            answer = "I didn't catch that. Could you please repeat your question?"
        else:
            answer = self._run_pipeline(user_text)

        return RecallAILLMStream(
            self,
            answer,
            chat_ctx=chat_ctx,
            tools=tools,
            conn_options=conn_options,
        )

    def _run_pipeline(self, query: str) -> str:
        """Synchronously execute the RecallAI pipeline and return a voice-ready answer."""
        try:
            if self._session_id:
                return self._run_meeting_pipeline(query)
            else:
                return self._run_workspace_pipeline(query)
        except Exception as exc:
            logger.exception("RecallAI voice pipeline error for query=%r: %s", query, exc)
            return "I ran into an error processing that. Could you try rephrasing your question?"

    def _run_meeting_pipeline(self, query: str) -> str:
        """Route through meeting-specific LangGraph + RAG pipeline."""
        session = self._store.get_session(self._session_id)
        if not session:
            return (
                f"I couldn't find the meeting context. "
                "Please make sure the meeting has been processed first."
            )

        # Retrieve conversation history from voice memory
        memory = _VOICE_MEMORY_MANAGER.get_memory(self._memory_key)
        history_turns = memory.get_recent_turns()

        vs = session.get("vector_store")
        rag_c = session.get("rag_chain")
        action_items = session.get("action_items_structured", [])

        result = run_assistant_workflow(
            query=query,
            session_id=self._session_id,
            history=history_turns,
            vector_store=vs,
            rag_chain=rag_c,
            action_items=action_items,
        )

        # Persist this turn to voice memory
        answer_text = result.get("answer", "")
        memory.add_turn(
            ConversationTurn(role="user", content=query),
        )
        memory.add_turn(
            ConversationTurn(role="assistant", content=answer_text),
        )

        # Handle MCP action confirmation requests verbally
        if result.get("requires_confirmation") and result.get("confirmation_message"):
            spoken = prepare_text_for_speech(result["confirmation_message"])
            return spoken or (
                "I need your confirmation before executing that action. "
                "Please use the chat interface to confirm or reject it."
            )

        spoken = prepare_text_for_speech(answer_text, max_chars=600)
        return spoken or "I wasn't able to find relevant information in this meeting."

    def _run_workspace_pipeline(self, query: str) -> str:
        """Route through cross-meeting workspace RAG pipeline."""
        memory = _VOICE_MEMORY_MANAGER.get_memory(self._memory_key)
        history_turns = memory.get_recent_turns()

        history_context = " ".join(t.content for t in history_turns[-4:]) if history_turns else ""

        result = run_workspace_assistant(
            query=query,
            store=self._store,
            top_k=5,
            conversation_history=history_context,
        )

        answer_text = result.get("answer", "")

        memory.add_turn(ConversationTurn(role="user", content=query))
        memory.add_turn(ConversationTurn(role="assistant", content=answer_text))

        spoken = prepare_text_for_speech(answer_text, max_chars=600)
        return spoken or "I couldn't find relevant information across your meetings."
