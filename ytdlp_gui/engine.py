from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from .models import (
    AudioCodec,
    DownloadStatus,
    DownloadTask,
    OutputFormat,
    QualityPreset,
    VideoInfo,
)

logger = logging.getLogger(__name__)

class QualityPresets:

    @staticmethod
    def maximum() -> dict[str, Any]:
        return {
            "format": (
                "bv*[height>=4320]+ba/"
                "bv*[height>=2160]+ba/"
                "bv*[height>=1440]+ba/"
                "bv*[height>=1080]+ba/"
                "bv*[height>=720]+ba/"
                "bv*+ba/best"
            ),
            "merge_output_format": "mkv",
            "format_sort": [
                "res:4320", "res:2160", "res:1440", "res:1080", "res:720",
                "res", "fps",
                "hdr:12",
                "codec:av01", "codec:vp9.2", "codec:vp9",
                "codec:hevc", "codec:h264",
                "vbr", "abr", "size",
            ],
            "format_sort_force": ["res", "fps"],
        }

    @staticmethod
    def high() -> dict[str, Any]:
        return {
            "format": (
                "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
                "bestvideo[height<=1080]+bestaudio/"
                "best[height<=1080]/best"
            ),
            "merge_output_format": "mp4",
            "format_sort": [
                "res:1080", "res", "fps",
                "codec:h264", "codec:hevc",
                "vbr", "abr",
            ],
        }

    @staticmethod
    def balanced() -> dict[str, Any]:
        return {
            "format": (
                "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
                "bestvideo[height<=720]+bestaudio/"
                "best[height<=720]/best"
            ),
            "merge_output_format": "mp4",
        }

    @staticmethod
    def audio(codec: AudioCodec = AudioCodec.MP3, quality: int = 320) -> dict[str, Any]:
        preferred = codec.value if codec != AudioCodec.BEST else "best"
        pp: dict[str, Any] = {
            "key": "FFmpegExtractAudio",
            "preferredcodec": preferred,
        }
        if codec in (AudioCodec.MP3, AudioCodec.AAC, AudioCodec.VORBIS, AudioCodec.OPUS):
            pp["preferredquality"] = str(min(max(quality, 64), 320))

        return {
            "format": "bestaudio/best",
            "postprocessors": [pp],
            "format_sort": ["abr", "acodec:opus", "acodec:aac"],
        }

    @staticmethod
    def video_only() -> dict[str, Any]:
        return {
            "format": (
                "bv[height>=4320]/"
                "bv[height>=2160]/"
                "bv[height>=1440]/"
                "bv[height>=1080]/"
                "bv[height>=720]/"
                "bv/bestvideo"
            ),
            "merge_output_format": "mp4",
            "format_sort": [
                "res:4320", "res:2160", "res:1440", "res:1080", "res:720",
                "res", "fps",
                "codec:av01", "codec:vp9", "codec:hevc", "codec:h264",
                "vbr",
            ],
            "format_sort_force": ["res", "fps"],
        }

_FALLBACK_FORMATS_VIDEO = [
    (
        "bv*[height>=4320]+ba/bv*[height>=2160]+ba/"
        "bv*[height>=1440]+ba/bv*[height>=1080]+ba/"
        "bv*[height>=720]+ba/bv*+ba/best"
    ),
    "bestvideo+bestaudio/best",
    "best[height>=1080]/best[height>=720]/best",
    "best",
]

_FALLBACK_FORMATS_AUDIO = [
    "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio/best",
    "bestaudio/best",
    "best",
]

ProgressCallback = Callable[[str, dict[str, Any]], None]
StatusCallback = Callable[[str, DownloadStatus], None]
LogCallback = Callable[[str, str], None]

class _YtdlpLogger:

    def __init__(self, engine: DownloadEngine, task_id: str) -> None:
        self._engine = engine
        self._task_id = task_id
        self.errors: list[str] = []

    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        pass

    def warning(self, msg: str) -> None:
        self._engine._log(self._task_id, f"[WARNING] {msg}")

    def error(self, msg: str) -> None:
        self.errors.append(msg)
        self._engine._log(self._task_id, f"[ERROR] {msg}")

