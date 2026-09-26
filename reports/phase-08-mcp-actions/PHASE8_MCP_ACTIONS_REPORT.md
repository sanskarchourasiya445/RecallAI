# JITSLY — PHASE 8: MCP & CONTROLLED EXTERNAL ACTIONS REPORT

**Project**: Jitsly / Gistly — AI Meeting & Video Intelligence Assistant  
**Date**: September 26, 2026  
**Phase**: Phase 8 — MCP & Controlled External Actions  
**Status**: **COMPLETED & VERIFIED (27/27 TESTS PASSED)**

> [!NOTE] Modernization Addendum (FastAPI REST Endpoints & LangGraph Tool Node)
> Following Phase 8, the action tool subsystem was modernized:
> 1. **Canonical Module Path**: The action tooling package is permanently organized under `core/actions/` (`action_resolver.py`, `tool_registry.py`, `confirmation.py`, `tools.py`).
> 2. **FastAPI REST API Exposure (`api/routes/actions.py`)**:
>    - `GET /api/v1/actions/tools` — List available action tools and parameter schemas.
>    - `POST /api/v1/actions` — Execute safe tools or stage consequential tools.
>    - `GET /api/v1/actions/pending` — List pending actions awaiting confirmation.
>    - `POST /api/v1/actions/{action_id}/confirm` — Explicit human-in-the-loop approval.
>    - `POST /api/v1/actions/{action_id}/reject` — Explicit action rejection.
> 3. **LangGraph StateGraph Integration**: Routed via `node_execute_actions` in `core/workflow.py`, dynamically executing or staging actions based on user query intent.

---

## 1. Phase Objective

Phase 8 elevates Jitsly from an assistant that merely understands meetings into an assistant that can **safely act on meeting intelligence through controlled tools**.

The action layer adheres to a strict safety doctrine:
> **Understand → Ground → Propose → Validate → Confirm → Act → Audit**

The system never blindly executes consequential external operations. Consequential actions (`send_email`, `create_calendar_event`) require explicit user confirmation through an isolated confirmation gate, and every executed action retains unbroken provenance back to the original transcript evidence and timestamp.

---

## 2. Phase 8 Architecture

```text
Meeting / Audio / Transcript
            │
            ▼
[Phase 6 Intelligence Layer] ────► Action Items, Decisions, Dilemmas
            │
            ▼
[User Intent / Natural Language]
            │
            ▼
[core/actions/action_resolver.py]
  - Resolves action items to tool arguments
  - Missing-info detection (refuses to guess dates/emails)
            │
            ▼
[core/actions/tool_registry.py]
  - Schema validation & parameter checks
  - Policy check: Does tool require confirmation?
            │
      ┌─────┴────────────────┐
      │                      │
(Safe / Low Risk)     (Consequential / Medium-High Risk)
      │                      │
      ▼                      ▼
 Direct Execution      [core/actions/confirmation.py]
      │                  - Stages Proposed Action (TTL: 15 min)
      │                  - Prevents duplicate confirmation
      │                  - Cross-session isolation check
      │                  - User [Confirm] / [Cancel]
      │                      │
      └──────────┬───────────┘
                 │
                 ▼
         [Tool Execution]
   (TaskTool, CalendarTool, EmailTool)
                 │
                 ▼
         [Audit Trail & Provenance]
   - Records execution_id, session_id, tool_name,
     arguments, results, evidence_ids, timestamp
                 │
                 ▼
       Auditable User Response
```

---

## 3. Tools Implemented

All 6 core tools are exposed with standard JSON schemas and are fully accessible via the in-process `ToolRegistry` and external Model Context Protocol (`mcp_server.server`):

| Tool Name | Purpose | Risk Level | Requires Confirmation | Input Schema Highlights |
|---|---|---|---|---|
| `create_task` | Create actionable task with owner, deadline, and meeting evidence | Low | **No** | `title`, `description`, `owner`, `deadline`, `source_session_id`, `source_evidence_ids` |
| `list_tasks` | Query and filter tasks created in a meeting session | Low | **No** | `session_id`, `owner` (filter), `status` (filter) |
| `create_calendar_event` | Schedule a calendar event for a meeting action or review | Medium | **Yes** | `title`, `start_time`, `end_time`, `participants`, `source_session_id`, `source_evidence_ids` |
| `list_calendar_events` | Query scheduled events for a meeting session | Low | **No** | `session_id`, `date` (filter) |
| `draft_email` | Prepare a follow-up email draft with meeting citations | Low | **No** | `recipient`, `subject`, `body`, `source_session_id`, `source_evidence_ids` |
| `send_email` | Dispatch an email to an external recipient | High | **Yes** | `recipient`, `subject`, `body`, `draft_id`, `source_session_id`, `source_evidence_ids` |

---

## 4. Safety Model & Confirmation Gate

