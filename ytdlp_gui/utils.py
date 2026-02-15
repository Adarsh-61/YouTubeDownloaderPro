from __future__ import annotations

import os
import re
import shutil
import sys

_YOUTUBE_PATTERNS = [
    r"https?://(?:www\.)?youtube\.com/watch\?.*v=[\w-]+",
    r"https?://(?:www\.)?youtube\.com/playlist\?.*list=[\w-]+",
    r"https?://(?:www\.)?youtube\.com/shorts/[\w-]+",
    r"https?://youtu\.be/[\w-]+",
    r"https?://(?:www\.)?youtube-nocookie\.com/embed/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/embed/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/@[\w.-]+(?:/[\w-]+)?",
    r"https?://(?:www\.)?youtube\.com/channel/[\w-]+(?:/[\w-]+)?",
    r"https?://(?:www\.)?youtube\.com/c/[\w.-]+(?:/[\w-]+)?",
    r"https?://(?:www\.)?youtube\.com/user/[\w.-]+(?:/[\w-]+)?",
    r"https?://music\.youtube\.com/watch\?.*v=[\w-]+",
    r"https?://music\.youtube\.com/playlist\?.*list=[\w-]+",
    r"https?://(?:www\.)?youtube\.com/live/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/clip/[\w-]+",
    r"https?://(?:www\.)?youtube\.com/feed/[\w-]+",
]

_YOUTUBE_RE = re.compile(
    "|".join(f"(?:{p})" for p in _YOUTUBE_PATTERNS),
    re.IGNORECASE,
)

def is_valid_youtube_url(url: str) -> bool:
    return bool(_YOUTUBE_RE.match(url.strip()))

def looks_like_playlist_url(url: str) -> bool:
    return bool(re.search(r"[?&]list=", url, re.IGNORECASE))

def format_bytes(num_bytes: int | float) -> str:
    if num_bytes <= 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    idx = 0
    size = float(num_bytes)
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    return f"{size:.1f} {units[idx]}"

def format_speed(bps: float) -> str:
    if bps <= 0:
        return "— MB/s"
    mb = bps / (1024 * 1024)
    if mb >= 1:
        return f"{mb:.1f} MB/s"
    kb = bps / 1024
    if kb >= 1:
        return f"{kb:.0f} KB/s"
    return f"{bps:.0f} B/s"

def format_eta(seconds: int) -> str:
    if seconds <= 0:
        return "--:--"
    if seconds >= 3600:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}:{m:02d}:{s:02d}"
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"

def format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "Unknown"
    if seconds >= 3600:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h}h {m}m {s}s"
    m, s = divmod(seconds, 60)
    return f"{m}m {s}s"

def format_count(n: int) -> str:
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)

def get_free_space(path: str) -> int:
    try:
        st = shutil.disk_usage(path if os.path.isdir(path) else os.path.dirname(path) or ".")
        return st.free
    except OSError:
        return 0

def has_enough_space(path: str, required_bytes: int, margin: float = 1.2) -> bool:
    if required_bytes <= 0:
        return True
    return get_free_space(path) >= int(required_bytes * margin)

def ffmpeg_installed() -> bool:
    return shutil.which("ffmpeg") is not None

def ffmpeg_path() -> str | None:
    return shutil.which("ffmpeg")

def open_folder(path: str) -> None:
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    if not os.path.isdir(folder):
        return
    if sys.platform == "win32":
        os.startfile(folder)
    elif sys.platform == "darwin":
        import subprocess
        subprocess.run(["open", folder], check=False, timeout=10)
    else:
        import subprocess
        subprocess.run(["xdg-open", folder], check=False, timeout=10)
