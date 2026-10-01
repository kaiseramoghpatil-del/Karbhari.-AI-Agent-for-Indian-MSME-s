from __future__ import annotations

import os

from .base import LLMClient, LLMError

_DEFAULT_GEMINI_MODEL = "gemini-flash-lite-latest"


def get_llm_client() -> LLMClient:
    """
    Reads LLM_PROVIDER (default "gemini") and dispatches to the matching
    concrete client. This is the one place that knows provider names --
    everything else in the app depends only on llm.base.LLMClient.
    """
    provider = os.environ.get("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        from .gemini_client import GeminiClient

        api_key = os.environ.get("GOOGLE_API_KEY", "")
        model = os.environ.get("LLM_MODEL", _DEFAULT_GEMINI_MODEL)
        return GeminiClient(api_key=api_key, model=model)

    raise LLMError(f"Unknown LLM_PROVIDER: {provider!r}")
