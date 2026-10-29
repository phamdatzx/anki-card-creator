from __future__ import annotations

import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from anki_card_creator.create_checks import problems_message
from anki_card_creator.openai_client import OpenAIError

from .anki_store import AnkiStore
from .auth import check_password, issue_token, verify_token
from .cards import CARD_TYPES, CardRequestError, check_payload, create_cards, lookup
from .decks import DeckError, create_deck, delete_deck, list_decks, rename_deck
from .settings import Settings, load_settings


class LoginBody(BaseModel):
    password: str


class LookupBody(BaseModel):
    type: str
    input: str


class CardsBody(BaseModel):
    type: str
    deckId: int  # noqa: N815 - JSON field name
    payload: dict[str, Any]


class ModelBody(BaseModel):
    model: str


class DeckBody(BaseModel):
    name: str


class SyncBody(BaseModel):
    forceDownload: bool = False  # noqa: N815 - JSON field name


def create_app(
    settings: Settings | None = None, store: AnkiStore | None = None
) -> FastAPI:
    settings = settings or load_settings()
    store = store or AnkiStore(
        settings.data_dir,
        ankiweb_username=settings.ankiweb_username,
        ankiweb_password=settings.ankiweb_password,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        store.open()
        if settings.sync_enabled:
            # The first sync may download a whole collection; don't block
            # startup on it. The store lock queues requests behind it.
            threading.Thread(target=store.sync, daemon=True).start()
        yield
        store.close()

    app = FastAPI(title="Word Inbox", lifespan=lifespan)
    app.state.store = store
    default_model = settings.config["openai_model"]
    model_choices = settings.model_choices or (default_model,)
    # In memory on purpose: a restart or redeploy goes back to OPENAI_MODEL.
    app.state.model = default_model

    def require_token(authorization: Annotated[str, Header()] = "") -> None:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not verify_token(
            settings.app_secret, token.strip()
        ):
            raise HTTPException(401, "Sign in again.")

    authed = [Depends(require_token)]

    def _card_type(value: str) -> str:
        if value not in CARD_TYPES:
            raise HTTPException(400, f"Unknown card type: {value}")
        return value

    @app.get("/api/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/api/login")
    def login(body: LoginBody) -> dict[str, str]:
        if not check_password(body.password, settings.app_password):
            raise HTTPException(401, "Wrong password.")
        return {"token": issue_token(settings.app_secret, settings.token_ttl_seconds)}

    @app.get("/api/status", dependencies=authed)
    def status() -> dict[str, Any]:
        return {"sync": store.sync_state.as_json()}

    def _model_state() -> dict[str, Any]:
        return {
            "model": app.state.model,
            "default": default_model,
            "choices": list(model_choices),
        }

    @app.get("/api/model", dependencies=authed)
    def get_model() -> dict[str, Any]:
        return _model_state()

    @app.put("/api/model", dependencies=authed)
    def set_model(body: ModelBody) -> dict[str, Any]:
        if body.model not in model_choices:
            raise HTTPException(
                400, f"{body.model} is not in OPENAI_MODELS on the server."
            )
        app.state.model = body.model
        return _model_state()

    @app.get("/api/decks", dependencies=authed)
    def decks() -> dict[str, Any]:
        return {
            "decks": store.read(list_decks),
            "defaultDeckId": store.deck_id(settings.default_deck),
        }

    def _deck_change(write: Any) -> tuple[Any, Any]:
        try:
            return store.change(write)
        except DeckError as exc:
            raise HTTPException(exc.status, str(exc)) from exc

    @app.post("/api/decks", dependencies=authed, status_code=201)
    def create_deck_route(body: DeckBody) -> dict[str, Any]:
        deck, sync = _deck_change(lambda col: create_deck(col, body.name))
        return {"deck": deck, "sync": sync.as_json()}

    @app.patch("/api/decks/{deck_id}", dependencies=authed)
    def rename_deck_route(deck_id: int, body: DeckBody) -> dict[str, Any]:
        deck, sync = _deck_change(lambda col: rename_deck(col, deck_id, body.name))
        return {"deck": deck, "sync": sync.as_json()}

    @app.delete("/api/decks/{deck_id}", dependencies=authed)
    def delete_deck_route(deck_id: int) -> dict[str, Any]:
        deleted, sync = _deck_change(lambda col: delete_deck(col, deck_id))
        return {"deleted": deleted, "sync": sync.as_json()}

    @app.post("/api/lookup", dependencies=authed)
    def lookup_route(body: LookupBody) -> dict[str, Any]:
        card_type = _card_type(body.type)
        try:
            config = {**settings.config, "openai_model": app.state.model}
            payload = lookup(card_type, body.input, config)  # type: ignore[arg-type]
        except OpenAIError as exc:
            raise HTTPException(502, str(exc)) from exc
        return {"type": card_type, "payload": payload}

    @app.post("/api/cards", dependencies=authed)
    def cards_route(body: CardsBody) -> dict[str, Any]:
        card_type = _card_type(body.type)
        try:
            payload = check_payload(card_type, body.payload)
        except CardRequestError as exc:
            raise HTTPException(400, problems_message(exc.problems)) from exc
        try:
            added, deck_name, sync = store.add(
                body.deckId,
                lambda col: create_cards(
                    col, body.deckId, card_type, payload, settings.config
                ),
            )
        except LookupError as exc:
            raise HTTPException(400, str(exc)) from exc
        except OpenAIError as exc:
            raise HTTPException(502, f"Could not create cards: {exc}") from exc
        return {"added": added, "deck": deck_name, "sync": sync.as_json()}

    @app.post("/api/sync", dependencies=authed)
    def sync_route(body: SyncBody) -> dict[str, Any]:
        return {"sync": store.sync(force_download=body.forceDownload).as_json()}

    @app.exception_handler(Exception)
    async def _unexpected(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"detail": f"Server error: {exc}"}, status_code=500)

    if settings.static_dir is not None and settings.static_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True))
    return app


def app() -> FastAPI:
    """uvicorn factory: ``uvicorn --factory word_inbox.app:app``."""
    return create_app()
