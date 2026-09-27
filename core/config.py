"""
RecallAI Central Configuration & System Health Diagnostic Module.
Single source of truth for:
- Environment variable parsing & safe defaults
- Resource limits & guardrails (upload size, audio duration, transcript length)
- Secret masking & sanitization
- Diagnostic system health checks
- Storage hygiene & temporary file garbage collection
"""

import os
import sys
import time
import shutil
import platform
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Load .env file safely at module import
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Core API Keys & Engine Identifiers
# ─────────────────────────────────────────────────────────────────────────────
MISTRAL_API_KEY: Optional[str] = os.getenv("MISTRAL_API_KEY")
SARVAM_API_KEY: Optional[str] = os.getenv("SARVAM_API_KEY")

# Gemini & Modern LLM Settings
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_FALLBACK_MODEL: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "auto")

# Modern Embeddings Configuration
EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")
LOCAL_EMBEDDINGS: bool = os.getenv("LOCAL_EMBEDDINGS", "true").lower() in ("1", "true", "yes")
GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
LOCAL_EMBEDDING_MODEL: str = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)

# Transcription Configuration
TRANSCRIPTION_PROVIDER: str = os.getenv("TRANSCRIPTION_PROVIDER", "whisper")
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
SARVAM_STT_MODEL: str = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

# Observability Configuration (Langfuse)
LANGFUSE_ENABLED: bool = os.getenv("LANGFUSE_ENABLED", "false").lower() in ("1", "true", "yes")
LANGFUSE_PUBLIC_KEY: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

# FastAPI Backend Configuration
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))
CORS_ORIGINS: list = [
    orig.strip()
    for orig in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if orig.strip()
]

# ─────────────────────────────────────────────────────────────────────────────
# Resource Limits & Guardrails
# ─────────────────────────────────────────────────────────────────────────────
def _get_int_env(key: str, default: int) -> int:
    try:
        val = os.getenv(key)
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def _get_float_env(key: str, default: float) -> float:
    try:
        val = os.getenv(key)
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

MAX_UPLOAD_SIZE_MB: int = _get_int_env("MAX_UPLOAD_SIZE_MB", 100)
MAX_AUDIO_DURATION_MINUTES: float = _get_float_env("MAX_AUDIO_DURATION_MINUTES", 90.0)
MAX_TRANSCRIPT_CHARS: int = _get_int_env("MAX_TRANSCRIPT_CHARS", 250000)

# ─────────────────────────────────────────────────────────────────────────────
# Storage & Persistence Paths
# ─────────────────────────────────────────────────────────────────────────────
DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloades")
CHROMA_DIR: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "vector_db")
AUDIT_LOG_PATH: str = os.getenv("AUDIT_LOG_PATH", "action_audit.jsonl")
YOUTUBE_COOKIE_FILE: Optional[str] = os.getenv("YOUTUBE_COOKIE_FILE", "cookies.txt")

# Ensure required runtime directories exist
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

# Application Mode
DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")


# ─────────────────────────────────────────────────────────────────────────────
# Secret Masking & Sanitization
# ─────────────────────────────────────────────────────────────────────────────
def mask_secret(secret: Optional[str]) -> str:
    """Safely mask API tokens and secrets for diagnostics and logs."""
    if not secret:
        return "None"
    s = str(secret).strip()
    if len(s) <= 8:
        return "***"
    return f"{s[:4]}...{s[-4:]}"


# ─────────────────────────────────────────────────────────────────────────────
# Validation Guardrails
# ─────────────────────────────────────────────────────────────────────────────
def validate_file_size(size_bytes: int) -> Tuple[bool, Optional[str]]:
    """Validate uploaded file size against MAX_UPLOAD_SIZE_MB."""
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        size_mb = size_bytes / (1024 * 1024)
        return False, (
            f"File size ({size_mb:.1f} MB) exceeds maximum allowed upload size "
            f"of {MAX_UPLOAD_SIZE_MB} MB. Please upload a smaller recording."
        )
    return True, None


def validate_audio_duration(duration_seconds: float) -> Tuple[bool, Optional[str]]:
    """Validate audio duration against MAX_AUDIO_DURATION_MINUTES."""
    max_sec = MAX_AUDIO_DURATION_MINUTES * 60.0
    if duration_seconds > max_sec:
        dur_min = duration_seconds / 60.0
        return False, (
            f"Audio duration ({dur_min:.1f} min) exceeds maximum limit "
            f"of {MAX_AUDIO_DURATION_MINUTES:.0f} minutes. Please trim the recording."
        )
    return True, None


def validate_transcript_length(char_count: int) -> Tuple[bool, Optional[str]]:
    """Validate transcript text length against MAX_TRANSCRIPT_CHARS."""
    if char_count > MAX_TRANSCRIPT_CHARS:
        return False, (
            f"Transcript character count ({char_count:,}) exceeds limit of "
            f"{MAX_TRANSCRIPT_CHARS:,} characters. Downstream extraction will be truncated."
        )
    return True, None


ALLOWED_MEDIA_EXTENSIONS: set = {
    ".wav", ".mp3", ".webm", ".m4a", ".mp4", ".aac", ".ogg", ".flac", ".mov", ".mkv",
}


