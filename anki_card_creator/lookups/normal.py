from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import NormalPayload, validate_normal_payload
from .schemas import NORMAL_SCHEMA

SYSTEM_PROMPT = """You are an English vocabulary learning assistant.
Given an English word or phrasal verb, return distinct dictionary-style senses
for learners. Use clear short definitions, Vietnamese meanings, natural
examples, and relevant synonyms. partOfSpeech should be a short label (noun,
verb, adjective, adverb, etc.). For phrasal verbs, use "phrasal verb" unless
another label is clearly better. For every sense, provide its precise standard
American English IPA in slash notation, using the pronunciation appropriate to
that sense.
For each sense rate popularity and difficulty as integers 1–5. Popularity 5 is
very common and 1 is rare; difficulty 5 is very hard for intermediate learners
and 1 is beginner-friendly. Return only data that matches the schema."""


def lookup_normal_word(
    word: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> NormalPayload:
    cleaned = word.strip()
    if not cleaned:
        raise OpenAIError("Enter a word or phrasal verb to look up.")
    try:
        return validate_normal_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Vocabulary entry: {cleaned}",
                schema_name="vocabulary_entry_lookup",
                schema=NORMAL_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
