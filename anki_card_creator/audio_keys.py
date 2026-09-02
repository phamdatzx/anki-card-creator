from __future__ import annotations

from .lookups.contracts import DefinitionResult

AudioKey = tuple[str, str]
DefinitionAudioKey = tuple[str, str, str]


def form_audio_key(word: str, part_of_speech: str) -> AudioKey:
    return word.strip().casefold(), part_of_speech.strip().casefold()


def definition_audio_key(
    word: str, result: DefinitionResult
) -> DefinitionAudioKey:
    return (
        word.strip().casefold(),
        str(result.get("partOfSpeech") or "").strip().casefold(),
        str(result.get("definition") or "").strip().casefold(),
    )