def validate_media_file_extension(filename: str) -> Tuple[bool, Optional[str]]:
    """Validate uploaded audio/video file extension against supported formats."""
    if not filename or not filename.strip():
        return False, "File name cannot be empty."
    ext = os.path.splitext(filename)[1].lower()
    if not ext or ext not in ALLOWED_MEDIA_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_MEDIA_EXTENSIONS))
        return False, f"Unsupported file extension '{ext}'. Supported formats: {allowed}."
    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# Storage Hygiene: Old Temporary File Cleanup
# ─────────────────────────────────────────────────────────────────────────────
def cleanup_old_temp_files(max_age_hours: float = 2.0) -> int:
    """
    Safely prune intermediate media files in DOWNLOAD_DIR older than max_age_hours.
    Prevents storage exhaustion on persistent container hosts.
    """
    removed_count = 0
    now = time.time()
    max_age_sec = max_age_hours * 3600.0

    if not os.path.exists(DOWNLOAD_DIR):
        return 0

    media_extensions = {".wav", ".mp3", ".webm", ".m4a", ".mp4", ".tmp"}
    for root, _, files in os.walk(DOWNLOAD_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in media_extensions:
                file_path = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(file_path)
                    if (now - mtime) > max_age_sec:
                        os.remove(file_path)
                        removed_count += 1
                except Exception:
                    pass

    return removed_count


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic Health Check
# ─────────────────────────────────────────────────────────────────────────────
def get_system_health() -> Dict[str, Any]:
    """
    Run diagnostic checks on system runtime, dependencies, API readiness,
    and storage paths. Returns structured health report.
    """
    ffmpeg_bin = shutil.which("ffmpeg")
    ffmpeg_ok = ffmpeg_bin is not None

    # Torch & CUDA
    torch_ok = False
    cuda_ok = False
    try:
        import torch
        torch_ok = True
        cuda_ok = torch.cuda.is_available()
    except ImportError:
        pass

    # Directory permissions
    download_writable = os.access(DOWNLOAD_DIR, os.W_OK)
    chroma_writable = os.access(CHROMA_DIR, os.W_OK)

    # API Key availability
    mistral_configured = bool(MISTRAL_API_KEY and not MISTRAL_API_KEY.startswith("mock-") and MISTRAL_API_KEY != "your_mistral_api_key_here")
    gemini_configured = bool(GEMINI_API_KEY and not GEMINI_API_KEY.startswith("mock-") and GEMINI_API_KEY != "your_gemini_api_key_here")
    sarvam_configured = bool(SARVAM_API_KEY and not SARVAM_API_KEY.startswith("mock-") and SARVAM_API_KEY != "your_sarvam_api_key_here")
    langfuse_configured = bool(LANGFUSE_ENABLED and LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)

    # LiveKit Voice configuration
    livekit_url = os.getenv("LIVEKIT_URL", "")
    livekit_key = os.getenv("LIVEKIT_API_KEY", "")
    livekit_secret = os.getenv("LIVEKIT_API_SECRET", "")
    livekit_configured = bool(
        livekit_url
        and livekit_key
        and livekit_secret
        and livekit_key != "your_livekit_api_key_here"
        and not livekit_key.startswith("mock-")
    )

    # Overall system status
    overall_status = "Healthy" if (ffmpeg_ok and download_writable and chroma_writable) else "Degraded"

    return {
        "status": overall_status,
        "runtime": {
            "python_version": platform.python_version(),
            "platform": f"{platform.system()} {platform.release()}",
            "ffmpeg_available": ffmpeg_ok,
            "ffmpeg_path": ffmpeg_bin,
            "torch_available": torch_ok,
            "cuda_available": cuda_ok,
        },
        "apis": {
            "gemini_configured": gemini_configured,
            "gemini_masked": mask_secret(GEMINI_API_KEY) if gemini_configured else "Not Set",
            "gemini_model": GEMINI_MODEL,
            "gemini_fallback_model": GEMINI_FALLBACK_MODEL,
            "llm_provider": LLM_PROVIDER,
            "mistral_configured": mistral_configured,
            "mistral_masked": mask_secret(MISTRAL_API_KEY) if mistral_configured else "Not Set",
            "sarvam_configured": sarvam_configured,
            "sarvam_masked": mask_secret(SARVAM_API_KEY) if sarvam_configured else "Not Set",
            "whisper_model": WHISPER_MODEL,
            "sarvam_model": SARVAM_STT_MODEL,
            "embedding_provider": EMBEDDING_PROVIDER,
            "local_embeddings": LOCAL_EMBEDDINGS,
            "local_embedding_model": LOCAL_EMBEDDING_MODEL,
            "gemini_embedding_model": GEMINI_EMBEDDING_MODEL,
            "transcription_provider": TRANSCRIPTION_PROVIDER,
            "langfuse_enabled": LANGFUSE_ENABLED,
            "langfuse_configured": langfuse_configured,
            "livekit_configured": livekit_configured,
        },
        "storage": {
            "download_dir": DOWNLOAD_DIR,
            "download_writable": download_writable,
            "chroma_dir": CHROMA_DIR,
            "chroma_writable": chroma_writable,
            "audit_log_path": AUDIT_LOG_PATH,
        },
        "limits": {
            "max_upload_size_mb": MAX_UPLOAD_SIZE_MB,
            "max_audio_duration_minutes": MAX_AUDIO_DURATION_MINUTES,
            "max_transcript_chars": MAX_TRANSCRIPT_CHARS,
            "demo_mode": DEMO_MODE,
        },
        "api": {
            "host": API_HOST,
            "port": API_PORT,
            "cors_origins": CORS_ORIGINS,
        }
    }
