from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from .models import (
    AudioCodec,
    DownloadTask,
    OutputFormat,
    QualityPreset,
    VideoInfo,
)
from .utils import (
    format_bytes,
    format_count,
    format_duration,
    format_eta,
    format_speed,
    is_valid_youtube_url,
    looks_like_playlist_url,
    open_folder,
)

if TYPE_CHECKING:
    from .app import App

_QUALITY_MAP: dict[str, QualityPreset] = {
    "Maximum (8K→720p)": QualityPreset.MAXIMUM,
    "High (1080p)": QualityPreset.HIGH,
    "Balanced (720p)": QualityPreset.BALANCED,
    "Audio Only": QualityPreset.AUDIO_ONLY,
    "Video Only (no audio)": QualityPreset.VIDEO_ONLY,
}

_FORMAT_MAP: dict[str, OutputFormat] = {
    "mp4": OutputFormat.MP4,
    "mkv": OutputFormat.MKV,
    "webm": OutputFormat.WEBM,
    "mp3": OutputFormat.MP3,
    "opus": OutputFormat.OPUS,
    "flac": OutputFormat.FLAC,
    "wav": OutputFormat.WAV,
}

_AUDIO_CODEC_MAP: dict[str, AudioCodec] = {
    "MP3": AudioCodec.MP3,
    "OPUS": AudioCodec.OPUS,
    "FLAC": AudioCodec.FLAC,
    "WAV": AudioCodec.WAV,
    "AAC": AudioCodec.AAC,
    "Best": AudioCodec.BEST,
}

_VIDEO_FORMATS = ["mp4", "mkv", "webm"]
_AUDIO_FORMATS = ["mp3", "opus", "flac", "wav"]

