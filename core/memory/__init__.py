"""
Conversational Memory package for Gistly.
Provides session-isolated multi-turn conversation memory and contextual referential resolution.
"""

import sys
from core.memory import memory
sys.modules[__name__] = memory
