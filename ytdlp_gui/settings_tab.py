from __future__ import annotations

import subprocess
import sys
import tkinter as tk
from typing import TYPE_CHECKING

import customtkinter as ctk

from .config import SettingsManager
from .models import AudioCodec, OutputFormat, QualityPreset
from .utils import ffmpeg_installed

if TYPE_CHECKING:
    from .app import App

class SettingsTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.sm: SettingsManager = app.settings
        self._build()

    def _build(self) -> None:
        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._section(scroll, "Appearance")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Theme:", width=160, anchor="w").pack(side="left")
        self.theme_var = tk.StringVar(value=self.sm.settings.theme)
        ctk.CTkOptionMenu(
            row, variable=self.theme_var,
            values=["dark", "light", "system"],
        ).pack(side="left")

        self._section(scroll, "Download Defaults")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Default quality:", width=160, anchor="w").pack(side="left")
        self.quality_var = tk.StringVar(value=self.sm.settings.quality)
        ctk.CTkOptionMenu(
            row, variable=self.quality_var,
            values=[p.value for p in QualityPreset],
        ).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Default format:", width=160, anchor="w").pack(side="left")
        self.format_var = tk.StringVar(value=self.sm.settings.format)
        ctk.CTkOptionMenu(
            row, variable=self.format_var,
            values=[f.value for f in OutputFormat],
        ).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Output directory:", width=160, anchor="w").pack(side="left")
        self.output_dir_var = tk.StringVar(value=self.sm.settings.output_dir)
        ctk.CTkEntry(row, textvariable=self.output_dir_var, width=320).pack(side="left", padx=(0, 4))
        ctk.CTkButton(row, text="Browse", width=70, command=self._browse_dir).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Max parallel:", width=160, anchor="w").pack(side="left")
        self.parallel_var = tk.StringVar(value=str(self.sm.settings.max_concurrent))
        ctk.CTkOptionMenu(
            row, variable=self.parallel_var,
            values=["1", "2", "3", "4", "5"],
        ).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Concurrent fragments:", width=160, anchor="w").pack(side="left")
        self.fragments_var = tk.StringVar(value=str(self.sm.settings.concurrent_fragments))
        ctk.CTkOptionMenu(
            row, variable=self.fragments_var,
            values=["1", "2", "4", "6", "8"],
        ).pack(side="left")

        self._section(scroll, "Audio Defaults")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Audio codec:", width=160, anchor="w").pack(side="left")
        self.audio_codec_var = tk.StringVar(value=self.sm.settings.audio_codec)
        ctk.CTkOptionMenu(
            row, variable=self.audio_codec_var,
            values=[c.value for c in AudioCodec],
        ).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Audio bitrate:", width=160, anchor="w").pack(side="left")
        self.audio_quality_var = tk.StringVar(value=str(self.sm.settings.audio_quality))
        ctk.CTkOptionMenu(
            row, variable=self.audio_quality_var,
            values=["128", "192", "256", "320"],
        ).pack(side="left")
        ctk.CTkLabel(row, text="kbps", text_color="gray").pack(side="left", padx=4)

        self._section(scroll, "Subtitles & Extras")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Subtitle languages:", width=160, anchor="w").pack(side="left")
        self.subtitle_var = tk.StringVar(value=self.sm.settings.subtitle_langs)
        ctk.CTkEntry(row, textvariable=self.subtitle_var, width=200, placeholder_text="en,es,fr").pack(side="left")
        ctk.CTkLabel(row, text="(comma-separated ISO codes)", text_color="gray", font=ctk.CTkFont(size=10)).pack(side="left", padx=6)

        self.chapters_var = tk.BooleanVar(value=self.sm.settings.chapters)
        ctk.CTkCheckBox(scroll, text="Embed chapter markers", variable=self.chapters_var).pack(anchor="w", pady=2)

        self.sponsorblock_var = tk.BooleanVar(value=self.sm.settings.sponsorblock)
        ctk.CTkCheckBox(scroll, text="Remove SponsorBlock segments", variable=self.sponsorblock_var).pack(anchor="w", pady=2)

        self._section(scroll, "Network")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Proxy:", width=160, anchor="w").pack(side="left")
        self.proxy_var = tk.StringVar(value=self.sm.settings.proxy)
        ctk.CTkEntry(
            row, textvariable=self.proxy_var, width=300,
            placeholder_text="socks5://127.0.0.1:1080 or http://proxy:8080",
        ).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Speed limit:", width=160, anchor="w").pack(side="left")
        self.speed_var = tk.StringVar(value=str(self.sm.settings.speed_limit))
        ctk.CTkEntry(
            row, textvariable=self.speed_var, width=120,
            placeholder_text="0 = unlimited",
        ).pack(side="left")
        ctk.CTkLabel(row, text="bytes/s  (e.g. 1000000 = 1 MB/s)", text_color="gray", font=ctk.CTkFont(size=10)).pack(side="left", padx=6)

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Cookies file:", width=160, anchor="w").pack(side="left")
        self.cookies_var = tk.StringVar(value=self.sm.settings.cookies_path)
        ctk.CTkEntry(row, textvariable=self.cookies_var, width=280, placeholder_text="Path to cookies.txt").pack(side="left", padx=(0, 4))
        ctk.CTkButton(row, text="Browse", width=70, command=self._browse_cookies).pack(side="left")

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Socket timeout:", width=160, anchor="w").pack(side="left")
        self.timeout_var = tk.StringVar(value=str(self.sm.settings.socket_timeout))
        ctk.CTkEntry(row, textvariable=self.timeout_var, width=80).pack(side="left")
        ctk.CTkLabel(row, text="seconds", text_color="gray").pack(side="left", padx=4)

        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text="Fragment retries:", width=160, anchor="w").pack(side="left")
        self.frag_retry_var = tk.StringVar(value=str(self.sm.settings.fragment_retries))
        ctk.CTkEntry(row, textvariable=self.frag_retry_var, width=80).pack(side="left")

        self._section(scroll, "File Handling")

        self.win_fn_var = tk.BooleanVar(value=self.sm.settings.windows_filenames)
        ctk.CTkCheckBox(scroll, text="Windows-safe filenames", variable=self.win_fn_var).pack(anchor="w", pady=2)

        self.restrict_fn_var = tk.BooleanVar(value=self.sm.settings.restrict_filenames)
        ctk.CTkCheckBox(scroll, text="Restrict filenames (ASCII only)", variable=self.restrict_fn_var).pack(anchor="w", pady=2)

        self.overwrite_var = tk.BooleanVar(value=self.sm.settings.overwrites)
        ctk.CTkCheckBox(scroll, text="Overwrite existing files", variable=self.overwrite_var).pack(anchor="w", pady=2)

        self._section(scroll, "Status")

        status_row = ctk.CTkFrame(scroll, fg_color="transparent")
        status_row.pack(fill="x", pady=2)
        ffmpeg_ok = ffmpeg_installed()
        ctk.CTkLabel(
            status_row,
            text=f"FFmpeg: {'✓ installed' if ffmpeg_ok else '✗ not found'}",
            text_color="#4CAF50" if ffmpeg_ok else "#f44336",
        ).pack(side="left")

        ctk.CTkButton(
            status_row, text="Update yt-dlp", width=110,
            command=self._update_ytdlp,
        ).pack(side="right")

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkButton(btn_row, text="Save", width=120, command=self._save).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_row, text="Reset to Defaults", width=140,
            fg_color="#FF9800", hover_color="#F57C00",
            command=self._reset,
        ).pack(side="left", padx=4)

        self.status_lbl = ctk.CTkLabel(btn_row, text="", text_color="gray")
        self.status_lbl.pack(side="left", padx=10)

    @staticmethod
    def _section(parent: ctk.CTkFrame, title: str) -> None:
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", pady=(14, 4))

    def _browse_dir(self) -> None:
        d = ctk.filedialog.askdirectory()
        if d:
            self.output_dir_var.set(d)

    def _browse_cookies(self) -> None:
        f = ctk.filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if f:
            self.cookies_var.set(f)

    def _save(self) -> None:
        s = self.sm.settings
        s.theme = self.theme_var.get()
        s.quality = self.quality_var.get()
        s.format = self.format_var.get()
        s.output_dir = self.output_dir_var.get().strip()
        try:
            s.max_concurrent = max(1, min(5, int(self.parallel_var.get())))
        except ValueError:
            s.max_concurrent = 2
        try:
            s.concurrent_fragments = max(1, min(8, int(self.fragments_var.get())))
        except ValueError:
            s.concurrent_fragments = 4

        s.audio_codec = self.audio_codec_var.get()
        try:
            s.audio_quality = int(self.audio_quality_var.get())
        except ValueError:
            s.audio_quality = 320
        s.subtitle_langs = self.subtitle_var.get().strip()
        s.chapters = self.chapters_var.get()
        s.sponsorblock = self.sponsorblock_var.get()
        s.proxy = self.proxy_var.get().strip()
        s.cookies_path = self.cookies_var.get().strip()
        try:
            s.speed_limit = max(0, int(self.speed_var.get().strip() or "0"))
        except ValueError:
            s.speed_limit = 0

        try:
            s.socket_timeout = max(5, int(self.timeout_var.get()))
        except ValueError:
            s.socket_timeout = 30
        try:
            s.fragment_retries = max(0, int(self.frag_retry_var.get()))
        except ValueError:
            s.fragment_retries = 10

        s.windows_filenames = self.win_fn_var.get()
        s.restrict_filenames = self.restrict_fn_var.get()
        s.overwrites = self.overwrite_var.get()

        self.sm.save()
        self._reload_engine()
        ctk.set_appearance_mode(s.theme)
        self.status_lbl.configure(text="Settings saved ✓", text_color="#4CAF50")

    def _reset(self) -> None:
        self.sm.reset()
        self._populate_from_settings()
        self.sm.save()
        self._reload_engine()
        self.status_lbl.configure(text="Defaults restored", text_color="#FF9800")

    def _populate_from_settings(self) -> None:
        s = self.sm.settings
        self.theme_var.set(s.theme)
        self.quality_var.set(s.quality)
        self.format_var.set(s.format)
        self.output_dir_var.set(s.output_dir)
        self.parallel_var.set(str(s.max_concurrent))
        self.fragments_var.set(str(s.concurrent_fragments))
        self.audio_codec_var.set(s.audio_codec)
        self.audio_quality_var.set(str(s.audio_quality))
        self.subtitle_var.set(s.subtitle_langs)
        self.chapters_var.set(s.chapters)
        self.sponsorblock_var.set(s.sponsorblock)
        self.proxy_var.set(s.proxy)
        self.cookies_var.set(s.cookies_path)
        self.speed_var.set(str(s.speed_limit))
        self.timeout_var.set(str(s.socket_timeout))
        self.frag_retry_var.set(str(s.fragment_retries))
        self.win_fn_var.set(s.windows_filenames)
        self.restrict_fn_var.set(s.restrict_filenames)
        self.overwrite_var.set(s.overwrites)

    def _reload_engine(self) -> None:
        if hasattr(self.app, "rebuild_engine"):
            self.app.rebuild_engine()

    def _update_ytdlp(self) -> None:
        self.status_lbl.configure(text="Updating yt-dlp…", text_color="gray")
        self.update_idletasks()

        import threading

        def _bg() -> None:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                    capture_output=True, text=True, timeout=120,
                )
                if result.returncode == 0:
                    self.after(0, lambda: self.status_lbl.configure(
                        text="yt-dlp updated ✓", text_color="#4CAF50"))
                else:
                    err = (result.stderr or result.stdout or "unknown error").strip()[-120:]
                    self.after(0, lambda: self.status_lbl.configure(
                        text=f"Update failed: {err}", text_color="#f44336"))
            except Exception as exc:
                self.after(0, lambda: self.status_lbl.configure(
                    text=f"Update failed: {exc}", text_color="#f44336"))

        threading.Thread(target=_bg, daemon=True).start()