class DownloadEngine:

    def __init__(
        self,
        *,
        max_concurrent: int = 2,
        concurrent_fragments: int = 4,
        max_retries: int = 10,
        fragment_retries: int = 10,
        http_chunk_size: int = 10_485_760,
        buffer_size: int = 131_072,
        socket_timeout: int = 30,
        on_progress: ProgressCallback | None = None,
        on_status_change: StatusCallback | None = None,
        on_log: LogCallback | None = None,
    ) -> None:
        self._max_concurrent = max_concurrent
        self._concurrent_fragments = concurrent_fragments
        self._max_retries = max_retries
        self._fragment_retries = fragment_retries
        self._http_chunk_size = http_chunk_size
        self._buffer_size = buffer_size
        self._socket_timeout = socket_timeout

        self._windows_filenames: bool = True
        self._restrict_filenames: bool = False
        self._overwrites: bool = False

        self._on_progress = on_progress
        self._on_status_change = on_status_change
        self._on_log = on_log

        self._semaphore = threading.Semaphore(max_concurrent)
        self._cancel_events: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    def analyze(self, url: str, cookies_path: str = "", proxy: str = "") -> VideoInfo:
        opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "socket_timeout": self._socket_timeout,
        }
        if cookies_path and os.path.isfile(cookies_path):
            opts["cookiefile"] = cookies_path
        if proxy:
            opts["proxy"] = proxy

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        vi = VideoInfo()
        if info is None:
            vi.error = "No information returned"
            return vi

        if "entries" in info:
            entries = list(info.get("entries") or [])
            vi.is_playlist = True
            vi.playlist_count = len(entries)
            vi.title = info.get("title") or "Unknown Playlist"
        else:
            vi.title = info.get("title") or "Unknown"
            vi.duration = info.get("duration") or 0
            vi.uploader = info.get("uploader") or "Unknown"
            vi.view_count = info.get("view_count") or 0
            vi.like_count = info.get("like_count") or 0
            vi.upload_date = info.get("upload_date") or ""
            vi.description = (info.get("description") or "")[:500]
            vi.thumbnail_url = info.get("thumbnail") or ""

            resolutions = sorted(
                {f["height"] for f in info.get("formats", []) if f.get("height")},
                reverse=True,
            )
            vi.available_resolutions = resolutions
            vi.max_resolution = resolutions[0] if resolutions else 0

            fps_values = [
                f.get("fps", 0) or 0
                for f in info.get("formats", [])
                if f.get("fps")
            ]
            vi.max_fps = max(fps_values) if fps_values else 0

            for f in info.get("formats", []):
                if (f.get("dynamic_range") or "").lower() in ("hdr", "hdr10", "hlg"):
                    vi.has_hdr = True
                    break

            for f in reversed(info.get("formats", [])):
                sz = f.get("filesize") or f.get("filesize_approx") or 0
                if sz > vi.filesize_approx:
                    vi.filesize_approx = sz

        return vi

    def submit(self, task: DownloadTask) -> None:
        cancel = threading.Event()
        with self._lock:
            self._cancel_events[task.id] = cancel
        task.status = DownloadStatus.WAITING

        t = threading.Thread(
            target=self._run,
            args=(task, cancel),
            daemon=True,
            name=f"dl-{task.id}",
        )
        with self._lock:
            self._threads[task.id] = t
        t.start()

    def cancel(self, task_id: str) -> None:
        with self._lock:
            ev = self._cancel_events.get(task_id)
        if ev:
            ev.set()

    def cancel_all(self) -> None:
        with self._lock:
            for ev in self._cancel_events.values():
                ev.set()

    @property
    def active_count(self) -> int:
        with self._lock:
            return sum(1 for t in self._threads.values() if t.is_alive())

    def _log(self, task_id: str, msg: str) -> None:
        if self._on_log:
            self._on_log(task_id, msg)

    def _set_status(self, task: DownloadTask, status: DownloadStatus) -> None:
        task.status = status
        if self._on_status_change:
            self._on_status_change(task.id, status)

    def _emit_progress(self, task: DownloadTask) -> None:
        if self._on_progress:
            self._on_progress(
                task.id,
                {
                    "progress": task.progress,
                    "speed": task.speed,
                    "eta": task.eta,
                    "downloaded": task.downloaded_bytes,
                    "total": task.total_bytes,
                    "title": task.title,
                    "status": task.status.value,
                    "playlist_index": task.playlist_index,
                    "playlist_total": task.playlist_total,
                },
            )

    def _build_opts(
        self,
        task: DownloadTask,
        cancel: threading.Event,
        *,
        format_override: str | None = None,
    ) -> dict[str, Any]:
        output_dir = task.output_dir
        os.makedirs(output_dir, exist_ok=True)

        outtmpl = "%(title)s.%(ext)s"
        if task.playlist_mode:
            outtmpl = (
                "%(playlist_title|Unknown Playlist)s/"
                "%(playlist_index&{:03d}|000)s - %(title)s.%(ext)s"
            )

        opts: dict[str, Any] = {
            "outtmpl": outtmpl,
            "paths": {"home": output_dir},
            "ignoreerrors": True,
            "no_warnings": False,
            "quiet": True,
            "no_color": True,
            "logger": _YtdlpLogger(self, task.id),
            "retries": self._max_retries,
            "fragment_retries": self._fragment_retries,
            "file_access_retries": 5,
            "extractor_retries": 5,
            "concurrent_fragment_downloads": self._concurrent_fragments,
            "buffersize": self._buffer_size,
            "http_chunk_size": self._http_chunk_size,
            "socket_timeout": self._socket_timeout,
            "progress_hooks": [self._make_progress_hook(task, cancel)],
            "postprocessor_hooks": [self._make_pp_hook(task)],
            "noplaylist": not task.playlist_mode,
            "windowsfilenames": self._windows_filenames,
            "restrictfilenames": self._restrict_filenames,
            "overwrites": self._overwrites,
        }

        if task.cookies_path and os.path.isfile(task.cookies_path):
            opts["cookiefile"] = task.cookies_path

        if task.proxy:
            opts["proxy"] = task.proxy
        if task.speed_limit and task.speed_limit > 0:
            opts["ratelimit"] = task.speed_limit

        is_audio = task.quality == QualityPreset.AUDIO_ONLY or task.format in (
            OutputFormat.MP3, OutputFormat.OPUS, OutputFormat.FLAC, OutputFormat.WAV,
        )

        if is_audio:
            opts.update(
                QualityPresets.audio(
                    codec=task.audio_codec,
                    quality=task.audio_quality,
                )
            )
        elif task.quality == QualityPreset.VIDEO_ONLY:
            opts.update(QualityPresets.video_only())
        elif task.quality == QualityPreset.MAXIMUM:
            opts.update(QualityPresets.maximum())
        elif task.quality == QualityPreset.HIGH:
            opts.update(QualityPresets.high())
        else:
            opts.update(QualityPresets.balanced())

        if format_override:
            opts["format"] = format_override

        postprocessors: list[dict[str, Any]] = list(opts.get("postprocessors", []))

        if task.thumbnail and not is_audio:
            postprocessors.append(
                {"key": "EmbedThumbnail", "already_have_thumbnail": False}
            )
            opts["writethumbnail"] = True

        if task.metadata:
            postprocessors.append(
                {"key": "FFmpegMetadata", "add_chapters": task.chapters}
            )

        if task.subtitles:
            langs = [lang.strip() for lang in task.subtitle_langs.split(",") if lang.strip()]
            opts["writesubtitles"] = True
            opts["writeautomaticsub"] = True
            opts["subtitleslangs"] = langs or ["en", "en-US"]
            postprocessors.append({"key": "FFmpegEmbedSubtitle"})

        if task.sponsorblock:
            postprocessors.append(
                {"key": "SponsorBlock", "categories": ["sponsor", "selfpromo", "interaction"]}
            )
            postprocessors.append({"key": "ModifyChapters", "remove_sponsor_segments": ["sponsor"]})

        if not is_audio and task.quality != QualityPreset.VIDEO_ONLY:
            if task.quality == QualityPreset.MAXIMUM:
                opts.setdefault("merge_output_format", "mkv")
            elif task.format == OutputFormat.MKV:
                opts["merge_output_format"] = "mkv"
            elif task.format == OutputFormat.WEBM:
                opts["merge_output_format"] = "webm"
            elif task.format == OutputFormat.MP4:
                if not opts.get("merge_output_format"):
                    postprocessors.append(
                        {"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}
                    )

        if postprocessors:
            opts["postprocessors"] = postprocessors

        return opts

    def _make_progress_hook(
        self, task: DownloadTask, cancel: threading.Event,
    ) -> Callable[[dict[str, Any]], None]:
        last_emit = {"t": 0.0}

        def hook(d: dict[str, Any]) -> None:
            if cancel.is_set():
                raise yt_dlp.utils.DownloadError("Canceled by user")

            status = d.get("status", "")

            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                task.speed = d.get("speed") or 0
                task.eta = d.get("eta") or 0
                task.downloaded_bytes = downloaded
                task.total_bytes = total
                if total > 0:
                    task.progress = min((downloaded / total) * 100, 100.0)

                info = d.get("info_dict") or {}
                pl_idx = info.get("playlist_index") or info.get("playlist_autonumber") or 0
                if pl_idx:
                    task.playlist_index = int(pl_idx)

                now = time.monotonic()
                if now - last_emit["t"] >= 0.20:
                    last_emit["t"] = now
                    self._emit_progress(task)

            elif status == "finished":
                filename = d.get("filename", "")
                if filename:
                    task.title = Path(filename).stem
                    task.output_path = filename
                    self._log(task.id, f"[INFO] Downloaded: {Path(filename).name}")

            elif status == "error":
                self._log(
                    task.id,
                    f"[ERROR] Fragment error: {d.get('error', 'unknown')}",
                )

        return hook

    def _make_pp_hook(
        self, task: DownloadTask,
    ) -> Callable[[dict[str, Any]], None]:
        def hook(d: dict[str, Any]) -> None:
            pp_status = d.get("status", "")
            if pp_status == "started":
                pp = d.get("postprocessor", "unknown")
                self._set_status(task, DownloadStatus.MERGING)
                self._log(task.id, f"[INFO] Post-processing: {pp}")
            elif pp_status == "finished":
                info = d.get("info_dict") or {}
                filepath = info.get("filepath") or info.get("filename") or ""
                if filepath:
                    task.output_path = filepath
                self._log(task.id, "[INFO] Post-processing complete")

        return hook

    def _run(self, task: DownloadTask, cancel: threading.Event) -> None:
        self._log(task.id, "[INFO] Waiting for download slot…")
        self._semaphore.acquire()

        task.started_at = time.time()
        self._set_status(task, DownloadStatus.DOWNLOADING)
        self._log(task.id, f"[INFO] Starting download: {task.url}")
        self._log(
            task.id,
            f"[INFO] Quality: {task.quality.value} | Format: {task.format.value}"
            + (f" | Proxy: {task.proxy}" if task.proxy else ""),
        )

        is_audio = task.quality == QualityPreset.AUDIO_ONLY or task.format in (
            OutputFormat.MP3, OutputFormat.OPUS, OutputFormat.FLAC, OutputFormat.WAV,
        )
        fallback_chain = _FALLBACK_FORMATS_AUDIO if is_audio else _FALLBACK_FORMATS_VIDEO

        try:
            try:
                opts0 = {
                    "quiet": True, "no_warnings": True,
                    "extract_flat": "in_playlist",
                    "socket_timeout": self._socket_timeout,
                }
                if task.cookies_path and os.path.isfile(task.cookies_path):
                    opts0["cookiefile"] = task.cookies_path
                if task.proxy:
                    opts0["proxy"] = task.proxy

                with yt_dlp.YoutubeDL(opts0) as ydl0:
                    info0 = ydl0.extract_info(task.url, download=False)
                if info0:
                    task.title = info0.get("title") or task.title
                    if "entries" in info0:
                        entries = list(info0.get("entries") or [])
                        task.playlist_total = len(entries)
                    self._emit_progress(task)
            except Exception:
                pass

            result = self._attempt_download(task, cancel, format_override=None)
            success = result is True

            if result is False and not cancel.is_set():
                for idx, fmt in enumerate(fallback_chain, start=1):
                    if cancel.is_set():
                        break
                    task.retries_used += 1
                    self._log(
                        task.id,
                        f"[WARNING] Retrying with fallback strategy {idx}/{len(fallback_chain)}…",
                    )
                    task.progress = 0
                    task.downloaded_bytes = 0
                    self._emit_progress(task)

                    result = self._attempt_download(task, cancel, format_override=fmt)
                    success = result is True
                    if result is True or result is None:
                        break

            if cancel.is_set():
                self._set_status(task, DownloadStatus.CANCELED)
                self._log(task.id, "[WARNING] Download canceled")
            elif success:
                task.progress = 100
                task.completed_at = time.time()
                elapsed = task.completed_at - task.started_at
                self._set_status(task, DownloadStatus.COMPLETED)
                self._log(task.id, f"[SUCCESS] Completed in {elapsed:.1f}s")
            else:
                if not task.error:
                    task.error = "All download strategies failed"
                self._set_status(task, DownloadStatus.FAILED)
                self._log(task.id, f"[ERROR] {task.error}")

        except Exception as exc:
            if cancel.is_set():
                self._set_status(task, DownloadStatus.CANCELED)
                self._log(task.id, "[WARNING] Download canceled")
            else:
                task.error = str(exc)
                self._set_status(task, DownloadStatus.FAILED)
                self._log(task.id, f"[ERROR] Unexpected: {exc}")
                logger.exception("Download failed for %s", task.url)

        finally:
            task.completed_at = task.completed_at or time.time()
            self._emit_progress(task)
            with self._lock:
                self._cancel_events.pop(task.id, None)
                self._threads.pop(task.id, None)
            self._semaphore.release()

    def _attempt_download(
        self,
        task: DownloadTask,
        cancel: threading.Event,
        *,
        format_override: str | None,
    ) -> bool | None:
        if cancel.is_set():
            return False
        try:
            opts = self._build_opts(task, cancel, format_override=format_override)
            ytdlp_logger: _YtdlpLogger = opts["logger"]
            with yt_dlp.YoutubeDL(opts) as ydl:
                exit_code = ydl.download([task.url])
            if exit_code == 0:
                task.error = ""
                return True

            if task.output_path:
                task.error = ""
                return True

            combined = " ".join(ytdlp_logger.errors)

            non_retryable = ("Video unavailable", "Private video", "This video is not available",
                             "copyright", "has been removed", "is not available in your country")
            if any(p.lower() in combined.lower() for p in non_retryable):
                task.error = combined[:300] or "Download failed"
                return None

            retryable = ("HTTP Error 403", "HTTP Error 429", "HTTP Error 503",
                         "urlopen error", "timed out", "Connection reset",
                         "Incomplete data", "Got server HTTP error")
            if any(p in combined for p in retryable):
                task.error = combined[:300]
                return False

            task.error = combined[:300] or "Download failed"
            return False

        except yt_dlp.utils.DownloadError as exc:
            msg = str(exc)
            if cancel.is_set():
                return False

            retryable_patterns = ("HTTP Error 403", "HTTP Error 429", "HTTP Error 503",
                                  "urlopen error", "timed out", "Connection reset",
                                  "Incomplete data", "Got server HTTP error")
            if any(p in msg for p in retryable_patterns):
                self._log(task.id, f"[WARNING] Retryable error: {msg[:200]}")
                return False

            task.error = msg
            self._log(task.id, f"[ERROR] {msg[:300]}")
            return None

        except Exception as exc:
            if cancel.is_set():
                return False
            task.error = str(exc)
            self._log(task.id, f"[ERROR] {exc}")
            logger.exception("Attempt failed for %s", task.url)
            return None
