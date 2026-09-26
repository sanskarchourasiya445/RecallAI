from dotenv import load_dotenv
load_dotenv()

import os
import uuid
import streamlit as st
import time
import html
import base64
from utils.audio_processor import process_input, cleanup_temp_files
from core.transcription import transcribe_all, transcribe_all_with_segments
from core.intelligence import (
    summarize,
    generate_title,
    extract_meeting_intelligence,
    extract_action_items,
    extract_key_decisions,
    extract_questions,
    format_action_items,
    format_key_decisions,
    format_open_questions,
)
from core.retrieval import (
    build_vector_store,
    build_rag_chain,
    ask_question,
    ask_question_with_provenance,
    ask_conversational_question,
    format_time_range,
)
from core.memory import SessionConversationMemory
from core.voice import transcribe_voice_input_safe, synthesize_answer
from core.actions import (
    DEFAULT_TOOL_REGISTRY,
    ActionResolver,
    ToolResult,
    PendingAction,
)
from core.workflow import run_assistant_workflow
from core.config import (
    get_system_health,
    validate_file_size,
    validate_audio_duration,
    cleanup_old_temp_files,
    MAX_UPLOAD_SIZE_MB,
    MAX_AUDIO_DURATION_MINUTES,
    MISTRAL_API_KEY,
    SARVAM_API_KEY,
)
from core.logger import get_logger
from core.demo import load_demo_meeting

logger = get_logger("gistly.app")


# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gistly",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,600&family=Jost:wght@400;500;600&display=swap');

/* ── Root Variables — soft vintage / cottage palette ── */
:root {
    --bg: #faf7f1;
    --surface: #ffffff;
    --surface-2: #f4efe6;
    --border: #e3d9c8;
    --accent: #9fb3c8;
    --accent-glow: #b9cbdb;
    --accent-2: #c4a077;
    --text: #4a4237;
    --text-muted: #a49a89;
    --success: #93a884;
    --warning: #cf9d5c;
    --danger: #bf7d68;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Cormorant Garamond', serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
}

/* Soft paper texture instead of tech grid */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    background-image: radial-gradient(rgba(159, 179, 200, 0.05) 1px, transparent 1px);
    background-size: 22px 22px;
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text) !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', serif !important;
    color: var(--text) !important;
    font-weight: 600 !important;
}

/* ── Hero Title ── */
.hero-title {
    font-family: 'Playfair Display', serif;
    font-style: italic;
    font-size: clamp(2rem, 5vw, 3.4rem);
    font-weight: 600;
    line-height: 1.15;
    margin: 0;
    color: var(--text);
}

.hero-sub {
    font-family: 'Jost', sans-serif;
    font-size: 0.72rem;
    color: var(--text-muted);
    letter-spacing: 0.28em;
    text-transform: uppercase;
    margin-top: 0.6rem;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.6rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(74, 66, 55, 0.05);
    transition: box-shadow 0.25s, transform 0.25s;
}

.card:hover {
    box-shadow: 0 6px 20px rgba(74, 66, 55, 0.09);
    transform: translateY(-1px);
}

.card-title {
    font-family: 'Jost', sans-serif;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent-2);
    margin-bottom: 0.85rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
    margin-left: 0.4rem;
}

