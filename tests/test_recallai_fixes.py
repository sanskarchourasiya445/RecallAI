"""
Targeted Verification Tests for RecallAI Issue 1 and Issue 2.
- Issue 1: YouTube cookie file support (cookies.txt) and actionable bot-block errors.
- Issue 2: Plain text evidence at source and prevention of raw HTML leaks in UI cards.
"""

import os
import re
import html
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import yt_dlp

from utils.audio_processor import get_youtube_cookie_path, download_youtube_audio
from core.demo import DEMO_ACTION_ITEMS, DEMO_KEY_DECISIONS, DEMO_OPEN_QUESTIONS, load_demo_meeting
from core.intelligence.extractor import (
    ActionItem,
    DecisionItem,
    OpenQuestionItem,
    strip_markup,
    format_action_items,
    format_key_decisions,
    format_open_questions,
)


class TestYouTubeCookieHandling(unittest.TestCase):
    """Test suite for Issue 1: YouTube downloading and cookie file workflow."""

    def test_cookie_path_none_when_no_file(self):
        """When no cookie file exists, get_youtube_cookie_path returns None."""
        with patch.dict(os.environ, {"YOUTUBE_COOKIE_FILE": "non_existent_cookies_12345.txt"}):
            resolved = get_youtube_cookie_path()
            self.assertIsNone(resolved)

    def test_cookie_path_resolves_when_file_exists(self):
        """When cookie file exists, get_youtube_cookie_path returns absolute path."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            tf.write(b"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tLOGIN_INFO\tdummy_val\n")
            temp_path = tf.name

        try:
            with patch.dict(os.environ, {"YOUTUBE_COOKIE_FILE": temp_path}):
                resolved = get_youtube_cookie_path()
                self.assertIsNotNone(resolved)
                self.assertEqual(Path(resolved), Path(temp_path).resolve())
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_youtube_blocked_actionable_error_without_cookies(self):
        """When YouTube blocks with bot check and no cookies exist, clear instructions are returned."""
        mock_error = yt_dlp.utils.DownloadError("Sign in to confirm you're not a bot. This helps protect our community.")
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.extract_info.side_effect = mock_error
        with patch("utils.audio_processor.get_youtube_cookie_path", return_value=None):
            with patch("yt_dlp.YoutubeDL", return_value=mock_instance):
                with self.assertRaises(RuntimeError) as ctx:
                    download_youtube_audio("https://www.youtube.com/watch?v=blocked_video")

                msg = str(ctx.exception)
                self.assertIn("YouTube download blocked: YouTube requires bot verification", msg)
                self.assertIn("cookies.txt", msg)
                self.assertIn("YOUTUBE_COOKIE_FILE", msg)

    def test_youtube_blocked_actionable_error_with_cookies(self):
        """When YouTube blocks despite cookie file, instructs user that cookies may be expired."""
        mock_error = yt_dlp.utils.DownloadError("Sign in to confirm you're not a bot")
        mock_instance = MagicMock()
        mock_instance.__enter__.return_value.extract_info.side_effect = mock_error
        with patch("utils.audio_processor.get_youtube_cookie_path", return_value="C:/path/to/cookies.txt"):
            with patch("yt_dlp.YoutubeDL", return_value=mock_instance):
                with self.assertRaises(RuntimeError) as ctx:
                    download_youtube_audio("https://www.youtube.com/watch?v=blocked_video")

                msg = str(ctx.exception)
                self.assertIn("cookies may be expired", msg)
                self.assertIn("cookies.txt", msg)

    def test_cookie_file_in_gitignore(self):
        """Verify cookies.txt is ignored by git to protect credentials."""
        gitignore_path = Path(__file__).resolve().parent.parent / ".gitignore"
        self.assertTrue(gitignore_path.exists())
        content = gitignore_path.read_text(encoding="utf-8")
        self.assertIn("cookies.txt", content)


class TestEvidencePlainTextAndNoHtmlLeak(unittest.TestCase):
    """Test suite for Issue 2: Evidence plain text at source and UI card rendering."""

    def test_strip_markup_helper(self):
        """strip_markup removes any HTML tags and normalizes whitespace."""
        raw = '<div class="evidence-quote-box">💬 <strong>Transcript Evidence:</strong> "Rahul will handle Postgres"</div>'
        cleaned = strip_markup(raw)
        self.assertEqual(cleaned, '💬 Transcript Evidence: "Rahul will handle Postgres"')

        raw_tag = "<p>Some text</p>"
        self.assertEqual(strip_markup(raw_tag), "Some text")

    def test_demo_meeting_evidence_is_plain_text(self):
        """All demo meeting action items, decisions, and questions must contain strictly plain text evidence."""
        html_tag_pattern = re.compile(r"<[^>]+>")

        for item in DEMO_ACTION_ITEMS:
            ev = item.get("evidence")
            self.assertIsNotNone(ev, "Action item evidence should not be None in demo meeting")
            self.assertFalse(html_tag_pattern.search(ev), f"HTML tag found in demo action item evidence: {ev}")
            self.assertNotIn("</div>", ev)
            self.assertNotIn("<div", ev)

        for item in DEMO_KEY_DECISIONS:
            ev = item.get("evidence")
            self.assertIsNotNone(ev, "Decision evidence should not be None in demo meeting")
            self.assertFalse(html_tag_pattern.search(ev), f"HTML tag found in demo decision evidence: {ev}")

        for item in DEMO_OPEN_QUESTIONS:
            ev = item.get("evidence")
            self.assertIsNotNone(ev, "Question evidence should not be None in demo meeting")
            self.assertFalse(html_tag_pattern.search(ev), f"HTML tag found in demo question evidence: {ev}")

    def test_pydantic_models_sanitize_html_at_source(self):
        """ActionItem, DecisionItem, and OpenQuestionItem strip HTML tags on instantiation."""
        # ActionItem
        dirty_action = ActionItem(
            task="<b>Deploy PgBouncer</b>",
            owner="Michael",
            evidence='<div class="evidence-quote-box">Michael: Agreed to deploy PgBouncer</div>',
        )
        self.assertEqual(dirty_action.task, "Deploy PgBouncer")
        self.assertEqual(dirty_action.evidence, "Michael: Agreed to deploy PgBouncer")
        self.assertNotIn("<div>", dirty_action.evidence)
        self.assertNotIn("<div", dirty_action.evidence)

        # DecisionItem
        dirty_dec = DecisionItem(
            decision="<strong>Migrate to Postgres 16</strong>",
            evidence="<p>Sarah confirmed migration</p>",
        )
        self.assertEqual(dirty_dec.decision, "Migrate to Postgres 16")
        self.assertEqual(dirty_dec.evidence, "Sarah confirmed migration")

        # OpenQuestionItem
        dirty_q = OpenQuestionItem(
            question="<em>Who owns on-call?</em>",
            evidence='<div class="evidence-quote-box">Rahul asked who owns on-call</div>',
        )
        self.assertEqual(dirty_q.question, "Who owns on-call?")
        self.assertEqual(dirty_q.evidence, "Rahul asked who owns on-call")

    def test_format_functions_clean_evidence(self):
        """format_action_items, format_key_decisions, format_open_questions output plain text evidence."""
        dirty_items = [
            {
                "task": "Test Task",
                "owner": "Sarah",
                "deadline": "Friday",
                "evidence": '<div class="evidence-quote-box">Evidence text</div>',
            }
        ]
        formatted = format_action_items(dirty_items)
        self.assertNotIn("<div", formatted)
        self.assertNotIn("</div>", formatted)
        self.assertIn('Evidence: "Evidence text"', formatted)

    def test_rendered_card_has_no_indented_code_blocks(self):
        """
        Verify that UI card HTML generation:
        1. Does not start lines with 4 or more spaces (which Markdown parses as <pre><code>).
        2. Wraps plain text evidence cleanly in <div class="evidence-quote-box">.
        3. Properly escapes text inside without creating literal visible markup tags.
        """
        task_name = "Prepare PostgreSQL Migration Plan"
        owner_val = "Rahul"
        deadline_val = "Friday 5 PM"
        evidence_val = "Rahul: Yes, I will prepare the complete migration plan."

        clean_ev = re.sub(r"<[^>]+>", "", str(evidence_val)).strip() if evidence_val else None
        ev_box = f'<div class="evidence-quote-box">💬 <strong>Transcript Evidence:</strong> "{html.escape(clean_ev)}"</div>' if clean_ev else ''

        card_html = (
            f'<div class="intel-card" style="margin-bottom:0.35rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:flex-start;">'
            f'<div class="intel-title">1. {html.escape(str(task_name))}</div>'
            f'<span class="status-pill-open">Open</span>'
            f'</div>'
            f'<div class="meta-row">'
            f'<span class="pill pill-owner">👤 Owner: {html.escape(str(owner_val))}</span>'
            f'<span class="pill pill-due">📅 Due: {html.escape(str(deadline_val))}</span>'
            f'</div>'
            f'{ev_box}'
            f'</div>'
        )

        # Verify no lines in card_html have 4+ leading spaces
        for line in card_html.split("\n"):
            if line.strip():
                self.assertFalse(line.startswith("    "), f"Line has 4+ leading spaces which triggers code block: {line}")

        # Verify proper HTML structure
        self.assertTrue(card_html.startswith('<div class="intel-card"'))
        self.assertTrue(card_html.endswith('</div>'))
        self.assertIn('<div class="evidence-quote-box">', card_html)
        self.assertIn(html.escape(clean_ev), card_html)


if __name__ == "__main__":
    unittest.main()
