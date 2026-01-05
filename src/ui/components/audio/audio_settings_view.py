import tkinter as tk
from tkinter import ttk, filedialog
import os
from src.controllers.audio_controller import AudioController
from src.config import FONTS
from src.utils.utils import ScrollableFrame, ToolTip
from src.ui.components.audio.track_card import TrackCard
from src.ui.components.audio.drag_drop_manager import DragDropManager
from src.utils.localization import translate

class AudioSettingsWindow(tk.Toplevel):
    def __init__(self, parent, controller: AudioController, colors: dict = None):
        super().__init__(parent)
        self.controller = controller
        self.colors = colors if colors else {"bg": "#1e1e1e", "fg": "#d4d4d4", "panel": "#252526", "accent": "#3794ff"}
        self.title(translate("audio_settings.title"))
        self.geometry("700x600")
        self.configure(bg=self.colors["bg"])

        self.scroll_frame = None
        self.track_cards = []

        # Drag & Drop Manager initialisieren
        self.drag_manager = DragDropManager(
            self,
            lambda: self.track_cards,
            self.controller,
            self.refresh_playlist,
            self.colors
        )

        self.setup_ui()

    def setup_ui(self):
        # Define styles for active track
        style = ttk.Style()
        style.configure("Active.Card.TFrame", background=self.colors["accent"])
        style.configure("Active.Card.TLabel", background=self.colors["accent"], foreground=self.colors["bg"])

        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Playlist Controls
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        btn_file = ttk.Button(btn_frame, text=translate("audio_settings.add_file"), command=self.add_file)
        btn_file.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(btn_file, translate("audio_settings.add_file_tooltip"))

        btn_folder = ttk.Button(btn_frame, text=translate("audio_settings.add_folder"), command=self.add_folder)
        btn_folder.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(btn_folder, translate("audio_settings.add_folder_tooltip"))


        btn_tta = ttk.Button(btn_frame, text="TabletopAudio", command=self.open_tabletopaudio)
        btn_tta.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(btn_tta, translate("audio_settings.open_tta_tooltip"))

        # Playlist Container
        list_frame = ttk.LabelFrame(main_frame, text=translate("audio_settings.playlist_label"), padding=5, style="Card.TLabelframe")
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.scroll_frame = ScrollableFrame(list_frame)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Configure ScrollableFrame canvas background to match theme
        self.scroll_frame.canvas.configure(bg=self.colors["panel"])
        self.scroll_frame.scrollable_frame.configure(style="Card.TFrame")

        self.refresh_playlist()

        # Subscribe to track changes
        self.controller.add_track_change_listener(self.on_track_changed)
        self.update_active_track()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.controller.remove_track_change_listener(self.on_track_changed)
        self.destroy()

    def on_track_changed(self, track):
        if self.winfo_exists():
            self.update_active_track()

    def update_active_track(self):
        current_idx = self.controller.current_index
        for card in self.track_cards:
            card.set_active(card.index == current_idx)


    def create_tooltip(self, widget, text):
        # Fallback colors if not present
        bg = self.colors.get("tooltip_bg", "#252526")
        fg = self.colors.get("tooltip_fg", "#d4d4d4")

        tt = ToolTip(widget, lambda: text, color_provider=lambda: (bg, fg))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def add_file(self):
        files = filedialog.askopenfilenames(filetypes=[(translate("dialog.file.audio"), "*.mp3 *.wav *.ogg")], parent=self)
        for f in files:
            self.controller.add_track(f)
        self.refresh_playlist()
        self.lift()
        self.focus_force()

    def add_folder(self):
        folder = filedialog.askdirectory(parent=self)
        if folder:
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(('.mp3', '.wav', '.ogg')):
                        self.controller.add_track(os.path.join(root, file))
        self.refresh_playlist()
        self.lift()
        self.focus_force()

    def open_tabletopaudio(self):
        import webbrowser
        webbrowser.open("https://tabletopaudio.com/")

    def refresh_playlist(self):
        # Clear existing cards
        for card in self.track_cards:
            card.destroy()
        self.track_cards = []

        for i, track in enumerate(self.controller.playlist):
            is_active = (i == self.controller.current_index)
            card = TrackCard(
                self.scroll_frame.scrollable_frame,
                track,
                i,
                self.controller,
                self.refresh_playlist,
                self.drag_manager.on_drag_start,
                self.drag_manager.on_drag_motion,
                self.drag_manager.on_drag_release,
                is_active=is_active,
                colors=self.colors
            )
            card.pack(fill=tk.X, pady=2, padx=2)
            self.track_cards.append(card)
