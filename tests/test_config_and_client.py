import json

import pytest

from anki_card_creator.config import DEFAULT_MODEL, normalize_config
from anki_card_creator.openai_client import (
    OpenAIError,
    error_detail,
    parse_chat_response,
)


def test_config_defaults_are_consistent():
    config = normalize_config()
    assert DEFAULT_MODEL == "gpt-5-mini"
    assert config["openai_model"] == DEFAULT_MODEL
    assert config["verify_ssl"] is False


def test_config_keeps_explicit_values():
    config = normalize_config({"openai_model": "custom", "verify_ssl": True})
    assert config["openai_model"] == "custom"
    assert config["verify_ssl"] is True


def test_parses_structured_chat_response():
    raw = json.dumps(
        {"choices": [{"message": {"content": '{"word":"record","results":[]}'}}]}
    )
    assert parse_chat_response(raw)["word"] == "record"


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "no choices"),
        ({"choices": [{"message": {"refusal": "no"}}]}, "Model refused"),
        ({"choices": [{"message": {"content": "not json"}}]}, "non-JSON"),
    ],
)
def test_chat_response_errors(payload, message):
    with pytest.raises(OpenAIError, match=message):
        parse_chat_response(json.dumps(payload))


def test_extracts_api_error_detail():
    assert error_detail('{"error":{"message":"bad key"}}', "fallback") == "bad key"
    assert error_detail("plain", "fallback") == "plain"
