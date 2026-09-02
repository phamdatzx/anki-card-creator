from __future__ import annotations

from typing import Any, TypedDict

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_TTS_VOICE = "alloy"


class AddonConfig(TypedDict):
    verify_ssl: bool
    openai_api_key: str
    openai_model: str
    openai_base_url: str
    openai_tts_model: str
    openai_tts_voice: str


def normalize_config(raw: dict[str, Any] | None = None) -> AddonConfig:
    values = raw or {}
    return {
        "verify_ssl": bool(values.get("verify_ssl", False)),
        "openai_api_key": str(values.get("openai_api_key") or ""),
        "openai_model": str(values.get("openai_model") or DEFAULT_MODEL),
        "openai_base_url": str(values.get("openai_base_url") or DEFAULT_BASE_URL),
        "openai_tts_model": str(
            values.get("openai_tts_model") or DEFAULT_TTS_MODEL
        ),
        "openai_tts_voice": str(
            values.get("openai_tts_voice") or DEFAULT_TTS_VOICE
        ),
    }


def chat_kwargs(config: AddonConfig) -> dict[str, Any]:
    return {
        "api_key": config["openai_api_key"],
        "model": config["openai_model"],
        "base_url": config["openai_base_url"],
        "verify_ssl": config["verify_ssl"],
    }


def tts_kwargs(config: AddonConfig) -> dict[str, Any]:
    return {
        "api_key": config["openai_api_key"],
        "model": config["openai_tts_model"],
        "base_url": config["openai_base_url"],
        "voice": config["openai_tts_voice"],
        "verify_ssl": config["verify_ssl"],
    }
