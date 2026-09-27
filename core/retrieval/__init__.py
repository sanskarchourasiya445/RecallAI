"""
Retrieval & Grounded Generation package for RecallAI.
Provides ChromaDB vector storage, embedding generation, evidence provenance,
and citation-grounded RAG reasoning.
"""

from core.retrieval.provenance import (
    TranscriptSegment,
    RetrievedEvidence,
    parse_transcript_segments,
    format_seconds,
    parse_timestamp,
    format_time_range,
    map_chunk_to_segments,
    verify_evidence_consistency,
)
from core.retrieval.vector_store import (
    build_vector_store,
    load_vector_store,
    get_retriever,
    get_embeddings,
    get_text_splitter,
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
)
from core.retrieval.rag_engine import (
    build_rag_chain,
    retrieve_evidence,
    ask_question,
    ask_question_with_provenance,
    ask_conversational_question,
    format_docs,
    get_llm,
    DEFAULT_K,
    DEFAULT_TEMPERATURE,
)

__all__ = [
    "TranscriptSegment",
    "RetrievedEvidence",
    "parse_transcript_segments",
    "format_seconds",
    "parse_timestamp",
    "format_time_range",
    "map_chunk_to_segments",
    "verify_evidence_consistency",
    "build_vector_store",
    "load_vector_store",
    "get_retriever",
    "get_embeddings",
    "get_text_splitter",
    "CHROMA_DIR",
    "COLLECTION_NAME",
    "EMBEDDING_MODEL",
    "DEFAULT_CHUNK_SIZE",
    "DEFAULT_CHUNK_OVERLAP",
    "build_rag_chain",
    "retrieve_evidence",
    "ask_question",
    "ask_question_with_provenance",
    "ask_conversational_question",
    "format_docs",
    "get_llm",
    "DEFAULT_K",
    "DEFAULT_TEMPERATURE",
]
