# PHASE 3 — EVIDENCE-GROUNDED MEETING INTELLIGENCE & SOURCE PROVENANCE
## Evaluation & Implementation Report

**System**: Jitsly / Gistly — AI Meeting & Video Intelligence Assistant  
**Phase**: Phase 3 (Evidence Grounding, Timestamp Attribution & Source Provenance)  
**Status**: **COMPLETE — ALL 11/11 PHASE 3 TESTS PASSED (100% REGRESSION-FREE)**  
**Environment**: Windows 11 | Python 3.11.15 | ChromaDB | LangChain | Whisper / Sarvam  

> [!NOTE] Modernization Addendum (Modular Package & API Citation Schemas)
> Following Phase 3, the provenance and citation subsystem was modernized:
> 1. **Canonical Package Path**: All provenance data structures (`TranscriptSegment`, `RetrievedEvidence`) and validators (`verify_evidence_consistency`) are permanently located in `core/retrieval/provenance.py`.
> 2. **FastAPI Schema Serialization (`api/schemas/chat.py`)**: Evidence and citations are exposed through strongly typed Pydantic models:
>    - `EvidenceItem`: `evidence_id`, `chunk_index`, `text`, `time_range`, `start_time`, `end_time`, `source`, `session_id`.
>    - `CitationItem`: `evidence_id`, `time_range`, `chunk_index`, `speaker`.
> 3. **LangGraph Pipeline Integration**: Grounded evidence retrieval is executed in `node_retrieve` (`core/workflow.py`) and stored in the compiled graph's `GistlyWorkflowState.evidence`.

---

## 1. Executive Summary

Phase 3 transitions Jitsly from an answer-generating RAG application into a **trustworthy, evidence-grounded meeting intelligence platform**. Every AI-generated output (RAG question answers, action items, key decisions, open dilemmas) is now traceable to verified transcript segments, concrete timestamp intervals (`HH:MM:SS – HH:MM:SS`), and deterministic source chunks.

### Key Architectural Milestones Achieved:
1. **Deterministic Timestamp Architecture**:
   - Introduced `TranscriptSegment` and `RetrievedEvidence` data structures in [`core/provenance.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/provenance.py).
   - Formatted all timestamps consistently (`00:01:10 – 00:01:24`).
   - Integrated Whisper segment extraction (`result["segments"]`) and Sarvam 25-second interval tracking in [`core/transcriber.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/transcriber.py).
2. **Chunk-to-Segment Overlap Mapping**:
   - Implemented `map_chunk_to_segments` to dynamically project character-split RAG chunks back to underlying conversational timestamps without altering document splitting mechanics.
3. **ChromaDB Document Metadata Enrichment**:
   - Stored `start_seconds`, `end_seconds`, `start_time`, `end_time`, `time_range`, and `segment_ids` in every indexed Document in [`core/vector_store.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/vector_store.py) while respecting Chroma's scalar type constraints.
4. **Evidence Retrieval & Consistency Guard**:
   - Added `retrieve_evidence` and `ask_question_with_provenance` in [`core/rag_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/rag_engine.py).
   - Enforced `verify_evidence_consistency` to deterministically reject inverted timestamps, negative indices, or cross-session data leaks before exposing citations to users.
5. **Prompt-Level Evidence Attribution**:
   - Updated `SYSTEM_PROMPT` to mandate explicit citation markers (`[E1]`, `[E2]`) referencing context blocks, strictly forbidding invented evidence IDs.
