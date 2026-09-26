import os
import re
import requests
import torch
import whisper
from pydub import AudioSegment
from core.retrieval.provenance import TranscriptSegment

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"

_model = None


def get_whisper_model() -> str:
    return os.getenv("WHISPER_MODEL", "small")


def get_sarvam_api_key() -> str:
    return os.getenv("SARVAM_API_KEY")


def get_sarvam_model() -> str:
    return os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")


def load_model():
    """Load and cache the Whisper model in memory (CPU or GPU)."""
    global _model

    if _model is None:
        whisper_model = get_whisper_model()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[Transcriber] Loading Whisper model: '{whisper_model}' on {device.upper()}...")
        _model = whisper.load_model(whisper_model, device=device)
        print("[Transcriber] Whisper model loaded successfully.")
    return _model


def transcribe_chunk_whisper_with_segments(
    chunk_path: str,
    language: str = "english",
    base_offset_seconds: float = 0.0,
    start_segment_id: int = 0,
) -> tuple:
    """
    Transcribe one audio chunk with Whisper and return (text, segments).
    Extracts start/end timestamps from Whisper's result["segments"].
    """
    model = load_model()

    lang_code = "en" if language.lower() == "english" else None
    use_fp16 = torch.cuda.is_available()

    initial_prompt = (
        "This is a transcript of a business meeting, presentation, or technical discussion. "
        "Please transcribe clearly with proper sentence boundaries, capitalization, and punctuation."
    )

    result = model.transcribe(
        chunk_path,
        task="transcribe",
        language=lang_code,
        temperature=0.0,
        condition_on_previous_text=False,
        initial_prompt=initial_prompt,
        fp16=use_fp16,
    )

    text = result.get("text", "").strip()
    segments = []
    seg_id = start_segment_id

    for s in result.get("segments", []):
        s_text = s.get("text", "").strip()
        if not s_text:
            continue
        start_sec = base_offset_seconds + float(s.get("start", 0.0))
        end_sec = base_offset_seconds + float(s.get("end", start_sec))
        segments.append(
            TranscriptSegment(
                segment_id=seg_id,
                text=s_text,
                start_time=start_sec,
                end_time=end_sec,
                source=os.path.basename(chunk_path),
            )
        )
        seg_id += 1

    return text, segments


def transcribe_chunk_whisper(chunk_path: str, language: str = "english") -> str:
    """
    Transcribe one audio chunk with Whisper using optimized parameters:
    - Explicit language code to avoid costly language-detection passes.
    - fp16 enabled on CUDA, disabled on CPU (eliminating UserWarnings).
    - Greedy temperature (0.0) for deterministic, fast decoding.
    - condition_on_previous_text=False to prevent hallucination / repetition loops.
    - initial_prompt to bias towards proper punctuation and casing.
    """
    text, _ = transcribe_chunk_whisper_with_segments(chunk_path, language=language)
    return text


