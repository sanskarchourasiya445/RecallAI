import os
import uuid
from langchain_chroma import Chroma
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from core.retrieval.provenance import (
    TranscriptSegment,
    parse_transcript_segments,
    map_chunk_to_segments,
    format_seconds,
    format_time_range,
)

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Retrieval chunking configuration
# chunk_size = 600 characters (~100-130 words, ~130-160 tokens) fits comfortably within all-MiniLM-L6-v2's 256-token context
# chunk_overlap = 100 characters ensures full sentence and thought continuity across chunk boundaries
DEFAULT_CHUNK_SIZE = 600
DEFAULT_CHUNK_OVERLAP = 100
CHUNK_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]


def get_collection_name(session_id: str) -> str:
    """
    Generate deterministic, model-isolated Chroma collection name (Option A).
    Prevents dimensional collision between 384-d (MiniLM) and 768-d (Gemini) embeddings.
    - Local MiniLM: 'meeting_{session_id}' (100% backward compatible with existing data & tests)
    - Gemini Embeddings: 'meeting_{session_id}_gemini_{model_slug}'
    """
    clean_sid = session_id.replace("meeting_", "")
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    local_only = os.getenv("LOCAL_EMBEDDINGS", "true").lower() in ("1", "true", "yes")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if provider == "gemini" and not local_only and gemini_key and not str(gemini_key).startswith("mock-") and gemini_key != "your_gemini_api_key_here":
        emb_model = os.getenv("GEMINI_EMBEDDING_MODEL") or os.getenv("EMBEDDING_MODEL") or "models/text-embedding-004"
        slug = emb_model.replace("models/", "").replace("/", "_").replace("-", "_")
        return f"meeting_{clean_sid}_gemini_{slug}"

    return f"meeting_{clean_sid}"


def get_embeddings():
    """
    Instantiate embeddings model with provider selection and local fallback.
    - If EMBEDDING_PROVIDER == 'gemini' and LOCAL_EMBEDDINGS is False and GEMINI_API_KEY is available:
      Uses GoogleGenerativeAIEmbeddings(model=GEMINI_EMBEDDING_MODEL, google_api_key=GEMINI_API_KEY).
    - Otherwise (default / offline / tests / demo mode):
      Uses local HuggingFaceEmbeddings(model_name=LOCAL_EMBEDDING_MODEL, model_kwargs={"device": "cpu"}).
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    local_only = os.getenv("LOCAL_EMBEDDINGS", "true").lower() in ("1", "true", "yes")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if provider == "gemini" and not local_only and gemini_key and not str(gemini_key).startswith("mock-") and gemini_key != "your_gemini_api_key_here":
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            emb_model = os.getenv("GEMINI_EMBEDDING_MODEL") or os.getenv("EMBEDDING_MODEL") or "models/text-embedding-004"
            print(f"[VectorStore] Initializing Gemini Embeddings model '{emb_model}'...")
            return GoogleGenerativeAIEmbeddings(
                model=emb_model,
                google_api_key=gemini_key,
            )
        except Exception as e:
            print(f"[VectorStore] Warning: Could not initialize Gemini Embeddings ({e}). Falling back to local model.")

    # Reliable local fallback
    model_name = os.getenv("LOCAL_EMBEDDING_MODEL") or EMBEDDING_MODEL
    if model_name.startswith("models/"):
        model_name = "all-MiniLM-L6-v2"
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
    )


def get_text_splitter(
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> RecursiveCharacterTextSplitter:
    """Instantiate a sentence- and paragraph-aware recursive text splitter for retrieval chunks."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CHUNK_SEPARATORS,
    )


