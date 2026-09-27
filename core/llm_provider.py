"""
Unified LLM Provider Abstraction for RecallAI.
Supports:
- Modern Google Gemini models (e.g., gemini-1.5-flash, gemini-2.0-flash)
- Mistral AI fallback (mistral-small-latest)
- Environment-driven provider selection (LLM_PROVIDER: 'auto', 'gemini', 'mistral')
- Safe API secret redaction in error reporting
"""

import os
from typing import Optional
from core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MISTRAL_API_KEY,
    LLM_PROVIDER,
)

DEFAULT_TEMPERATURE = 0.1


def get_llm(temperature: float = DEFAULT_TEMPERATURE, model_name: Optional[str] = None):
    """
    Instantiate and return the configured ChatModel.
    Priority:
    1. If LLM_PROVIDER is 'gemini' or ('auto' and GEMINI_API_KEY is available):
       Instantiates ChatGoogleGenerativeAI with GEMINI_MODEL.
    2. If MISTRAL_API_KEY is available:
       Instantiates ChatMistralAI as reliable fallback.
    3. If neither is available, raises RuntimeError with clear setup instructions.
    """
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
    gemini_model = os.getenv("GEMINI_MODEL") or GEMINI_MODEL or "gemini-1.5-flash"
    provider = (os.getenv("LLM_PROVIDER") or LLM_PROVIDER or "auto").lower()

    # Determine if Gemini should be used
    use_gemini = False
    if provider == "gemini":
        use_gemini = True
    elif provider == "auto" and gemini_key and not str(gemini_key).startswith("mock-") and gemini_key != "your_gemini_api_key_here":
        use_gemini = True

    if use_gemini:
        if not gemini_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment or .env file.")
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            selected_model = model_name or gemini_model
            return ChatGoogleGenerativeAI(
                model=selected_model,
                google_api_key=gemini_key,
                temperature=temperature,
            )
        except Exception as e:
            fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")
            if fallback_model and fallback_model != (model_name or gemini_model):
                try:
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    print(f"[LLM] Primary model '{selected_model}' failed ({e}). Attempting fallback '{fallback_model}'.")
                    return ChatGoogleGenerativeAI(
                        model=fallback_model,
                        google_api_key=gemini_key,
                        temperature=temperature,
                    )
                except Exception:
                    pass
            raise RuntimeError(f"Failed to initialize Gemini model '{selected_model}': {e}")

    # Fallback to Mistral
    api_key = MISTRAL_API_KEY or os.getenv("MISTRAL_API_KEY")
    if api_key:
        try:
            from langchain_mistralai import ChatMistralAI
            return ChatMistralAI(
                model=model_name or "mistral-small-latest",
                mistral_api_key=api_key,
                temperature=temperature,
            )
        except ImportError as e:
            raise RuntimeError(f"langchain-mistralai is required for Mistral models: {e}")

    # Neither available
    raise RuntimeError(
        "No LLM API key configured. Please set GEMINI_API_KEY or MISTRAL_API_KEY in your .env file."
    )


def redact_secrets(text: str) -> str:
    """Mask active API keys from runtime trace and exception messages."""
    if not text:
        return ""
    clean = str(text)
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY", "SARVAM_API_KEY"):
        val = os.getenv(var)
        if val and val in clean:
            clean = clean.replace(val, "[REDACTED]")
    return clean


def is_llm_configured() -> bool:
    """Check if an active LLM API key (Gemini or Mistral) is configured and not placeholder."""
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or GEMINI_API_KEY
    if gemini_key and not str(gemini_key).startswith("mock-") and gemini_key != "your_gemini_api_key_here":
        return True
    mistral_key = os.getenv("MISTRAL_API_KEY") or MISTRAL_API_KEY
    if mistral_key and not str(mistral_key).startswith("mock-") and mistral_key != "your_mistral_api_key_here":
        return True
    return False

