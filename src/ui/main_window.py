import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from typing import Dict, Any, Optional
from src.models.character import Character
from src.utils.utils import ToolTip, generate_health_bar
from src.controllers.import_handler import ImportHandler
from src.controllers.library_handler import LibraryHandler
from src.controllers.edit_handler import EditHandler
from src.controllers.hotkey_handler import HotkeyHandler
from src.ui.ui_layout import UILayout
from src.utils.config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS, FONTS, FILES, WINDOW_SIZE, APP_TITLE, RULES
from src.core.engine import CombatEngine
from src.controllers.persistence import PersistenceHandler
from src.core.history import HistoryManager
from src.utils.logger import setup_logging
from src.models.enums import CharacterType, EventType

logger = setup_logging()

class CombatTracker:
    """
    Hauptklasse der Anwendung (Controller/View-Controller).
    Verbindet die UI (Tkinter) mit der Logik (CombatEngine).
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE["main"])

        # --- Modern Dark Theme Configuration ---
        self.colors: Dict[str, str] = COLORS

        self.engine = CombatEngine()

        self.history_manager = HistoryManager(self.engine)
        self.persistence_handler = PersistenceHandler(self.root)
        self.import_handler = ImportHandler(self.engine, self.history_manager, self.root, self.colors)
        self.library_handler = LibraryHandler(self.engine, self.history_manager, self.root, self.colors)
        self.edit_handler = EditHandler(self.engine, self.history_manager, self.root, self.colors)
        self.hotkey_handler = HotkeyHandler(self.root, self.colors)
        self.ui_layout = UILayout(self, self.root)

        # Subscribe to engine events
        self.engine.subscribe(EventType.UPDATE, self.ui_layout.update_listbox)
        self.engine.subscribe(EventType.LOG, self.log_message)
        # self.engine.subscribe(EventType.TURN_CHANGE, self.on_turn_change) # Optional, if we want specific handling

        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        style.theme_use('clam')

        # Allgemeine Styles
        style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"], font=FONTS["main"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TButton", background=self.colors["panel"], foreground=self.colors["fg"], borderwidth=1, focuscolor=self.colors["accent"])
        style.map("TButton", background=[('active', self.colors["accent"])])

        style.configure("TEntry", fieldbackground=self.colors["entry_bg"], foreground=self.colors["fg"], insertcolor=self.colors["fg"])
        style.configure("TCombobox", fieldbackground=self.colors["entry_bg"], background=self.colors["entry_bg"], foreground=self.colors["fg"], arrowcolor=self.colors["fg"])
        style.map("TCombobox", fieldbackground=[('readonly', self.colors["entry_bg"])],
                               selectbackground=[('readonly', self.colors["entry_bg"])],
                               selectforeground=[('readonly', self.colors["fg"])],
                               foreground=[('readonly', self.colors["fg"])])

        self.root.option_add('*TCombobox*Listbox.background', self.colors["entry_bg"])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors["fg"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors["accent"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.colors["bg"])

        # Treeview (Tabelle) Styles
        style.configure("Treeview",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        fieldbackground=self.colors["panel"],
                        rowheight=30,
                        font=FONTS["main"])
        style.configure("Treeview.Heading",
                        background=self.colors["panel"],
                        foreground=self.colors["accent"],
                        font=FONTS["bold"],
                        borderwidth=0)
        style.map("Treeview", background=[('selected', self.colors["accent"])])

        # Frame Styles (Karten-Look)
        style.configure("Card.TFrame", background=self.colors["panel"], relief="flat")
        style.configure("Card.TLabelframe", background=self.colors["panel"], foreground=self.colors["fg"], relief="flat")
        style.configure("Card.TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["accent"], font=('Segoe UI', 11, 'bold'))


        # UI Widgets placeholders
        self.tree: Optional[ttk.Treeview] = None
        self.context_menu: Optional[tk.Menu] = None
        self.entry_name: Optional[ttk.Entry] = None
        self.entry_lp: Optional[ttk.Entry] = None
        self.entry_rp: Optional[ttk.Entry] = None
        self.entry_sp: Optional[ttk.Entry] = None
        self.entry_init: Optional[ttk.Entry] = None
        self.entry_gew: Optional[ttk.Entry] = None
        self.entry_type: Optional[ttk.Combobox] = None
        self.var_surprise: Optional[tk.BooleanVar] = None
        self.action_value: Optional[ttk.Entry] = None
        self.action_type: Optional[ttk.Combobox] = None
        self.status_rank: Optional[ttk.Entry] = None
        self.status_combobox: Optional[ttk.Combobox] = None
        self.status_duration: Optional[ttk.Entry] = None
        self.round_label: Optional[ttk.Label] = None
        self.log: Optional[tk.Text] = None
        self.management_target_var: Optional[tk.StringVar] = None
        self.btn_edit: Optional[ttk.Button] = None
        self.dice_roller: Any = None # DiceRoller instance

        # Info-Texte für Tooltips
        self.damage_descriptions: Dict[str, str] = DAMAGE_DESCRIPTIONS
        self.status_descriptions: Dict[str, str] = STATUS_DESCRIPTIONS

        self.setup_ui()

        # Hotkeys setup
        hotkey_callbacks = {
            "next_turn": self.next_turn,
            "undo": self.undo_action,
            "redo": self.redo_action,
            "delete_char": self.delete_character,
            "focus_damage": lambda: self.action_value.focus_set() if self.action_value else None
        }
        self.hotkey_handler.setup_hotkeys(hotkey_callbacks)
        # self.load_enemies()

    def open_hotkey_settings(self) -> None:
        """Öffnet das Fenster für die Hotkey-Einstellungen."""
        self.hotkey_handler.open_hotkey_settings()

    def apply_preset(self, name: str) -> None:
        """Füllt die Eingabefelder basierend auf der Auswahl."""
        data = self.library_handler.get_preset(name)
        if data:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, name)

            self.entry_lp.delete(0, tk.END)
            self.entry_lp.insert(0, str(data.get("lp", 10)))

            self.entry_rp.delete(0, tk.END)
            self.entry_rp.insert(0, str(data.get("rp", 0)))

            self.entry_sp.delete(0, tk.END)
            self.entry_sp.insert(0, str(data.get("sp", 0)))

            self.entry_gew.delete(0, tk.END)
            self.entry_gew.insert(0, str(data.get("gew", 1)))

            self.entry_init.delete(0, tk.END)
            self.entry_init.insert(0, str(data.get("init", 0)))

            self.entry_type.set(data.get("type", CharacterType.ENEMY.value))

    def create_tooltip(self, widget: tk.Widget, text_func: Any) -> None:
        """Erstellt einen Tooltip für ein Widget."""
        tt = ToolTip(widget, text_func)
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def setup_ui(self) -> None:
        """Initialisiert das UI-Layout."""
        self.ui_layout.setup_ui()

    def show_context_menu(self, event: tk.Event) -> None:
        """Zeigt das Kontextmenü bei Rechtsklick auf die Tabelle."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def add_character_quick(self) -> None:
        """Fügt einen Charakter aus den Eingabefeldern hinzu."""
        self.history_manager.save_snapshot()
        name = self.entry_name.get()
        if not name:
            messagebox.showwarning("Fehler", "Name ist erforderlich!")
            return
        try:
            lp = int(self.entry_lp.get() or 0)
            rp = int(self.entry_rp.get() or 0)
            sp = int(self.entry_sp.get() or 0)
            init = int(self.entry_init.get() or 0)
            gew = int(self.entry_gew.get() or 1)
        except ValueError:
            messagebox.showerror("Fehler", "Zahlenwerte ungültig.")
            return

        char_type = self.entry_type.get()
        char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type)

        surprise = self.var_surprise.get()
        self.insert_character(char, surprise=surprise)
        self.update_listbox()

        # Felder leeren
        self.entry_name.delete(0, tk.END)
        self.entry_lp.delete(0, tk.END)
        self.entry_rp.delete(0, tk.END)
        self.entry_sp.delete(0, tk.END)
        self.entry_init.delete(0, tk.END)
        self.entry_gew.delete(0, tk.END)
        self.entry_name.focus()
        # Checkbox zurücksetzen
        self.var_surprise.set(False)

    def insert_character(self, char: Character, surprise: bool = False) -> None:
        """Fügt einen Charakter in die Liste ein. Delegiert an Engine."""
        self.engine.insert_character(char, surprise)

    def roll_initiative_all(self) -> None:
        """Sorts characters based on their initiative. Rolls for those with 0 init."""
        self.history_manager.save_snapshot()
        self.engine.roll_initiatives()

        # Zeige den ersten Charakter als aktiv an
        if self.engine.characters:
            char = self.engine.characters[0]
            self.log_message(f"▶ {char.name} ist am Zug!")

    def reset_initiative(self, target_type: str = "All") -> None:
        """Setzt die Initiative zurück."""
        self.history_manager.save_snapshot()
        self.engine.reset_initiative(target_type)

    def next_turn(self) -> None:
        """Moves to the next turn, considering status and conditions."""
        self.history_manager.save_snapshot()
        self.engine.next_turn()

        # self.update_listbox() # Removed, handled by event

    def highlight_current_char(self, char: Character) -> None:
        """Markiert den aktuellen Charakter in der Tabelle."""
        # Einfache visuelle Markierung (Auswahl)
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == char.name:
                self.tree.selection_set(item)
                self.tree.focus(item)
                break

    def get_action_value(self) -> int:
        """Hilfsfunktion: Liest den Wert aus dem Interaktions-Feld."""
        try:
            val = self.action_value.get()
            return int(val) if val else 0
        except ValueError:
            return 0

    def deal_damage(self) -> None:
        """Liest Schaden direkt aus dem UI-Feld und wendet ihn an."""
        char = self.get_selected_char()
        if not char: return

        dmg = self.get_action_value()
        if dmg <= 0:
            messagebox.showinfo("Info", "Bitte einen Schadenswert > 0 im Feld 'Wert' eingeben.")
            return

        dmg_type = self.action_type.get()

        # Ermittle max_rank basierend auf dem sekundären Effekt des Schadens
        max_rank = 6
        if dmg_type in RULES.get("damage_types", {}):
            sec_effect = RULES["damage_types"][dmg_type].get("secondary_effect")
            if sec_effect and sec_effect in RULES.get("status_effects", {}):
                max_rank = RULES["status_effects"][sec_effect].get("max_rank", 6)

        try:
            rank = int(self.status_rank.get())
            if rank > max_rank: rank = max_rank
        except ValueError:
            rank = 1

        # Anwenden des Schadens
        self.history_manager.save_snapshot()
        log = char.apply_damage(dmg, dmg_type, rank)
        self.log_message(log)
        self.engine.notify(EventType.UPDATE) # Notify update manually as we modified character directly

    def add_status_to_character(self) -> None:
        """Fügt dem ausgewählten Charakter einen Status hinzu."""
        char = self.get_selected_char()
        if not char: return

        status = self.status_combobox.get()
        duration_str = self.status_duration.get()
        rank_str = self.status_rank.get()

        if not status:
            messagebox.showwarning("Fehler", "Bitte einen Status eingeben oder auswählen.")
            return

        # Ermittle max_rank für den Status
        max_rank = 6 # Default fallback
        if status in RULES.get("status_effects", {}):
             max_rank = RULES["status_effects"][status].get("max_rank", 6)

        try:
            duration = int(duration_str)
            rank = int(rank_str)
            if duration <= 0 or rank <= 0: raise ValueError

            if rank > max_rank:
                rank = max_rank
                messagebox.showinfo("Info", f"Maximaler Rang für '{status}' ist {max_rank}. Rang wurde angepasst.")
        except ValueError:
            messagebox.showwarning("Fehler", "Bitte gültige Zahlen für Dauer und Rang eingeben.")
            return

        self.history_manager.save_snapshot()
        char.add_status(status, duration, rank)
        self.log_message(f"{char.name} erhält Status '{status}' (Rang {rank}) für {duration} Runden.")
        self.engine.notify(EventType.UPDATE) # Notify update manually as we modified character directly

    def load_enemies(self, pfad: Optional[str] = None) -> None:
        """
        Loads enemy data from an Excel file and opens a preview window for selection and editing.
        """
        self.history_manager.save_snapshot()
        self.import_handler.load_from_excel(pfad)

    def add_single_enemy(self) -> None:
        """Veraltet: Fügt einen einzelnen Gegner hinzu."""
        # Veraltet durch Quick-Add, aber kann als Fallback bleiben oder entfernt werden
        pass

    def edit_selected_char(self) -> None:
        """Bearbeitet alle Werte des ausgewählten Charakters."""
        self.edit_handler.edit_selected_char()

    def delete_character(self) -> None:
        """Löscht den ausgewählten Charakter."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        # Index finden
        item = selection[0]
        # Treeview index corresponds to display order, which might be rotated
        # We need to find the actual character in self.engine.characters

        # Retrieve values from selected item to identify character
        values = self.tree.item(item, "values")
        char_name = values[1] # Name is in column 1

        # Find character in list (assuming unique names or just taking first match which is risky but standard for simple lists)
        # Better: Use the rotation logic to map back if possible, or just search.
        # Since we rotate the display list, the treeview index 0 is self.engine.characters[rot].

        # Let's recalculate rotation to find the correct index
        rot = 0
        if self.engine.initiative_rolled and self.engine.turn_index >= 0:
             if self.engine.turn_index < len(self.engine.characters):
                rot = self.engine.turn_index

        tree_index = self.tree.index(item)
        actual_index = (rot + tree_index) % len(self.engine.characters)

        deleted_char = self.engine.characters[actual_index]

        # Safety check
        if deleted_char.name != char_name:
            # Fallback search if index calculation is off (should not happen if logic is consistent)
            for i, c in enumerate(self.engine.characters):
                if c.name == char_name:
                    actual_index = i
                    deleted_char = c
                    break

        self.history_manager.save_snapshot()
        self.engine.remove_character(actual_index)
        # self.update_listbox() # Removed, handled by event
        self.log_message(f"❌ Charakter '{deleted_char.name}' wurde gelöscht.")

    def delete_group(self, char_type: str) -> None:
        """Löscht alle Charaktere eines bestimmten Typs."""
        if messagebox.askyesno("Bestätigung", f"Alle {char_type} wirklich löschen?"):
            self.history_manager.save_snapshot()
            # Create a new list excluding the type
            self.engine.characters = [c for c in self.engine.characters if c.char_type != char_type]
            # Reset turn index if needed, or just let update_listbox handle it (might be risky if index out of bounds)
            if self.engine.turn_index >= len(self.engine.characters):
                self.engine.turn_index = 0
            self.engine.notify(EventType.UPDATE) # Notify update manually as we modified characters directly
            self.log_message(f"Alle {char_type} wurden gelöscht.")

    def manage_edit(self) -> None:
        """Handhabt das Bearbeiten basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.management_target_var.get()
        if target == "Ausgewählter Charakter":
            self.edit_selected_char()
        else:
            messagebox.showinfo("Info", "Massenbearbeitung ist derzeit nicht verfügbar.")

    def manage_delete(self) -> None:
        """Handhabt das Löschen basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.management_target_var.get()
        if target == "Ausgewählter Charakter":
            self.delete_character()
        elif target == "Alle Gegner":
            self.delete_group("Gegner")
        elif target == "Alle Spieler":
            self.delete_group("Spieler")
        elif target == "Alle NPCs":
            self.delete_group("NPC")
        elif target == "Alle Charaktere":
            if messagebox.askyesno("Bestätigung", "Wirklich ALLE Charaktere löschen?"):
                self.history_manager.save_snapshot()
                self.engine.characters.clear()
                self.engine.reset_combat()
                # self.update_listbox() # Removed, handled by event
                self.log_message("Alle Charaktere wurden gelöscht.")

    def apply_healing(self) -> None:
        """Wendet Heilung auf den ausgewählten Charakter an."""
        char = self.get_selected_char()
        if not char: return

        val = self.get_action_value()
        if val <= 0:
            messagebox.showinfo("Info", "Bitte einen Heilwert > 0 im Feld 'Wert' eingeben.")
            return

        self.history_manager.save_snapshot()
        heal_log = char.heal(val)
        self.log_message(heal_log)
        self.engine.notify(EventType.UPDATE) # Notify update manually as we modified character directly

    def apply_shield(self) -> None:
        """Erhöht den Schildwert des ausgewählten Charakters."""
        char = self.get_selected_char()
        if not char: return
        val = self.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            char.sp += val
            self.log_message(f"{char.name} erhält {val} Schild.")
            self.engine.notify(EventType.UPDATE) # Notify update manually as we modified character directly

    def apply_armor(self) -> None:
        """Erhöht den Rüstungswert des ausgewählten Charakters."""
        char = self.get_selected_char()
        if not char: return
        val = self.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            char.rp += val
            self.log_message(f"{char.name} erhält {val} Rüstung.")
            self.engine.notify(EventType.UPDATE) # Notify update manually as we modified character directly

    def save_session(self) -> None:
        state = self.engine.get_state()
        file_path = self.persistence_handler.save_session(state)
        if file_path:
            self.log_message(f"Kampf gespeichert unter: {file_path}")

    def load_session(self) -> None:
        state = self.persistence_handler.load_session()
        if state:
            self.engine.load_state(state)
            self.engine.initiative_rolled = (self.engine.turn_index != -1)
            self.ui_layout.update_listbox()
            self.log_message("Kampf geladen.")

    def autosave(self) -> None:
        state = self.engine.get_state()
        self.persistence_handler.autosave(state)

    def load_autosave(self) -> None:
        state = self.persistence_handler.load_autosave()
        if state:
            self.engine.load_state(state)
            self.engine.initiative_rolled = (self.engine.turn_index != -1)
            self.ui_layout.update_listbox()
            self.log_message("Autosave geladen.")


    def get_selected_char(self) -> Optional[Character]:
        """Gibt das Character-Objekt zurück, das aktuell in der Tabelle ausgewählt ist."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Fehler", "Kein Charakter ausgewählt.")
            return None

        tree_index = self.tree.index(selection[0])

        # Rotation berücksichtigen
        rot = 0
        if self.engine.initiative_rolled and self.engine.turn_index >= 0:
            if self.engine.turn_index < len(self.engine.characters):
                rot = self.engine.turn_index

        # Den tatsächlichen Index in der self.engine.characters Liste berechnen
        actual_index = (rot + tree_index) % len(self.engine.characters)

        return self.engine.characters[actual_index]

    def log_message(self, msg: str) -> None:
        """Schreibt eine Nachricht in das Log-Fenster."""
        self.log.insert(tk.END, str(msg).strip() + "\n")
        self.log.see(tk.END)

    def undo_action(self) -> None:
        """Macht die letzte Aktion rückgängig."""
        if self.history_manager.undo():
            # self.update_listbox() # Removed, handled by load_state in engine
            self.log_message("↩ Undo ausgeführt.")

    def redo_action(self) -> None:
        """Wiederholt die letzte rückgängig gemachte Aktion."""
        if self.history_manager.redo():
            # self.update_listbox() # Removed, handled by load_state in engine
            self.log_message("↪ Redo ausgeführt.")

    def change_theme(self, theme_name: str) -> None:
        """Wechselt das Farbschema der Anwendung."""
        from .config import THEMES
        if theme_name not in THEMES:
            return

        new_colors = THEMES[theme_name]
        self.colors = new_colors
        self.ui_layout.colors = new_colors
        self.edit_handler.colors = new_colors
        self.import_handler.colors = new_colors
        self.library_handler.colors = new_colors
        self.hotkey_handler.colors = new_colors

        # Update Root
        self.root.configure(bg=self.colors["bg"])

        # Update Styles
        style = ttk.Style()
        style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"], font=FONTS["main"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TButton", background=self.colors["panel"], foreground=self.colors["fg"], borderwidth=1, focuscolor=self.colors["accent"])
        style.map("TButton", background=[('active', self.colors["accent"])])

        style.configure("TEntry", fieldbackground=self.colors["entry_bg"], foreground=self.colors["fg"], insertcolor=self.colors["fg"])
        style.configure("TCombobox", fieldbackground=self.colors["entry_bg"], background=self.colors["entry_bg"], foreground=self.colors["fg"], arrowcolor=self.colors["fg"])
        style.map("TCombobox", fieldbackground=[('readonly', self.colors["entry_bg"])],
                               selectbackground=[('readonly', self.colors["entry_bg"])],
                               selectforeground=[('readonly', self.colors["fg"])],
                               foreground=[('readonly', self.colors["fg"])])

        self.root.option_add('*TCombobox*Listbox.background', self.colors["entry_bg"])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors["fg"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors["accent"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.colors["bg"])

        style.configure("Treeview",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        fieldbackground=self.colors["panel"])
        style.configure("Treeview.Heading",
                        background=self.colors["panel"],
                        foreground=self.colors["accent"])
        style.map("Treeview", background=[('selected', self.colors["accent"])])

        style.configure("Card.TFrame", background=self.colors["panel"])
        style.configure("Card.TLabelframe", background=self.colors["panel"], foreground=self.colors["fg"])
        style.configure("Card.TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["accent"])

        # Manuelle Updates für Widgets, die nicht automatisch aktualisiert werden
        if self.log:
            self.log.configure(bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"])

        if self.round_label:
            self.round_label.configure(background=self.colors["bg"], foreground=self.colors["fg"])

        if self.dice_roller:
            self.dice_roller.update_colors(self.colors)

        # Update Treeview Tags
        if self.tree:
            self.tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
            self.tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

        # Refresh UI components if necessary (e.g. recreating parts or just forcing update)
        # For simple color changes, style update + specific widget config is usually enough.

        self.log_message(f"Theme gewechselt zu: {theme_name}")
