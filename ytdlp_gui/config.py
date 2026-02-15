from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".ytdlp_gui"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

@dataclass
class AppSettings:
    output_dir: str = str(Path.home() / "Downloads" / "YouTube")
    quality: str = "Maximum"
    format: str = "mp4"
    theme: str = "light"
    window_width: int = 1100
    window_height: int = 820

    subtitles: bool = False
    subtitle_langs: str = "en,en-US"
    thumbnail: bool = True
    metadata: bool = True
    chapters: bool = True
    sponsorblock: bool = False

    audio_codec: str = "mp3"
    audio_quality: int = 320

    cookies_path: str = ""
    proxy: str = ""
    speed_limit: int = 0

    max_concurrent: int = 2
    max_retries: int = 10
    fragment_retries: int = 10
    concurrent_fragments: int = 4
    http_chunk_size: int = 10_485_760
    buffer_size: int = 131_072
    socket_timeout: int = 30

    windows_filenames: bool = True
    restrict_filenames: bool = False
    overwrites: bool = False

class SettingsManager:

    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.settings: AppSettings = self._load()

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any) -> None:
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)

    def save(self) -> None:
        try:
            SETTINGS_FILE.write_text(
                json.dumps(asdict(self.settings), indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Failed to save settings: %s", exc)

    def reset(self) -> None:
        self.settings = AppSettings()
        self.save()

    def _load(self) -> AppSettings:
        if SETTINGS_FILE.exists():
            try:
                raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                known_fields = {f.name for f in fields(AppSettings)}
                known = {
                    k: v for k, v in raw.items() if k in known_fields
                }
                return AppSettings(**known)
            except Exception:
                logger.warning("Corrupt settings file — using defaults")
        return AppSettings()

_MAX_HISTORY = 1000

def load_history() -> list[dict[str, Any]]:
    if HISTORY_FILE.exists():
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data[:_MAX_HISTORY]
        except Exception:
            pass
    return []

def save_history(entries: list[dict[str, Any]]) -> None:
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        trimmed = entries[:_MAX_HISTORY]
        HISTORY_FILE.write_text(
            json.dumps(trimmed, indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as exc:
        logger.error("Failed to save history: %s", exc)
