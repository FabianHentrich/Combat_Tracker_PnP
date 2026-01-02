import tkinter as tk
from tkinter import ttk
from src.config import FONTS

from src.utils.utils import format_time

class TrackCard(ttk.Frame):
    def __init__(self, parent, track, index, controller, refresh_callback, drag_start_callback, drag_motion_callback, drag_release_callback, is_active=False, colors=None):
        self.is_active = is_active
        self.colors = colors if colors else {"bg": "#1e1e1e", "fg": "#d4d4d4", "panel": "#252526", "accent": "#3794ff"}

        style_prefix = "Active.Card" if self.is_active else "Card"

        super().__init__(parent, style=f"{style_prefix}.TFrame", padding=5)
        self.track = track
        self.index = index
        self.controller = controller
        self.refresh_callback = refresh_callback
        self.drag_start_callback = drag_start_callback
        self.drag_motion_callback = drag_motion_callback
        self.drag_release_callback = drag_release_callback
        self.style_prefix = style_prefix

        self._setup_ui()

    def _setup_ui(self):
        # Layout
        self.columnconfigure(2, weight=1)

        # Drag Handle (Visual indicator)
        lbl_handle = ttk.Label(self, text="☰", font=FONTS["large"], cursor="hand2", style=f"{self.style_prefix}.TLabel")
        lbl_handle.grid(row=0, column=0, rowspan=2, padx=(0, 5))

        # Number
        lbl_number = ttk.Label(self, text=f"{self.index + 1}.", font=FONTS["bold"], style=f"{self.style_prefix}.TLabel")
        lbl_number.grid(row=0, column=1, rowspan=2, padx=(0, 5))

        # Title
        lbl_title = ttk.Label(self, text=self.track["title"], font=FONTS["bold"], style=f"{self.style_prefix}.TLabel")
        lbl_title.grid(row=0, column=2, sticky="w")

        # Path (truncated)
        path_text = self.track["path"]
        if len(path_text) > 50:
            path_text = "..." + path_text[-47:]
        lbl_path = ttk.Label(self, text=path_text, font=FONTS["small"], style=f"{self.style_prefix}.TLabel")
        lbl_path.grid(row=1, column=2, sticky="w")

        # Duration
        duration = self.track.get("duration", 0)
        duration_text = format_time(duration)
        lbl_duration = ttk.Label(self, text=duration_text, font=FONTS["small"], style=f"{self.style_prefix}.TLabel")
        lbl_duration.grid(row=0, column=3, rowspan=2, padx=5)

        # Play Button
        btn_play = ttk.Button(self, text="▶", width=3, command=self.play_track)
        btn_play.grid(row=0, column=4, rowspan=2, padx=5)

        # Remove Button
        btn_remove = ttk.Button(self, text="🗑", width=3, command=self.remove_track)
        btn_remove.grid(row=0, column=5, rowspan=2, padx=5)

        # Bindings for Drag & Drop
        for widget in (self, lbl_handle, lbl_number, lbl_title, lbl_path):
            widget.bind("<Button-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)
            widget.bind("<ButtonRelease-1>", self.on_drag_release)

    def play_track(self):
        if self.controller.current_index == self.index:
            self.controller.toggle_playback()
        else:
            self.controller.play(self.index)

    def remove_track(self):
        self.controller.remove_track(self.index)
        self.refresh_callback()

    def on_drag_start(self, event):
        self.drag_start_callback(event, self)

    def on_drag_motion(self, event):
        self.drag_motion_callback(event)

    def on_drag_release(self, event):
        self.drag_release_callback(event)

    def set_active(self, is_active: bool):
        if self.is_active == is_active:
            return

        self.is_active = is_active
        self.style_prefix = "Active.Card" if self.is_active else "Card"

        # Update own style
        self.configure(style=f"{self.style_prefix}.TFrame")

        # Update children styles
        for widget in self.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.configure(style=f"{self.style_prefix}.TLabel")