def _send_to_sarvam(piece_path: str) -> str:
    """Send one ≤30s WAV file to Sarvam and return the English transcript."""
    api_key = get_sarvam_api_key()
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    headers = {"api-subscription-key": api_key}
    sarvam_model = get_sarvam_model()

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": sarvam_model, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\n[Transcriber] [ERROR] Sarvam returned {response.status_code}")
        print(f"[Transcriber] Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "").strip()


def transcribe_chunk_sarvam_with_segments(
    chunk_path: str,
    base_offset_seconds: float = 0.0,
    start_segment_id: int = 0,
) -> tuple:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and return (full_text, segments).
    """
    api_key = get_sarvam_api_key()
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    segments = []
    seg_id = start_segment_id
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start : start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f"  -> [Transcriber] Sarvam piece {i + 1}/{total_pieces} ...")
            piece_text = _send_to_sarvam(piece_path)
            if piece_text:
                full_text += piece_text + " "
                p_start = base_offset_seconds + (start / 1000.0)
                p_end = base_offset_seconds + ((start + len(piece)) / 1000.0)
                segments.append(
                    TranscriptSegment(
                        segment_id=seg_id,
                        text=piece_text,
                        start_time=p_start,
                        end_time=p_end,
                        source=os.path.basename(chunk_path),
                    )
                )
                seg_id += 1
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip(), segments


def transcribe_chunk_sarvam(chunk_path: str) -> str:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    text, _ = transcribe_chunk_sarvam_with_segments(chunk_path)
    return text


def transcribe_chunk_gemini_with_segments(
    chunk_path: str,
    base_offset_seconds: float = 0.0,
    start_segment_id: int = 0,
) -> tuple:
    """
    Transcribe one audio chunk with Google Gemini Multimodal Audio API.
    Returns (text, List[TranscriptSegment]).
    Gracefully falls back to local Whisper if API key is missing or call fails.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key or str(gemini_key).startswith("mock-") or gemini_key == "your_gemini_api_key_here":
        print("[Transcriber] Live Gemini API key not configured; falling back to Whisper.")
        return transcribe_chunk_whisper_with_segments(
            chunk_path,
            base_offset_seconds=base_offset_seconds,
            start_segment_id=start_segment_id,
        )

    try:
        from google import genai
        client = genai.Client(api_key=gemini_key)
        audio_file = client.files.upload(file=chunk_path)
        prompt = (
            "Generate an accurate, verbatim transcript of this audio. "
            "Output each spoken sentence or turn with timestamp in format: [MM:SS - MM:SS] Text"
        )
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            contents=[prompt, audio_file],
        )
        raw_text = response.text or ""

        segments = []
        seg_id = start_segment_id
        pattern = re.compile(r"\[(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\]\s*(.*)")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        for line in lines:
            m = pattern.match(line)
            if m:
                s_str, e_str, seg_txt = m.groups()
                s_parts = [float(x) for x in s_str.split(":")]
                e_parts = [float(x) for x in e_str.split(":")]
                start_sec = base_offset_seconds + (s_parts[0] * 60 + s_parts[1])
                end_sec = base_offset_seconds + (e_parts[0] * 60 + e_parts[1])
                segments.append(
                    TranscriptSegment(
                        segment_id=seg_id,
                        text=seg_txt.strip(),
                        start_time=start_sec,
                        end_time=end_sec,
                        source=os.path.basename(chunk_path),
                    )
                )
                seg_id += 1

        if not segments and raw_text:
            segments.append(
                TranscriptSegment(
                    segment_id=seg_id,
                    text=raw_text.strip(),
                    start_time=base_offset_seconds,
                    end_time=base_offset_seconds + 30.0,
                    source=os.path.basename(chunk_path),
                )
            )

        return raw_text, segments
    except Exception as e:
        print(f"[Transcriber] Gemini transcription failed ({e}); falling back to local Whisper.")
        return transcribe_chunk_whisper_with_segments(
            chunk_path,
            base_offset_seconds=base_offset_seconds,
            start_segment_id=start_segment_id,
        )


