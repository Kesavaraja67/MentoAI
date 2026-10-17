"""
llm/providers.py — Provider allowlist and base URL mapping.

Strict allowlist per Section 8.1 of the specification:
Prevents Server-Side Request Forgery (SSRF) from user-supplied URLs.
Only these four providers and their official base URLs are permitted.
Arbitrary base URLs are strictly rejected.
"""
from __future__ import annotations

PROVIDER_BASE_URLS: dict[str, str] = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "openai": "https://api.openai.com/v1",
}

DEFAULT_MODELS: dict[str, str] = {
    "groq": "llama-3.3-70b-versatile",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "gemini": "gemini-1.5-flash",
    "openai": "gpt-4o-mini",
}


def get_base_url(provider: str) -> str:
    """Return the official base URL for an approved provider, or raise ValueError."""
    prov = provider.lower().strip()
    if prov not in PROVIDER_BASE_URLS:
        raise ValueError(
            f"Provider '{provider}' is not in the approved allowlist: "
            f"{list(PROVIDER_BASE_URLS.keys())}"
        )
    return PROVIDER_BASE_URLS[prov]


def get_default_model(provider: str) -> str:
    prov = provider.lower().strip()
    return DEFAULT_MODELS.get(prov, "gpt-4o-mini")


# Aliases for agent runtime compatibility
ALLOWED_PROVIDERS = list(PROVIDER_BASE_URLS.keys())
get_provider_base_url = get_base_url

