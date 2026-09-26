"""
LangGraph Stateful Workflow Orchestration for Gistly / Jitsly.
Orchestrates:
  User Request
      ↓
  Understand / Resolve Context (Pronoun rewriting, conversation history, intent detection)
      ↓
  Retrieve Meeting Evidence (Session-isolated vector store search)
      ↓
  Evaluate Grounding (Citation consistency, evidence sufficiency, refusal check)
      ↓
  Answer OR Action (Grounded answer with citations [E1],[E2] OR Controlled MCP Tool invocation)
"""

import os
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END

from core.retrieval.provenance import RetrievedEvidence, verify_evidence_consistency
from core.retrieval.rag_engine import DEFAULT_K, format_docs, ask_question, retrieve_evidence
from core.memory import ConversationTurn, resolve_conversational_query
from core.actions.models import ToolResult
from core.actions.tool_registry import ToolRegistry, DEFAULT_TOOL_REGISTRY
from core.actions.action_resolver import ActionResolver
from core.intelligence.extractor import ActionItem
from core.observability import get_langfuse_callbacks


class MeetingWorkflowState(TypedDict, total=False):
    # Inputs
    query: str
    session_id: str
    history: List[ConversationTurn]

    # Workflow Reasoning State
    resolved_query: str
    intent: str  # "question" | "action" | "clarify"
    evidence: List[RetrievedEvidence]
    is_grounded: bool

    # Action / MCP State
    action_tool_name: Optional[str]
    action_args: Optional[Dict[str, Any]]
    action_result: Optional[Dict[str, Any]]
    requires_confirmation: bool
    pending_action_id: Optional[str]
    confirmation_message: Optional[str]

    # Final Output
    answer: str


