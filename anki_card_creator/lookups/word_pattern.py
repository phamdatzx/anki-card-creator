from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import WordPatternPayload, validate_word_pattern_payload
from .schemas import WORD_PATTERN_SCHEMA

SYSTEM_PROMPT = """You are an English question creator for Vietnamese learners.
Given a collocation or usage pattern, create one gap-fill question in a natural
English context of one or two sentences. Hide the entire target pattern and put
its Vietnamese meaning where it was removed, inside parentheses. answer is the
exact conjugated English text that fills the gap; vietnamese is the same short
gloss used in the gap; pattern is the full English base form; explanation is a
brief English usage note; examples are natural English sentences. Return only
data that matches the schema."""


def lookup_word_pattern(
    pattern: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> WordPatternPayload:
    cleaned = pattern.strip()
    if not cleaned:
        raise OpenAIError("Enter a word pattern / collocation.")
    try:
        return validate_word_pattern_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Pattern: {cleaned}",
                schema_name="word_pattern_lookup",
                schema=WORD_PATTERN_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
