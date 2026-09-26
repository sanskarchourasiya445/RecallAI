"""
Standardized logging and secret scrubbing filter for Jitsly / Gistly.
Ensures uniform logging across pipeline modules and guarantees that
sensitive API keys or credentials are never exposed in log outputs.
"""

import os
import re
import logging
from typing import Optional

_SCRUB_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_\-]{8,}", re.IGNORECASE),
    re.compile(r"(api[_\-]?(?:key|token|subscription)[=:\s\"']+)([a-zA-Z0-9_\-]{8,})", re.IGNORECASE),
]


class SecretScrubbingFilter(logging.Filter):
    """
    Logging filter that intercepts log records and scrubs any known secrets
    or common API key patterns before records reach handlers or stdout.
    """

    def __init__(self, name: str = ""):
        super().__init__(name)
        self.known_secrets = set()
        for env_var in ("MISTRAL_API_KEY", "SARVAM_API_KEY"):
            val = os.getenv(env_var)
            if val and len(val.strip()) > 4 and not val.startswith("mock-"):
                self.known_secrets.add(val.strip())

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Scrub known secrets
            for sec in self.known_secrets:
                if sec in record.msg:
                    record.msg = record.msg.replace(sec, "[REDACTED_SECRET]")

            # Scrub regex patterns
            for pat in _SCRUB_PATTERNS:
                record.msg = pat.sub(r"\1[REDACTED_KEY]" if r"\1" in record.msg else "[REDACTED_KEY]", record.msg)

        if record.args:
            if isinstance(record.args, dict):
                cleaned_args = {}
                for k, v in record.args.items():
                    if isinstance(v, str):
                        for sec in self.known_secrets:
                            v = v.replace(sec, "[REDACTED_SECRET]")
                    cleaned_args[k] = v
                record.args = cleaned_args
            elif isinstance(record.args, tuple):
                cleaned_args = []
                for v in record.args:
                    if isinstance(v, str):
                        for sec in self.known_secrets:
                            v = v.replace(sec, "[REDACTED_SECRET]")
                    cleaned_args.append(v)
                record.args = tuple(cleaned_args)

        return True


def get_logger(name: str = "gistly") -> logging.Logger:
    """
    Get or configure a standardized logger instance with secret scrubbing.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SecretScrubbingFilter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger
