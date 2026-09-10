"""
LLM client — unified async wrapper supporting Gemini and Ollama.

Provider selection (in priority order):
  1. Supabase `app_settings` table — key "LLM_PROVIDER" (live, no restart needed)
  2. `.env` LLM_PROVIDER value (startup default)

Supported providers:
  - "gemini" → Google Gemini via google-generativeai SDK
  - "ollama" → Local Ollama server via ollama SDK

Usage:
    from app.ml.llm_client import get_llm_client
    llm = await get_llm_client()

    # Plain text response
    answer = await llm.chat("Summarise this text: ...")

    # JSON structured response
    data = await llm.chat_json("Extract skills from: ...")

    # Streaming (token by token)
    async for token in llm.stream("Tell me about hackathons"):
        print(token, end="", flush=True)
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List, Optional

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


# ── Provider resolution ────────────────────────────────────────────────────────

async def _get_active_provider() -> str:
    """
    Fetch the active LLM provider from Supabase app_settings table.
    Falls back to settings.LLM_PROVIDER (.env) if DB is unavailable.
    """
    try:
        from app.core.supabase_client import supabase_admin
        resp = (
            supabase_admin.table("app_settings")
            .select("value")
            .eq("key", "LLM_PROVIDER")
            .maybe_single()
            .execute()
        )
        if resp.data and resp.data.get("value"):
            return resp.data["value"].lower().strip()
    except Exception as exc:
        logger.debug(f"Could not read LLM_PROVIDER from app_settings: {exc}")
    return settings.LLM_PROVIDER.lower()


async def _get_setting(key: str, fallback: str) -> str:
    """Fetch a single setting from app_settings table with .env fallback."""
    try:
        from app.core.supabase_client import supabase_admin
        resp = (
            supabase_admin.table("app_settings")
            .select("value")
            .eq("key", key)
            .maybe_single()
            .execute()
        )
        if resp.data and resp.data.get("value"):
            return resp.data["value"].strip()
    except Exception:
        pass
    return fallback


# ── Gemini Client ──────────────────────────────────────────────────────────────

class GeminiClient:
    """Async wrapper around Google Gemini via google-generativeai SDK."""

    def __init__(self, model: str) -> None:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._genai = genai
        self._model_name = model
        logger.info(f"Gemini client initialised with model={model}")

    def _get_model(self, system_prompt: Optional[str] = None):
        """Return a configured GenerativeModel instance."""
        kwargs: Dict[str, Any] = {}
        if system_prompt:
            kwargs["system_instruction"] = system_prompt
        return self._genai.GenerativeModel(self._model_name, **kwargs)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15), reraise=True)
    async def chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Return a plain-text response from Gemini."""
        model = self._get_model(system_prompt)
        # Build conversation with history
        messages = []
        if history:
            for msg in history:
                role = "user" if msg.get("role") == "user" else "model"
                messages.append({"role": role, "parts": [msg.get("content", "")]})
        messages.append({"role": "user", "parts": [user_prompt]})

        generation_config = self._genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        response = await model.generate_content_async(
            messages,
            generation_config=generation_config,
        )
        return response.text.strip()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15), reraise=True)
    async def chat_json(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Return a parsed JSON dict from Gemini."""
        json_instruction = "Always respond with valid JSON only, no markdown fences."
        full_system = f"{system_prompt}\n{json_instruction}" if system_prompt else json_instruction
        raw = await self.chat(user_prompt, full_system, history, temperature, max_tokens)
        # Strip markdown fences if model adds them
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)

    async def stream(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Yield response tokens as they stream from Gemini."""
        model = self._get_model(system_prompt)
        generation_config = self._genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        async for chunk in await model.generate_content_async(
            [{"role": "user", "parts": [user_prompt]}],
            generation_config=generation_config,
            stream=True,
        ):
            if chunk.text:
                yield chunk.text


# ── Ollama Client ──────────────────────────────────────────────────────────────

class OllamaClient:
    """Async wrapper around local Ollama server."""

    def __init__(self, host: str, model: str) -> None:
        import ollama as _ollama
        self._ollama = _ollama
        self._host = host
        self._model = model
        logger.info(f"Ollama client initialised with host={host} model={model}")

    def _build_messages(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_prompt})
        return messages

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15), reraise=True)
    async def chat(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Return a plain-text response from Ollama."""
        client = self._ollama.AsyncClient(host=self._host)
        messages = self._build_messages(user_prompt, system_prompt, history)
        response = await client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
        )
        return response["message"]["content"].strip()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15), reraise=True)
    async def chat_json(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Return a parsed JSON dict from Ollama."""
        json_instruction = "Respond ONLY with valid JSON. No explanations."
        full_system = f"{system_prompt}\n{json_instruction}" if system_prompt else json_instruction
        raw = await self.chat(user_prompt, full_system, history, temperature, max_tokens)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)

    async def stream(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Yield response tokens as they stream from Ollama."""
        client = self._ollama.AsyncClient(host=self._host)
        messages = self._build_messages(user_prompt, system_prompt)
        async for chunk in await client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": temperature, "num_predict": max_tokens},
            stream=True,
        ):
            delta = chunk.get("message", {}).get("content", "")
            if delta:
                yield delta


# ── Unified LLM Client Factory ─────────────────────────────────────────────────

async def get_llm_client() -> GeminiClient | OllamaClient:
    """
    Return the correct LLM client based on active provider.
    Checks Supabase app_settings table first (live override),
    falls back to LLM_PROVIDER in .env.
    """
    provider = await _get_active_provider()
    logger.debug(f"Active LLM provider: {provider}")

    if provider == "ollama":
        host = await _get_setting("OLLAMA_HOST", settings.OLLAMA_HOST)
        model = await _get_setting("OLLAMA_MODEL", settings.OLLAMA_MODEL)
        return OllamaClient(host=host, model=model)

    # Default: Gemini
    model = await _get_setting("GEMINI_MODEL", settings.GEMINI_MODEL)
    return GeminiClient(model=model)
