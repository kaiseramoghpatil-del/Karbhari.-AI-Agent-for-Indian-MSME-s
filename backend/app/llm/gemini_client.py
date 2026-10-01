"""
Gemini REST implementation of LLMClient.

Uses the plain REST API (not the google-genai SDK) deliberately: one fewer
heavyweight/fast-moving dependency, and the request shape is simple enough
that a direct httpx call is easier to keep stable than tracking an SDK's
API surface. If that trade-off stops making sense, only this file changes.
"""

from __future__ import annotations

import httpx

from .base import LLMClient, LLMError

API_BASE = "https://generativelanguage.googleapis.com/v1beta"


class GeminiClient(LLMClient):
    def __init__(self, api_key: str, model: str, timeout_seconds: float = 60.0):
        if not api_key:
            raise LLMError("GOOGLE_API_KEY is not set.")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds

    def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
    ) -> str:
        url = f"{API_BASE}/models/{self._model}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": temperature,
            },
        }

        try:
            resp = httpx.post(
                url, params={"key": self._api_key}, json=payload, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc

        if resp.status_code != 200:
            raise LLMError(f"Gemini API error {resp.status_code}: {resp.text[:500]}")

        data = resp.json()
        try:
            candidates = data["candidates"]
            parts = candidates[0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected Gemini response shape: {data}") from exc

        if not text.strip():
            raise LLMError(f"Gemini returned an empty response: {data}")

        return text
