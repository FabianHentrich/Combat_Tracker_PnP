from typing import TYPE_CHECKING, Optional, List
from src.models.character import Character
from src.config.rule_manager import get_rules
from src.models.enums import EventType

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager
    from src.ui.interfaces import ICombatView

class CombatActionHandler:
    """
    Controller für Kampfaktionen wie Schaden, Heilung, Status und Initiative.
    Unterstützt jetzt Mehrfachauswahl.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', view_provider):
        self.engine = engine
        self.history_manager = history_manager
        self._view_provider = view_provider

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
        """Liest Schaden aus dem UI-Panel und wendet ihn auf alle ausgewählten Charaktere an."""
        chars = self._get_selected_chars()
        if not chars: return

        damage_amount, damage_details = self.view.get_damage_data()
        
        if damage_amount <= 0:
            self.view.show_info("Info", "Bitte einen Schadenswert > 0 eingeben.")
            return

        first_part = damage_details.split(",")[0].strip()
        parts = first_part.split(" ", 1)
        main_type = parts[1] if len(parts) > 1 else "Normal"

        rules = get_rules()
        max_rank = 6
        if main_type in rules.get("damage_types", {}):
            sec_effect = rules["damage_types"][main_type].get("secondary_effect")
            if sec_effect and sec_effect in rules.get("status_effects", {}):
                max_rank = rules["status_effects"][sec_effect].get("max_rank", 6)

        status_input = self.view.get_status_input()
        try:
            rank = int(status_input["rank"])
            if rank > max_rank: rank = max_rank
        except ValueError:
            rank = 1

        self.history_manager.save_snapshot()
        
        for char in chars:
            self.engine.apply_damage(char, damage_amount, main_type, rank)
        
        if "," in damage_details:
            self.engine.log(f"Details: {damage_details}")
        
        if len(chars) > 1:
            self.engine.log(f"Schaden auf {len(chars)} Ziele angewendet.")

    def add_status_to_character(self) -> None:
        """Fügt allen ausgewählten Charakteren einen Status hinzu."""
        chars = self._get_selected_chars()
        if not chars: return

        status_input = self.view.get_status_input()
        status = status_input["status"]
        duration_str = status_input["duration"]
        rank_str = status_input["rank"]

        if not status:
            self.view.show_warning("Fehler", "Bitte einen Status eingeben oder auswählen.")
            return

        rules = get_rules()
        max_rank = 6
        if status in rules.get("status_effects", {}):
             max_rank = rules["status_effects"][status].get("max_rank", 6)

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
        for char in chars:
            self.engine.add_status_effect(char, status, duration, rank)
            
        if len(chars) > 1:
            self.engine.log(f"Status '{status}' auf {len(chars)} Ziele angewendet.")

    def apply_healing(self) -> None:
        """Wendet Heilung auf alle ausgewählten Charaktere an."""
        chars = self._get_selected_chars()
        if not chars: return

        val = self.view.get_action_value()
        if val <= 0:
            self.view.show_info("Info", "Bitte einen Heilwert > 0 im Feld 'Wert' eingeben.")
            return

        self.history_manager.save_snapshot()
        for char in chars:
            self.engine.apply_healing(char, val)

    def apply_shield(self) -> None:
        """Erhöht den Schildwert aller ausgewählten Charaktere."""
        chars = self._get_selected_chars()
        if not chars: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            for char in chars:
                self.engine.apply_shield(char, val)

    def apply_armor(self) -> None:
        """Erhöht den Rüstungswert aller ausgewählten Charaktere."""
        chars = self._get_selected_chars()
        if not chars: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            for char in chars:
                self.engine.apply_armor(char, val)

    def _get_selected_chars(self) -> List[Character]:
        """Hilfsmethode: Holt alle ausgewählten Charaktere über die View."""
        char_ids = self.view.get_selected_char_ids() # Beachte das 's' am Ende
        if not char_ids:
            self.view.show_error("Fehler", "Kein Charakter ausgewählt.")
            return []
        
        chars = [self.engine.get_character_by_id(cid) for cid in char_ids]
        return [c for c in chars if c is not None]
