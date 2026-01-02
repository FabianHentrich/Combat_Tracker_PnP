import tkinter as tk
from src.config import FONTS

class DragDropManager:
    """
    Verwaltet die Drag & Drop Logik für die Playlist-Sortierung.
    """
    def __init__(self, root_window, get_cards_callback, controller, refresh_callback, colors):
        self.root_window = root_window
        self.get_cards_callback = get_cards_callback # Funktion, die die aktuelle Liste der Karten zurückgibt
        self.controller = controller
        self.refresh_callback = refresh_callback
        self.colors = colors

        self.drag_window = None
        self.drag_data = None

    def on_drag_start(self, event, card):
        self.drag_data = {"item": card, "index": card.index, "y": event.y_root}

        # Create drag window (visual feedback)
        self.drag_window = tk.Toplevel(self.root_window)
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
            track_cards = self.get_cards_callback()

            for card in track_cards:
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

        track_cards = self.get_cards_callback()

        # Clear highlights
        for card in track_cards:
            if "active" in card.state():
                card.state(["!active"])

        if not self.drag_data:
            return

        target_index = self._calculate_drop_index(event.y_root, track_cards)

        if target_index != -1 and target_index != self.drag_data["index"]:
            # Perform move
            from_index = self.drag_data["index"]

            # Adjust logic for insertion
            if from_index < target_index:
                target_index -= 1

            # Clamp
            target_index = max(0, min(target_index, len(self.controller.playlist) - 1))

            if from_index != target_index:
                self.controller.move_track(from_index, target_index)
                self.refresh_callback()

        self.drag_data = None

    def _calculate_drop_index(self, y_root: int, track_cards: list) -> int:
        """Berechnet den Index, an dem das Element fallen gelassen wurde."""
        target_index = -1

        for i, card in enumerate(track_cards):
            card_y_root = card.winfo_rooty()
            card_height = card.winfo_height()

            if card_y_root <= y_root <= card_y_root + card_height:
                target_index = i
                break

        # If dropped below all cards or above first
        if target_index == -1 and track_cards:
             last_card = track_cards[-1]
             if y_root > last_card.winfo_rooty() + last_card.winfo_height():
                 target_index = len(track_cards)
             elif y_root < track_cards[0].winfo_rooty():
                 target_index = 0

        return target_index

