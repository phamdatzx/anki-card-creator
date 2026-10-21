from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import CollocationPayload, validate_collocation_payload
from .schemas import COLLOCATION_SCHEMA

SYSTEM_PROMPT = """You are an English collocation teacher for Vietnamese learners.
Given a keyword, list 6 to 12 of its most frequent, natural collocations, spread
over several patterns (for example verb + noun, adjective + noun, noun + preposition,
adverb + adjective). Prefer the combinations Vietnamese learners most often get
wrong. keyword is the keyword in base form. For each item: pattern names the
pattern with the keyword written out, e.g. "verb + decision"; collocation is the
full base form, e.g. "make a decision"; gap is one natural English sentence that
uses the collocation, with the keyword kept and only the partner word replaced by
exactly one ___ (three underscores); answer is the exact text that fills the gap,
inflected as needed; vietnamese is a short gloss of the whole collocation: one
common Vietnamese word, or a short phrase only when no single word exists; usage
is a brief English note on register or typical use, e.g. "formal, written". Return
only data that matches the schema."""


def lookup_collocations(
    keyword: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> CollocationPayload:
    cleaned = keyword.strip()
    if not cleaned:
        raise OpenAIError("Enter a keyword to find its collocations.")
    try:
        return validate_collocation_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Keyword: {cleaned}",
                schema_name="collocation_lookup",
                schema=COLLOCATION_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
