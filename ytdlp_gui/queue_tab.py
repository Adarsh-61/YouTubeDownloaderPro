from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

from .utils import format_bytes, format_speed, format_eta

if TYPE_CHECKING:
    from .app import App

_STATUS_COLORS = {
    "queued": "gray",
    "waiting": "#9E9E9E",
    "downloading": "#2196F3",
    "merging": "#FF9800",
    "completed": "#4CAF50",
    "failed": "#f44336",
    "canceled": "#9E9E9E",
}

class _TaskCard(ctk.CTkFrame):

    def __init__(
        self,
        master: ctk.CTkFrame,
        task_id: str,
        title: str,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
        on_open: Callable[[str], None],
    ) -> None:
        super().__init__(master, corner_radius=8)
        self.task_id = task_id
        self.current_status = "queued"
        self._on_retry = on_retry
        self._on_open = on_open

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=(8, 2))

        self.title_lbl = ctk.CTkLabel(
            top, text=title,
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        )
        self.title_lbl.pack(side="left", fill="x", expand=True)

        self.status_lbl = ctk.CTkLabel(
            top, text="Queued",
            font=ctk.CTkFont(size=11), text_color="gray",
        )
        self.status_lbl.pack(side="right", padx=(8, 0))

        self.open_btn = ctk.CTkButton(
            top, text="📂", width=30, height=26,
            fg_color="transparent", hover_color="#4CAF50",
            command=lambda: self._on_open(self.task_id),
        )

        self.retry_btn = ctk.CTkButton(
            top, text="↻", width=30, height=26,
            fg_color="transparent", hover_color="#FF9800",
            command=lambda: self._on_retry(self.task_id),
        )

        ctk.CTkButton(
            top, text="✕", width=30, height=26,
            fg_color="transparent", hover_color="#dc3545",
            command=lambda: on_cancel(task_id),
        ).pack(side="right")

        self.pbar = ctk.CTkProgressBar(self, height=10)
        self.pbar.pack(fill="x", padx=10, pady=2)
        self.pbar.set(0)

        self.detail_lbl = ctk.CTkLabel(
            self, text="Waiting…",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w",
        )
        self.detail_lbl.pack(fill="x", padx=10, pady=(0, 8))

    def update_data(self, data: dict) -> None:
        progress = float(data.get("progress", 0))
        self.pbar.set(progress / 100)

        title = str(data.get("title", "Downloading…"))
        status = str(data.get("status", "queued"))
        prev_status = self.current_status
        self.current_status = status

        self.title_lbl.configure(text=title)
        self.status_lbl.configure(
            text=status.capitalize(),
            text_color=_STATUS_COLORS.get(status, "gray"),
        )

        if status == "completed":
            self.detail_lbl.configure(text="Download complete ✓")
            if prev_status != "completed":
                self.open_btn.pack(side="right", padx=(4, 0))
        elif status == "failed":
            self.detail_lbl.configure(text="Failed — click ↻ to retry")
            if prev_status != "failed":
                self.retry_btn.pack(side="right", padx=(4, 0))
        elif status == "canceled":
            self.detail_lbl.configure(text="Canceled")
        else:
            dl = format_bytes(int(data.get("downloaded", 0)))
            total = format_bytes(int(data.get("total", 0)))
            spd = format_speed(float(data.get("speed", 0)))
            eta_s = format_eta(int(data.get("eta", 0)))

            pl_idx = int(data.get("playlist_index", 0))
            pl_total = int(data.get("playlist_total", 0))
            pl_str = f"  [{pl_idx}/{pl_total}]" if pl_total > 1 else ""

            self.detail_lbl.configure(
                text=f"{dl} / {total}   ·   {spd}   ·   ETA {eta_s}   ·   {progress:.1f}%{pl_str}",
            )

class QueueTab(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, app: App) -> None:
        super().__init__(master, fg_color="transparent")
        self.app = app
        self._cards: dict[str, _TaskCard] = {}
        self._build()

    def _build(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            header, text="Download Queue",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left")

        self.summary_lbl = ctk.CTkLabel(
            header, text="", font=ctk.CTkFont(size=11), text_color="gray",
        )
        self.summary_lbl.pack(side="left", padx=(16, 0))

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        ctk.CTkButton(
            btn_frame, text="Clear Done", width=100,
            command=self._clear_completed,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="Cancel All", width=100,
            fg_color="#dc3545", hover_color="#c82333",
            command=self.app.cancel_all_downloads,
        ).pack(side="left")

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.empty_lbl = ctk.CTkLabel(
            self.scroll, text="No downloads in queue", text_color="gray",
        )
        self.empty_lbl.pack(pady=50)

    def add_task(self, task_id: str, title: str) -> None:
        if self.empty_lbl.winfo_ismapped():
            self.empty_lbl.pack_forget()

        card = _TaskCard(
            self.scroll, task_id, title,
            on_cancel=self.app.cancel_download,
            on_retry=self.app.retry_download,
            on_open=self.app.open_task_folder,
        )
        card.pack(fill="x", pady=3)
        self._cards[task_id] = card
        self._update_summary()

    def update_task(self, task_id: str, data: dict) -> None:
        card = self._cards.get(task_id)
        if card:
            card.update_data(data)
        self._update_summary()

    def remove_task(self, task_id: str) -> None:
        card = self._cards.pop(task_id, None)
        if card:
            card.destroy()
        if not self._cards:
            self.empty_lbl.pack(pady=50)
        self._update_summary()

    def _clear_completed(self) -> None:
        done = [
            tid for tid, c in self._cards.items()
            if c.current_status in ("completed", "failed", "canceled")
        ]
        for tid in done:
            self.remove_task(tid)

    def _update_summary(self) -> None:
        active = sum(
            1 for c in self._cards.values()
            if c.current_status in ("downloading", "merging", "waiting")
        )
        total = len(self._cards)
        completed = sum(1 for c in self._cards.values() if c.current_status == "completed")
        self.summary_lbl.configure(
            text=f"{active} active  ·  {completed} done  ·  {total} total",
        )
