from __future__ import annotations

import logging
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from .config import SettingsManager
from .download_tab import DownloadTab
from .engine import DownloadEngine
from .history_tab import HistoryTab
from .models import DownloadStatus, DownloadTask, VideoInfo
from .queue_tab import QueueTab
from .settings_tab import SettingsTab
from .utils import open_folder

logger = logging.getLogger(__name__)

class App(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.settings = SettingsManager()
        ctk.set_appearance_mode(self.settings.settings.theme)
        ctk.set_default_color_theme("blue")

        self.title("YouTube Downloader Pro  v3.0")
        w = self.settings.settings.window_width
        h = self.settings.settings.window_height
        self.geometry(f"{w}x{h}")
        self.minsize(860, 620)

        self.engine = self._create_engine()

        self._tasks: dict[str, DownloadTask] = {}
        self._focused_task_id: str | None = None

        self._build_ui()

        self.after(400, self._check_deps)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_engine(self) -> DownloadEngine:
        s = self.settings.settings
        engine = DownloadEngine(
            max_concurrent=s.max_concurrent,
            concurrent_fragments=s.concurrent_fragments,
            max_retries=s.max_retries,
            fragment_retries=s.fragment_retries,
            http_chunk_size=s.http_chunk_size,
            buffer_size=s.buffer_size,
            socket_timeout=s.socket_timeout,
            on_progress=self._on_progress,
            on_status_change=self._on_status_change,
            on_log=self._on_log,
        )
        engine._windows_filenames = s.windows_filenames
        engine._restrict_filenames = s.restrict_filenames
        engine._overwrites = s.overwrites
        return engine

    def rebuild_engine(self) -> None:
        if self.engine.active_count > 0:
            return
        self.engine = self._create_engine()

    def _build_ui(self) -> None:
        self.tabview = ctk.CTkTabview(self, anchor="nw")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        self.tabview.add("Download")
        self.tabview.add("Queue")
        self.tabview.add("History")
        self.tabview.add("Settings")

        self.download_tab = DownloadTab(self.tabview.tab("Download"), self)
        self.download_tab.pack(fill="both", expand=True)

        self.queue_tab = QueueTab(self.tabview.tab("Queue"), self)
        self.queue_tab.pack(fill="both", expand=True)

        self.history_tab = HistoryTab(self.tabview.tab("History"), self)
        self.history_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(self.tabview.tab("Settings"), self)
        self.settings_tab.pack(fill="both", expand=True)

        self.status_bar = ctk.CTkLabel(
            self, text="Ready", anchor="w", height=26,
            font=ctk.CTkFont(size=11),
        )
        self.status_bar.pack(fill="x", padx=10, pady=(0, 6))

    def _check_deps(self) -> None:
        parts: list[str] = []
        if shutil.which("ffmpeg"):
            parts.append("FFmpeg: OK")
        else:
            parts.append("FFmpeg: NOT FOUND — install from ffmpeg.org")
        try:
            import yt_dlp
            parts.append(f"yt-dlp: {yt_dlp.version.__version__}")
        except Exception:
            parts.append("yt-dlp: NOT FOUND")

        self.status_bar.configure(text="   |   ".join(parts))

    def submit_download(self, task: DownloadTask) -> None:
        self._tasks[task.id] = task
        self._focused_task_id = task.id
        self.queue_tab.add_task(task.id, task.url)
        self.engine.submit(task)
        self.download_tab.append_log(f"[INFO] Queued: {task.url}")

    def cancel_download(self, task_id: str) -> None:
        self.engine.cancel(task_id)

    def cancel_all_downloads(self) -> None:
        self.engine.cancel_all()

    def retry_download(self, task_id: str) -> None:
        old = self._tasks.get(task_id)
        if old is None:
            return
        new = DownloadTask(
            url=old.url,
            output_dir=old.output_dir,
            quality=old.quality,
            format=old.format,
            subtitles=old.subtitles,
            subtitle_langs=old.subtitle_langs,
            thumbnail=old.thumbnail,
            metadata=old.metadata,
            chapters=old.chapters,
            sponsorblock=old.sponsorblock,
            cookies_path=old.cookies_path,
            proxy=old.proxy,
            speed_limit=old.speed_limit,
            playlist_mode=old.playlist_mode,
            audio_codec=old.audio_codec,
            audio_quality=old.audio_quality,
        )
        self.submit_download(new)
        self.status_bar.configure(text=f"Retrying: {old.title}")

    def open_task_folder(self, task_id: str) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return
        path = task.output_path or task.output_dir
        if path:
            open_folder(path)

    def redownload_url(self, url: str) -> None:
        self.download_tab.url_entry.delete(0, "end")
        self.download_tab.url_entry.insert(0, url)
        self.tabview.set("Download")

    def analyze_url(self, url: str, callback: Any) -> None:
        def _bg() -> None:
            try:
                cookies = self.settings.settings.cookies_path or ""
                proxy = self.settings.settings.proxy or ""
                info = self.engine.analyze(url, cookies, proxy)
                self.after(0, callback, info)
            except Exception as exc:
                self.after(
                    0, lambda: self.status_bar.configure(text=f"Analysis failed: {exc}"),
                )

        threading.Thread(target=_bg, daemon=True).start()

    def _on_progress(self, task_id: str, data: dict[str, Any]) -> None:
        self.after(0, self._handle_progress, task_id, data)

    def _on_status_change(self, task_id: str, status: DownloadStatus) -> None:
        self.after(0, self._handle_status_change, task_id, status)

    def _on_log(self, task_id: str, msg: str) -> None:
        def _update() -> None:
            self.status_bar.configure(text=msg[:140])
            if task_id == self._focused_task_id:
                self.download_tab.append_log(msg)

        self.after(0, _update)

    def _handle_progress(self, task_id: str, data: dict[str, Any]) -> None:
        self.queue_tab.update_task(task_id, data)

        status = str(data.get("status", ""))
        if task_id == self._focused_task_id and status not in (
            "completed",
            "failed",
            "canceled",
        ):
            self.download_tab.update_progress(data)

    def _handle_status_change(self, task_id: str, status: DownloadStatus) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            return

        if status in (
            DownloadStatus.COMPLETED,
            DownloadStatus.FAILED,
            DownloadStatus.CANCELED,
        ):
            self.history_tab.add_entry(
                {
                    "url": task.url,
                    "title": task.title,
                    "status": status.value,
                    "quality": task.quality.value,
                    "format": task.format.value,
                    "duration": round(task.completed_at - task.started_at, 1)
                    if task.completed_at and task.started_at
                    else 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": task.error,
                }
            )

            if task_id == self._focused_task_id:
                if status == DownloadStatus.COMPLETED:
                    self.download_tab.show_completed(task.title)
                elif status == DownloadStatus.FAILED:
                    self.download_tab.show_error(task.error or "Unknown error")
                elif status == DownloadStatus.CANCELED:
                    self.download_tab.show_canceled()

            if status == DownloadStatus.COMPLETED:
                self.status_bar.configure(text=f"✓ Completed: {task.title}")
            elif status == DownloadStatus.FAILED:
                self.status_bar.configure(text=f"✗ Failed: {task.error}")

    def _on_close(self) -> None:
        if self.engine.active_count > 0:
            if not messagebox.askyesno(
                "Confirm Exit",
                "Downloads are still running.\nAre you sure you want to exit?",
            ):
                return
            self.engine.cancel_all()

        self.settings.set("window_width", self.winfo_width())
        self.settings.set("window_height", self.winfo_height())
        self.settings.save()
        self.destroy()

def main() -> None:
    if sys.version_info < (3, 10):
        print("Python 3.10 or newer is required.")
        sys.exit(1)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = App()

    app.update_idletasks()
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    w, h = app.winfo_width(), app.winfo_height()
    app.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")

    app.mainloop()
