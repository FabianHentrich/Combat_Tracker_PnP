import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import os
from src.controllers.audio_controller import AudioController
from src.utils.config import FONTS
from src.utils.utils import ScrollableFrame, ToolTip

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

        # Layout
        self.columnconfigure(2, weight=1)

        # Drag Handle (Visual indicator)
        lbl_handle = ttk.Label(self, text="☰", font=FONTS["large"], cursor="hand2", style=f"{style_prefix}.TLabel")
        lbl_handle.grid(row=0, column=0, rowspan=2, padx=(0, 5))

        # Number
        lbl_number = ttk.Label(self, text=f"{index + 1}.", font=FONTS["bold"], style=f"{style_prefix}.TLabel")
        lbl_number.grid(row=0, column=1, rowspan=2, padx=(0, 5))

        # Title
        lbl_title = ttk.Label(self, text=track["title"], font=FONTS["bold"], style=f"{style_prefix}.TLabel")
        lbl_title.grid(row=0, column=2, sticky="w")

        # Path (truncated)
        path_text = track["path"]
        if len(path_text) > 50:
            path_text = "..." + path_text[-47:]
        lbl_path = ttk.Label(self, text=path_text, font=FONTS["small"], style=f"{style_prefix}.TLabel")
        lbl_path.grid(row=1, column=2, sticky="w")

        # Duration
        duration = track.get("duration", 0)
        m, s = divmod(int(duration), 60)
        duration_text = f"{m:02d}:{s:02d}"
        lbl_duration = ttk.Label(self, text=duration_text, font=FONTS["small"], style=f"{style_prefix}.TLabel")
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


class AudioSettingsWindow(tk.Toplevel):
    def __init__(self, parent, controller: AudioController, colors: dict = None):
        super().__init__(parent)
        self.controller = controller
        self.colors = colors if colors else {"bg": "#1e1e1e", "fg": "#d4d4d4", "panel": "#252526", "accent": "#3794ff"}
        self.title("Musikplayer Einstellungen")
        self.geometry("700x600")
        self.configure(bg=self.colors["bg"])

        self.scroll_frame = None
        self.track_cards = []
        self.drag_window = None
        self.drag_data = None

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

        btn_file = ttk.Button(btn_frame, text="Datei hinzufügen...", command=self.add_file)
        btn_file.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(btn_file, "Einzelne Audio-Dateien (mp3, wav, ogg) zur Playlist hinzufügen.")

        btn_folder = ttk.Button(btn_frame, text="Ordner hinzufügen...", command=self.add_folder)
        btn_folder.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(btn_folder, "Alle Audio-Dateien aus einem Ordner (und Unterordnern) hinzufügen.")


        btn_tta = ttk.Button(btn_frame, text="TabletopAudio", command=self.open_tabletopaudio)
        btn_tta.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(btn_tta, "Öffnet tabletopaudio.com im Browser für hochwertige Ambience-Sounds.")

        # Playlist Container
        list_frame = ttk.LabelFrame(main_frame, text="Playlist (Drag & Drop zum Sortieren)", padding=5, style="Card.TLabelframe")
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.scroll_frame = ScrollableFrame(list_frame)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)

        # Configure ScrollableFrame canvas background to match theme
        self.scroll_frame.canvas.configure(bg=self.colors["panel"])
        self.scroll_frame.scrollable_frame.configure(style="Card.TFrame")

        self.refresh_playlist()

    def create_tooltip(self, widget, text):
        # Fallback colors if not present
        bg = self.colors.get("tooltip_bg", "#252526")
        fg = self.colors.get("tooltip_fg", "#d4d4d4")

        tt = ToolTip(widget, lambda: text, color_provider=lambda: (bg, fg))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def add_file(self):
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg")], parent=self)
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
                self.on_drag_start,
                self.on_drag_motion,
                self.on_drag_release,
                is_active=is_active,
                colors=self.colors
            )
            card.pack(fill=tk.X, pady=2, padx=2)
            self.track_cards.append(card)

    # --- Drag & Drop Logic ---

    def on_drag_start(self, event, card):
        self.drag_data = {"item": card, "index": card.index, "y": event.y_root}

        # Create drag window (visual feedback)
        self.drag_window = tk.Toplevel(self)
        self.drag_window.overrideredirect(True)
        self.drag_window.attributes("-alpha", 0.8)

        # Copy card content to drag window
        lbl = tk.Label(self.drag_window, text=card.track["title"], bg=self.colors["accent"], fg=self.colors["bg"], font=FONTS["bold"], padx=10, pady=5)
        lbl.pack()

        self.drag_window.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def on_drag_motion(self, event):
        if self.drag_window:
            self.drag_window.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

            # Highlight drop target
            y_root = event.y_root
            for card in self.track_cards:
                if card == self.drag_data["item"]:
                    continue

                card_y = card.winfo_rooty()
                card_h = card.winfo_height()

                if card_y <= y_root <= card_y + card_h:
                    if "active" not in card.state():
                        card.state(["active"])
                else:
                    if "active" in card.state():
                        card.state(["!active"])

    def on_drag_release(self, event):
        if self.drag_window:
            self.drag_window.destroy()
            self.drag_window = None

        # Clear highlights
        for card in self.track_cards:
            if "active" in card.state():
                card.state(["!active"])

        if not self.drag_data:
            return

        # Find drop target
        # We need to map root coordinates to the scrollable frame coordinates
        y_root = event.y_root

        target_index = -1

        # Iterate over cards to find where we dropped
        # This is a simple heuristic based on y-coordinates
        for i, card in enumerate(self.track_cards):
            card_y_root = card.winfo_rooty()
            card_height = card.winfo_height()

            if card_y_root <= y_root <= card_y_root + card_height:
                target_index = i
                break

        # If dropped below all cards
        if target_index == -1:
             if self.track_cards:
                 last_card = self.track_cards[-1]
                 if y_root > last_card.winfo_rooty() + last_card.winfo_height():
                     target_index = len(self.track_cards)
                 elif y_root < self.track_cards[0].winfo_rooty():
                     target_index = 0

        if target_index != -1 and target_index != self.drag_data["index"]:
            # Perform move
            from_index = self.drag_data["index"]

            # Adjust logic for insertion
            if from_index < target_index:
                target_index -= 1 # Because removing the item shifts indices

            # Clamp
            target_index = max(0, min(target_index, len(self.controller.playlist) - 1))

            if from_index != target_index:
                self.controller.move_track(from_index, target_index)
                self.refresh_playlist()

        self.drag_data = None

