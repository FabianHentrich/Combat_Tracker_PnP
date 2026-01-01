from typing import List, Optional, Callable, Dict, Any
import random
from src.models.character import Character
from src.utils.utils import wuerfle_initiative
from src.utils.logger import setup_logging
from src.models.enums import EventType

logger = setup_logging()

class CombatEngine:
    """
    Kern-Logik des Combat Trackers.
    Verwaltet die Liste der Charaktere, die Initiative-Reihenfolge und den Rundenablauf.
    Implementiert das Observer-Pattern, um UI-Updates zu triggern.
    """
    def __init__(self):
        self.characters: List[Character] = []
        self.turn_index: int = -1
        self.round_number: int = 1
        self.initiative_rolled: bool = False
        self.listeners: Dict[EventType, List[Callable[..., None]]] = {
            EventType.UPDATE: [],
            EventType.LOG: [],
            EventType.TURN_CHANGE: []
        }
        logger.info("CombatEngine initialisiert.")

    def subscribe(self, event_type: EventType, callback: Callable[..., None]) -> None:
        """Registriert einen Callback für ein bestimmtes Event."""
        if event_type in self.listeners:
            self.listeners[event_type].append(callback)

    def notify(self, event_type: EventType, *args: Any, **kwargs: Any) -> None:
        """Benachrichtigt alle Listener eines Events."""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                callback(*args, **kwargs)

    def log(self, message: str) -> None:
        """Fügt eine Nachricht zum Log hinzu und benachrichtigt Listener."""
        logger.info(f"Game Log: {message}")
        self.notify(EventType.LOG, message)

    def add_character(self, character: Character) -> None:
        """Fügt einen Charakter am Ende der Liste hinzu."""
        self.characters.append(character)
        self.log(f"{character.name} wurde dem Kampf hinzugefügt.")
        self.notify(EventType.UPDATE)

    def remove_character(self, index: int) -> None:
        """Entfernt einen Charakter an der gegebenen Position."""
        if 0 <= index < len(self.characters):
            char = self.characters.pop(index)
            self.log(f"{char.name} wurde entfernt.")
            # Adjust turn index if necessary
            if index < self.turn_index:
                self.turn_index -= 1
            elif index == self.turn_index:
                # If we removed the current character, the next one shifts into this spot.
                # We keep the index same, unless it's out of bounds.
                if self.turn_index >= len(self.characters):
                    self.turn_index = 0
            self.notify(EventType.UPDATE)

    def get_character(self, index: int) -> Optional[Character]:
        """Gibt den Charakter an der gegebenen Position zurück."""
        if 0 <= index < len(self.characters):
            return self.characters[index]
        return None

    def get_all_characters(self) -> List[Character]:
        """Gibt eine Liste aller Charaktere zurück."""
        return self.characters

    def sort_initiative(self) -> None:
        """Sortiert die Charaktere absteigend nach Initiative."""
        # Sort descending by initiative
        self.characters.sort(key=lambda c: c.init, reverse=True)
        self.log("Initiative sortiert.")
        self.notify(EventType.UPDATE)

    def roll_all_initiatives(self) -> None:
        """Würfelt die Initiative für alle Charaktere neu."""
        for char in self.characters:
            char.init = wuerfle_initiative(char.gew)
        self.sort_initiative()
        self.log("Alle Initiativen neu gewürfelt.")
        self.notify(EventType.UPDATE)

    def roll_initiatives(self, reroll_all: bool = False) -> None:
        """
        Würfelt Initiative für Charaktere mit Init 0 (oder alle, wenn reroll_all=True).
        Startet dann den Kampf (Runde 1, erster Spieler).
        """
        for char in self.characters:
            if reroll_all or char.init == 0:
                char.init = wuerfle_initiative(char.gew)

        self.sort_initiative()
        self.turn_index = 0
        self.round_number = 1
        self.initiative_rolled = True
        self.log("Initiative gewürfelt! Reihenfolge erstellt.")
        self.log(f"--- Runde {self.round_number} beginnt ---")
        self.notify(EventType.UPDATE)

    def reset_initiative(self, target_type: str = "All") -> int:
        """
        Setzt die Initiative zurück.
        target_type: "All" oder ein spezifischer CharacterType (als String).
        Gibt die Anzahl der betroffenen Charaktere zurück.
        """
        count = 0
        for char in self.characters:
            if target_type == "All" or char.char_type == target_type:
                char.init = 0
                count += 1

        self.turn_index = -1
        self.round_number = 1
        self.initiative_rolled = False

        type_text = "aller Charaktere" if target_type == "All" else f"aller {target_type}s"
        self.log(f"Initiative {type_text} wurde zurückgesetzt ({count} betroffen).")
        self.notify(EventType.UPDATE)
        return count

    def next_turn(self) -> Optional[Character]:
        """
        Schaltet zum nächsten Charakter in der Initiative-Reihenfolge weiter.
        Behandelt Rundenwechsel, Status-Effekte und übersprungene Züge.
        """
        if not self.characters:
            return None

        self.turn_index += 1

        # Check for new round
        if self.turn_index >= len(self.characters):
            self.turn_index = 0
            self.round_number += 1
            self.log(f"--- Runde {self.round_number} beginnt ---")

        current_char = self.characters[self.turn_index]

        # Handle status effects at start of turn
        if current_char.status:
            log_msg = current_char.update_status()
            if log_msg:
                self.log(log_msg)

        # Handle skip turn
        if current_char.skip_turns > 0:
            self.log(f"{current_char.name} setzt aus.")
            current_char.skip_turns -= 1
            self.notify(EventType.UPDATE) # Update status display
            return self.next_turn() # Recursively call next turn

        # Prepare status info string for logging
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
             self.log(f"💀 {current_char.name} ist kampfunfähig.{status_info}")
        else:
             self.log(f"▶ {current_char.name} ist am Zug!{status_info}")

        self.notify(EventType.TURN_CHANGE, current_char)
        self.notify(EventType.UPDATE)

        return current_char

    def reset_combat(self) -> None:
        """Setzt den Kampf zurück (Runde 1, kein aktiver Zug)."""
        self.turn_index = -1
        self.round_number = 1
        self.log("Kampf zurückgesetzt.")
        self.notify(EventType.UPDATE)

    def insert_character(self, char: Character, surprise: bool = False) -> None:
        """
        Fügt einen Charakter in die Liste ein.
        Wenn 'surprise' True ist, wird er an der aktuellen Position eingefügt (sofort dran).
        Sonst wird er basierend auf seiner Initiative einsortiert.
        """
        if self.turn_index == -1: # Initiative not started/rolled
            self.characters.append(char)
            self.log(f"{char.name} wurde hinzugefügt.")
        else:
            if surprise:
                target_index = max(0, self.turn_index)
                self.characters.insert(target_index, char)
                if self.turn_index < 0:
                    self.turn_index = 0
                self.log(f"⚠ {char.name} springt überraschend in den Kampf!")
            else:
                inserted = False
                for i, c in enumerate(self.characters):
                    if char.init > c.init:
                        self.characters.insert(i, char)
                        if i <= self.turn_index:
                            self.turn_index += 1
                        inserted = True
                        break
                if not inserted:
                    self.characters.append(char)
                self.log(f"{char.name} wurde einsortiert.")
        self.notify(EventType.UPDATE)

    def get_state(self) -> dict:
        """Gibt den aktuellen Zustand als Dictionary zurück (für Speichern/Undo)."""
        return {
            "characters": [c.to_dict() for c in self.characters],
            "turn_index": self.turn_index,
            "round_number": self.round_number
        }

    def load_state(self, state: dict) -> None:
        """Lädt einen Zustand aus einem Dictionary."""
        self.characters = [Character.from_dict(c_data) for c_data in state["characters"]]
        self.turn_index = state["turn_index"]
        self.round_number = state["round_number"]
        self.log("Kampfstatus geladen.")
        self.notify(EventType.UPDATE)
