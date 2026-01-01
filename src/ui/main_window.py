import tkinter as tk
import json
import os
from typing import Dict, Any, Optional
from src.models.character import Character
from src.utils.utils import ToolTip, generate_health_bar
from src.controllers.import_handler import ImportHandler
from src.controllers.library_handler import LibraryHandler
from src.controllers.edit_handler import EditHandler
from src.controllers.hotkey_handler import HotkeyHandler
from src.ui.main_view import MainView
from src.ui.interfaces import ICombatView
from src.utils.config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS, FONTS, FILES, WINDOW_SIZE, APP_TITLE, RULES
from src.core.engine import CombatEngine
from src.controllers.persistence import PersistenceHandler
from src.core.history import HistoryManager
from src.utils.logger import setup_logging
from src.models.enums import CharacterType, EventType

logger = setup_logging()

class CombatTracker:
    """
    Hauptklasse der Anwendung (Controller).
    Verbindet die UI (View) mit der Logik (CombatEngine).
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

        # View initialisieren
        self.view: ICombatView = MainView(self, self.root)

        # Subscribe to engine events
        self.engine.subscribe(EventType.UPDATE, self.view.update_listbox)
        self.engine.subscribe(EventType.LOG, self.log_message)

        self.root.configure(bg=self.colors["bg"])

        # View Setup aufrufen (erstellt Widgets)
        self.view.setup_ui()

        # Initial Theme Application
        self.view.update_colors(self.colors)

        # Hotkeys setup
        hotkey_callbacks = {
            "next_turn": self.next_turn,
            "undo": self.undo_action,
            "redo": self.redo_action,
            "delete_char": self.delete_character,
            "focus_damage": self.view.focus_damage_input
        }
        self.hotkey_handler.setup_hotkeys(hotkey_callbacks)

    def open_hotkey_settings(self) -> None:
        """Öffnet das Fenster für die Hotkey-Einstellungen."""
        self.hotkey_handler.open_hotkey_settings()

    def apply_preset(self, name: str) -> None:
        """Füllt die Eingabefelder basierend auf der Auswahl."""
        data = self.library_handler.get_preset(name)
        if data:
            self.view.fill_input_fields(data)

    def add_character_quick(self) -> None:
        """Fügt einen Charakter aus den Eingabefeldern hinzu."""
        self.history_manager.save_snapshot()

        data = self.view.get_quick_add_data()
        name = data["name"]

        if not name:
            self.view.show_warning("Fehler", "Name ist erforderlich!")
            return
        try:
            lp = int(data["lp"] or 0)
            rp = int(data["rp"] or 0)
            sp = int(data["sp"] or 0)
            init = int(data["init"] or 0)
            gew = int(data["gew"] or 1)
        except ValueError:
            self.view.show_error("Fehler", "Zahlenwerte ungültig.")
            return

        char_type = data["type"]
        char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type)

        surprise = data["surprise"]
        self.insert_character(char, surprise=surprise)
        self.view.update_listbox()

        self.view.clear_quick_add_fields()

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

    def deal_damage(self) -> None:
        """Liest Schaden direkt aus dem UI-Feld und wendet ihn an."""
        char = self.get_selected_char()
        if not char: return

        dmg = self.view.get_action_value()
        if dmg <= 0:
            self.view.show_info("Info", "Bitte einen Schadenswert > 0 im Feld 'Wert' eingeben.")
            return

        dmg_type = self.view.get_action_type()

        # Ermittle max_rank basierend auf dem sekundären Effekt des Schadens
        max_rank = 6
        if dmg_type in RULES.get("damage_types", {}):
            sec_effect = RULES["damage_types"][dmg_type].get("secondary_effect")
            if sec_effect and sec_effect in RULES.get("status_effects", {}):
                max_rank = RULES["status_effects"][sec_effect].get("max_rank", 6)

        status_input = self.view.get_status_input()
        try:
            rank = int(status_input["rank"])
            if rank > max_rank: rank = max_rank
        except ValueError:
            rank = 1

        # Anwenden des Schadens
        self.history_manager.save_snapshot()
        self.engine.apply_damage(char, dmg, dmg_type, rank)

    def add_status_to_character(self) -> None:
        """Fügt dem ausgewählten Charakter einen Status hinzu."""
        char = self.get_selected_char()
        if not char: return

        status_input = self.view.get_status_input()
        status = status_input["status"]
        duration_str = status_input["duration"]
        rank_str = status_input["rank"]

        if not status:
            self.view.show_warning("Fehler", "Bitte einen Status eingeben oder auswählen.")
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
                self.view.show_info("Info", f"Maximaler Rang für '{status}' ist {max_rank}. Rang wurde angepasst.")
        except ValueError:
            self.view.show_warning("Fehler", "Bitte gültige Zahlen für Dauer und Rang eingeben.")
            return

        self.history_manager.save_snapshot()
        self.engine.add_status_effect(char, status, duration, rank)

    def load_enemies(self, pfad: Optional[str] = None) -> None:
        """
        Loads enemy data from an Excel file and opens a preview window for selection and editing.
        """
        self.history_manager.save_snapshot()
        self.import_handler.load_from_excel(pfad)

    def edit_selected_char(self) -> None:
        """Bearbeitet alle Werte des ausgewählten Charakters."""
        char = self.get_selected_char()
        if char:
            self.edit_handler.open_edit_character_window(char)

    def delete_character(self) -> None:
        """Löscht den ausgewählten Charakter."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        # Charakter finden
        deleted_char = None
        actual_index = -1

        for i, char in enumerate(self.engine.characters):
            if char.id == char_id:
                deleted_char = char
                actual_index = i
                break

        if deleted_char:
            self.history_manager.save_snapshot()
            self.engine.remove_character(actual_index)
        else:
            self.view.show_error("Fehler", "Charakter nicht gefunden (Interner Fehler).")

    def delete_group(self, char_type: str) -> None:
        """Löscht alle Charaktere eines bestimmten Typs."""
        if self.view.ask_yes_no("Bestätigung", f"Alle {char_type} wirklich löschen?"):
            self.history_manager.save_snapshot()
            self.engine.remove_characters_by_type(char_type)

    def manage_edit(self) -> None:
        """Handhabt das Bearbeiten basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.view.get_management_target()
        if target == "Ausgewählter Charakter":
            self.edit_selected_char()
        else:
            self.view.show_info("Info", "Massenbearbeitung ist derzeit nicht verfügbar.")

    def manage_delete(self) -> None:
        """Handhabt das Löschen basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.view.get_management_target()
        if target == "Ausgewählter Charakter":
            self.delete_character()
        elif target == "Alle Gegner":
            self.delete_group("Gegner")
        elif target == "Alle Spieler":
            self.delete_group("Spieler")
        elif target == "Alle NPCs":
            self.delete_group("NPC")
        elif target == "Alle Charaktere":
            if self.view.ask_yes_no("Bestätigung", "Wirklich ALLE Charaktere löschen?"):
                self.history_manager.save_snapshot()
                self.engine.clear_all_characters()

    def apply_healing(self) -> None:
        """Wendet Heilung auf den ausgewählten Charakter an."""
        char = self.get_selected_char()
        if not char: return

        val = self.view.get_action_value()
        if val <= 0:
            self.view.show_info("Info", "Bitte einen Heilwert > 0 im Feld 'Wert' eingeben.")
            return

        self.history_manager.save_snapshot()
        self.engine.apply_healing(char, val)

    def apply_shield(self) -> None:
        """Erhöht den Schildwert des ausgewählten Charakters."""
        char = self.get_selected_char()
        if not char: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            self.engine.apply_shield(char, val)

    def apply_armor(self) -> None:
        """Erhöht den Rüstungswert des ausgewählten Charakters."""
        char = self.get_selected_char()
        if not char: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            self.engine.apply_armor(char, val)

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
            self.view.update_listbox()
            self.log_message("Kampf geladen.")

    def autosave(self) -> None:
        state = self.engine.get_state()
        self.persistence_handler.autosave(state)

    def load_autosave(self) -> None:
        state = self.persistence_handler.load_autosave()
        if state:
            self.engine.load_state(state)
            self.engine.initiative_rolled = (self.engine.turn_index != -1)
            self.view.update_listbox()
            self.log_message("Autosave geladen.")

    def get_selected_char(self) -> Optional[Character]:
        """Gibt das Character-Objekt zurück, das aktuell in der Tabelle ausgewählt ist."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error("Fehler", "Kein Charakter ausgewählt.")
            return None

        # Suche Charakter nach ID
        for char in self.engine.characters:
            if char.id == char_id:
                return char

        return None

    def log_message(self, msg: str) -> None:
        """Schreibt eine Nachricht in das Log-Fenster."""
        self.view.log_message(msg)

    def undo_action(self) -> None:
        """Macht die letzte Aktion rückgängig."""
        if self.history_manager.undo():
            self.log_message("↩ Undo ausgeführt.")

    def redo_action(self) -> None:
        """Wiederholt die letzte rückgängig gemachte Aktion."""
        if self.history_manager.redo():
            self.log_message("↪ Redo ausgeführt.")

    def change_theme(self, theme_name: str) -> None:
        """Wechselt das Farbschema der Anwendung."""
        from src.utils.config import THEMES
        if theme_name not in THEMES:
            return

        new_colors = THEMES[theme_name]
        self.colors = new_colors
        self.view.update_colors(new_colors)
        self.edit_handler.colors = new_colors
        self.import_handler.colors = new_colors
        self.library_handler.colors = new_colors
        self.hotkey_handler.colors = new_colors


        self.log_message(f"Theme gewechselt zu: {theme_name}")
