from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from anki.errors import SyncError, SyncErrorKind
from anki.sync_pb2 import SyncAuth, SyncCollectionResponse

from word_inbox.anki_store import AnkiStore

R = SyncCollectionResponse.ChangesRequired


class FakeCollection:
    def __init__(self, required: int, unsynced: int = 0) -> None:
        self.required = required
        self.unsynced = unsynced
        self.calls: list[str] = []
        self.logins = 0
        self.fail_auth_once = False
        self.db = SimpleNamespace(scalar=lambda _sql: self.unsynced)

    def sync_login(self, username: str, password: str, endpoint: None) -> SyncAuth:
        self.logins += 1
        return SyncAuth(hkey=f"key-{self.logins}")

    def sync_collection(self, auth: SyncAuth, sync_media: bool) -> SyncCollectionResponse:
        if self.fail_auth_once:
            self.fail_auth_once = False
            raise SyncError("expired", None, None, None, SyncErrorKind.AUTH)
        self.calls.append(f"sync:{auth.hkey}")
        return SyncCollectionResponse(
            required=self.required, new_endpoint="https://sync2.ankiweb.net/"
        )

    def close_for_full_sync(self) -> None:
        self.calls.append("close")

    def full_upload_or_download(self, *, auth, server_usn, upload: bool) -> None:
        self.calls.append("upload" if upload else "download")

    def reopen(self, after_full_sync: bool = False) -> None:
        self.calls.append("reopen")

    def sync_media(self, auth: SyncAuth) -> None:
        self.calls.append("media")

    def media_sync_status(self):
        return SimpleNamespace(active=False)


@pytest.fixture
def store(tmp_path: Path) -> AnkiStore:
    return AnkiStore(tmp_path, ankiweb_username="me@example.com", ankiweb_password="pw")


def test_normal_sync_logs_in_once_and_keeps_new_endpoint(store: AnkiStore, tmp_path: Path):
    col = FakeCollection(R.NORMAL_SYNC)
    state = store._sync_locked(col)
    assert state.ok and state.message == "Synced with AnkiWeb."
    store._sync_locked(col)
    assert col.logins == 1
    assert col.calls == ["sync:key-1", "media", "sync:key-1", "media"]
    saved = json.loads((tmp_path / "sync_auth.json").read_text())
    assert saved == {"hkey": "key-1", "endpoint": "https://sync2.ankiweb.net/"}


def test_expired_key_logs_in_again(store: AnkiStore):
    col = FakeCollection(R.NO_CHANGES)
    store._sync_locked(col)
    col.fail_auth_once = True
    assert store._sync_locked(col).ok
    assert col.logins == 2


def test_full_sync_downloads_and_never_uploads(store: AnkiStore):
    col = FakeCollection(R.FULL_SYNC)
    state = store._sync_locked(col)
    assert state.ok and state.message == "Downloaded the collection from AnkiWeb."
    assert col.calls == ["sync:key-1", "close", "download", "reopen", "media"]

    upload = FakeCollection(R.FULL_UPLOAD)
    state = store._sync_locked(upload)
    assert not state.ok and "never does" in state.message
    assert "upload" not in upload.calls


def test_full_sync_with_unsynced_server_notes_needs_confirmation(store: AnkiStore):
    col = FakeCollection(R.FULL_DOWNLOAD, unsynced=3)
    state = store._sync_locked(col)
    assert not state.ok and state.needs_forced_download
    assert "3 note(s)" in state.message
    assert "download" not in col.calls

    state = store._sync_locked(col, force_download=True)
    assert state.ok and "download" in col.calls


def test_changes_pull_before_and_push_after(store: AnkiStore):
    col = FakeCollection(R.NORMAL_SYNC)
    store._col = col  # the store syncs whatever collection it holds
    result, state = store.change(lambda held: held.calls.append("write") or "done")
    assert result == "done" and state.ok
    assert col.calls == ["sync:key-1", "media", "write", "sync:key-1", "media"]
