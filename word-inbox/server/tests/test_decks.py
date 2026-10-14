from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from word_inbox.app import create_app
from word_inbox.settings import load_settings


@pytest.fixture
def client(tmp_path: Path):
    settings = load_settings({"APP_PASSWORD": "pw", "DATA_DIR": str(tmp_path)})
    with TestClient(create_app(settings)) as test_client:
        token = test_client.post("/api/login", json={"password": "pw"}).json()["token"]
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client


def _names(client: TestClient) -> list[str]:
    return [deck["name"] for deck in client.get("/api/decks").json()["decks"]]


def test_create_rename_delete(client: TestClient):
    created = client.post("/api/decks", json={"name": "  Langs :: Spanish "})
    assert created.status_code == 201, created.text
    deck = created.json()["deck"]
    assert deck["name"] == "Langs::Spanish" and deck["cards"] == 0
    assert created.json()["sync"]["enabled"] is False
    assert "Langs::Spanish" in _names(client)

    renamed = client.patch(f"/api/decks/{deck['id']}", json={"name": "Spanish"})
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["deck"] == {"id": deck["id"], "name": "Spanish", "cards": 0}

    deleted = client.delete(f"/api/decks/{deck['id']}")
    assert deleted.json()["deleted"] == {"name": "Spanish", "cards": 0}
    assert "Spanish" not in _names(client)
    assert client.delete(f"/api/decks/{deck['id']}").status_code == 404


def test_names_are_validated(client: TestClient):
    spanish = client.post("/api/decks", json={"name": "Spanish"}).json()["deck"]
    french = client.post("/api/decks", json={"name": "French"}).json()["deck"]

    # Anki would silently make "spanish+"; refuse instead (names ignore case).
    duplicate = client.post("/api/decks", json={"name": "spanish"})
    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["detail"]
    clash = client.patch(f"/api/decks/{french['id']}", json={"name": "SPANISH"})
    assert clash.status_code == 409

    for bad in ("", "   ", "Parent::", "::Child"):
        assert client.post("/api/decks", json={"name": bad}).status_code == 400

    # Changing only the case of a deck's own name is allowed.
    same = client.patch(f"/api/decks/{spanish['id']}", json={"name": "SPANISH"})
    assert same.status_code == 200 and same.json()["deck"]["name"] == "SPANISH"


def test_default_deck_cannot_be_deleted(client: TestClient):
    response = client.delete("/api/decks/1")
    assert response.status_code == 400
    assert "Default" in response.json()["detail"]
    assert "Default" in _names(client)


def test_deleting_a_parent_removes_subdecks_and_cards(client: TestClient):
    child = client.post("/api/decks", json={"name": "Langs::French"}).json()["deck"]
    with client.app.state.store.collection() as col:
        note = col.new_note(col.models.by_name("Basic"))
        note["Front"], note["Back"] = "bonjour", "hello"
        col.add_note(note, child["id"])
    decks = {deck["name"]: deck for deck in client.get("/api/decks").json()["decks"]}
    assert decks["Langs"]["cards"] == 1  # counts include subdecks, for the confirm

    deleted = client.delete(f"/api/decks/{decks['Langs']['id']}").json()["deleted"]
    assert deleted == {"name": "Langs", "cards": 1}
    assert not {"Langs", "Langs::French"} & set(_names(client))
