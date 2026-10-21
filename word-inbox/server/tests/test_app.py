from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from word_inbox.app import create_app
from word_inbox.auth import issue_token, verify_token
from word_inbox.settings import load_settings

DEFINITION = {
    "definition": "to choose after thinking",
    "vietnamese": "quyết định",
    "partOfSpeech": "verb",
    "ipa": "/dɪˈsaɪd/",
    "synonyms": ["choose"],
    "examples": ["We decided to stay."],
    "popularity": 5,
    "difficulty": 2,
}


def _form(word: str, pos: str) -> dict[str, Any]:
    return {
        "word": word,
        "type": pos,
        "definition": f"{word} meaning",
        "vietnamese": "vi",
        "examples": [f"An example with {word}."],
        "ipa": "",
        "popularity": None,
        "difficulty": None,
    }


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def fake_chat(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["api_key"] == "sk-test"
        return {"word": "decide", "results": [DEFINITION, DEFINITION]}

    monkeypatch.setattr("anki_card_creator.lookups.normal.chat_json", fake_chat)
    monkeypatch.setattr(
        "anki_card_creator.audio.speech_mp3", lambda **_kwargs: b"ID3fake"
    )
    settings = load_settings(
        {
            "APP_PASSWORD": "pw",
            "DATA_DIR": str(tmp_path),
            "OPENAI_API_KEY": "sk-test",
        }
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        token = test_client.post("/api/login", json={"password": "pw"}).json()["token"]
        test_client.headers["Authorization"] = f"Bearer {token}"
        yield test_client


def test_token_round_trip_and_expiry():
    token = issue_token("secret", 60, now=1000)
    assert verify_token("secret", token, now=1030)
    assert not verify_token("secret", token, now=1061)
    assert not verify_token("other", token, now=1030)
    assert not verify_token("secret", "garbage", now=1030)


def test_login_and_auth_are_required(tmp_path: Path):
    settings = load_settings({"APP_PASSWORD": "pw", "DATA_DIR": str(tmp_path)})
    with TestClient(create_app(settings)) as anonymous:
        assert anonymous.post("/api/login", json={"password": "no"}).status_code == 401
        assert anonymous.get("/api/decks").status_code == 401
        assert anonymous.get("/api/health").json() == {"ok": True}


def test_lookup_then_create_writes_notes_with_audio(client: TestClient):
    found = client.post("/api/lookup", json={"type": "normal", "input": "decide"})
    assert found.status_code == 200
    payload = found.json()["payload"]
    assert payload["word"] == "decide"

    decks = client.get("/api/decks").json()
    deck_id = decks["defaultDeckId"]
    assert deck_id is not None
    payload["results"] = payload["results"][:1]
    payload["results"][0]["definition"] = "edited definition"
    created = client.post(
        "/api/cards", json={"type": "normal", "deckId": deck_id, "payload": payload}
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["added"] == 1
    assert body["deck"] == "Default"
    assert body["sync"]["enabled"] is False

    with _collection(client) as col:
        note_ids = col.find_notes('"note:VIP Translate"')
        assert len(note_ids) == 1
        note = col.get_note(note_ids[0])
        assert note["Word"] == "decide"
        assert note["Definition"] == "edited definition"
        assert note["Audio"].startswith("[sound:anki-card-creator-")


def _collection(client: TestClient):
    return client.app.state.store.collection()


def test_create_reports_problems(client: TestClient):
    deck_id = client.get("/api/decks").json()["defaultDeckId"]

    def post(card_type: str, payload: dict[str, Any], deck: int = deck_id):
        return client.post(
            "/api/cards", json={"type": card_type, "deckId": deck, "payload": payload}
        )

    empty = post("normal", {"word": "decide", "results": []})
    assert empty.status_code == 400
    assert empty.json()["detail"] == "Select at least one definition."

    incomplete_root = {**_form("decide", "verb"), "examples": []}
    forms = post("word_form", {"rootWord": incomplete_root, "other": [_form("decision", "noun")]})
    assert forms.status_code == 400
    assert "• root word" in forms.json()["detail"]

    blank_word = post("vietnamese", {"query": "q", "results": [{**DEFINITION, "word": ""}]})
    assert blank_word.json()["detail"] == "Each selected result needs a word:\n• result 1"

    malformed = post("word_pattern", {"gap": "x"})
    assert malformed.status_code == 400
    assert malformed.json()["detail"].startswith("Invalid payload:")

    missing_deck = post("sentence", {"vietnamese": "xin chào", "sentence": "hello"}, 999)
    assert missing_deck.status_code == 400
    assert client.post("/api/lookup", json={"type": "nope", "input": "x"}).status_code == 400


def test_word_form_and_sentence_cards(client: TestClient):
    deck_id = client.get("/api/decks").json()["defaultDeckId"]
    payload = {
        "rootWord": _form("decide", "verb"),
        "other": [_form("decision", "noun"), _form("decisive", "adjective")],
    }
    forms = client.post(
        "/api/cards", json={"type": "word_form", "deckId": deck_id, "payload": payload}
    )
    assert forms.status_code == 200, forms.text
    assert forms.json()["added"] == 2
    sentence = client.post(
        "/api/cards",
        json={
            "type": "sentence",
            "deckId": deck_id,
            "payload": {"vietnamese": "xin chào", "sentence": "hello"},
        },
    )
    assert sentence.json()["added"] == 1
    with _collection(client) as col:
        assert len(col.find_notes('"note:VIP Word Form"')) == 2
        assert len(col.find_notes('"note:VIP Sentence"')) == 1


COLLOCATIONS = {
    "keyword": "decision",
    "items": [
        {
            "pattern": "verb + decision",
            "collocation": "make a decision",
            "gap": "She finally ___ a decision to move abroad.",
            "answer": "made",
            "vietnamese": "đưa ra quyết định",
            "usage": "neutral, very common",
        },
        {
            "pattern": "adjective + decision",
            "collocation": "a tough decision",
            "gap": "It was a ___ decision for the whole family.",
            "answer": "tough",
            "vietnamese": "quyết định khó khăn",
            "usage": "informal",
        },
        {
            "pattern": "decision + preposition",
            "collocation": "decision on",
            "gap": "We need a decision ___ the budget.",
            "answer": "on",
            "vietnamese": "quyết định về",
            "usage": "neutral",
        },
    ],
}


def test_collocation_lookup_then_create_one_note_per_item(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    def fake_chat(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["schema_name"] == "collocation_lookup"
        assert kwargs["user"] == "Keyword: decision"
        return COLLOCATIONS

    monkeypatch.setattr("anki_card_creator.lookups.collocation.chat_json", fake_chat)
    found = client.post("/api/lookup", json={"type": "collocation", "input": "decision"})
    assert found.status_code == 200, found.text
    payload = found.json()["payload"]
    assert len(payload["items"]) == 3

    payload["items"] = payload["items"][:2]
    payload["items"][1]["usage"] = "edited usage"
    deck_id = client.get("/api/decks").json()["defaultDeckId"]
    created = client.post(
        "/api/cards", json={"type": "collocation", "deckId": deck_id, "payload": payload}
    )
    assert created.status_code == 200, created.text
    assert created.json()["added"] == 2

    with _collection(client) as col:
        notes = [col.get_note(nid) for nid in col.find_notes('"note:VIP Collocation"')]
        by_answer = {note["Answer"]: note for note in notes}
        assert set(by_answer) == {"made", "tough"}
        made = by_answer["made"]
        assert made["Keyword"] == "decision"
        assert made["Pattern"] == "verb + decision"
        assert made["Gap"] == "She finally ___ a decision to move abroad."
        assert made["Sentence"] == "She finally <b>made</b> a decision to move abroad."
        assert made["Collocation"] == "make a decision"
        assert by_answer["tough"]["Usage"] == "edited usage"
        assert made.cards()[0].did == deck_id


def test_collocation_create_reports_problems(client: TestClient):
    deck_id = client.get("/api/decks").json()["defaultDeckId"]

    def post(payload: dict[str, Any]):
        return client.post(
            "/api/cards", json={"type": "collocation", "deckId": deck_id, "payload": payload}
        )

    none = post({"keyword": "decision", "items": []})
    assert none.status_code == 400
    assert none.json()["detail"] == "Select at least one collocation."
    broken = {**COLLOCATIONS["items"][0], "gap": "She made a decision."}
    bad = post({"keyword": "decision", "items": [broken]})
    assert bad.status_code == 400
    assert bad.json()["detail"].endswith("• make a decision")


PHRASE = {
    "phrase": "sharp fall",
    "results": [
        {
            "structure": "adjective + noun",
            "definition": "a sudden, large decrease",
            "vietnamese": "sự giảm mạnh",
            "examples": ["Shares saw a sharp fall in early trading."],
            "usage": "news, business",
        },
        {
            "structure": "adjective + noun",
            "definition": "a steep drop in level or height",
            "vietnamese": "dốc đứng",
            "examples": ["There is a sharp fall to the river."],
            "usage": "descriptive",
        },
        {
            "structure": "adjective + noun",
            "definition": "a hard tumble to the ground",
            "vietnamese": "cú ngã mạnh",
            "examples": ["She had a sharp fall on the ice."],
            "usage": "neutral",
        },
    ],
}


def test_phrase_lookup_then_create_one_note_per_sense(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    def fake_chat(**kwargs: Any) -> dict[str, Any]:
        assert kwargs["schema_name"] == "phrase_lookup"
        assert kwargs["user"] == "Phrase: sharp fall"
        return PHRASE

    monkeypatch.setattr("anki_card_creator.lookups.phrase.chat_json", fake_chat)
    found = client.post("/api/lookup", json={"type": "phrase", "input": "sharp fall"})
    assert found.status_code == 200, found.text
    payload = found.json()["payload"]
    assert len(payload["results"]) == 3

    payload["results"] = [payload["results"][0], payload["results"][2]]
    payload["results"][1]["usage"] = "edited usage"
    deck_id = client.get("/api/decks").json()["defaultDeckId"]
    created = client.post(
        "/api/cards", json={"type": "phrase", "deckId": deck_id, "payload": payload}
    )
    assert created.status_code == 200, created.text
    assert created.json()["added"] == 2

    with _collection(client) as col:
        notes = [col.get_note(nid) for nid in col.find_notes('"note:VIP Phrase"')]
        by_definition = {note["Definition"]: note for note in notes}
        assert set(by_definition) == {
            "a sudden, large decrease",
            "a hard tumble to the ground",
        }
        first = by_definition["a sudden, large decrease"]
        assert first["Phrase"] == "sharp fall"
        assert first["Hint"] == "s___ f___"
        assert first["Examples"] == (
            '<ul class="examples-list"><li>Shares saw a sharp fall in early trading.</li></ul>'
        )
        assert by_definition["a hard tumble to the ground"]["Usage"] == "edited usage"
        assert first.cards()[0].did == deck_id


def test_phrase_create_reports_problems(client: TestClient):
    deck_id = client.get("/api/decks").json()["defaultDeckId"]

    def post(payload: dict[str, Any]):
        return client.post(
            "/api/cards", json={"type": "phrase", "deckId": deck_id, "payload": payload}
        )

    none = post({"phrase": "sharp fall", "results": []})
    assert none.status_code == 400
    assert none.json()["detail"] == "Select at least one meaning."
    blank = post({"phrase": " ", "results": PHRASE["results"][:1]})
    assert blank.json()["detail"] == "Enter the phrase."
    empty_definition = {**PHRASE["results"][0], "definition": ""}
    bad = post({"phrase": "sharp fall", "results": [empty_definition]})
    assert bad.status_code == 400
    assert bad.json()["detail"].endswith("• meaning 1")
