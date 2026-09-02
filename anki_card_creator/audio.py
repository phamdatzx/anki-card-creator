from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any
from uuid import uuid4

from .audio_keys import (
    AudioKey,
    DefinitionAudioKey,
    definition_audio_key,
    form_audio_key,
)
from .config import AddonConfig, tts_kwargs
from .lookups.contracts import DefinitionResult, WordFormItem, WordFormPayload
from .openai_client import speech_mp3
from .text import as_text


def tts_instructions(
    *,
    part_of_speech: str = "",
    definition: str = "",
    examples: Any = None,
    ipa: str = "",
) -> str:
    instructions = (
        "Pronounce only the supplied English word or phrase naturally in standard "
        "American English. Do not spell it or say any labels."
    )
    if part_of_speech.strip():
        instructions += (
            f" Use the {part_of_speech.strip()} sense to choose the correct "
            "pronunciation and stress."
        )
    if definition.strip():
        instructions += f' Intended definition: "{definition.strip()}".'
    if ipa.strip():
        instructions += (
            f" Use this IPA pronunciation exactly: {ipa.strip()}. "
            "Do not read the IPA symbols aloud."
        )
    example_text = as_text(examples, multiline=True)
    if example_text:
        first_example = example_text.splitlines()[0].strip()
        if first_example:
            instructions += f' Example context: "{first_example}".'
    return instructions


def store_audio(
    text: str,
    config: AddonConfig,
    write_data: Callable[[str, bytes], str | None],
    *,
    part_of_speech: str = "",
    definition: str = "",
    examples: Any = None,
    ipa: str = "",
) -> str:
    audio = speech_mp3(
        text=text,
        instructions=tts_instructions(
            part_of_speech=part_of_speech,
            definition=definition,
            examples=examples,
            ipa=ipa,
        ),
        **tts_kwargs(config),
    )
    filename = f"anki-card-creator-{uuid4().hex}.mp3"
    stored_name = write_data(filename, audio)
    if isinstance(stored_name, str):
        filename = stored_name
    return f"[sound:{filename}]"


def definition_audio_tags(
    word: str,
    results: list[DefinitionResult],
    config: AddonConfig,
    write_data: Callable[[str, bytes], str | None],
    on_progress: Callable[[int, int], None],
) -> list[str]:
    unique: dict[DefinitionAudioKey, DefinitionResult] = {}
    for result in results:
        unique.setdefault(definition_audio_key(word, result), result)
    tags: dict[DefinitionAudioKey, str] = {}
    for index, (key, result) in enumerate(unique.items(), start=1):
        on_progress(index, len(unique))
        tags[key] = store_audio(
            word,
            config,
            write_data,
            part_of_speech=str(result.get("partOfSpeech") or ""),
            definition=str(result.get("definition") or ""),
            examples=result.get("examples"),
            ipa=str(result.get("ipa") or ""),
        )
    return [tags[definition_audio_key(word, result)] for result in results]


def unique_forms(
    forms: Iterable[WordFormItem],
) -> dict[AudioKey, tuple[str, str, str, str]]:
    unique: dict[AudioKey, tuple[str, str, str, str]] = {}
    for item in forms:
        word = str(item.get("word") or "").strip()
        part_of_speech = str(item.get("type") or "").strip()
        if word:
            unique.setdefault(
                form_audio_key(word, part_of_speech),
                (
                    word,
                    part_of_speech,
                    str(item.get("special_definition") or ""),
                    str(item.get("ipa") or ""),
                ),
            )
    return unique


def word_form_audio(
    payload: WordFormPayload,
    config: AddonConfig,
    write_data: Callable[[str, bytes], str | None],
    on_progress: Callable[[int, int], None],
) -> tuple[str, dict[AudioKey, str]]:
    root = payload.get("rootWord") or {}
    forms = unique_forms(payload.get("other") or [])
    total = len(forms) + 1
    on_progress(1, total)
    root_audio = store_audio(
        str(root.get("word") or ""),
        config,
        write_data,
        part_of_speech=str(root.get("type") or ""),
        definition=str(root.get("definition") or ""),
        ipa=str(root.get("ipa") or ""),
    )
    tags: dict[AudioKey, str] = {}
    for index, (key, (word, pos, definition, ipa)) in enumerate(
        forms.items(), start=2
    ):
        on_progress(index, total)
        tags[key] = store_audio(
            word,
            config,
            write_data,
            part_of_speech=pos,
            definition=definition,
            ipa=ipa,
        )
    return root_audio, tags
