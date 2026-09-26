"""
Voice interaction package for Gistly.
Provides voice input transcription and synthesized spoken answer audio.
"""

import sys
from core.voice import voice
sys.modules[__name__] = voice