1. **Explicit Confirmation Gate**:
   - High-impact operations (`send_email`, `create_calendar_event`) cannot execute directly. They are staged as `PendingAction` objects with a 15-minute TTL.
   - Confirmation cannot be inferred from previous chat history, meeting transcripts, or ambiguous user responses ("okay", "yes"). The user must explicitly approve the specific staged `action_id`.
2. **Duplicate Execution Prevention**:
   - Actions marked `confirmed` or `rejected` are sealed against repeated execution (`ALREADY_PROCESSED`).
3. **Cross-Session Isolation**:
   - An action staged in Meeting Session A cannot be viewed, confirmed, or executed from Meeting Session B (`SESSION_MISMATCH`).
4. **Strict Grounding & Missing Information**:
   - If a meeting mentions *"Let's meet next week"*, the system rejects ambiguous datetime strings (`MISSING_DATE_TIME`) and requests specific date and time bounds from the user rather than hallucinating timestamps.
   - If an action item has no assigned owner or deadline, it remains `None` without guessing.

---

## 5. Provenance & Audit Trail

Every resource created by Jitsly permanently embeds evidence provenance:
```json
{
  "task_id": "task_cae140",
  "title": "Migrate database schema",
  "owner": "Rahul",
  "deadline": "Friday 5 PM",
  "status": "Open",
  "source_session_id": "sess_p8_a_123456",
  "source_evidence_ids": ["E1", "E2"],
  "source_timestamp": "00:01:40 - 00:02:15",
  "created_at": 1727329980.12,
  "created_by": "jitsly"
}
```
Through `ConfirmationManager.explain_action(resource_id)`, Jitsly can deterministically explain:
- **What was done**: `Tool: create_task`
- **Why it was done**: Grounded in action item commitment from meeting dialogue
- **Which evidence backed it**: `[E1, E2]` at transcript interval `00:01:40 - 00:02:15`
- **Session boundary**: Strictly scoped to active meeting session

---

## 6. Actual Test Results

Test suite: [`tests/phase8/test_phase8_actions.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/tests/phase8/test_phase8_actions.py)

```text
===========================================================================
PHASE 8 TEST SUMMARY:
  Test 1: Tool Registry Loading                : PASS
  Test 2: Create Task                          : PASS
  Test 3: List Tasks                           : PASS
  Test 4: Create Calendar Event                : PASS
  Test 5: List Events                          : PASS
  Test 6: Draft Email                          : PASS
  Test 7: Send Email Confirmation              : PASS
  Test 8: Invalid Input Handling               : PASS
  Test 9: Missing Fields                       : PASS
  Test 10: Malformed Email                     : PASS
  Test 11: Confirmation Policy                 : PASS
  Test 12: Confirmation Rejection              : PASS
  Test 13: Duplicate Confirmation              : PASS
  Test 14: Invalid Evidence Handling           : PASS
  Test 15: Cross-Session Isolation             : PASS
  Test 16: Action Item -> Task                 : PASS
  Test 17: Action Item -> Calendar Missing Info: PASS
  Test 18: Action Item -> Email Draft          : PASS
  Test 19: Missing Info Handling               : PASS
  Test 20: Conversational Follow-Up to Tool    : PASS
  Test 21: Source Evidence Preserved           : PASS
  Test 22: Source Session Preserved            : PASS
  Test 23: Action Audit Preserved              : PASS
  Test 24: Phase 7 Regression                  : PASS
  Test 25: Phase 6 Regression                  : PASS
  Test 26: Phase 5 Regression                  : PASS
  Test 27: Phase 4 Regression                  : PASS
===========================================================================
ALL 27 PHASE 8 TESTS & REGRESSIONS PASSED SUCCESSFULLY!
```

---

## 7. Live vs. Mock Dependency Status

- **Task Tool**: `LOCAL / DETERMINISTIC` (Session-isolated in-memory task repository).
- **Calendar Tool**: `LOCAL / DETERMINISTIC` (Session-isolated calendar repository with ISO datetime validator).
- **Email Tool**: `LOCAL / DETERMINISTIC` (Session-isolated draft & sent email repository with RFC email regex).
- **MCP Server**: `ACTIVE & FULLY OPERATIONAL` (JSON-RPC 2.0 stdio server available via `python -m mcp_server.server`).
- **Live Google/Microsoft APIs**: `MOCKED / PLUGGABLE` (No external OAuth credentials required; clean adapter contracts allow direct future plug-in).

---

## 8. Limitations

1. **In-Memory Storage**: Current task, event, and email adapters are persisted per session in memory. A database migration for enterprise persistence (PostgreSQL/Redis) is deferred to future production deployment.
2. **Deterministic Boundaries**: External calendar and SMTP network calls are mocked locally to guarantee 100% deterministic test execution without reliance on third-party uptime or network latency.
