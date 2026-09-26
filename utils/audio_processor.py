import os
from pathlib import Path
from typing import Optional, List
import yt_dlp
from pydub import AudioSegment, effects

DOWNLOAD_DIR = "downloades"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def get_youtube_cookie_path() -> Optional[str]:
    """
    Resolve configured YouTube cookie file if present on disk.
    Checks environment / core.config YOUTUBE_COOKIE_FILE (default: 'cookies.txt').
    Searches both current working directory and project root.
    Returns validated absolute file path if file exists, else None.
    Never exposes or logs cookie contents.
    """
    cookie_setting = os.getenv("YOUTUBE_COOKIE_FILE")
    if not cookie_setting:
        try:
            from core.config import YOUTUBE_COOKIE_FILE
            cookie_setting = YOUTUBE_COOKIE_FILE
        except ImportError:
            cookie_setting = "cookies.txt"

    if not cookie_setting:
        return None

    # Check direct path or relative to current working directory
    cand = Path(cookie_setting)
    if cand.is_file():
        return str(cand.resolve())

    # Check relative to project root
    project_root = Path(__file__).resolve().parent.parent
    root_cand = project_root / cookie_setting
    if root_cand.is_file():
        return str(root_cand.resolve())

    return None


def download_youtube_audio(url: str) -> str:
    """
    Download audio from YouTube and extract as 16kHz mono WAV.
    Supports optional Netscape-format cookie file (cookies.txt) for bot-protected videos.
    Does not use live browser cookie extraction to prevent database lock issues on Windows.
    """
    output_path = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": ["-ar", "16000", "-ac", "1"],
        "quiet": True,
        "no_warnings": True,
    }

    cookie_path = get_youtube_cookie_path()
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path
        print(f"[AudioProcessor] Using configured YouTube cookie file: {os.path.basename(cookie_path)}")
    else:
        print("[AudioProcessor] No YouTube cookie file found. Proceeding without authentication cookies.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            raw_filename = ydl.prepare_filename(info)
            wav_path = os.path.splitext(raw_filename)[0] + ".wav"
    except yt_dlp.utils.DownloadError as e:
        err_msg = str(e)
        is_blocked = any(term in err_msg.lower() for term in (
            "sign in to confirm",
            "confirm you're not a bot",
            "bot",
            "sign in",
            "login",
            "429",
            "http error 429",
            "private video",
            "members-only",
        ))
        if is_blocked:
            if cookie_path:
                raise RuntimeError(
                    f"YouTube download was blocked by verification despite using cookie file '{os.path.basename(cookie_path)}'. "
                    "Your cookies may be expired or invalid. Please re-export fresh cookies from your browser into cookies.txt."
                ) from e
            else:
                raise RuntimeError(
                    "YouTube download blocked: YouTube requires bot verification or authentication ('Sign in to confirm you\\'re not a bot'). "
                    "To fix this, export your YouTube cookies in Netscape format (e.g., using a browser extension like 'Get cookies.txt LOCALLY') "
                    "and save them as 'cookies.txt' in the project root, or set YOUTUBE_COOKIE_FILE in your .env file."
                ) from e
        raise RuntimeError(f"YouTube download failed: {err_msg}") from e
    except Exception as e:
        raise RuntimeError(f"YouTube audio extraction failed: {e}") from e

    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"Extracted audio file not found at expected path: {wav_path}")
    if os.path.getsize(wav_path) == 0:
        raise ValueError(f"Downloaded audio file is empty (0 bytes): {wav_path}")

    return wav_path


