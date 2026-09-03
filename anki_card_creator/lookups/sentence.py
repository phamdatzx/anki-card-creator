from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import SentencePayload, validate_sentence_payload
from .schemas import SENTENCE_SCHEMA

SYSTEM_PROMPT = """You translate English sentences into natural Vietnamese for
Vietnamese English learners. Preserve the sentence's intended meaning, tense,
tone, and level of formality. Return only data that matches the schema."""


def lookup_sentence(
    sentence: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> SentencePayload:
    cleaned = sentence.strip()
    if not cleaned:
        raise OpenAIError("Enter an English sentence.")
    try:
        return validate_sentence_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Sentence: {cleaned}",
                schema_name="sentence_lookup",
                schema=SENTENCE_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
