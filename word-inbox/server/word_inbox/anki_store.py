"""The server's headless Anki collection and its AnkiWeb sync."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TypeVar

from anki.collection import Collection
from anki.errors import SyncError, SyncErrorKind
from anki.sync_pb2 import SyncAuth, SyncCollectionResponse

T = TypeVar("T")
_REQUIRED = SyncCollectionResponse.ChangesRequired
MEDIA_SYNC_TIMEOUT = 600.0


class SyncBlockedError(RuntimeError):
    """A full download would discard cards that only exist on the server."""


@dataclass
class SyncState:
    enabled: bool
    at: float | None = None
    ok: bool | None = None
    message: str = ""
    # True when only a forced download (losing unsynced server cards) helps.
    needs_forced_download: bool = False

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


class AnkiStore:
    """One open collection; every access goes through a lock.

    A collection is not thread-safe, and FastAPI runs plain ``def`` routes in
    a thread pool, so lookups run in parallel while collection work queues.
    """

    def __init__(
        self,
        data_dir: Path,
        *,
        ankiweb_username: str = "",
        ankiweb_password: str = "",
    ) -> None:
        self.data_dir = data_dir
        self.path = data_dir / "collection.anki2"
        self._auth_path = data_dir / "sync_auth.json"
        self._username = ankiweb_username
        self._password = ankiweb_password
        self._lock = threading.Lock()
        self._col: Collection | None = None
        self.sync_state = SyncState(enabled=bool(ankiweb_username))

    def open(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._col = Collection(str(self.path))

    def close(self) -> None:
        with self._lock:
            if self._col is not None:
                self._col.close()
                self._col = None

    @contextmanager
    def collection(self) -> Iterator[Collection]:
        with self._lock:
            if self._col is None:
                raise RuntimeError("The collection is not open.")
            yield self._col

    def read(self, query: Callable[[Collection], T]) -> T:
        """Run a read-only query; no sync."""
        with self.collection() as col:
            return query(col)

    def deck_id(self, name: str) -> int | None:
        with self.collection() as col:
            found = col.decks.id_for_name(name)
            return int(found) if found else None

    def change(self, write: Callable[[Collection], T]) -> tuple[T, SyncState]:
        """Pull, write, push. A failed sync never discards the change.

        Pulling first means ``write`` sees decks made or renamed elsewhere.
        """
        with self.collection() as col:
            if self.sync_state.enabled:
                self._sync_locked(col)
            result = write(col)
            state = (
                self._sync_locked(col)
                if self.sync_state.enabled
                else self.sync_state
            )
            return result, state

    def add(
        self, deck_id: int, write: Callable[[Collection], T]
    ) -> tuple[T, str, SyncState]:
        def checked(col: Collection) -> tuple[T, str]:
            deck = col.decks.get(deck_id, default=False)
            if not deck:
                raise LookupError(f"Deck {deck_id} does not exist.")
            return write(col), str(deck["name"])

        (result, name), state = self.change(checked)
        return result, name, state

    def sync(self, *, force_download: bool = False) -> SyncState:
        with self.collection() as col:
            if not self.sync_state.enabled:
                self.sync_state.message = "AnkiWeb sync is not configured."
                return self.sync_state
            return self._sync_locked(col, force_download=force_download)

    def _sync_locked(self, col: Collection, *, force_download: bool = False) -> SyncState:
        try:
            message = self._run_sync(col, force_download)
        except SyncBlockedError as exc:
            self.sync_state = SyncState(True, time.time(), False, str(exc), True)
        except Exception as exc:  # report any sync failure to the browser
            self.sync_state = SyncState(
                True, time.time(), False, f"Sync failed: {exc}"
            )
        else:
            self.sync_state = SyncState(True, time.time(), True, message)
        return self.sync_state

    def _run_sync(self, col: Collection, force_download: bool) -> str:
        auth = self._auth(col)
        try:
            out = col.sync_collection(auth, sync_media=False)
        except SyncError as exc:
            if exc.kind is not SyncErrorKind.AUTH or not self._password:
                raise
            # The cached key was revoked; log in again once.
            self._auth_path.unlink(missing_ok=True)
            auth = self._auth(col)
            out = col.sync_collection(auth, sync_media=False)
        if out.new_endpoint:
            auth.endpoint = out.new_endpoint
            self._save_auth(auth)

        if out.required in (_REQUIRED.NO_CHANGES, _REQUIRED.NORMAL_SYNC):
            message = "Synced with AnkiWeb."
        elif out.required == _REQUIRED.FULL_UPLOAD:
            # Uploading would replace the real collection with the server's.
            raise RuntimeError(
                "AnkiWeb asked for a full upload, which the server never does. "
                "Sync your collection from desktop Anki first."
            )
        else:
            pending = self._unsynced_notes(col)
            if pending and not force_download:
                raise SyncBlockedError(
                    f"AnkiWeb needs a one-way sync, and {pending} note(s) on the "
                    "server were never uploaded. Downloading from AnkiWeb would "
                    "discard them."
                )
            col.close_for_full_sync()
            try:
                col.full_upload_or_download(auth=auth, server_usn=None, upload=False)
            finally:
                col.reopen(after_full_sync=True)
            message = "Downloaded the collection from AnkiWeb."

        self._sync_media(col, auth)
        if out.server_message:
            message += f" AnkiWeb says: {out.server_message}"
        return message

    @staticmethod
    def _unsynced_notes(col: Collection) -> int:
        return int(col.db.scalar("select count() from notes where usn = -1") or 0)

    @staticmethod
    def _sync_media(col: Collection, auth: SyncAuth) -> None:
        col.sync_media(auth)
        deadline = time.monotonic() + MEDIA_SYNC_TIMEOUT
        while col.media_sync_status().active:
            if time.monotonic() > deadline:
                raise RuntimeError("Media sync is taking too long; try again later.")
            time.sleep(0.5)

    def _auth(self, col: Collection) -> SyncAuth:
        if self._auth_path.is_file():
            saved = json.loads(self._auth_path.read_text())
            auth = SyncAuth(hkey=saved["hkey"])
            if saved.get("endpoint"):
                auth.endpoint = saved["endpoint"]
            return auth
        if not self._password:
            raise RuntimeError("Set ANKIWEB_PASSWORD to log in to AnkiWeb.")
        auth = col.sync_login(self._username, self._password, endpoint=None)
        self._save_auth(auth)
        return auth

    def _save_auth(self, auth: SyncAuth) -> None:
        data = {"hkey": auth.hkey}
        if auth.HasField("endpoint"):
            data["endpoint"] = auth.endpoint
        self._auth_path.write_text(json.dumps(data))
        self._auth_path.chmod(0o600)
