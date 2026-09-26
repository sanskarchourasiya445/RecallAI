"""
Phase 7 Evaluation Runner Entry Point.
Executes the comprehensive evaluation suite in tests/evaluation/evaluation_runner.py.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from tests.evaluation.evaluation_runner import run_evaluation

if __name__ == "__main__":
    results = run_evaluation()
    print("\nPhase 7 Evaluation completed successfully.")