class DownloadTab(ctk.CTkFrame):

    def __init__(self, master: ctk.CTkFrame, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._current_task_id: str | None = None
        self._build()

    def _build(self) -> None:
        s = self.app.settings.settings

        url_frame = ctk.CTkFrame(self)
        url_frame.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            url_frame, text="Video / Playlist URL",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))

        row = ctk.CTkFrame(url_frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(0, 4))

        self.url_entry = ctk.CTkEntry(
            row, placeholder_text="Paste a YouTube URL here…", height=38,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.url_entry.bind("<Return>", lambda _: self._start_download())

        ctk.CTkButton(row, text="Paste", width=70, command=self._paste).pack(
            side="left", padx=(0, 4),
        )
        ctk.CTkButton(row, text="Analyze", width=80, command=self._analyze).pack(
            side="left",
        )

        self.info_label = ctk.CTkLabel(
            url_frame, text="", font=ctk.CTkFont(size=12), text_color="gray",
            wraplength=900,
        )
        self.info_label.pack(anchor="w", padx=12, pady=(0, 8))

        q_frame = ctk.CTkFrame(self)
        q_frame.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            q_frame, text="Quality",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))

        quality_names = list(_QUALITY_MAP.keys())
        self.quality_var = tk.StringVar(value=quality_names[0])
        ctk.CTkSegmentedButton(
            q_frame, values=quality_names,
            variable=self.quality_var,
            command=self._on_quality_change,
        ).pack(fill="x", padx=12, pady=(0, 6))

        fmt_row = ctk.CTkFrame(q_frame, fg_color="transparent")
        fmt_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(fmt_row, text="Format:").pack(side="left", padx=(0, 4))
        self.format_var = tk.StringVar(value=s.format)
        self.format_menu = ctk.CTkOptionMenu(
            fmt_row, values=_VIDEO_FORMATS,
            variable=self.format_var, width=90,
        )
        self.format_menu.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(fmt_row, text="Audio codec:").pack(side="left", padx=(0, 4))
        self.acodec_var = tk.StringVar(value=s.audio_codec.upper() if s.audio_codec != "best" else "Best")
        self.acodec_menu = ctk.CTkOptionMenu(
            fmt_row, values=list(_AUDIO_CODEC_MAP.keys()),
            variable=self.acodec_var, width=80,
        )
        self.acodec_menu.pack(side="left", padx=(0, 14))

        ctk.CTkLabel(fmt_row, text="Bitrate:").pack(side="left", padx=(0, 4))
        self.bitrate_var = tk.StringVar(value=str(s.audio_quality))
        self.bitrate_menu = ctk.CTkOptionMenu(
            fmt_row, values=["128", "192", "256", "320"],
            variable=self.bitrate_var, width=70,
        )
        self.bitrate_menu.pack(side="left")

        opt_frame = ctk.CTkFrame(self)
        opt_frame.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            opt_frame, text="Options",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))

        opts_row = ctk.CTkFrame(opt_frame, fg_color="transparent")
        opts_row.pack(fill="x", padx=12, pady=(0, 4))

        self.sub_var = tk.BooleanVar(value=s.subtitles)
        ctk.CTkCheckBox(opts_row, text="Subtitles", variable=self.sub_var).pack(
            side="left", padx=(0, 12),
        )
        self.thumb_var = tk.BooleanVar(value=s.thumbnail)
        ctk.CTkCheckBox(opts_row, text="Thumbnail", variable=self.thumb_var).pack(
            side="left", padx=(0, 12),
        )
        self.meta_var = tk.BooleanVar(value=s.metadata)
        ctk.CTkCheckBox(opts_row, text="Metadata", variable=self.meta_var).pack(
            side="left", padx=(0, 12),
        )
        self.chapters_var = tk.BooleanVar(value=s.chapters)
        ctk.CTkCheckBox(opts_row, text="Chapters", variable=self.chapters_var).pack(
            side="left", padx=(0, 12),
        )
        self.sponsor_var = tk.BooleanVar(value=s.sponsorblock)
        ctk.CTkCheckBox(opts_row, text="SponsorBlock", variable=self.sponsor_var).pack(
            side="left",
        )

        opts_row2 = ctk.CTkFrame(opt_frame, fg_color="transparent")
        opts_row2.pack(fill="x", padx=12, pady=(0, 10))

        self.playlist_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(opts_row2, text="Playlist mode", variable=self.playlist_var).pack(
            side="left", padx=(0, 14),
        )

        ctk.CTkLabel(opts_row2, text="Subtitle langs:").pack(side="left", padx=(0, 4))
        self.sublang_entry = ctk.CTkEntry(opts_row2, width=140, height=28)
        self.sublang_entry.pack(side="left")
        self.sublang_entry.insert(0, s.subtitle_langs)

        dir_frame = ctk.CTkFrame(self)
        dir_frame.pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(
            dir_frame, text="Output Directory",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))

        dir_row = ctk.CTkFrame(dir_frame, fg_color="transparent")
        dir_row.pack(fill="x", padx=12, pady=(0, 10))

        self.dir_entry = ctk.CTkEntry(dir_row, height=36)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.dir_entry.insert(0, s.output_dir)

        ctk.CTkButton(dir_row, text="Browse", width=80, command=self._browse).pack(
            side="left", padx=(0, 4),
        )
        ctk.CTkButton(dir_row, text="Open", width=60, command=self._open_dir).pack(
            side="left",
        )

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(padx=12, pady=6)

        self.dl_btn = ctk.CTkButton(
            btn_row, text="   Start Download   ", height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._start_download,
        )
        self.dl_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            btn_row, text="Cancel", height=44, width=100,
            fg_color="#dc3545", hover_color="#c82333",
            state="disabled", command=self._cancel,
        )
        self.cancel_btn.pack(side="left")

        prog_frame = ctk.CTkFrame(self)
        prog_frame.pack(fill="x", padx=12, pady=4)

        self.prog_title = ctk.CTkLabel(
            prog_frame, text="Ready",
            font=ctk.CTkFont(size=13), anchor="w",
        )
        self.prog_title.pack(fill="x", padx=12, pady=(10, 4))

        self.prog_bar = ctk.CTkProgressBar(prog_frame, height=14)
        self.prog_bar.pack(fill="x", padx=12, pady=(0, 2))
        self.prog_bar.set(0)

        self.prog_detail = ctk.CTkLabel(
            prog_frame, text="", font=ctk.CTkFont(size=11),
            text_color="gray", anchor="w",
        )
        self.prog_detail.pack(fill="x", padx=12, pady=(0, 10))

        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(4, 10))

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(
            log_header, text="Log",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            log_header, text="Clear", width=60, height=26,
            command=self._clear_log,
        ).pack(side="right")

        self.log_box = ctk.CTkTextbox(
            log_frame, height=100,
            font=ctk.CTkFont(family="Consolas", size=11),
            state="disabled",
        )
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 10))

    def _on_quality_change(self, value: str) -> None:
        preset = _QUALITY_MAP.get(value, QualityPreset.MAXIMUM)
        if preset == QualityPreset.AUDIO_ONLY:
            self.format_menu.configure(values=_AUDIO_FORMATS)
            self.format_var.set("mp3")
        elif preset == QualityPreset.VIDEO_ONLY:
            self.format_menu.configure(values=_VIDEO_FORMATS)
            if self.format_var.get() in _AUDIO_FORMATS:
                self.format_var.set("mp4")
        else:
            self.format_menu.configure(values=_VIDEO_FORMATS)
            if self.format_var.get() in _AUDIO_FORMATS:
                self.format_var.set("mp4")

    def _paste(self) -> None:
        try:
            text = self.clipboard_get()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, text.strip())
            if looks_like_playlist_url(text):
                self.playlist_var.set(True)
        except tk.TclError:
            pass

    def _analyze(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            return
        self.info_label.configure(text="Analyzing…", text_color="gray")
        self.app.analyze_url(url, self._on_analysis_done)

    def _on_analysis_done(self, vi: Any) -> None:
        info: VideoInfo = vi
        if info.error:
            self.info_label.configure(text=f"Error: {info.error}", text_color="#f44336")
            return

        if info.is_playlist:
            text = f"Playlist: {info.title} — {info.playlist_count} videos"
            self.playlist_var.set(True)
        else:
            parts = [info.title]
            if info.duration:
                parts.append(format_duration(info.duration))
            if info.max_resolution:
                res_label = f"{info.max_resolution}p"
                if info.max_fps and info.max_fps > 30:
                    res_label += f" {info.max_fps}fps"
                if info.has_hdr:
                    res_label += " HDR"
                parts.append(res_label)
            if info.view_count:
                parts.append(f"{format_count(info.view_count)} views")
            if info.uploader and info.uploader != "Unknown":
                parts.append(f"by {info.uploader}")
            if info.filesize_approx:
                parts.append(f"~{format_bytes(info.filesize_approx)}")
            text = "  ·  ".join(parts)

        self.info_label.configure(text=text, text_color="#4CAF50")

    def _browse(self) -> None:
        folder = ctk.filedialog.askdirectory()
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)

    def _open_dir(self) -> None:
        folder = self.dir_entry.get().strip()
        if folder:
            open_folder(folder)

    def _clear_log(self) -> None:
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _cancel(self) -> None:
        if self._current_task_id:
            self.app.cancel_download(self._current_task_id)
            self.cancel_btn.configure(state="disabled")

    def _start_download(self) -> None:
        url = self.url_entry.get().strip()
        if not url:
            self.info_label.configure(text="Please enter a URL", text_color="#f44336")
            return

        if not is_valid_youtube_url(url):
            self.info_label.configure(text="Invalid YouTube URL", text_color="#f44336")
            return

        out_dir = self.dir_entry.get().strip()
        if not out_dir:
            self.info_label.configure(
                text="Please select an output directory", text_color="#f44336",
            )
            return

        preset = _QUALITY_MAP.get(self.quality_var.get(), QualityPreset.MAXIMUM)
        fmt = _FORMAT_MAP.get(self.format_var.get(), OutputFormat.MP4)
        acodec = _AUDIO_CODEC_MAP.get(self.acodec_var.get(), AudioCodec.MP3)

        try:
            bitrate = int(self.bitrate_var.get())
        except ValueError:
            bitrate = 320

        task = DownloadTask(
            url=url,
            output_dir=out_dir,
            quality=preset,
            format=fmt,
            subtitles=self.sub_var.get(),
            subtitle_langs=self.sublang_entry.get().strip() or "en,en-US",
            thumbnail=self.thumb_var.get(),
            metadata=self.meta_var.get(),
            chapters=self.chapters_var.get(),
            sponsorblock=self.sponsor_var.get(),
            cookies_path=self.app.settings.settings.cookies_path,
            proxy=self.app.settings.settings.proxy,
            speed_limit=self.app.settings.settings.speed_limit,
            playlist_mode=self.playlist_var.get(),
            audio_codec=acodec,
            audio_quality=bitrate,
        )

        self._current_task_id = task.id
        self.cancel_btn.configure(state="normal")
        self.prog_bar.set(0)
        self.prog_title.configure(text="Queued…", text_color=("gray10", "gray90"))
        self.prog_detail.configure(text="")
        self.info_label.configure(text="Download queued ✓", text_color="#2196F3")
        self.app.submit_download(task)

    def update_progress(self, data: dict[str, object]) -> None:
        progress = float(data.get("progress", 0))
        self.prog_bar.set(progress / 100)

        title = str(data.get("title", "Downloading…"))
        status = str(data.get("status", ""))
        speed_s = format_speed(float(data.get("speed", 0)))
        eta_s = format_eta(int(data.get("eta", 0)))
        dl = format_bytes(int(data.get("downloaded", 0)))
        total = format_bytes(int(data.get("total", 0)))

        pl_idx = int(data.get("playlist_index", 0))
        pl_total = int(data.get("playlist_total", 0))
        title_extra = f"  [{pl_idx}/{pl_total}]" if pl_total > 1 else ""

        self.prog_title.configure(
            text=f"{title}{title_extra}  ({status})",
            text_color=("gray10", "gray90"),
        )
        self.prog_detail.configure(
            text=f"{dl} / {total}   ·   {speed_s}   ·   ETA {eta_s}   ·   {progress:.1f}%",
        )

    def show_completed(self, title: str) -> None:
        self.prog_bar.set(1.0)
        self.prog_title.configure(text=f"✓  {title}", text_color="#4CAF50")
        self.prog_detail.configure(text="Download completed")
        self.cancel_btn.configure(state="disabled")
        self._current_task_id = None

    def show_error(self, error: str) -> None:
        self.prog_title.configure(text="✗  Download failed", text_color="#f44336")
        self.prog_detail.configure(text=error[:300])
        self.cancel_btn.configure(state="disabled")
        self._current_task_id = None

    def show_canceled(self) -> None:
        self.prog_bar.set(0)
        self.prog_title.configure(text="Download canceled", text_color="#FF9800")
        self.prog_detail.configure(text="")
        self.cancel_btn.configure(state="disabled")
        self._current_task_id = None

    def append_log(self, msg: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
