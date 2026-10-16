"""
llm — LLM interface, providers, prompts, validators, and templates.
"""
from app.llm.client import chat
from app.llm.providers import get_base_url, get_default_model, PROVIDER_BASE_URLS
from app.llm.validators import validate_tutor_output
from app.llm.templates import render_template
from app.llm.prompts import (
    build_tutor_system_prompt,
    build_tutor_user_payload,
    build_story_prompt,
)
from app.llm.fake import fake_chat

__all__ = [
    "chat",
    "get_base_url",
    "get_default_model",
    "PROVIDER_BASE_URLS",
    "validate_tutor_output",
    "render_template",
    "build_tutor_system_prompt",
    "build_tutor_user_payload",
    "build_story_prompt",
    "fake_chat",
]
