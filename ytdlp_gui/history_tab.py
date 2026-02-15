from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from .config import load_history, save_history

if TYPE_CHECKING:
    from .app import App

_STATUS_COLORS = {
    "completed": "#4CAF50",
    "failed": "#f44336",
    "canceled": "#9E9E9E",
}

class HistoryTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.entries: list[dict[str, Any]] = load_history()
        self._render_job: str | None = None
        self._build()
        self._render()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            header, text="Download History",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._schedule_render())
        search_entry = ctk.CTkEntry(
            header, textvariable=self.search_var,
            placeholder_text="Search…", width=200, height=30,
        )
        search_entry.pack(side="left", padx=(20, 0))

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(btn_row, text="Export", width=80, command=self._export).pack(
            side="left", padx=4,
        )
        ctk.CTkButton(
            btn_row, text="Clear All", width=80,
            fg_color="#dc3545", hover_color="#c82333",
            command=self._clear,
        ).pack(side="left")

        self.count_lbl = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray",
        )
        self.count_lbl.pack(anchor="w", padx=16)

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(4, 10))

    def _schedule_render(self) -> None:
        if self._render_job is not None:
            self.after_cancel(self._render_job)
        self._render_job = self.after(250, self._render)

    def _render(self) -> None:
        self._render_job = None
        for w in self.scroll.winfo_children():
            w.destroy()

        query = self.search_var.get().strip().lower()
        filtered = [
            e for e in self.entries
            if not query or query in (e.get("title", "") + e.get("url", "")).lower()
        ]

        self.count_lbl.configure(text=f"{len(filtered)} of {len(self.entries)} entries")

        if not filtered:
            ctk.CTkLabel(
                self.scroll, text="No matching history", text_color="gray",
            ).pack(pady=50)
            return

        for entry in filtered[:300]:
            card = ctk.CTkFrame(self.scroll, corner_radius=6)
            card.pack(fill="x", pady=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=10, pady=(6, 2))

            ctk.CTkLabel(
                top, text=entry.get("title", "Unknown"),
                font=ctk.CTkFont(size=12, weight="bold"), anchor="w",
            ).pack(side="left", fill="x", expand=True)

            status = entry.get("status", "unknown")
            ctk.CTkLabel(
                top, text=status.capitalize(),
                font=ctk.CTkFont(size=11),
                text_color=_STATUS_COLORS.get(status, "gray"),
            ).pack(side="right", padx=(8, 0))

            url = entry.get("url", "")
            if url:
                ctk.CTkButton(
                    top, text="↻", width=28, height=24,
                    fg_color="transparent", hover_color="#FF9800",
                    command=lambda u=url: self.app.redownload_url(u),
                ).pack(side="right", padx=(4, 0))

                ctk.CTkButton(
                    top, text="📋", width=28, height=24,
                    fg_color="transparent", hover_color="#2196F3",
                    command=lambda u=url: self._copy_url(u),
                ).pack(side="right", padx=(4, 0))

            bottom = ctk.CTkFrame(card, fg_color="transparent")
            bottom.pack(fill="x", padx=10, pady=(0, 6))

            ts = str(entry.get("timestamp", ""))[:19]
            quality = entry.get("quality", "")
            fmt = entry.get("format", "")
            duration_s = entry.get("duration", 0)
            dur_str = f"{duration_s}s" if duration_s else ""
            error = entry.get("error", "")
            meta = "   ·   ".join(filter(None, [ts, quality, fmt, dur_str]))
            if error and status == "failed":
                meta += f"   ·   {error[:80]}"

            ctk.CTkLabel(
                bottom, text=meta,
                font=ctk.CTkFont(size=10), text_color="gray", anchor="w",
            ).pack(side="left", fill="x", expand=True)

    def add_entry(self, entry: dict[str, Any]) -> None:
        self.entries.insert(0, entry)
        if len(self.entries) > 1000:
            self.entries = self.entries[:1000]
        save_history(self.entries)
        self._render()

    def _copy_url(self, url: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(url)

    def _export(self) -> None:
        if not self.entries:
            return
        path = ctk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        )
        if path:
            Path(path).write_text(
                json.dumps(self.entries, indent=2, default=str),
                encoding="utf-8",
            )

    def _clear(self) -> None:
        self.entries.clear()
        save_history(self.entries)
        self._render()