def prepare_transcript_documents(
    transcript: str,
    session_id: str = None,
    source: str = None,
    source_type: str = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    extra_metadata: dict = None,
    segments: list = None,
) -> list:
    """
    Transform raw transcript text into clean, ordered, metadata-enriched LangChain Documents for RAG.
    - Deterministically cleans transcript text using clean_transcript.
    - Splits text using paragraph- and sentence-aware recursive text splitting.
    - Enriches chunks with timestamps, time ranges, and segment IDs when available.
    - Attaches rich metadata (session_id, chunk_index, total_chunks, char_count, word_count, source, source_type).
    - Enforces deduplication across consecutive identical slices.
    - Guarantees non-empty document list for Chroma compatibility.
    """
    from core.transcription.transcriber import clean_transcript

    if not session_id:
        session_id = uuid.uuid4().hex[:8]

    inferred_source_type = source_type or (
        "youtube" if str(source).startswith(("http://", "https://"))
        else "local_file" if source
        else "meeting_transcript"
    )

    if not transcript or not transcript.strip():
        print(f"[VectorStore] Warning: Empty transcript provided for session '{session_id}'. Creating safe fallback document.")
        return [
            Document(
                page_content="No transcript content available for this session.",
                metadata={
                    "session_id": session_id,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "char_count": 0,
                    "word_count": 0,
                    "source": source or "unknown",
                    "source_type": "empty",
                    "start_seconds": 0.0,
                    "end_seconds": 0.0,
                    "start_time": "00:00:00",
                    "end_time": "00:00:00",
                    "time_range": "Not specified",
                    "segment_ids": "",
                },
            )
        ]

    # If segments were not passed in explicitly, attempt parsing from transcript text
    active_segments = segments
    if active_segments is None:
        parsed_segs = parse_transcript_segments(transcript, source=source or "meeting_transcript")
        if any(s.start_time > 0 or s.end_time > 0 for s in parsed_segs):
            active_segments = parsed_segs

    cleaned_text = clean_transcript(transcript)
    splitter = get_text_splitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    raw_chunks = splitter.split_text(cleaned_text)

    # Deduplication guard: filter out exact identical consecutive duplicate chunks
    filtered_chunks = []
    for c in raw_chunks:
        c_str = c.strip()
        if c_str and (not filtered_chunks or c_str != filtered_chunks[-1]):
            filtered_chunks.append(c_str)

    if not filtered_chunks:
        filtered_chunks = ["No transcript content available for this session."]

    total_chunks = len(filtered_chunks)
    docs = []

    for i, chunk in enumerate(filtered_chunks):
        start_sec, end_sec, seg_ids = None, None, []
        if active_segments:
            start_sec, end_sec, seg_ids = map_chunk_to_segments(chunk, active_segments)

        if start_sec is not None and end_sec is not None:
            time_range_str = format_time_range(start_sec, end_sec)
            start_time_str = format_seconds(start_sec)
            end_time_str = format_seconds(end_sec)
        else:
            start_sec = 0.0
            end_sec = 0.0
            start_time_str = "00:00:00"
            end_time_str = "00:00:00"
            time_range_str = "Not specified"
            seg_ids = []

        meta = {
            "session_id": session_id,
            "chunk_index": i,
            "total_chunks": total_chunks,
            "char_count": len(chunk),
            "word_count": len(chunk.split()),
            "source": source or "meeting_transcript",
            "source_type": inferred_source_type,
            "start_seconds": float(start_sec),
            "end_seconds": float(end_sec),
            "start_time": start_time_str,
            "end_time": end_time_str,
            "time_range": time_range_str,
            "segment_ids": ",".join(map(str, seg_ids)),
        }
        if extra_metadata:
            meta.update(extra_metadata)

        docs.append(Document(page_content=chunk, metadata=meta))

    print(f"[VectorStore] Prepared {len(docs)} retrieval document(s) for session '{session_id}' (chunk_size={chunk_size}, overlap={chunk_overlap}).")
    return docs


def build_vector_store(
    transcript: str,
    session_id: str = None,
    source: str = None,
    source_type: str = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    extra_metadata: dict = None,
    segments: list = None,
) -> Chroma:
    """Build or populate a per-session isolated Chroma collection with retrieval-ready documents."""
    print("[VectorStore] Building vector store...")

    docs = prepare_transcript_documents(
        transcript=transcript,
        session_id=session_id,
        source=source,
        source_type=source_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        extra_metadata=extra_metadata,
        segments=segments,
    )

    actual_session_id = docs[0].metadata["session_id"]
    collection_name = get_collection_name(actual_session_id)

    embeddings = get_embeddings()
    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=CHROMA_DIR,
    )

    print(f"[VectorStore] Vector store built successfully for collection '{collection_name}' ({len(docs)} docs).")
    return vector_store


def load_vector_store(collection_name: str = None) -> Chroma:
    """Load an existing Chroma collection from disk with model compatibility check."""
    embeddings = get_embeddings()
    if collection_name:
        if collection_name.startswith("meeting_"):
            target_collection = collection_name
        else:
            target_collection = get_collection_name(collection_name)
    else:
        target_collection = get_collection_name(COLLECTION_NAME)

    vector_store = Chroma(
        collection_name=target_collection,
        embedding_function=embeddings,
        persist_directory=CHROMA_DIR,
    )
    return vector_store


def get_retriever(vector_store: Chroma, k: int = 4, score_threshold: float = None):
    """Obtain a similarity search retriever for the provided vector store."""
    search_kwargs = {"k": k}
    search_type = "similarity"
    if score_threshold is not None:
        search_type = "similarity_score_threshold"
        search_kwargs["score_threshold"] = score_threshold

    return vector_store.as_retriever(
        search_type=search_type,
        search_kwargs=search_kwargs,
    )

