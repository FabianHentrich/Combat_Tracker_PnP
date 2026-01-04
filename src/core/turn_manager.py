from typing import List, Optional, TYPE_CHECKING
from src.models.character import Character
from src.core.mechanics import wuerfle_initiative
from src.models.enums import EventType

if TYPE_CHECKING:
    from src.core.engine import CombatEngine

class TurnManager:
    """
    Verwaltet die Initiative, Runden und den aktuellen Zug.
    """
    def __init__(self, engine: 'CombatEngine'):
        self.engine = engine
        self.turn_index: int = -1
        self.round_number: int = 1
        self.initiative_rolled: bool = False

    def sort_initiative(self) -> None:
        """Sortiert die Charaktere absteigend nach Initiative."""
        self.engine.characters.sort(key=lambda c: c.init, reverse=True)
        self.engine.log("Initiative sortiert.")
        self.engine.notify(EventType.UPDATE)

    def roll_all_initiatives(self) -> None:
        """Würfelt die Initiative für alle Charaktere neu."""
        for char in self.engine.characters:
            char.init = wuerfle_initiative(char.gew)
        self.sort_initiative()
        self.engine.log("Alle Initiativen neu gewürfelt.")
        self.engine.notify(EventType.UPDATE)

    def roll_initiatives(self, reroll_all: bool = False) -> None:
        """
        Würfelt Initiative für Charaktere mit Init 0 (oder alle).
        Startet dann den Kampf.
        """
        for char in self.engine.characters:
            if reroll_all or char.init == 0:
                char.init = wuerfle_initiative(char.gew)

        self.sort_initiative()
        self.turn_index = 0
        self.round_number = 1
        self.initiative_rolled = True
        self.engine.log("Initiative gewürfelt! Reihenfolge erstellt.")
        self.engine.log(f"--- Runde {self.round_number} beginnt ---")
        self.engine.notify(EventType.UPDATE)

    def reset_initiative(self, target_type: str = "All") -> int:
        """Setzt die Initiative zurück."""
        count = 0
        for char in self.engine.characters:
            if target_type == "All" or char.char_type == target_type:
                char.init = 0
                count += 1

        self.turn_index = -1
        self.round_number = 1
        self.initiative_rolled = False

        type_text = "aller Charaktere" if target_type == "All" else f"aller {target_type}s"
        self.engine.log(f"Initiative {type_text} wurde zurückgesetzt ({count} betroffen).")
        self.engine.notify(EventType.UPDATE)
        return count

    def _update_character_status(self, character: Character) -> None:
        """
        Aktualisiert alle aktiven Status-Effekte für einen Charakter.
        Diese Methode gehört logisch zum TurnManager, da sie zu Beginn eines Zuges ausgeführt wird.
        """
        log_msg = ""
        new_status = []
        character.skip_turns = 0

        for s in character.status:
            s.active_rounds += 1
            log_msg += s.apply_round_effect(character)

            s.duration -= 1
            if s.duration > 0:
                new_status.append(s)

        character.status = new_status
        if log_msg:
            self.engine.log(log_msg)

    def next_turn(self) -> Optional[Character]:
        """
        Schaltet zum nächsten Charakter weiter und wendet Statuseffekte an.
        """
        if not self.engine.characters:
            return None

        self.turn_index += 1

        # Neue Runde
        if self.turn_index >= len(self.engine.characters):
            self.turn_index = 0
            self.round_number += 1
            self.engine.log(f"--- Runde {self.round_number} beginnt ---")

        current_char = self.engine.characters[self.turn_index]

        # Status-Effekte verarbeiten
        self._update_character_status(current_char)

        # Aussetzen verarbeiten
        if current_char.skip_turns > 0:
            self.engine.log(f"{current_char.name} setzt aus.")
            current_char.skip_turns -= 1 # Wird in _update_character_status auf 0 gesetzt, hier aber für den Fall, dass es mehrere Runden sind
            self.engine.notify(EventType.UPDATE)
            return self.next_turn() # Rekursiv weiter

        # Status Info für Log
        status_info = current_char.get_status_string()

        if current_char.lp <= 0 or current_char.max_lp <= 0:
             self.engine.log(f"💀 {current_char.name} ist kampfunfähig.{status_info}")
        else:
             self.engine.log(f"▶ {current_char.name} ist am Zug!{status_info}")

        self.engine.notify(EventType.TURN_CHANGE, current_char)
        self.engine.notify(EventType.UPDATE)

        return current_char

    def reset_combat(self) -> None:
        self.turn_index = -1
        self.round_number = 1
        self.initiative_rolled = False

    def insert_character(self, char: Character, surprise: bool = False) -> None:
        """
        Fügt einen Charakter in die Liste ein und berücksichtigt Initiative/Surprise.
        """
        if self.turn_index == -1: # Initiative noch nicht gewürfelt
            self.engine.characters.append(char)
            self.engine.log(f"{char.name} wurde hinzugefügt.")
        else:
            if surprise:
                # Surprise: Füge VOR dem aktuellen Zug ein (oder an aktueller Stelle)
                target_index = max(0, self.turn_index)
                self.engine.characters.insert(target_index, char)
                if self.turn_index < 0:
                    self.turn_index = 0
                self.engine.log(f"⚠ {char.name} springt überraschend in den Kampf!")
            else:
                # Normales Einsortieren nach Initiative
                inserted = False
                for i, c in enumerate(self.engine.characters):
                    if char.init > c.init:
                        self.engine.characters.insert(i, char)
                        if i <= self.turn_index:
                            self.turn_index += 1
                        inserted = True
                        break
                if not inserted:
                    self.engine.characters.append(char)
                self.engine.log(f"{char.name} wurde einsortiert.")

        self.engine.notify(EventType.UPDATE)

    def remove_character(self, index: int) -> None:
        """Entfernt einen Charakter und passt den Turn-Index an."""
        if 0 <= index < len(self.engine.characters):
            char = self.engine.characters.pop(index)
            self.engine.log(f"{char.name} wurde entfernt.")

            # Turn Index anpassen
            if index < self.turn_index:
                self.turn_index -= 1
            elif index == self.turn_index:
                if self.turn_index >= len(self.engine.characters):
                    self.turn_index = 0
                    if not self.engine.characters:
                        self.turn_index = -1

            self.engine.notify(EventType.UPDATE)

    def remove_characters_by_type(self, char_type: str) -> None:
        """Entfernt alle Charaktere eines bestimmten Typs."""
        self.engine.characters = [c for c in self.engine.characters if c.char_type != char_type]

        # Turn Index korrigieren
        if self.turn_index >= len(self.engine.characters):
            self.turn_index = 0
            if not self.engine.characters:
                self.turn_index = -1

        self.engine.log(f"Alle {char_type} wurden gelöscht.")
        self.engine.notify(EventType.UPDATE)

    def clear_all_characters(self) -> None:
        """Löscht alle Charaktere und setzt den Kampf zurück."""
        self.engine.characters.clear()
        self.reset_combat()
        self.engine.log("Alle Charaktere wurden gelöscht.")
        self.engine.notify(EventType.UPDATE)
