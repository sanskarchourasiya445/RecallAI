# PHASE 2 — AUDIO, TRANSCRIPTION & RAG PIPELINE STABILIZATION REPORT

**Project:** Jitsly / Gistly — AI Meeting & Video Intelligence Assistant  
**Phase:** Phase 2 (Sub-phases 2A, 2B, 2C, 2D, 2E)  
**Status:** **COMPLETE & VERIFIED**  
**Associated Test Scripts:** `scratch/test_phase2c_retrieval.py`, `scratch/test_phase2d_llm_quality.py`, `scratch/test_phase2e_pipeline.py`

> [!NOTE] Modernization Addendum (Modular Structure & Multi-Provider AI)
> The foundational pipelines established in Phase 2 have been evolved into modern modular architectures:
> 1. **STT Package Organization (`core/transcription/`)**: Local Whisper (`whisper_stt.py`) and Sarvam AI (`sarvam_stt.py`) were organized into a dedicated package, alongside a new cloud Gemini STT provider (`gemini_stt.py`).
> 2. **Retrieval Package Organization (`core/retrieval/`)**: Dense vector storage (`vector_store.py`) and provenance tracking (`provenance.py`) are complemented by a provider-abstracted embeddings module (`embeddings.py`), supporting both local `sentence-transformers/all-MiniLM-L6-v2` and optional Gemini embeddings with automatic local fallback.
> 3. **LangGraph RAG Orchestration (`core/workflow.py`)**: RAG retrieval and answer generation are choreographed as explicit graph nodes (`node_retrieve`, `node_generate`) powered by a multi-provider LLM tier (`core/llm_provider.py`) prioritizing Google Gemini (configurable via `GEMINI_MODEL`, default: `gemini-1.5-flash`) with Mistral API fallback.

---

## 1. Executive Summary

Phase 2 tackled the foundational audio ingestion, transcription, transcript processing, vector retrieval, and LLM answer generation pipelines. Prior to Phase 2, the application suffered from fragile audio conversion, unhandled silence clipping, unconstrained vector stores that mixed data across multiple meetings, and hallucinated answers on unanswerable questions.

Phase 2 was executed across five targeted iterations:
- **Phase 2A (Audio Extraction & STT Quality)**: Robust 16 kHz mono WAV conversion, silence-aware acoustic chunking via PyDub RMS minimization, and dual Whisper/Sarvam STT routing.
- **Phase 2B (Transcript Cleaning & Retrieval Prep)**: Structural dialogue cleaning, sentence-preserving text chunking, and metadata tagging.
- **Phase 2C (RAG Retrieval Quality & Grounding)**: Per-session ChromaDB collections, dense vector embeddings (`all-MiniLM-L6-v2`), and similarity retrieval.
- **Phase 2D (LLM Answer Quality & Factuality)**: Strict XML prompt constraints (`<meeting_context>`, `<user_question>`), explicit citation rules, and anti-hallucination guardrails for missing info.
- **Phase 2E (End-to-End Pipeline Validation & Reliability)**: Integrated failure cleanup of audio files and deterministic pipeline verification.

---

## 2. Key Architectural Deliverables

### 2.1 Audio Processing (`utils/audio_processor.py`)
- Standardized audio ingestion pipeline (`process_input`) for both YouTube URLs (via `yt-dlp`) and local media files.
- Peak volume normalization (-0.5 dBFS headroom) and standardization to 16 kHz Mono 16-bit PCM.
- Silence-aware acoustic chunking (`find_silence_split`) searching ±5 seconds for minimum acoustic energy (`min_rms`), preventing splits mid-word.
- Deterministic cleanup of intermediate audio chunks (`cleanup_temp_files`).

### 2.2 Dual STT Routing (`core/transcriber.py`)
- Route English audio to local `openai-whisper` (default model weight: `small`).
- Route Hindi/Hinglish audio to Sarvam AI (`saaras:v2.5`), splitting chunks into 25-second pieces to respect Sarvam's 30-second API limit.

### 2.3 Vector Storage & Session Isolation (`core/vector_store.py`)
- Replaced monolithic shared vector stores with per-session collections: `meeting_<session_id>`.
- Sentence-aware chunking (`chunk_size=600`, `chunk_overlap=100`) preserving semantic continuity.
- CPU-efficient dense embeddings via `sentence-transformers/all-MiniLM-L6-v2`.

### 2.4 Grounded Generation & Guardrails (`core/rag_engine.py`)
- Bounded temperature (`0.1`) and strict system prompt.
- Refusal behavior: mandates answering *"I could not find this information in the meeting transcript."* when context does not contain the answer.
- Retry wrapper (`invoke_with_retry`) with exponential backoff for transient LLM API errors.

---

## 3. Test Verification & Empirical Results

The pipeline was validated across multiple unit and integration suites:
- **Phase 2C Suite**: Validated chunking, metadata propagation, similarity ranking, and session isolation.
- **Phase 2D Suite**: Validated answer grounding, refusal on missing facts, and false-premise rejection.
- **Phase 2E Suite**: Validated end-to-end processing across synthetic transcripts, verifying that Session A and Session B data never mixed in ChromaDB.

---

## 4. Known Limitations & Transition to Phase 3

While Phase 2 produced stable text and vector retrieval, it lacked verifiable source attribution:
- Answers did not state *where* or *when* in the audio a statement was spoken.
- Timestamps from Whisper (`result["segments"]`) were discarded after raw transcription.
- This limitation led directly to the design and implementation of **Phase 3 (Evidence Provenance & Timestamp Attribution)**.
