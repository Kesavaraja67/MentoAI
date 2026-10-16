"""
llm/client.py — Provider client with BYOK, allowlist, validation, caching, and fallback.

Per Section 8.1 of the specification:
- Exposes `chat(messages, max_tokens, temperature, byok_provider, byok_model, byok_key) -> str`
- OpenAI-compatible /chat/completions over httpx
- Strict provider allowlist (Groq, OpenRouter, Gemini, OpenAI) to prevent SSRF
- Never logs, echoes, or stores API keys
- 6-second timeout with one retry, then template fallback
- In-memory LRU cache keyed by prompt hash
- LLM_MODE=fake routes directly to fake_chat()
"""
from __future__ import annotations

import os
import hashlib
import logging
from collections import OrderedDict
from typing import Optional
import httpx

from app.config import settings
from app.llm.providers import get_base_url, get_default_model
from app.llm.fake import fake_chat

logger = logging.getLogger("primer.llm")

# In-memory LRU cache (capacity: 256 responses)
_CACHE: OrderedDict[str, str] = OrderedDict()
_CACHE_MAX_SIZE = 256


def _cache_get(key: str) -> Optional[str]:
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return _CACHE[key]
    return None


def _cache_set(key: str, value: str) -> None:
    _CACHE[key] = value
    _CACHE.move_to_end(key)
    if len(_CACHE) > _CACHE_MAX_SIZE:
        _CACHE.popitem(last=False)


def _make_cache_key(provider: str, model: str, messages: list[dict]) -> str:
    serialized = f"{provider}:{model}:{str(messages)}"
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def chat(
    messages: list[dict],
    max_tokens: int = 60,
    temperature: float = 0.3,
    byok_provider: Optional[str] = None,
    byok_model: Optional[str] = None,
    byok_key: Optional[str] = None,
) -> str:
    """
    Send messages to an LLM provider and return the response text.
    Handles BYOK headers, fallback to fake if LLM_MODE=fake, validation, and LRU cache.
    """
    # 1. Check for fake / offline mode
    llm_mode = os.environ.get("LLM_MODE", settings.llm_mode).lower().strip()
    if llm_mode == "fake":
        return fake_chat(messages, max_tokens=max_tokens, temperature=temperature)

    # 2. Resolve provider, model, key (request BYOK overrides env defaults)
    provider = byok_provider or os.environ.get("LLM_PROVIDER", settings.llm_provider) or "groq"
    provider = provider.lower().strip()

    # Throws ValueError if not on approved allowlist (SSRF protection)
    base_url = get_base_url(provider)

    model = byok_model or os.environ.get("LLM_MODEL", settings.llm_model) or get_default_model(provider)
    api_key = byok_key or os.environ.get("LLM_API_KEY", settings.llm_api_key)

    if not api_key:
        logger.info("No LLM API key provided; falling back to deterministic fake")
        return fake_chat(messages, max_tokens=max_tokens, temperature=temperature)

    # 3. Check LRU Cache
    cache_key = _make_cache_key(provider, model, messages)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    # 4. Make HTTP call with timeout and 1 retry
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    last_error: Optional[Exception] = None
    for attempt in range(2):
        try:
            with httpx.Client(timeout=6.0) as http_client:
                resp = http_client.post(endpoint, json=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    text = content.strip() if content else ""
                    if text:
                        _cache_set(cache_key, text)
                        return text
                else:
                    # Log status without exposing API key
                    logger.warning(
                        "LLM call failed with status %d on provider %s",
                        resp.status_code, provider,
                    )
        except Exception as e:
            last_error = e
            logger.warning("LLM call attempt %d error on provider %s", attempt + 1, provider)

    # Fallback to fake client on network/API failure
    logger.info("Falling back to fake LLM response after API attempts failed")
    return fake_chat(messages, max_tokens=max_tokens, temperature=temperature)
