from __future__ import annotations

import os
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from anki_card_creator.config import AddonConfig, normalize_config

_TRUE = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_password: str
    app_secret: str
    data_dir: Path
    config: AddonConfig
    ankiweb_username: str
    ankiweb_password: str
    default_deck: str
    static_dir: Path | None
    # Models the page may switch lookups to; the first is OPENAI_MODEL.
    model_choices: tuple[str, ...] = ()
    token_ttl_seconds: int = 30 * 24 * 3600

    @property
    def sync_enabled(self) -> bool:
        return bool(self.ankiweb_username)


def _flag(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in _TRUE


def _secret(env: Mapping[str, str], data_dir: Path) -> str:
    """Use APP_SECRET, else a random secret persisted in the data dir."""
    explicit = env.get("APP_SECRET", "").strip()
    if explicit:
        return explicit
    path = data_dir / "app_secret"
    if path.is_file():
        return path.read_text().strip()
    data_dir.mkdir(parents=True, exist_ok=True)
    value = secrets.token_hex(32)
    path.write_text(value)
    path.chmod(0o600)
    return value


def _model_choices(listed: str, default: str) -> tuple[str, ...]:
    """OPENAI_MODELS in order, deduplicated, with the default first."""
    names = [name.strip() for name in listed.split(",")]
    return tuple(dict.fromkeys([default, *(name for name in names if name)]))


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    values = os.environ if env is None else env
    password = values.get("APP_PASSWORD", "")
    if not password:
        raise RuntimeError("Set APP_PASSWORD before starting Word Inbox.")
    data_dir = Path(values.get("DATA_DIR") or "/data")
    static = values.get("STATIC_DIR", "").strip()
    config = normalize_config(
        {
            # Unlike Anki's bundled OpenSSL, a server's CA store works,
            # so verify certificates unless told otherwise.
            "verify_ssl": _flag(values.get("VERIFY_SSL"), True),
            "openai_api_key": values.get("OPENAI_API_KEY", ""),
            "openai_model": values.get("OPENAI_MODEL", "").strip(),
            "openai_base_url": values.get("OPENAI_BASE_URL", ""),
            "openai_tts_model": values.get("OPENAI_TTS_MODEL", ""),
            "openai_tts_voice": values.get("OPENAI_TTS_VOICE", ""),
        }
    )
    return Settings(
        app_password=password,
        app_secret=_secret(values, data_dir),
        data_dir=data_dir,
        config=config,
        ankiweb_username=values.get("ANKIWEB_USERNAME", "").strip(),
        ankiweb_password=values.get("ANKIWEB_PASSWORD", ""),
        default_deck=values.get("DEFAULT_DECK", "").strip() or "Default",
        static_dir=Path(static) if static else None,
        model_choices=_model_choices(
            values.get("OPENAI_MODELS", ""), config["openai_model"]
        ),
    )
