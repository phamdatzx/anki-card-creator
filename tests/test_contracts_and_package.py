import json
import subprocess
import zipfile
from pathlib import Path
from typing import get_type_hints

import pytest

from anki_card_creator.lookups.contracts import (
    NormalPayload,
    WordFormPayload,
    WordPatternPayload,
    validate_normal_payload,
)
from anki_card_creator.lookups.schemas import (
    NORMAL_SCHEMA,
    WORD_FORM_SCHEMA,
    WORD_PATTERN_SCHEMA,
)

ROOT = Path(__file__).parents[1]


def test_payload_contracts_match_schema_top_level_keys():
    pairs = (
        (NormalPayload, NORMAL_SCHEMA),
        (WordFormPayload, WORD_FORM_SCHEMA),
        (WordPatternPayload, WORD_PATTERN_SCHEMA),
    )
    for contract, schema in pairs:
        assert set(get_type_hints(contract)) == set(schema["properties"])
        assert set(schema["required"]) == set(schema["properties"])
        assert schema["additionalProperties"] is False


def test_checked_in_config_uses_code_default():
    config = json.loads((ROOT / "anki_card_creator/config.json").read_text())
    assert config["openai_model"] == "gpt-5-mini"


def test_normal_payload_validation_checks_nested_fields_and_scores():
    payload = {
        "word": "record",
        "results": [
            {
                "definition": "to save information",
                "vietnamese": "ghi lại",
                "partOfSpeech": "verb",
                "ipa": "/rɪˈkɔrd/",
                "synonyms": ["save"],
                "examples": ["Record the meeting."],
                "popularity": 5,
                "difficulty": 2,
            }
        ],
    }
    assert validate_normal_payload(payload) is payload
    payload["results"][0]["popularity"] = 6
    with pytest.raises(ValueError, match="integer from 1 to 5"):
        validate_normal_payload(payload)


def test_normal_payload_validation_rejects_invalid_nested_shape():
    with pytest.raises(ValueError, match="list of strings"):
        validate_normal_payload(
            {
                "word": "record",
                "results": [
                    {
                        "definition": "save",
                        "vietnamese": "ghi lại",
                        "partOfSpeech": "verb",
                        "ipa": "/r/",
                        "synonyms": "save",
                        "examples": [],
                        "popularity": 4,
                        "difficulty": 2,
                    }
                ],
            }
        )


def test_package_is_recursive_and_excludes_local_files(tmp_path):
    package = ROOT / "anki-card-creator.ankiaddon"
    subprocess.run([str(ROOT / "package.sh")], cwd=ROOT, check=True)
    with zipfile.ZipFile(package) as archive:
        names = set(archive.namelist())
    assert "lookups/normal.py" in names
    assert "notes/word_form.py" in names
    assert "ui/dialog.py" in names
    assert "bootstrap.py" in names
    assert "audio.py" in names
    assert "config.json" in names
    assert "manifest.json" in names
    assert "meta.json" not in names
    assert not any("__pycache__" in name for name in names)
