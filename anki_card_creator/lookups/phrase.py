from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import PhrasePayload, validate_phrase_payload
from .schemas import PHRASE_SCHEMA

SYSTEM_PROMPT = """You are an English phrase teacher for Vietnamese learners.
Given a multi-word phrase, list its distinct common senses, usually 1 to 3,
most frequent first. phrase is the phrase in its usual base form. For each
sense: structure names its grammar, e.g. "adjective + noun" or "verb + particle";
definition is a short, learner-friendly English definition that must not use
any word of the phrase itself, because it is shown while the learner tries to
recall the phrase; vietnamese is one common Vietnamese word, or a short phrase
only when no single word exists, never a translation of the definition;
examples are 2 or 3 natural English sentences using the phrase in that sense;
usage is a brief note on register or typical context, e.g. "news, business".
Return only data that matches the schema."""


def lookup_phrase(
    phrase: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> PhrasePayload:
    cleaned = phrase.strip()
    if not cleaned:
        raise OpenAIError("Enter a phrase to look up.")
    try:
        return validate_phrase_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Phrase: {cleaned}",
                schema_name="phrase_lookup",
                schema=PHRASE_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
