from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import WordFormPayload, validate_word_form_payload
from .schemas import WORD_FORM_SCHEMA

SYSTEM_PROMPT = """You are an English vocabulary learning assistant.
The user may type any form from a word family. Identify the true morphological
base or lemma as rootWord (for example, "neatly" has root "neat") and include
the typed derived form in other. Return related noun, verb, adjective, adverb,
and other forms. Provide a short natural Vietnamese meaning for rootWord and use
special_definition for a related form's distinct meaning. Keep type labels
short. Provide precise standard American English IPA in slash notation for
every form. Rate popularity and difficulty for every form separately as
integers 1–5. Return only data that matches the schema."""


def lookup_word_form(
    word: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> WordFormPayload:
    cleaned = word.strip()
    if not cleaned:
        raise OpenAIError("Enter a word to look up (any form in the family).")
    try:
        return validate_word_form_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT,
                user=f"Word (any form; find the true root): {cleaned}",
                schema_name="word_form_lookup",
                schema=WORD_FORM_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
