from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from word_inbox.app import create_app
from word_inbox.settings import load_settings

ENV = {
    "APP_PASSWORD": "pw",
    "OPENAI_API_KEY": "sk-test",
    "OPENAI_MODEL": "gpt-5-mini",
    "OPENAI_MODELS": " gpt-5 , gpt-5-mini,,gpt-4.1-mini, gpt-5",
}


def _login(client: TestClient) -> TestClient:
    token = client.post("/api/login", json={"password": "pw"}).json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


def test_choices_are_trimmed_deduplicated_and_default_first(tmp_path: Path):
    settings = load_settings({**ENV, "DATA_DIR": str(tmp_path)})
    assert settings.model_choices == ("gpt-5-mini", "gpt-5", "gpt-4.1-mini")
    only_default = load_settings({"APP_PASSWORD": "pw", "DATA_DIR": str(tmp_path)})
    assert only_default.model_choices == (only_default.config["openai_model"],)


def test_switching_model_changes_lookups_until_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    seen: list[str] = []

    def fake_chat(**kwargs: Any) -> dict[str, Any]:
        seen.append(kwargs["model"])
        return {"vietnamese": "xin chào"}

    monkeypatch.setattr("anki_card_creator.lookups.sentence.chat_json", fake_chat)
    settings = load_settings({**ENV, "DATA_DIR": str(tmp_path)})
    with TestClient(create_app(settings)) as client:
        _login(client)
        state = client.get("/api/model").json()
        assert state == {
            "model": "gpt-5-mini",
            "default": "gpt-5-mini",
            "choices": ["gpt-5-mini", "gpt-5", "gpt-4.1-mini"],
        }

        def look_up() -> None:
            response = client.post("/api/lookup", json={"type": "sentence", "input": "hi"})
            assert response.status_code == 200, response.text

        look_up()
        changed = client.put("/api/model", json={"model": "gpt-5"})
        assert changed.status_code == 200 and changed.json()["model"] == "gpt-5"
        look_up()

        refused = client.put("/api/model", json={"model": "gpt-unknown"})
        assert refused.status_code == 400
        assert client.get("/api/model").json()["model"] == "gpt-5"
        look_up()
        assert seen == ["gpt-5-mini", "gpt-5", "gpt-5"]

    # A restart builds a fresh app from the same settings: back to the default.
    with TestClient(create_app(settings)) as restarted:
        assert _login(restarted).get("/api/model").json()["model"] == "gpt-5-mini"


def test_model_routes_need_login(tmp_path: Path):
    settings = load_settings({**ENV, "DATA_DIR": str(tmp_path)})
    with TestClient(create_app(settings)) as anonymous:
        assert anonymous.get("/api/model").status_code == 401
        assert anonymous.put("/api/model", json={"model": "gpt-5"}).status_code == 401