.card-content {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.05rem;
    line-height: 1.7;
    color: var(--text);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Accent Badge ── */
.badge {
    display: inline-block;
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    font-family: 'Jost', sans-serif;
    font-size: 0.62rem;
    font-weight: 500;
    letter-spacing: 0.15em;
    text-transform: uppercase;
}

.badge-purple { background: rgba(159,179,200,0.18); color: #6f8298; border: 1px solid rgba(159,179,200,0.4); }
.badge-cyan   { background: rgba(196,160,119,0.15); color: var(--accent-2); border: 1px solid rgba(196,160,119,0.35); }
.badge-green  { background: rgba(147,168,132,0.15); color: var(--success); border: 1px solid rgba(147,168,132,0.35); }

/* ── Input & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.05rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(159,179,200,0.25) !important;
}

.stButton > button {
    background: var(--bg) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--accent) !important;
    border-radius: 999px !important;
    font-family: 'Jost', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.18em !important;
    padding: 0.65rem 1.75rem !important;
    transition: all 0.25s !important;
    text-transform: uppercase !important;
}

.stButton > button:hover {
    background: var(--accent) !important;
    color: #ffffff !important;
    border-color: var(--accent) !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
}

/* ── Progress / Status ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: var(--surface-2);
    border-radius: 3px;
    margin: 0.4rem 0;
    border: 1px solid var(--border);
    font-family: 'Cormorant Garamond', serif;
    font-size: 0.95rem;
}

.status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
}

.dot-active   { background: var(--accent-2); box-shadow: 0 0 6px var(--accent-2); animation: pulse 1.5s infinite; }
.dot-done     { background: var(--success); }
.dot-pending  { background: var(--border); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ── Workspace Overview & Metrics ── */
.workspace-metrics {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.25rem;
    flex-wrap: wrap;
}
.metric-box {
    flex: 1;
    min-width: 140px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 0.85rem 1.1rem;
    box-shadow: 0 1px 4px rgba(74, 66, 55, 0.04);
}
.metric-number {
    font-family: 'Syne', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    line-height: 1.1;
    margin-bottom: 0.2rem;
    color: var(--text);
}
.metric-label {
    font-family: 'Jost', sans-serif;
    font-size: 0.65rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
}

/* ── Intelligence Item Cards ── */
.intel-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1rem 1.25rem;
    margin-bottom: 0.85rem;
    box-shadow: 0 1px 4px rgba(74, 66, 55, 0.04);
    transition: all 0.2s ease;
}
.intel-card:hover {
    border-color: var(--accent);
    box-shadow: 0 3px 10px rgba(159, 179, 200, 0.12);
}
.intel-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.4rem;
    line-height: 1.4;
}
.meta-row {
    display: flex;
    gap: 0.6rem;
    align-items: center;
    flex-wrap: wrap;
    font-family: 'Jost', sans-serif;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.2rem 0.55rem;
    border-radius: 4px;
    background: var(--surface-2);
    border: 1px solid var(--border);
}
.pill-owner { background: rgba(159,179,200,0.12); color: #5a6e82; border-color: rgba(159,179,200,0.3); }
.pill-due   { background: rgba(196,160,119,0.12); color: #8c6a43; border-color: rgba(196,160,119,0.3); }
.pill-time  { background: rgba(74,66,55,0.06); color: var(--text); font-family: monospace; font-size: 0.72rem; }

.status-pill-open       { background: rgba(207, 157, 92, 0.15); color: #9c6c2e; border: 1px solid rgba(207, 157, 92, 0.4); border-radius: 4px; padding: 2px 7px; font-size: 0.72rem; font-weight: 600; }
.status-pill-inprogress { background: rgba(159, 179, 200, 0.2); color: #4e657c; border: 1px solid rgba(159, 179, 200, 0.5); border-radius: 4px; padding: 2px 7px; font-size: 0.72rem; font-weight: 600; }
.status-pill-done       { background: rgba(147, 168, 132, 0.2); color: #3d6e2e; border: 1px solid rgba(147, 168, 132, 0.5); border-radius: 4px; padding: 2px 7px; font-size: 0.72rem; font-weight: 600; }

.evidence-quote-box {
    margin-top: 0.5rem;
    padding: 0.55rem 0.85rem;
    background: var(--surface-2);
    border-left: 3px solid var(--accent);
    border-radius: 0 4px 4px 0;
    font-family: 'Cormorant Garamond', serif;
    font-style: italic;
    font-size: 0.95rem;
    color: #5d5447;
    line-height: 1.5;
}
.empty-notice {
    padding: 1.5rem;
    background: var(--surface-2);
    border: 1px dashed var(--border);
    border-radius: 4px;
    text-align: center;
    color: var(--text-muted);
    font-family: 'Cormorant Garamond', serif;
    font-size: 1rem;
    font-style: italic;
}

/* ── Chat ── */
.chat-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.25rem;
    max-height: 420px;
    overflow-y: auto;
    margin-bottom: 1rem;
    box-shadow: 0 2px 10px rgba(74, 66, 55, 0.05);
}

.chat-msg {
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}

.chat-label {
    font-family: 'Jost', sans-serif;
    font-size: 0.6rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
}

.chat-bubble {
    display: inline-block;
    padding: 0.7rem 1.1rem;
    border-radius: 6px;
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.02rem;
    line-height: 1.6;
    max-width: 90%;
}

.user-label  { color: #6f8298; }
.bot-label   { color: var(--accent-2); }

.user-bubble { background: rgba(159,179,200,0.16); border: 1px solid rgba(159,179,200,0.35); align-self: flex-end; }
.bot-bubble  { background: rgba(196,160,119,0.12); border: 1px solid rgba(196,160,119,0.3);  align-self: flex-start; }

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Transcript box ── */
.transcript-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 1.25rem;
    font-family: 'Cormorant Garamond', serif;
    font-size: 1rem;
    line-height: 1.8;
    max-height: 300px;
    overflow-y: auto;
    color: var(--text-muted);
    white-space: pre-wrap;
    word-break: break-word;
}

/* ── Stale Streamlit elements ── */
.stProgress > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: var(--text) !important; }
label { color: var(--text-muted) !important; font-size: 0.8rem !important; }

/* scrollbar */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.8rem">Gistly</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)
    source = st.text_input("YouTube URL or File Path", placeholder="https://youtube.com/watch?v=... or /path/to/file.mp4")

    language = st.selectbox("Language", ["english", "hinglish"], index=0)

    run_btn = st.button("⚡  Analyse", use_container_width=True)

    st.markdown("<div style='text-align:center;font-size:0.75rem;color:var(--text-muted);margin:0.35rem 0;'>— or explore instantly —</div>", unsafe_allow_html=True)
    demo_btn = st.button("🎯  Load Demo Meeting", use_container_width=True, help="Load pre-analyzed backend architecture meeting instantly without external API keys")

    status_placeholder = st.empty()

    def render_sidebar_status():
        with status_placeholder.container():
            st.markdown("---")
            st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
            for step, icon, label in [
                ("audio",      "🔊", "Audio Processing"),
                ("transcript", "📝", "Transcription"),
                ("title",      "🏷️", "Title Generation"),
                ("summary",    "📋", "Summarisation"),
                ("extract",    "🔍", "Extraction"),
                ("rag",        "🧠", "RAG Engine"),
            ]:
                render_step_bar(label, step, icon)

    if st.session_state.pipeline_done or st.session_state.processing:
        render_sidebar_status()

    st.markdown("---")
    with st.expander("🩺 System Diagnostics", expanded=False):
        health = get_system_health()
        status_icon = "🟢" if health["status"] == "Healthy" else "🟡"
        st.markdown(f"**Engine Status:** {status_icon} `{health['status']}`")
        st.caption(f"Python: `{health['runtime']['python_version']}`")
        st.caption(f"FFmpeg: {'✅ Found' if health['runtime']['ffmpeg_available'] else '❌ Not Found'}")
        gemini_active = health["apis"].get("gemini_configured", False)
        mistral_active = health["apis"].get("mistral_configured", False)
        if gemini_active:
            llm_label = f"✅ Gemini ({health['apis'].get('gemini_model', '1.5-flash')})"
        elif mistral_active:
            llm_label = "✅ Mistral (mistral-small)"
        else:
            llm_label = "⚠️ Offline / Demo Mode"
        st.caption(f"LLM Engine: `{llm_label}`")
        st.caption(f"Workflow: `LangGraph Stateful Engine`")
        st.caption(f"Embeddings: `{'Gemini Embeddings' if health['apis'].get('embedding_provider') == 'gemini' and not health['apis'].get('local_embeddings') else 'Local (all-MiniLM-L6-v2)'}`")
        st.caption(f"Whisper Model: `{health['apis']['whisper_model']}`")
        st.caption(f"Sarvam STT: {'✅ Active' if health['apis']['sarvam_configured'] else '⚠️ Not Set (Whisper Only)'}")
        if health["apis"].get("langfuse_configured"):
            st.caption("Observability: `✅ Langfuse Active`")
        st.caption(f"Limits: max `{health['limits']['max_upload_size_mb']} MB` / `{health['limits']['max_audio_duration_minutes']:.0f} min`")

# ─── Demo Meeting Trigger ────────────────────────────────────────────────────────
if demo_btn:
    st.session_state.processing = False
    st.session_state.pipeline_done = True
    st.session_state.chat_history = []
    with st.spinner("Loading pre-analyzed demo meeting..."):
        demo_data = load_demo_meeting()
        st.session_state.result = demo_data
        st.session_state.memory = SessionConversationMemory(session_id=demo_data["session_id"])
        st.session_state.pipeline_steps = {
            "audio": "done",
            "transcript": "done",
            "title": "done",
            "summary": "done",
            "extract": "done",
            "rag": "done",
        }
    st.success("🎯 Loaded Demo Meeting: Backend Platform Migration & Cloud Infrastructure Sync")
    time.sleep(0.3)
    st.rerun()

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">Gistly</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    if not source.strip():
        st.error("Please enter a YouTube URL or file path.")
    else:
        # Resource Guardrails
        clean_src = source.strip()
        if os.path.exists(clean_src) and os.path.isfile(clean_src):
            is_valid_sz, sz_err = validate_file_size(os.path.getsize(clean_src))
            if not is_valid_sz:
                st.error(f"⚠️ {sz_err}")
                st.stop()

        if language.lower() in ("hinglish", "hindi") and not SARVAM_API_KEY:
            st.warning("⚠️ SARVAM_API_KEY is not configured in .env. Falling back to Whisper English STT engine.")
            language = "english"

        st.session_state.processing = True
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.memory = None
        st.session_state.pipeline_steps = {
            "audio": "pending",
            "transcript": "pending",
            "title": "pending",
            "summary": "pending",
            "extract": "pending",
            "rag": "pending",
        }
        render_sidebar_status()

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state
            render_sidebar_status()

        chunks = []
        session_id = uuid.uuid4().hex[:8]
        st.session_state.memory = SessionConversationMemory(session_id=session_id)
        try:
            with progress_placeholder.container():
                st.info(f"⚙️ Pipeline running (Session: {session_id}) — see sidebar for live status…")

            update_step("audio", "active")
            chunks = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            transcript, segments = transcribe_all_with_segments(chunks, language)
            update_step("transcript", "done")

            if not transcript or not transcript.strip():
                raise ValueError("Transcription yielded no audible speech or text in the provided source. Pipeline stopped cleanly.")

            update_step("title", "active")
            try:
                title = generate_title(transcript)
            except Exception as e:
                logger.warning("Title generation fallback triggered: %s", e)
                title = "Untitled Meeting"
            update_step("title", "done")

            update_step("summary", "active")
            try:
                summary = summarize(transcript)
            except Exception as e:
                logger.warning("Summarization fallback triggered: %s", e)
                summary = f"Summary generation unavailable: {e}"
            update_step("summary", "done")

            update_step("extract", "active")
            try:
                intel = extract_meeting_intelligence(transcript)
                action_items_structured = intel.get("action_items", [])
                decisions_structured = intel.get("key_decisions", [])
                questions_structured = intel.get("open_questions", [])

                action_items_str = format_action_items(action_items_structured)
                decisions_str = format_key_decisions(decisions_structured)
                questions_str = format_open_questions(questions_structured)
            except Exception as e:
                logger.warning("Meeting intelligence extraction fallback triggered: %s", e)
                action_items_structured = []
                decisions_structured = []
                questions_structured = []
                action_items_str = "Action item extraction unavailable."
                decisions_str = "Key decisions extraction unavailable."
                questions_str = "Open questions extraction unavailable."
            update_step("extract", "done")

            update_step("rag", "active")
            vector_store = None
            try:
                vector_store = build_vector_store(transcript, session_id=session_id, source=source, segments=segments)
                rag_chain = build_rag_chain(transcript, session_id=session_id, source=source, segments=segments)
            except Exception as e:
                logger.warning("RAG indexing initialization fallback triggered: %s", e)
                rag_chain = None
            update_step("rag", "done")

            st.session_state.result = {
                "session_id": session_id,
                "title": title,
                "transcript": transcript,
                "segments": segments,
                "summary": summary,
                "action_items": action_items_str,
                "key_decisions": decisions_str,
                "open_questions": questions_str,
                "action_items_structured": action_items_structured,
                "key_decisions_structured": decisions_structured,
                "open_questions_structured": questions_structured,
                "rag_chain": rag_chain,
                "vector_store": vector_store,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            render_sidebar_status()
            logger.error("Pipeline failure: %s", e, exc_info=True)
            progress_placeholder.error(f"❌ Analysis stopped cleanly: {e}")
        finally:
            st.session_state.processing = False
            cleanup_temp_files(chunks)

# ── Results & Meeting Intelligence Workspace ─────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result
    session_id = r.get("session_id", "default")

    # Session-isolated action item status storage
    if "action_statuses" not in st.session_state:
        st.session_state.action_statuses = {}
    if session_id not in st.session_state.action_statuses:
        st.session_state.action_statuses[session_id] = {}

    actions_list = r.get("action_items_structured", [])
    decisions_list = r.get("key_decisions_structured", [])
    questions_list = r.get("open_questions_structured", [])

    # Initialize status values for active session
    for idx, item in enumerate(actions_list):
        if idx not in st.session_state.action_statuses[session_id]:
            item_st = item.get("status") if isinstance(item, dict) else getattr(item, "status", "Open")
            st.session_state.action_statuses[session_id][idx] = item_st or "Open"

    sess_statuses = st.session_state.action_statuses[session_id]

    # Calculate dynamic overview metrics
    total_decisions = len(decisions_list)
    total_actions = len(actions_list)
    total_questions = len(questions_list)

    count_open = sum(1 for idx in range(total_actions) if sess_statuses.get(idx, "Open") == "Open")
    count_in_progress = sum(1 for idx in range(total_actions) if sess_statuses.get(idx, "Open") == "In Progress")
    count_done = sum(1 for idx in range(total_actions) if sess_statuses.get(idx, "Open") == "Done")

    # 1. Session Title & Workspace Overview Banner
    title_escaped = html.escape(str(r.get('title', '')))
    st.markdown(f"""
    <div class="card" style="margin-bottom:1rem;">
        <div class="card-title">📌 Meeting Intelligence Workspace</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.2rem;">
            {title_escaped}
        </div>
        <div style="font-size:0.8rem;color:var(--text-muted);font-family:'Jost',sans-serif;letter-spacing:0.12em;text-transform:uppercase;">
            Session ID: {html.escape(session_id)}
        </div>
    </div>""", unsafe_allow_html=True)

    # 2. Dynamic Overview Metrics Bar
    progress_str = f'<span style="color:#9c6c2e;">{count_open} Open</span> · <span style="color:#4e657c;">{count_in_progress} Active</span> · <span style="color:#3d6e2e;">{count_done} Done</span>' if total_actions > 0 else '<span style="color:var(--text-muted);">None</span>'
    st.markdown(f"""
    <div class="workspace-metrics">
        <div class="metric-box">
            <div class="metric-number">{total_decisions}</div>
            <div class="metric-label">Confirmed Decisions</div>
        </div>
        <div class="metric-box">
            <div class="metric-number">{total_actions}</div>
            <div class="metric-label">Action Items</div>
        </div>
        <div class="metric-box">
            <div class="metric-number">{total_questions}</div>
            <div class="metric-label">Open Dilemmas</div>
        </div>
        <div class="metric-box">
            <div class="metric-number" style="font-size:1.15rem;padding-top:0.35rem;">
                {progress_str}
            </div>
            <div class="metric-label">Action Execution</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # 3. Top row: Summary + Full Transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        summary_escaped = html.escape(str(r.get('summary', '')))
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📋 Executive Summary</div>
            <div class="card-content">{summary_escaped}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript (Timestamped)", expanded=False):
            segments = r.get("segments")
            if segments and isinstance(segments, list) and any(s.start_time > 0 or s.end_time > 0 for s in segments):
                seg_lines = []
                for s in segments:
                    spk = f"<strong>{html.escape(s.speaker)}:</strong> " if getattr(s, 'speaker', None) else ""
                    seg_lines.append(f"<div style='margin-bottom:8px;'><span style='color:var(--accent-2);font-size:0.8rem;font-family:monospace;font-weight:600;'>[{s.time_range}]</span> {spk}{html.escape(s.text)}</div>")
                st.markdown(f'<div class="transcript-box">{"".join(seg_lines)}</div>', unsafe_allow_html=True)
            else:
                transcript_escaped = html.escape(str(r.get('transcript', '')))
                st.markdown(f'<div class="transcript-box">{transcript_escaped}</div>', unsafe_allow_html=True)

    # 4. Action Items Register
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.25rem;font-weight:700;margin-top:1.5rem;margin-bottom:0.25rem;">✅ Action Items Register</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.85rem;">Concrete commitments extracted with owner, deadline, and supporting evidence. Update execution status as tasks progress.</div>', unsafe_allow_html=True)

    if not actions_list:
        st.markdown('<div class="empty-notice">No action items identified from this meeting.</div>', unsafe_allow_html=True)
    else:
        for idx, item in enumerate(actions_list):
            if isinstance(item, dict):
                task_name = item.get("task", "Unnamed Task")
                owner_val = item.get("owner") or "Not specified"
                deadline_val = item.get("deadline") or "Not specified"
                evidence_val = item.get("evidence")
                timestamp_val = item.get("timestamp")
            else:
                task_name = getattr(item, "task", "Unnamed Task")
                owner_val = getattr(item, "owner", None) or "Not specified"
                deadline_val = getattr(item, "deadline", None) or "Not specified"
                evidence_val = getattr(item, "evidence", None)
                timestamp_val = getattr(item, "timestamp", None)

            curr_status = sess_statuses.get(idx, "Open")
            status_cls = "status-pill-open" if curr_status == "Open" else ("status-pill-inprogress" if curr_status == "In Progress" else "status-pill-done")

            with st.container():
                col_act1, col_act2 = st.columns([4, 1.2])
                with col_act1:
                    ts_badge = f'<span class="pill pill-time">⏱️ {html.escape(str(timestamp_val))}</span>' if timestamp_val else ''
                    clean_ev = re.sub(r"<[^>]+>", "", str(evidence_val)).strip() if evidence_val else None
                    ev_box = f'<div class="evidence-quote-box">💬 <strong>Transcript Evidence:</strong> "{html.escape(clean_ev)}"</div>' if clean_ev else ''
                    card_html = (
                        f'<div class="intel-card" style="margin-bottom:0.35rem;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
                        f'<div class="intel-title">{idx + 1}. {html.escape(str(task_name))}</div>'
                        f'<span class="{status_cls}">{curr_status}</span>'
                        f'</div>'
                        f'<div class="meta-row">'
                        f'<span class="pill pill-owner">👤 Owner: {html.escape(str(owner_val))}</span>'
                        f'<span class="pill pill-due">📅 Due: {html.escape(str(deadline_val))}</span>'
                        f'{ts_badge}'
                        f'</div>'
                        f'{ev_box}'
                        f'</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)
                with col_act2:
                    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
                    new_st = st.selectbox(
                        "Status",
                        options=["Open", "In Progress", "Done"],
                        index=["Open", "In Progress", "Done"].index(curr_status) if curr_status in ["Open", "In Progress", "Done"] else 0,
                        key=f"status_select_{session_id}_{idx}",
                        label_visibility="collapsed",
                    )
                    if new_st != curr_status:
                        st.session_state.action_statuses[session_id][idx] = new_st
                        st.rerun()

                # Phase 8: Quick Action Buttons for each Action Item
                col_btn1, col_btn2, col_btn3 = st.columns([1.2, 1.2, 1.2])
                with col_btn1:
                    if st.button("📌 Create Task", key=f"create_task_btn_{session_id}_{idx}", help="Convert to task with provenance"):
                        res = DEFAULT_TOOL_REGISTRY.execute_tool("create_task", {
                            "title": task_name,
                            "owner": owner_val if owner_val != "Not specified" else None,
                            "deadline": deadline_val if deadline_val != "Not specified" else None,
                            "source_session_id": session_id,
                            "source_evidence_ids": [evidence_val] if evidence_val else [],
                            "source_timestamp": timestamp_val,
                        })
                        if res.success:
                            st.toast(f"✅ Created Task {res.resource_id}!")
                            st.rerun()
                with col_btn2:
                    with st.popover("📅 Schedule Event"):
                        st.caption(f"Schedule meeting for: {task_name}")
                        start_dt = st.text_input("Start Time (e.g. 2026-10-15 14:00)", key=f"cal_start_{session_id}_{idx}")
                        end_dt = st.text_input("End Time (e.g. 2026-10-15 15:00)", key=f"cal_end_{session_id}_{idx}")
                        participants_str = st.text_input("Participants (comma-separated emails)", value="team@example.com", key=f"cal_parts_{session_id}_{idx}")
                        if st.button("Propose Event", key=f"propose_event_btn_{session_id}_{idx}"):
                            parts = [p.strip() for p in participants_str.split(",") if p.strip()]
                            stage_res = DEFAULT_TOOL_REGISTRY.execute_tool("create_calendar_event", {
                                "title": task_name,
                                "start_time": start_dt,
                                "end_time": end_dt,
                                "participants": parts,
                                "source_session_id": session_id,
                                "source_evidence_ids": [evidence_val] if evidence_val else [],
                                "source_timestamp": timestamp_val,
                            })
                            if stage_res.success:
                                st.rerun()
                            else:
                                st.error(stage_res.message)
                with col_btn3:
                    with st.popover("✉️ Draft Email"):
                        st.caption(f"Draft email for: {task_name}")
                        recip = st.text_input("Recipient Email", key=f"email_recip_{session_id}_{idx}")
                        email_subj = st.text_input("Subject", value=f"Action Item: {task_name}", key=f"email_subj_{session_id}_{idx}")
                        email_body = st.text_area("Body", value=f"Hi,\n\nFollowing up on our discussion regarding:\n• {task_name}\n• Due: {deadline_val}\n\nEvidence: {evidence_val or 'From sync'}", key=f"email_body_{session_id}_{idx}")
                        if st.button("Save Draft", key=f"save_draft_btn_{session_id}_{idx}"):
                            d_res = DEFAULT_TOOL_REGISTRY.execute_tool("draft_email", {
                                "recipient": recip,
                                "subject": email_subj,
                                "body": email_body,
                                "source_session_id": session_id,
                                "source_evidence_ids": [evidence_val] if evidence_val else [],
                                "source_timestamp": timestamp_val,
                            })
                            if d_res.success:
                                st.toast("✅ Email draft saved!")
                                st.rerun()
                            else:
                                st.error(d_res.message)

        # Phase 8: Meeting Action Center & Confirmation Gate
        pending_actions = DEFAULT_TOOL_REGISTRY.confirmation_mgr.get_pending_actions(session_id)
        if pending_actions:
            st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.15rem;font-weight:700;margin-top:1.2rem;color:#b25e2e;">⚠️ Pending Action Confirmations</div>', unsafe_allow_html=True)
            for pending in pending_actions:
                with st.container():
                    st.warning(f"**Proposed {pending.tool_name.replace('_', ' ').title()}** (Risk: {pending.risk_level.upper()})\n\n{pending.preview_summary}")
                    c_col1, c_col2 = st.columns([1, 1])
                    if c_col1.button("✅ Confirm & Execute", key=f"conf_btn_{pending.action_id}"):
                        res = DEFAULT_TOOL_REGISTRY.confirm_action(pending.action_id, session_id=session_id)
                        if res.success:
                            st.toast(f"✅ Action {pending.tool_name} executed successfully!")
                        else:
                            st.error(res.message)
                        st.rerun()
                    if c_col2.button("❌ Cancel Action", key=f"rej_btn_{pending.action_id}"):
                        DEFAULT_TOOL_REGISTRY.reject_action(pending.action_id, session_id=session_id)
                        st.toast("Action cancelled.")
                        st.rerun()

        sess_tasks = DEFAULT_TOOL_REGISTRY.task_tool.list_tasks(session_id).metadata.get("tasks", [])
        sess_events = DEFAULT_TOOL_REGISTRY.calendar_tool.list_calendar_events(session_id).metadata.get("events", [])
        sess_drafts = DEFAULT_TOOL_REGISTRY.email_tool.list_drafts(session_id).metadata.get("drafts", [])
        if sess_tasks or sess_events or sess_drafts:
            with st.expander(f"🛠️ Active Meeting Actions Center ({len(sess_tasks)} Tasks, {len(sess_events)} Events, {len(sess_drafts)} Drafts)", expanded=False):
                if sess_tasks:
                    st.markdown("**Tasks Created:**")
                    for t in sess_tasks:
                        st.markdown(f"• `{t['task_id']}`: **{html.escape(t['title'])}** (Owner: {t.get('owner') or 'Unassigned'}, Due: {t.get('deadline') or 'Not specified'})")
                if sess_events:
                    st.markdown("**Scheduled Events:**")
                    for e in sess_events:
                        st.markdown(f"• `{e['event_id']}`: **{html.escape(e['title'])}** ({e['start_time']} - {e['end_time']})")
                if sess_drafts:
                    st.markdown("**Email Drafts:**")
                    for d in sess_drafts:
                        st.markdown(f"• `{d['draft_id']}`: To `{d['recipient']}` - *{html.escape(d['subject'])}*")


    # 5. Key Decisions & Open Questions Row
    col_dec, col_q = st.columns(2, gap="medium")

    with col_dec:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.25rem;font-weight:700;margin-top:1.5rem;margin-bottom:0.25rem;">🔑 Key Decisions Register</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.85rem;">Confirmed decisions agreed upon during the discussion.</div>', unsafe_allow_html=True)

        if not decisions_list:
            st.markdown('<div class="empty-notice">No finalized decisions recorded.</div>', unsafe_allow_html=True)
        else:
            for idx, dec in enumerate(decisions_list):
                if isinstance(dec, dict):
                    d_text = dec.get("decision") or dec.get("text") or str(dec)
                    d_ev = dec.get("evidence")
                    d_ts = dec.get("timestamp")
                else:
                    d_text = getattr(dec, "decision", str(dec))
                    d_ev = getattr(dec, "evidence", None)
                    d_ts = getattr(dec, "timestamp", None)

                ts_badge = f'<span class="pill pill-time">⏱️ {html.escape(str(d_ts))}</span>' if d_ts else ''
                clean_d_ev = re.sub(r"<[^>]+>", "", str(d_ev)).strip() if d_ev else None
                ev_box = f'<div class="evidence-quote-box">💬 <strong>Transcript Evidence:</strong> "{html.escape(clean_d_ev)}"</div>' if clean_d_ev else ''
                card_html = (
                    f'<div class="intel-card">'
                    f'<div class="intel-title" style="color:var(--success);">✓ {idx + 1}. {html.escape(str(d_text))}</div>'
                    f'<div class="meta-row">{ts_badge}</div>'
                    f'{ev_box}'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

    with col_q:
        st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.25rem;font-weight:700;margin-top:1.5rem;margin-bottom:0.25rem;">❓ Open Questions & Dilemmas</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.85rem;">Open questions, unresolved dilemmas, and topics requiring follow-up.</div>', unsafe_allow_html=True)

        if not questions_list:
            st.markdown('<div class="empty-notice">No unresolved questions identified.</div>', unsafe_allow_html=True)
        else:
            for idx, q in enumerate(questions_list):
                if isinstance(q, dict):
                    q_text = q.get("question") or q.get("text") or str(q)
                    q_ev = q.get("evidence")
                    q_ts = q.get("timestamp")
                else:
                    q_text = getattr(q, "question", str(q))
                    q_ev = getattr(q, "evidence", None)
                    q_ts = getattr(q, "timestamp", None)

                ts_badge = f'<span class="pill pill-time">⏱️ {html.escape(str(q_ts))}</span>' if q_ts else ''
                clean_q_ev = re.sub(r"<[^>]+>", "", str(q_ev)).strip() if q_ev else None
                ev_box = f'<div class="evidence-quote-box">💬 <strong>Transcript Evidence:</strong> "{html.escape(clean_q_ev)}"</div>' if clean_q_ev else ''
                card_html = (
                    f'<div class="intel-card">'
                    f'<div class="intel-title" style="color:#cf9d5c;">❓ {idx + 1}. {html.escape(str(q_text))}</div>'
                    f'<div class="meta-row">{ts_badge}</div>'
                    f'{ev_box}'
                    f'</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:0.5rem">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    def _execute_chat_turn(query_text: str):
        rag_c = r.get("rag_chain")
        vs = r.get("vector_store")
        evidence = []
        audio_b64 = None
        sid = r.get("session_id", "default")
        q_lower = query_text.lower().strip()

        # LangGraph Stateful Assistant Workflow (Intent Detection -> Retrieval -> Grounding -> Actions)
        actions_list_active = r.get("action_items_structured", [])

        if "memory" not in st.session_state or st.session_state.memory is None:
            st.session_state.memory = SessionConversationMemory(session_id=sid)

        with st.spinner("Processing request with LangGraph workflow..."):
            workflow_res = run_assistant_workflow(
                query=query_text,
                session_id=sid,
                history=st.session_state.memory.get_recent_turns(),
                vector_store=vs,
                rag_chain=rag_c,
                tool_registry=DEFAULT_TOOL_REGISTRY,
                action_items=actions_list_active,
            )
            answer = workflow_res.get("answer", "")
            evidence = workflow_res.get("evidence", [])
            resolved_query = workflow_res.get("resolved_query", query_text)

            # Guard when vector store is missing for question inquiries
            if not vs and not rag_c and workflow_res.get("intent") == "question":
                answer = "RAG chat is unavailable for this session because vector indexing was bypassed or failed."

            # Record turn in session memory if it was a question or conversation
            if workflow_res.get("intent") in ("question", "clarify"):
                ev_ids = [ev.evidence_id for ev in evidence] if evidence else []
                st.session_state.memory.add_turn(
                    user_message=query_text,
                    assistant_message=answer,
                    evidence_ids=ev_ids,
                    resolved_query=resolved_query,
                )

        if st.session_state.get("enable_voice_tts", True) and answer:
            try:
                audio_bytes = synthesize_answer(answer, language=language)
                if audio_bytes:
                    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as tts_err:
                logger.warning("Voice TTS synthesis skipped: %s", tts_err)

        st.session_state.chat_history.append({"role": "user", "content": query_text})
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": answer,
            "evidence": evidence,
            "audio_b64": audio_b64,
        })
        # Reset voice review state
        st.session_state["recognized_voice_query"] = ""
        st.session_state["last_processed_voice_id"] = None
        st.rerun()

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            content_escaped = html.escape(str(msg.get('content', ''))).replace("\n", "<br>")
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{content_escaped}</div>
                </div>"""
            else:
                ev_html = ""
                ev_items = msg.get("evidence", [])
                if ev_items:
                    ev_badges = []
                    for ev in ev_items:
                        ev_id = html.escape(str(getattr(ev, 'evidence_id', 'E')))
                        tr = html.escape(str(getattr(ev, 'time_range', '')))
                        chunk_i = getattr(ev, 'chunk_index', 0)
                        ev_badges.append(f"<span style='background:rgba(159,179,200,0.18);border:1px solid #9fb3c8;border-radius:4px;padding:2px 6px;font-size:0.75rem;margin-right:6px;'>[{ev_id}] {tr} (Chunk #{chunk_i})</span>")
                    ev_html = f"<div style='margin-top:8px;font-size:0.8rem;color:#7a7266;'><strong>Cited Evidence:</strong> {' '.join(ev_badges)}</div>"

                audio_html = ""
                if msg.get("audio_b64"):
                    audio_html = f"""<div style='margin-top:10px;'>
                        <span style='font-size:0.75rem;color:#7a7266;font-family:sans-serif;'>🔊 Spoken Answer:</span>
                        <audio controls style='height:30px;width:100%;margin-top:4px;' src='data:audio/mp3;base64,{msg["audio_b64"]}'></audio>
                    </div>"""

                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">🤖 Assistant</span>
                    <div class="chat-bubble bot-bubble">{content_escaped}{ev_html}{audio_html}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript via text or voice recording</div>
        </div>""", unsafe_allow_html=True)

    col_input_opt1, col_input_opt2 = st.columns([4, 2])
    with col_input_opt2:
        st.session_state["enable_voice_tts"] = st.checkbox("🔊 Spoken Answers (TTS)", value=st.session_state.get("enable_voice_tts", True))

    # 1. Text input form for Enter-to-submit
    with st.form(key="chat_form", clear_on_submit=True):
        chat_col1, chat_col2 = st.columns([5, 1], gap="small")
        with chat_col1:
            user_input = st.text_input("Your question", placeholder="Type a question or use the microphone below...", label_visibility="collapsed")
        with chat_col2:
            send_btn = st.form_submit_button("Send →", use_container_width=True)

    if send_btn and user_input.strip():
        _execute_chat_turn(user_input.strip())

    # 2. Voice Input UI (Record question -> Transcribe -> Review/Edit -> Submit)
    with st.expander("🎤 Ask with Voice (Microphone)", expanded=False):
        st.markdown("<span style='font-size:0.85rem;color:var(--text-muted);'>Record a question with your microphone. You can review and edit the transcribed question before sending.</span>", unsafe_allow_html=True)
        voice_audio = st.audio_input("Record your question", key="mic_recorder")
        if voice_audio is not None:
            v_bytes = voice_audio.getvalue() if hasattr(voice_audio, "getvalue") else voice_audio.read()
            v_id = f"voice_{len(v_bytes)}_{hash(v_bytes[:64]) if len(v_bytes)>=64 else len(v_bytes)}"
            if st.session_state.get("last_processed_voice_id") != v_id:
                with st.spinner("Transcribing your question..."):
                    stt_res = transcribe_voice_input_safe(v_bytes, language=language)
                    if stt_res["error"]:
                        st.warning(f"Voice note: {stt_res['error']}")
                        st.session_state["recognized_voice_query"] = ""
                    else:
                        st.session_state["recognized_voice_query"] = stt_res["text"]
                    st.session_state["last_processed_voice_id"] = v_id

            if st.session_state.get("recognized_voice_query"):
                st.markdown("<strong style='font-size:0.9rem;'>Recognized Question (review / edit before asking):</strong>", unsafe_allow_html=True)
                edited_voice_query = st.text_input(
                    "Recognized question",
                    value=st.session_state.get("recognized_voice_query", ""),
                    key="voice_query_edit_box",
                    label_visibility="collapsed",
                )
                col_v1, col_v2 = st.columns([2, 4])
                with col_v1:
                    submit_voice_btn = st.button("Ask Voice Question →", key="btn_submit_voice", type="primary")
                with col_v2:
                    if st.button("Discard Recording", key="btn_discard_voice"):
                        st.session_state["recognized_voice_query"] = ""
                        st.session_state["last_processed_voice_id"] = None
                        st.rerun()

                if submit_voice_btn and edited_voice_query.strip():
                    _execute_chat_turn(edited_voice_query.strip())

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            if "memory" in st.session_state and st.session_state.memory is not None:
                st.session_state.memory.clear()
            st.session_state["recognized_voice_query"] = ""
            st.session_state["last_processed_voice_id"] = None
            st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="font-size:4rem;margin-bottom:1rem">🎬</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Ready to Analyse
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:380px;line-height:1.7">
            Paste a YouTube URL or local file path in the sidebar, choose your language, and hit <strong>Analyse</strong> to get started.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Transcription</span>
            <span class="badge badge-cyan">Summarisation</span>
            <span class="badge badge-green">RAG Chat</span>
        </div>
    </div>""", unsafe_allow_html=True)