def convert_to_wav(input_path: str) -> str:
    """
    Convert any audio/video file to 16kHz Mono 16-bit PCM WAV.
    Applies conservative peak volume normalization if headroom is available.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Source file not found: {input_path}")
    if os.path.getsize(input_path) == 0:
        raise ValueError(f"Source audio file is empty (0 bytes): {input_path}")

    try:
        audio = AudioSegment.from_file(input_path)
    except Exception as e:
        raise ValueError(f"Could not decode audio from source '{input_path}': {e}")

    if len(audio) == 0:
        raise ValueError(f"Audio file contains zero duration / no audio data: {input_path}")

    # Standardize to 16kHz Mono 16-bit PCM (optimal for Whisper & Sarvam STT)
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

    # Conservative volume normalization: lift quiet recordings to -0.5 dBFS peak without distortion
    if audio.max_dBFS > -60.0 and audio.max_dBFS < -1.0:
        audio = effects.normalize(audio, headroom=0.5)

    output_path = os.path.splitext(input_path)[0] + "_converted.wav"
    audio.export(output_path, format="wav")
    return output_path


def find_silence_split(audio: AudioSegment, target_ms: int, window_ms: int = 5000, step_ms: int = 100) -> int:
    """
    Find the timestamp with minimum acoustic energy (silence/pause) near target_ms.
    Searches within [target_ms - window_ms, target_ms + window_ms] in step_ms increments.
    Prevents splitting audio mid-word or mid-syllable.
    """
    target_ms = int(target_ms)
    window_ms = int(window_ms)
    step_ms = int(step_ms)
    start_search = max(0, target_ms - window_ms)
    end_search = min(len(audio), target_ms + window_ms)
    if end_search <= start_search:
        return target_ms

    min_rms = float("inf")
    best_split = target_ms

    for t in range(int(start_search), int(end_search), int(step_ms)):
        sample = audio[t : t + 200]
        rms = sample.rms
        if rms < min_rms:
            min_rms = rms
            best_split = t

    return best_split


def chunk_audio(wav_path: str, chunk_minutes: float = 10) -> list:
    """
    Split a WAV audio file into sequential chunks.
    Uses silence-aware boundary detection so cuts occur at natural speech pauses.
    """
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"Audio file not found for chunking: {wav_path}")

    try:
        audio = AudioSegment.from_wav(wav_path)
    except Exception as e:
        raise ValueError(f"Could not read WAV file for chunking '{wav_path}': {e}")

    if len(audio) == 0:
        raise ValueError(f"Audio file has zero duration: {wav_path}")

    chunk_ms = int(chunk_minutes * 60 * 1000)
    chunks = []

    # If shorter than chunk_minutes, export a single chunk
    if len(audio) <= chunk_ms:
        chunk_path = f"{wav_path}_chunk_0.wav"
        audio.export(chunk_path, format="wav")
        chunks.append(chunk_path)
        return chunks

    cursor = 0
    chunk_index = 0

    while cursor < len(audio):
        remaining = len(audio) - cursor

        # If remaining audio fits in one chunk, take the rest
        if remaining <= chunk_ms:
            split_point = len(audio)
        else:
            # Find natural pause near the boundary
            target = cursor + chunk_ms
            split_point = find_silence_split(audio, target, window_ms=5000)

            # Avoid tiny slices (< 1s remaining at the end)
            if len(audio) - split_point < 1000:
                split_point = len(audio)

        slice_seg = audio[cursor:split_point]
        chunk_path = f"{wav_path}_chunk_{chunk_index}.wav"
        slice_seg.export(chunk_path, format="wav")
        chunks.append(chunk_path)

        cursor = split_point
        chunk_index += 1

    return chunks


def cleanup_temp_files(file_paths: list):
    """Safely remove temporary audio chunks without deleting user source files."""
    if not file_paths:
        return
    removed_count = 0
    for path in file_paths:
        try:
            if path and os.path.exists(path):
                os.remove(path)
                removed_count += 1
        except Exception as e:
            print(f"[AudioProcessor] Warning: Failed to remove temporary file {path}: {e}")
    if removed_count > 0:
        print(f"[AudioProcessor] Cleanup complete: {removed_count} temporary file(s) removed.")


def process_input(source: str) -> list:
    """
    Orchestrate input acquisition, audio standardization, and chunking.
    Provides structured logging covering input properties, preprocessing, and chunk metrics.
    Guarantees failure cleanup of intermediate audio files.
    """
    if not source or not str(source).strip():
        raise ValueError("Invalid source: path or URL cannot be empty.")

    clean_source = str(source).strip()
    print(f"\n[AudioProcessor] Input: {clean_source}")

    is_yt = clean_source.startswith("http://") or clean_source.startswith("https://")
    wav_path = None
    try:
        if is_yt:
            print("[AudioProcessor] Detected YouTube URL. Downloading audio...")
            wav_path = download_youtube_audio(clean_source)
        else:
            print("[AudioProcessor] Detected local file. Converting to standardized WAV...")
            wav_path = convert_to_wav(clean_source)

        # Inspect audio properties
        try:
            probe = AudioSegment.from_wav(wav_path)
            duration_sec = len(probe) / 1000.0
            channels = probe.channels
            rate = probe.frame_rate
            dbfs = probe.dBFS
            print(f"[AudioProcessor] Properties: duration={duration_sec:.2f}s, channels={channels}, rate={rate}Hz, dBFS={dbfs:.1f}")
        except Exception as e:
            print(f"[AudioProcessor] Warning: Could not probe audio properties: {e}")
            duration_sec = 0.0

        print("[AudioProcessor] Preprocessing: verified 16kHz mono PCM, peak normalized.")
        print("[AudioProcessor] Chunking audio with silence-aware boundaries...")
        chunks = chunk_audio(wav_path)

        # Calculate individual chunk durations for logging
        chunk_durations = []
        for c in chunks:
            try:
                c_seg = AudioSegment.from_wav(c)
                chunk_durations.append(len(c_seg) / 1000.0)
            except Exception:
                chunk_durations.append(0.0)

        dur_str = ", ".join(f"{d:.1f}s" for d in chunk_durations)
        print(f"[AudioProcessor] Chunking complete: {len(chunks)} chunk(s) created (durations: {dur_str}).")

        # Clean up intermediate master WAV (both converted local WAV and raw YouTube download)
        if wav_path and os.path.exists(wav_path):
            if is_yt or wav_path.endswith("_converted.wav"):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

        return chunks

    except Exception as e:
        # Failure cleanup: remove intermediate downloaded/converted WAV if chunking or probing failed
        if wav_path and os.path.exists(wav_path):
            if is_yt or wav_path.endswith("_converted.wav"):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass
        raise e