def create_meeting_workflow(
    vector_store=None,
    rag_chain=None,
    tool_registry: Optional[ToolRegistry] = None,
    action_resolver: Optional[ActionResolver] = None,
    action_items: Optional[List[Any]] = None,
):
    """
    Build and compile an explicit LangGraph StateGraph coordinating RAG,
    evidence evaluation, conversational memory, and MCP action tools.
    """
    registry = tool_registry or DEFAULT_TOOL_REGISTRY
    resolver = action_resolver or ActionResolver(registry=registry)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Node: Understand Request
    # ─────────────────────────────────────────────────────────────────────────
    def node_understand_request(state: MeetingWorkflowState) -> Dict[str, Any]:
        raw_query = (state.get("query") or "").strip()
        history = state.get("history") or []
        sid = state.get("session_id", "default")

        if not raw_query:
            return {
                "resolved_query": "",
                "intent": "clarify",
                "answer": "Please ask a question or request an action.",
            }

        # Resolve pronouns and elliptical follow-up references
        resolved = resolve_conversational_query(raw_query, history)
        q_lower = resolved.lower()

        # Action Intent Detection
        # 1. List tasks
        if "list tasks" in q_lower or "show tasks" in q_lower:
            return {
                "resolved_query": resolved,
                "intent": "action",
                "action_tool_name": "list_tasks",
                "action_args": {"session_id": sid},
            }

        # 2. List events
        if "list events" in q_lower or "list calendar" in q_lower or "show events" in q_lower:
            return {
                "resolved_query": resolved,
                "intent": "action",
                "action_tool_name": "list_calendar_events",
                "action_args": {"session_id": sid},
            }

        # 3. Create task from action items
        if any(kw in q_lower for kw in ("create task", "add task", "new task", "assign task", "create a task")):
            if action_items:
                matched = resolver.find_action_item_by_query(resolved, action_items)
                if matched:
                    task_ai = ActionItem(**matched) if isinstance(matched, dict) else matched
                    t_res = resolver.resolve_action_item_to_task(task_ai, session_id=sid)
                    if t_res.is_ready:
                        return {
                            "resolved_query": resolved,
                            "intent": "action",
                            "action_tool_name": "create_task",
                            "action_args": t_res.arguments,
                        }
                    return {
                        "resolved_query": resolved,
                        "intent": "clarify",
                        "answer": t_res.clarification_prompt,
                    }
                return {
                    "resolved_query": resolved,
                    "intent": "clarify",
                    "answer": "I could not identify which action item you would like to convert. Please specify the task name or number.",
                }
            return {
                "resolved_query": resolved,
                "intent": "action",
                "action_tool_name": "create_task",
                "action_args": {"title": resolved, "session_id": sid},
            }

        # 4. Schedule calendar event
        if "schedule" in q_lower or "calendar" in q_lower:
            if action_items:
                matched = resolver.find_action_item_by_query(resolved, action_items)
                if matched:
                    task_ai = ActionItem(**matched) if isinstance(matched, dict) else matched
                    cal_res = resolver.resolve_action_item_to_calendar(task_ai, session_id=sid)
                    return {
                        "resolved_query": resolved,
                        "intent": "clarify",
                        "answer": cal_res.clarification_prompt,
                    }
            return {
                "resolved_query": resolved,
                "intent": "clarify",
                "answer": "I can schedule a calendar event for you, but I need: event title, date, start time, end time, and attendees.",
            }

        # 5. Draft email
        if "draft email" in q_lower or "prepare email" in q_lower:
            if action_items:
                matched = resolver.find_action_item_by_query(resolved, action_items)
                if matched:
                    task_ai = ActionItem(**matched) if isinstance(matched, dict) else matched
                    email_res = resolver.resolve_action_item_to_email(task_ai, session_id=sid)
                    return {
                        "resolved_query": resolved,
                        "intent": "clarify",
                        "answer": email_res.clarification_prompt,
                    }
            return {
                "resolved_query": resolved,
                "intent": "clarify",
                "answer": "I can draft an email for you, but what should the recipient email address and subject be?",
            }

        # 6. Send email (consequential action)
        if "send email" in q_lower:
            return {
                "resolved_query": resolved,
                "intent": "action",
                "action_tool_name": "send_email",
                "action_args": {"session_id": sid},
            }

        # Default: Question inquiry
        return {
            "resolved_query": resolved,
            "intent": "question",
            "action_tool_name": None,
            "action_args": {},
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Node: Retrieve Evidence
    # ─────────────────────────────────────────────────────────────────────────
    def node_retrieve_evidence(state: MeetingWorkflowState) -> Dict[str, Any]:
        resolved_q = state.get("resolved_query") or state.get("query") or ""
        if not vector_store or not resolved_q:
            return {"evidence": [], "is_grounded": False}

        raw_evidence = retrieve_evidence(vector_store, resolved_q, k=DEFAULT_K)
        active_sid = state.get("session_id", "")

        # Verify evidence consistency against active session
        verified = [
            ev for ev in raw_evidence
            if verify_evidence_consistency(ev, active_session_id=active_sid)
        ]

        return {
            "evidence": verified,
            "is_grounded": len(verified) > 0,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Node: Evaluate Evidence
    # ─────────────────────────────────────────────────────────────────────────
    def node_evaluate_evidence(state: MeetingWorkflowState) -> Dict[str, Any]:
        evidence = state.get("evidence") or []
        is_grounded = len(evidence) > 0
        # In offline fallback (no active LLM), distance > 1.5 indicates unmentioned/unrelated query
        if rag_chain is None and evidence and evidence[0].score is not None and evidence[0].score > 1.5:
            is_grounded = False
        return {"is_grounded": is_grounded}

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Node: Generate Answer
    # ─────────────────────────────────────────────────────────────────────────
    def node_generate_answer(state: MeetingWorkflowState) -> Dict[str, Any]:
        # Handle clarification
        if state.get("intent") == "clarify":
            return {"answer": state.get("answer") or "Please ask a specific question about the meeting."}

        # Handle ungrounded / missing evidence
        if not state.get("is_grounded"):
            return {
                "answer": "I could not find this information in the meeting transcript."
            }

        resolved_q = state.get("resolved_query") or state.get("query") or ""
        evidence = state.get("evidence") or []

        # If RAG chain is provided, invoke grounded LLM with Langfuse tracing
        if rag_chain is not None:
            callbacks = get_langfuse_callbacks(session_id=state.get("session_id"))
            config = {"callbacks": callbacks} if callbacks else {}
            try:
                answer = rag_chain.invoke(resolved_q, config=config) if config else rag_chain.invoke(resolved_q)
            except Exception:
                answer = ask_question(rag_chain, resolved_q)
        else:
            # Deterministic fallback extract from verified evidence
            first_ev = evidence[0]
            answer = (
                f"Transcript evidence at {first_ev.time_range} [{first_ev.evidence_id}]: "
                f"\"{first_ev.text.strip()}\"\n\n*(Note: LLM API key is not configured; showing grounded retrieval extract.)*"
            )

        return {"answer": answer}

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Node: Execute Action (MCP Tools)
    # ─────────────────────────────────────────────────────────────────────────
    def node_execute_action(state: MeetingWorkflowState) -> Dict[str, Any]:
        tool_name = state.get("action_tool_name")
        args = state.get("action_args") or {}

        if not tool_name or not registry.get_tool(tool_name):
            available = [t["name"] for t in registry.list_tools()]
            return {
                "answer": f"Unknown action tool '{tool_name}'. Available tools: {available}",
                "action_result": None,
                "requires_confirmation": False,
            }

        # Execute through ToolRegistry with confirmation gate enforcement
        t_res: ToolResult = registry.execute_tool(tool_name, args)

        # Check if action was staged for human-in-the-loop confirmation
        is_pending = bool(
            getattr(t_res, "pending_action_id", None)
            or (t_res.metadata and t_res.metadata.get("status") == "pending_confirmation")
        )
        if is_pending:
            act_id = getattr(t_res, "pending_action_id", None) or (t_res.metadata or {}).get("action_id")
            return {
                "answer": f"Action '{tool_name}' is consequential and requires your explicit confirmation before proceeding.",
                "requires_confirmation": True,
                "pending_action_id": act_id,
                "confirmation_message": t_res.message,
                "action_result": {"status": "pending_confirmation", "action_id": act_id},
            }

        # Format successful outputs
        if tool_name == "list_tasks":
            tasks = (t_res.metadata or {}).get("tasks", [])
            if tasks:
                lines = [f"• `{t['task_id']}`: **{t['title']}** (Owner: {t.get('owner') or 'Unassigned'}, Due: {t.get('deadline') or 'Not specified'})" for t in tasks]
                answer = "Here are the active tasks for this meeting session:\n\n" + "\n".join(lines)
            else:
                answer = "No tasks have been created yet for this meeting session. You can create one from any action item."
        elif tool_name == "list_calendar_events":
            events = (t_res.metadata or {}).get("events", [])
            if events:
                lines = [f"• `{e['event_id']}`: **{e['title']}** ({e['start_time']} - {e['end_time']})" for e in events]
                answer = "Here are the scheduled events for this meeting session:\n\n" + "\n".join(lines)
            else:
                answer = "No calendar events have been scheduled yet for this meeting session."
        elif tool_name == "create_task":
            ts_val = args.get("source_timestamp")
            ts_line = f"\n• **Timestamp**: {ts_val}" if ts_val else ""
            answer = (
                f"✅ **Task Created Successfully**\n\n"
                f"• **Task ID**: `{t_res.resource_id}`\n"
                f"• **Title**: {args.get('title')}\n"
                f"• **Owner**: {args.get('owner') or 'Unassigned'}\n"
                f"• **Due Date**: {args.get('deadline') or 'Not specified'}\n"
                f"• **Evidence Provenance**: \"{args.get('description', '')}\""
                f"{ts_line}"
            )
        else:
            answer = t_res.message or f"Successfully executed action '{tool_name}'."

        return {
            "answer": answer,
            "action_result": t_res.metadata,
            "requires_confirmation": False,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Workflow Routing Functions
    # ─────────────────────────────────────────────────────────────────────────
    def route_after_understand(state: MeetingWorkflowState) -> str:
        intent = state.get("intent", "question")
        if intent == "action":
            return "execute_action"
        if intent == "clarify":
            return "generate_answer"
        return "retrieve_evidence"

    # ─────────────────────────────────────────────────────────────────────────
    # Build LangGraph StateGraph
    # ─────────────────────────────────────────────────────────────────────────
    workflow = StateGraph(MeetingWorkflowState)

    workflow.add_node("understand_request", node_understand_request)
    workflow.add_node("retrieve_evidence", node_retrieve_evidence)
    workflow.add_node("evaluate_evidence", node_evaluate_evidence)
    workflow.add_node("generate_answer", node_generate_answer)
    workflow.add_node("execute_action", node_execute_action)

    workflow.set_entry_point("understand_request")

    workflow.add_conditional_edges(
        "understand_request",
        route_after_understand,
        {
            "execute_action": "execute_action",
            "retrieve_evidence": "retrieve_evidence",
            "generate_answer": "generate_answer",
        },
    )
    workflow.add_edge("retrieve_evidence", "evaluate_evidence")
    workflow.add_edge("evaluate_evidence", "generate_answer")
    workflow.add_edge("generate_answer", END)
    workflow.add_edge("execute_action", END)

    return workflow.compile()


def run_assistant_workflow(
    query: str,
    session_id: str = "default",
    history: Optional[List[ConversationTurn]] = None,
    vector_store=None,
    rag_chain=None,
    tool_registry: Optional[ToolRegistry] = None,
    action_resolver: Optional[ActionResolver] = None,
    action_items: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Convenience runner executing the compiled LangGraph meeting assistant workflow.
    Returns:
    {
        "answer": str,
        "evidence": List[RetrievedEvidence],
        "resolved_query": str,
        "intent": str,
        "action_result": Optional[dict],
        "requires_confirmation": bool,
        "pending_action_id": Optional[str],
        "confirmation_message": Optional[str],
    }
    """
    compiled_app = create_meeting_workflow(
        vector_store=vector_store,
        rag_chain=rag_chain,
        tool_registry=tool_registry,
        action_resolver=action_resolver,
        action_items=action_items,
    )

    initial_state: MeetingWorkflowState = {
        "query": query,
        "session_id": session_id,
        "history": history or [],
    }

    final_state = compiled_app.invoke(initial_state)

    return {
        "answer": final_state.get("answer", ""),
        "evidence": final_state.get("evidence", []),
        "resolved_query": final_state.get("resolved_query", query),
        "intent": final_state.get("intent", "question"),
        "action_result": final_state.get("action_result"),
        "requires_confirmation": final_state.get("requires_confirmation", False),
        "pending_action_id": final_state.get("pending_action_id"),
        "confirmation_message": final_state.get("confirmation_message"),
    }
