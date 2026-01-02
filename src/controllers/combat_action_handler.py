from typing import TYPE_CHECKING, Optional, Dict, Any
from src.models.character import Character
from src.config import RULES
from src.models.enums import EventType

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager
    from src.ui.interfaces import ICombatView

class CombatActionHandler:
    """
    Controller für Kampfaktionen wie Schaden, Heilung, Status und Initiative.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', view_provider):
        self.engine = engine
        self.history_manager = history_manager
        self._view_provider = view_provider # Lambda oder Funktion, um View zu holen (da View erst später initiiert wird)

    @property
    def view(self) -> 'ICombatView':
        return self._view_provider()

    def roll_initiative_all(self) -> None:
        """Sortiert Charaktere basierend auf Initiative. Würfelt für die mit 0."""
        self.history_manager.save_snapshot()
        self.engine.roll_initiatives()

        if self.engine.characters:
            char = self.engine.characters[0]
            self.engine.notify(EventType.LOG, f"▶ {char.name} ist am Zug!")

    def reset_initiative(self, target_type: str = "All") -> None:
        """Setzt die Initiative zurück."""
        self.history_manager.save_snapshot()
        self.engine.reset_initiative(target_type)

    def next_turn(self) -> None:
        """Geht zum nächsten Zug über."""
        self.history_manager.save_snapshot()
        self.engine.next_turn()

    def deal_damage(self) -> None:
        """Liest Schaden direkt aus dem UI-Feld und wendet ihn an."""
        char = self._get_selected_char()
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

        self.history_manager.save_snapshot()
        self.engine.apply_damage(char, dmg, dmg_type, rank)

    def add_status_to_character(self) -> None:
        """Fügt dem ausgewählten Charakter einen Status hinzu."""
        char = self._get_selected_char()
        if not char: return

        status_input = self.view.get_status_input()
        status = status_input["status"]
        duration_str = status_input["duration"]
        rank_str = status_input["rank"]

        if not status:
            self.view.show_warning("Fehler", "Bitte einen Status eingeben oder auswählen.")
            return

        max_rank = 6
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

    def apply_healing(self) -> None:
        """Wendet Heilung auf den ausgewählten Charakter an."""
        char = self._get_selected_char()
        if not char: return

        val = self.view.get_action_value()
        if val <= 0:
            self.view.show_info("Info", "Bitte einen Heilwert > 0 im Feld 'Wert' eingeben.")
            return

        self.history_manager.save_snapshot()
        self.engine.apply_healing(char, val)

    def apply_shield(self) -> None:
        """Erhöht den Schildwert des ausgewählten Charakters."""
        char = self._get_selected_char()
        if not char: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            self.engine.apply_shield(char, val)

    def apply_armor(self) -> None:
        """Erhöht den Rüstungswert des ausgewählten Charakters."""
        char = self._get_selected_char()
        if not char: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            self.engine.apply_armor(char, val)

    def _get_selected_char(self) -> Optional[Character]:
        """Hilfsmethode: Holt den ausgewählten Charakter über die View."""
        char_id = self.view.get_selected_char_id()
        if not char_id:
            self.view.show_error("Fehler", "Kein Charakter ausgewählt.")
            return None
        return self.engine.get_character_by_id(char_id)