def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    Route one chunk to appropriate STT provider (Gemini, Sarvam, or Whisper).
    - hinglish/hindi → Sarvam AI
    - gemini provider → Google Gemini Multimodal Audio
    - english/default → Local OpenAI Whisper
    """
    if language.lower() in ("hinglish", "hindi"):
        return transcribe_chunk_sarvam(chunk_path)

    provider = os.getenv("TRANSCRIPTION_PROVIDER", "whisper").lower()
    if provider == "gemini":
        text, _ = transcribe_chunk_gemini_with_segments(chunk_path)
        return text

    return transcribe_chunk_whisper(chunk_path, language=language)


def clean_transcript(text: str) -> str:
    """
    Deterministic post-processing cleanup:
    - Normalizes multi-spaces and horizontal tabs.
    - Corrects whitespace before punctuation marks.
    - Cleans accidental duplicate commas and semicolons.
    - Normalizes spacing between letters after commas without breaking numbers (e.g. '10,000').
    - Ensures space after sentence-ending punctuation when followed by a capital letter,
      while strictly preserving URLs, decimals (e.g. '3.14'), technical names ('Node.js', 'Next.js'),
      acronyms, and symbols ('C++', 'C#').
    - Normalizes excessive blank lines to standard paragraph breaks (max 2 newlines).
    - Preserves exact content wording and meaning.
    """
    if not text:
        return ""

    # Normalize horizontal whitespace (tabs and multiple spaces within lines)
    text = re.sub(r"[ \t]+", " ", text)

    # Remove unwanted whitespace before punctuation marks
    text = re.sub(r"\s+([,.:;?!])", r"\1", text)

    # Clean accidental duplicated commas or semicolons (e.g., ',,' -> ',', ';;' -> ';')
    text = re.sub(r",{2,}", ",", text)
    text = re.sub(r";{2,}", ";", text)

    # Add space after comma between letters ('apples,bananas' -> 'apples, bananas')
    # but NOT between digits (preserves '10,000' or '1,000,000')
    text = re.sub(r"([a-zA-Z]),([a-zA-Z])", r"\1, \2", text)

    # Add space after sentence-ending punctuation (. ? !) if followed immediately by a capitalized word
    # (preserves '3.14', 'Node.js', 'Next.js', 'https://example.com/api', etc.)
    text = re.sub(r"([a-z0-9][.?!])([A-Z])", r"\1 \2", text)

    # Collapse 3 or more consecutive linebreaks to standard paragraph breaks (2)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def transcribe_all_with_segments(chunks: list, language: str = "english") -> tuple:
    """
    Iterate sequentially over audio chunks, transcribe each, and return (full_transcript, segments).
    Maintains cumulative time offsets across multi-chunk files.
    """
    if not chunks:
        print("[Transcriber] Warning: No chunks provided for transcription.")
        return "", []

    trans_provider = os.getenv("TRANSCRIPTION_PROVIDER", "whisper").lower()
    if language.lower() in ("hinglish", "hindi"):
        engine = "Sarvam AI"
        engine_info = ""
    elif trans_provider == "gemini" and os.getenv("GEMINI_API_KEY"):
        engine = "Google Gemini"
        engine_info = f" ({os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')})"
    else:
        engine = "Whisper"
        engine_info = f" ({get_whisper_model()})"

    print(f"\n[Transcriber] STT Engine: {engine}{engine_info} | Language: {language}")
    print(f"[Transcriber] Processing {len(chunks)} audio chunk(s)...")

    successful_chunks = 0
    failed_chunks = 0
    chunk_texts = []
    all_segments = []
    last_error = None
    cumulative_offset = 0.0

    for i, chunk in enumerate(chunks):
        # Calculate chunk duration for logging
        try:
            c_audio = AudioSegment.from_wav(chunk)
            dur_sec = len(c_audio) / 1000.0
        except Exception:
            dur_sec = 0.0

        print(f"[Transcriber] Chunk {i + 1}/{len(chunks)} ({dur_sec:.1f}s) ...")

        try:
            if language.lower() in ("hinglish", "hindi"):
                text, segs = transcribe_chunk_sarvam_with_segments(
                    chunk,
                    base_offset_seconds=cumulative_offset,
                    start_segment_id=len(all_segments),
                )
            elif engine == "Google Gemini":
                text, segs = transcribe_chunk_gemini_with_segments(
                    chunk,
                    base_offset_seconds=cumulative_offset,
                    start_segment_id=len(all_segments),
                )
            else:
                text, segs = transcribe_chunk_whisper_with_segments(
                    chunk,
                    language=language,
                    base_offset_seconds=cumulative_offset,
                    start_segment_id=len(all_segments),
                )

            if text:
                chunk_texts.append(text)
                all_segments.extend(segs)
                print(f"[Transcriber] Chunk {i + 1} transcribed ({len(text)} chars, {len(segs)} segments).")
            else:
                print(f"[Transcriber] Chunk {i + 1} produced no text (possible silence).")
            successful_chunks += 1
        except Exception as e:
            failed_chunks += 1
            last_error = e
            print(f"[Transcriber] [ERROR] Error in chunk {i + 1}: {e}")

        cumulative_offset += dur_sec

    # If all chunks failed, raise the error so the pipeline doesn't proceed with empty output
    if failed_chunks > 0 and successful_chunks == 0:
        raise RuntimeError(f"All {failed_chunks} audio chunk(s) failed transcription. Last error: {last_error}")

    # Multi-chunk joining with paragraph breaks; single-chunk preserved as-is
    assembled_raw = "\n\n".join(chunk_texts)
    full_transcript = clean_transcript(assembled_raw)

    word_count = len(full_transcript.split())
    print(f"[Transcriber] Completed: {successful_chunks} successful, {failed_chunks} failed chunk(s).")
    print(f"[Transcriber] Final transcript length: {len(full_transcript)} characters (~{word_count} words, {len(all_segments)} segments).\n")

    return full_transcript, all_segments


def transcribe_all(chunks: list, language: str = "english") -> str:
    """
    Iterate sequentially over audio chunks, transcribe each, and assemble the transcript.
    Includes structured logging and safe handling of individual chunk failures.
    """
    full_transcript, _ = transcribe_all_with_segments(chunks, language=language)
    return full_transcript
