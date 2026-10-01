"""
Provider-agnostic LLM interface.

KARBHARI's agent code (backend/app/agent/*) talks to this interface only --
never to a specific provider's SDK or REST shape. Today there is one
implementation (Gemini, via REST). Adding OpenAI/Anthropic/etc. later means
writing one more class here and a branch in factory.py; nothing in agent/
changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMError(RuntimeError):
    """Raised when the LLM provider fails or returns something unusable."""


class LLMClient(ABC):
    @abstractmethod
    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
    ) -> str:
        """
        Sends a prompt and returns the raw JSON text of the response.
        Callers are responsible for parsing/validating the JSON (typically
        into a pydantic model) -- this layer only guarantees it talked to
        the model and got text back, not that the text matches any
        particular shape.
        """
        raise NotImplementedError
