import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field, asdict


def format_seconds(seconds: float) -> str:
    """
    Format a duration or timestamp in seconds to standard HH:MM:SS format.
    E.g.: 70.0 -> '00:01:10', 3724.5 -> '01:02:04'.
    """
    if seconds is None or seconds < 0:
        return "00:00:00"
    total_sec = int(round(seconds))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_timestamp(ts_str: str) -> float:
    """
    Parse a timestamp string ('MM:SS' or 'HH:MM:SS') into seconds.
    E.g.: '01:10' -> 70.0, '00:01:10' -> 70.0, '01:12:31' -> 4351.0.
    """
    if not ts_str or not isinstance(ts_str, str):
        return 0.0
    clean = ts_str.strip().strip("[]()")
    parts = clean.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return float(h) * 3600 + float(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return float(m) * 60 + float(s)
        elif len(parts) == 1:
            return float(parts[0])
    except ValueError:
        pass
    return 0.0


def format_time_range(start_sec: Optional[float], end_sec: Optional[float]) -> str:
    """
    Format start and end seconds into a consistent range string.
    E.g.: 70.0, 84.0 -> '00:01:10 – 00:01:24'.
    """
    if start_sec is None or end_sec is None:
        return "Not specified"
    if start_sec == 0.0 and end_sec == 0.0:
        return "00:00:00 – 00:00:00"
    return f"{format_seconds(start_sec)} – {format_seconds(end_sec)}"


@dataclass
class TranscriptSegment:
    """A discrete timestamped segment of meeting dialogue."""
    segment_id: int
    text: str
    start_time: float  # in seconds
    end_time: float    # in seconds
    speaker: Optional[str] = None
    source: str = "meeting_transcript"

    @property
    def start_formatted(self) -> str:
        return format_seconds(self.start_time)

    @property
    def end_formatted(self) -> str:
        return format_seconds(self.end_time)

    @property
    def time_range(self) -> str:
        return format_time_range(self.start_time, self.end_time)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RetrievedEvidence:
    """A retrieved context unit enriched with deterministic provenance metadata."""
    evidence_id: str        # 'E1', 'E2', ...
    chunk_index: int
    text: str
    time_range: str
    start_time: str
    end_time: str
    start_seconds: float
    end_seconds: float
    source: str
    source_type: str
    session_id: str
    score: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


def parse_transcript_segments(text: str, source: str = "meeting_transcript") -> List[TranscriptSegment]:
    """
    Parse a transcript containing inline timestamps or speaker blocks into structured TranscriptSegments.
    Recognizes patterns such as:
      00:01:10
      Sarah: The backend database...
    or:
      [00:01:10 - 00:01:24] Sarah: ...
    If no timestamps are present in the text, segments the text by paragraphs
    with sequential index and default 0.0 timestamps.
    """
    if not text or not text.strip():
        return []

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    segments: List[TranscriptSegment] = []
    
    # Regex to detect timestamp on its own line or at the start of a line
    ts_pattern = re.compile(r"^\[?(\d{1,2}:\d{2}(?::\d{2})?)(?:\s*[-–—]\s*(\d{1,2}:\d{2}(?::\d{2})?))?\]?:?\s*(.*)$")
    speaker_pattern = re.compile(r"^([A-Za-z0-9_ ]+):\s*(.*)$")

    current_start: Optional[float] = None
    current_end: Optional[float] = None
    current_speaker: Optional[str] = None
    current_text_parts: List[str] = []
    seg_idx = 0

    def flush_segment():
        nonlocal seg_idx, current_start, current_end, current_speaker, current_text_parts
        if current_text_parts:
            combined_text = " ".join(current_text_parts).strip()
            if combined_text:
                st = current_start if current_start is not None else 0.0
                et = current_end if current_end is not None else st
                segments.append(
                    TranscriptSegment(
                        segment_id=seg_idx,
                        text=combined_text,
                        start_time=st,
                        end_time=et,
                        speaker=current_speaker,
                        source=source,
                    )
                )
                seg_idx += 1
        current_text_parts = []
        current_start = None
        current_end = None
        current_speaker = None

    i = 0
    while i < len(lines):
        line = lines[i]
        ts_match = ts_pattern.match(line)
        if ts_match:
            # New timestamped block found
            flush_segment()
            start_str = ts_match.group(1)
            end_str = ts_match.group(2)
            remainder = ts_match.group(3).strip()

            current_start = parse_timestamp(start_str)
            current_end = parse_timestamp(end_str) if end_str else current_start

            if remainder:
                spk_match = speaker_pattern.match(remainder)
                if spk_match:
                    current_speaker = spk_match.group(1).strip()
                    remainder_text = spk_match.group(2).strip()
                    if remainder_text:
                        current_text_parts.append(remainder_text)
                else:
                    current_text_parts.append(remainder)
        else:
            spk_match = speaker_pattern.match(line)
            if spk_match and not current_text_parts:
                current_speaker = spk_match.group(1).strip()
                spk_text = spk_match.group(2).strip()
                if spk_text:
                    current_text_parts.append(spk_text)
            else:
                current_text_parts.append(line)
        i += 1

    flush_segment()

    # If segments were extracted with zero duration for consecutive points, estimate end times
    for idx in range(len(segments)):
        if segments[idx].end_time <= segments[idx].start_time:
            if idx + 1 < len(segments) and segments[idx + 1].start_time > segments[idx].start_time:
                segments[idx].end_time = segments[idx + 1].start_time
            else:
                # Estimate ~150 words per minute (~2.5 words per second)
                words = len(segments[idx].text.split())
                est_duration = max(3.0, words / 2.5)
                segments[idx].end_time = segments[idx].start_time + est_duration

    # If no timestamps were detected in the text, treat paragraphs as sequential untimed segments
    if not segments and text.strip():
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for p_idx, p in enumerate(paragraphs):
            segments.append(
                TranscriptSegment(
                    segment_id=p_idx,
                    text=p,
                    start_time=0.0,
                    end_time=0.0,
                    source=source,
                )
            )

    return segments


def map_chunk_to_segments(
    chunk_text: str,
    segments: List[TranscriptSegment],
) -> Tuple[Optional[float], Optional[float], List[int]]:
    """
    Given a text chunk and a list of TranscriptSegments, identify overlapping segments
    and return (start_seconds, end_seconds, segment_ids).
    """
    if not segments:
        return None, None, []

    chunk_clean = chunk_text.lower()
    matching_segs = []

    for seg in segments:
        seg_text_clean = seg.text.lower()
        # Check if significant portion of segment text is in chunk or vice versa
        # Compare first 40 chars or full text
        sample = seg_text_clean[:min(40, len(seg_text_clean))]
        if sample in chunk_clean or chunk_clean[:min(40, len(chunk_clean))] in seg_text_clean:
            matching_segs.append(seg)
        elif any(phrase in chunk_clean for phrase in seg_text_clean.split(". ") if len(phrase) > 15):
            matching_segs.append(seg)

    if not matching_segs:
        # Fallback: find closest lexical word overlap
        chunk_words = set(re.findall(r"\b\w{4,}\b", chunk_clean))
        scored = []
        for seg in segments:
            seg_words = set(re.findall(r"\b\w{4,}\b", seg.text.lower()))
            overlap = len(chunk_words.intersection(seg_words))
            if overlap >= 2:
                scored.append((overlap, seg))
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored:
            top_overlap = scored[0][0]
            matching_segs = [seg for score, seg in scored if score >= max(2, top_overlap - 1)]

    if matching_segs:
        start_sec = min(s.start_time for s in matching_segs)
        end_sec = max(s.end_time for s in matching_segs)
        seg_ids = [s.segment_id for s in matching_segs]
        return start_sec, end_sec, seg_ids

    return None, None, []


def verify_evidence_consistency(
    evidence: RetrievedEvidence,
    active_session_id: str,
) -> bool:
    """
    Deterministic consistency verification before exposing citation to user:
    - Evidence must belong to active session.
    - Evidence ID and chunk index must be non-negative.
    - Evidence text must be non-empty.
    - Start time must not exceed end time.
    """
    if not evidence or not isinstance(evidence, RetrievedEvidence):
        return False
    if evidence.session_id != active_session_id:
        return False
    if not evidence.text or not evidence.text.strip():
        return False
    if evidence.chunk_index < 0:
        return False
    if evidence.start_seconds > evidence.end_seconds:
        return False
    return True
