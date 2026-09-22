from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import VietnamesePayload, validate_vietnamese_payload
from .schemas import VIETNAMESE_SCHEMA

SYSTEM_PROMPT = """You are an English vocabulary learning assistant for
Vietnamese speakers. The user gives a Vietnamese word or meaning. Find
distinct English words or short phrases (single dictionary headwords or
phrasal verbs) that best express that meaning, ordered from most to least
relevant. Return each candidate as its own result with its own word. Use
clear short English definitions, a natural Vietnamese meaning for that exact
sense (refine or restate the user's input as needed), natural examples, and
relevant synonyms. partOfSpeech should be a short label (noun, verb,
adjective, adverb, etc.). Provide precise standard American English IPA in
slash notation for every result, using the pronunciation appropriate to that
sense. For each result rate popularity and difficulty as integers 1–5.
Return only data that matches the schema."""


def lookup_vietnamese_word(
    meaning: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> VietnamesePayload:
    cleaned = meaning.strip()
    if not cleaned:
        raise OpenAIError("Enter a Vietnamese word or meaning to look up.")
    try:
        return validate_vietnamese_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Vietnamese meaning: {cleaned}",
                schema_name="vietnamese_meaning_lookup",
                schema=VIETNAMESE_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
