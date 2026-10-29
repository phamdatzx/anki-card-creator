from __future__ import annotations

from ..openai_client import OpenAIError, chat_json
from .contracts import (
    NormalGroupedPayload,
    NormalPayload,
    validate_normal_grouped_payload,
    validate_normal_payload,
)
from .schemas import NORMAL_GROUPED_SCHEMA, NORMAL_SCHEMA

SYSTEM_PROMPT = """You are an English vocabulary learning assistant.
Given an English word or phrasal verb, return distinct dictionary-style senses
for learners. Use clear short definitions, natural examples, and relevant
synonyms. For each sense, vietnamese must be a brief equivalent, not a
translation of the English definition: prefer one common Vietnamese word,
and use a short phrase of a few words only when no single word exists. partOfSpeech should be a short label (noun,
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


GROUPING_PROMPT = """
Also give every sense a group number, starting at 1. Senses of different parts
of speech that share one core meaning and belong to the same word family go in
the same group, because they are learned together on one card: "test" (verb,
to check) and "test" (noun, an exam or check) share a group. Senses with
unrelated meanings get different groups, even for the same part of speech:
"bank" (edge of a river) and "bank" (money institution) do not. Number groups
in order of first appearance, and list a group's senses next to each other."""


FAMILY_PROMPT = """
Follow these rules exactly, in order.

1. ROOT. input is the text exactly as given. word is its dictionary headword,
found by undoing inflection only: plural -s/-es, third-person -s, past -ed,
-ing, comparative -er and superlative -est, and irregular forms (went -> go,
children -> child, better -> good, mice -> mouse). Never undo derivation:
"decision", "happiness", "quickly" and "unhappy" are headwords already. One
exception: when an -ing or -ed form is a common word with its own dictionary
entry and that is its likely meaning ("interesting", "building", "tired",
"advanced"), keep it as word and put the verb in family instead.
2. inputNote names the inflection that was undone, in English, e.g. "-ing form
of decide", "past tense of go", "plural of child". It is an empty string when
input already is the headword.
3. results describe word, the headword, never the inflected input.
4. FAMILY. family lists other words built from the same root that a learner
should learn together with word, e.g. for decide: decision (noun), decisive
(adjective), decisively (adverb), indecisive (adjective). Each member must be
a different word from word, and must differ from it in part of speech or in
meaning. Never include: word itself, its inflections (decides, decided,
deciding), compounds, phrasal verbs, or rare, archaic, dialect or technical
words. List each (word, partOfSpeech) pair at most once, give only its most
common sense, and fill every field exactly as for results, including word,
ipa, vietnamese, synonyms, examples, popularity and difficulty. List at most 8
members, most frequent first; family is empty when word has no common family.
5. CHECK before answering. For every family member confirm that it is a real,
correctly spelled English word found in a standard learner's dictionary, that
its partOfSpeech is correct for the sense you give, and that its meaning
really comes from the same root as word. Remove any member you are not sure
of: a short correct family is better than a long one.

Examples. input "deciding": word "decide", inputNote "-ing form of decide",
family decision (noun), decisive (adjective), decisively (adverb), indecisive
(adjective). input "children": word "child", inputNote "plural of child",
family childhood (noun), childish (adjective), childlike (adjective). input
"happiness": word "happiness", inputNote "", family happy (adjective),
happily (adverb), unhappy (adjective)."""


def lookup_normal_grouped(
    word: str,
    *,
    api_key: str,
    model: str,
    base_url: str,
    verify_ssl: bool = False,
) -> NormalGroupedPayload:
    """Like ``lookup_normal_word``, for Word Inbox.

    Related senses are grouped per card, the input is reduced to its root
    word, and the root's word family comes back as extra cards to pick from.
    """
    cleaned = word.strip()
    if not cleaned:
        raise OpenAIError("Enter a word or phrasal verb to look up.")
    try:
        return validate_normal_grouped_payload(
            chat_json(
                api_key=api_key,
                model=model,
                base_url=base_url,
                verify_ssl=verify_ssl,
                system=SYSTEM_PROMPT + GROUPING_PROMPT + FAMILY_PROMPT,
                user=f"Vocabulary entry: {cleaned}",
                schema_name="vocabulary_entry_grouped_lookup",
                schema=NORMAL_GROUPED_SCHEMA,
            )
        )
    except ValueError as exc:
        raise OpenAIError(f"Unexpected structured output: {exc}") from exc