6. **Provenance-Aware Streamlit UI**:
   - Enhanced [`app.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/app.py) with interactive timestamped transcript viewer, assistant response citation badges (`[E1] 00:01:10 – 00:01:24 (Chunk #0)`), and evidence-backed action items.

---

## 2. Evidence & Provenance Data Contracts

### 2.1. `TranscriptSegment` (`core/provenance.py`)
```python
@dataclass
class TranscriptSegment:
    segment_id: int
    text: str
    start_time: float  # Seconds
    end_time: float    # Seconds
    speaker: Optional[str] = None
    source: str = "meeting_transcript"

    @property
    def time_range(self) -> str:
        return format_time_range(self.start_time, self.end_time)
```

### 2.2. `RetrievedEvidence` (`core/provenance.py`)
```python
@dataclass
class RetrievedEvidence:
    evidence_id: str        # 'E1', 'E2', ...
    chunk_index: int
    text: str
    time_range: str         # '00:01:10 – 00:01:24'
    start_time: str         # '00:01:10'
    end_time: str           # '00:01:24'
    start_seconds: float    # 70.0
    end_seconds: float      # 84.0
    source: str
    source_type: str
    session_id: str
    score: Optional[float] = None
```

### 2.3. `ActionItem` Model (`core/extractor.py`)
```python
class ActionItem(BaseModel):
    task: str = Field(description="Clear, actionable task description")
    owner: Optional[str] = Field(default=None, description="Explicit owner or null")
    deadline: Optional[str] = Field(default=None, description="Explicit deadline or null")
    evidence: Optional[str] = Field(default=None, description="Direct quote or fact from transcript")
    timestamp: Optional[str] = Field(default=None, description="Timestamp or time range")
```

---

## 3. Phase 3 Deterministic Test Results

Test Suite: `scratch/test_phase3_provenance.py`  
Status: **11/11 PASSED (100%)**

| Test # | Test Case Description | Verified Attributes | Result |
|---|---|---|:---:|
| **Test 1** | **Timestamp Parsing & Segments** | Parsed 8 dialogue segments with start/end seconds, speakers, and formatted time ranges (`00:00:05 – 00:00:20`). | **PASS** |
| **Test 2** | **Chunk-to-Segment Mapping** | Text slice mapped to overlapping segment IDs (`[1]`) and accurate time range (`00:00:25 – 00:00:55`). | **PASS** |
| **Test 3** | **Document Metadata Enrichment** | Vector store documents enriched with `start_seconds`, `end_seconds`, `time_range`, `segment_ids`. | **PASS** |
| **Test 4** | **Evidence Retrieval (Direct QA)** | Query: *"What database did the team decide to migrate to?"* -> Retrieved PostgreSQL evidence with verified time range `00:00:05 – 00:02:05`. | **PASS** |
| **Test 5** | **Action Item Owner & Deadline** | Query: *"Who will prepare migration plan?"* -> Sarah, Friday, timestamp `00:00:05 – 00:02:05`, and direct quotation verified. | **PASS** |
| **Test 6** | **Project Deadline Attribution** | Query: *"When is project deadline?"* -> November 15th attributed at timestamp `00:02:10 – 00:04:10`. | **PASS** |
| **Test 7** | **Open Question Attribution** | Query: *"Who will own long-term db operations?"* -> Identified unresolved dilemma with evidence citation. | **PASS** |
| **Test 8** | **Cross-Session Evidence Guard** | Query against Session A does not retrieve Session B (MongoDB). Foreign evidence rejected by consistency validator. | **PASS** |
| **Test 9** | **Consistency Validator Edge Cases** | Accurately rejects inverted timestamps (`start > end`), empty strings, negative chunk indices, and foreign session IDs. | **PASS** |
| **Test 10** | **Grounded Context Formatting** | Formats context with `[Evidence E1] [Chunk 0] \| Time: ... \| Source: ...` and safe fallback on empty. | **PASS** |
| **Test 11** | **Regression Verification** | Validated zero regressions across Phase 1, Phase 2A, Phase 2B, Phase 2C, Phase 2D, and Phase 2E contracts. | **PASS** |

---

## 4. Multi-Phase Regression Matrix

All 4 test suites were executed sequentially on the live codebase:

```text
======================================================================
TEST SUITE RUNNER SUMMARY
======================================================================
1. Phase 3 Evidence & Provenance Suite       : 11 / 11 PASSED (100%)
2. Phase 2E End-to-End Pipeline Suite        : 11 / 11 PASSED (100%)
3. Phase 2D LLM Answer Quality Suite         : 11 / 11 PASSED (100%)
4. Phase 2C RAG Retrieval Quality Suite       : 11 / 11 PASSED (100%)
======================================================================
TOTAL SUITE RESULTS                          : 44 / 44 PASSED (100%)
REGRESSIONS INTRODUCED                       : 0
======================================================================
```

---

## 5. Architectural Diagram: Evidence & Provenance Flow

```mermaid
flowchart TD
    subgraph AudioSTT ["Audio & Transcription Pipeline"]
        A[Audio Input WAV] --> B[Silence-Aware Chunking]
        B --> C[Whisper / Sarvam STT]
        C --> D[transcribe_all_with_segments]
        D --> E[Full Transcript Text]
        D --> F[TranscriptSegments with Timestamps]
    end

    subgraph VectorPrep ["Vector Indexing & Enrichment"]
        E --> G[clean_transcript]
        G --> H[RecursiveCharacterTextSplitter]
        F --> I[map_chunk_to_segments]
        H --> I
        I --> J[Enriched Documents<br/>time_range, start/end_seconds, segment_ids]
        J --> K[(Per-Session ChromaDB)]
    end

    subgraph ProvenanceRAG ["Evidence Retrieval & Grounded Q&A"]
        L[User Question] --> M[retrieve_evidence]
        K --> M
        M --> N[RetrievedEvidence Objects E1, E2...]
        N --> O[verify_evidence_consistency]
        O --> P[Grounded Prompt with Evidence Markers]
        P --> Q[LLM Output Generation]
        Q --> R[Answer with Citations [E1]]
    end

    subgraph UserInterface ["Streamlit Presentation (app.py)"]
        R --> S[Chat Display + Evidence Badges]
        F --> T[Timestamped Transcript Accordion]
        E --> U[Intelligence Cards with Provenance]
    end
```

---

## 6. Files Modified and Validated

1. [`core/provenance.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/provenance.py) *(New)*: Core provenance models, segment parser, chunk mapping, and consistency validation.
2. [`core/vector_store.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/vector_store.py): Timestamp metadata enrichment, scalar Chroma types, segments parameter passthrough.
3. [`core/rag_engine.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/rag_engine.py): `SYSTEM_PROMPT` citation rules, `format_docs` with evidence labels, `retrieve_evidence`, `ask_question_with_provenance`.
4. [`core/transcriber.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/transcriber.py): `transcribe_all_with_segments`, Whisper `result["segments"]` mapping, Sarvam piece timestamping.
5. [`core/extractor.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/core/extractor.py): `ActionItem` timestamp and evidence fields, backward-compatible formatter.
6. [`main.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/main.py): Pipeline integration with `transcribe_all_with_segments` and segments result dictionary.
7. [`app.py`](file:///c:/Users/DELL/OneDrive/Desktop/New%20folder/Gistly-AI-Meeting-Video-Intelligence-Assistant-/app.py): Evidence badges in chat, interactive timestamped transcript viewer.
8. [`scratch/test_phase3_provenance.py`](file:///C:/Users/DELL/.gemini/antigravity/brain/cbfe16f8-bbc0-4a9a-b72a-c012129b1b28/scratch/test_phase3_provenance.py) *(New)*: Complete deterministic Phase 3 test harness.
