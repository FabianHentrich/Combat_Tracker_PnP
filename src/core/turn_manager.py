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

    def next_turn(self) -> Optional[Character]:
        """
        Schaltet zum nächsten Charakter weiter.
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
        if current_char.status:
            log_msg = current_char.update_status()
            if log_msg:
                self.engine.log(log_msg)

        # Aussetzen verarbeiten
        if current_char.skip_turns > 0:
            self.engine.log(f"{current_char.name} setzt aus.")
            current_char.skip_turns -= 1
            self.engine.notify(EventType.UPDATE)
            return self.next_turn() # Rekursiv weiter

        # Status Info für Log
        status_info = ""
        if current_char.status:
            status_list = []
            for s in current_char.status:
                name = s.name
                if hasattr(name, 'value'):
                    name = name.value
                status_list.append(f"{name} (Rang {s.rank}, {s.duration} Rd.)")
            status_info = " | Status: " + ", ".join(status_list)

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
                # Turn index muss nicht angepasst werden, da der neue Char jetzt an turn_index steht
                # und der alte Char eins nach hinten rutscht.
                # Aber: Wenn wir wollen, dass der neue Char SOFORT dran ist, muss turn_index gleich bleiben (er zeigt auf den neuen).
                # Wenn wir wollen, dass er als nächstes dran ist, müssten wir insert(turn_index + 1) machen.
                # Die Logik "springt überraschend in den Kampf" impliziert meist "ist jetzt dran" oder "unterbricht".
                # Im alten Code: insert an target_index. Wenn turn_index < 0 war, setze auf 0.
                if self.turn_index < 0:
                    self.turn_index = 0
                self.engine.log(f"⚠ {char.name} springt überraschend in den Kampf!")
            else:
                # Normales Einsortieren nach Initiative
                inserted = False
                for i, c in enumerate(self.engine.characters):
                    if char.init > c.init:
                        self.engine.characters.insert(i, char)
                        # Wenn wir VOR dem aktuellen Index einfügen, muss der Index erhöht werden,
                        # damit der aktive Spieler aktiv bleibt.
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
                # Ein Charakter vor dem aktuellen wurde gelöscht -> Index verringern
                self.turn_index -= 1
            elif index == self.turn_index:
                # Der aktuelle Charakter wurde gelöscht -> Index bleibt gleich (nächster rutscht nach),
                # außer wir waren am Ende der Liste.
                if self.turn_index >= len(self.engine.characters):
                    self.turn_index = 0
                    # Falls Liste jetzt leer ist, wird turn_index 0 sein, aber len 0.
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
