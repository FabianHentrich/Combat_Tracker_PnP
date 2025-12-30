from typing import List, Optional, Callable
import random
from .character import Character
from .utils import wuerfle_initiative
from .logger import setup_logging

logger = setup_logging()

class CombatEngine:
    def __init__(self):
        self.characters: List[Character] = []
        self.turn_index: int = -1
        self.round_number: int = 1
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_turn_change: Optional[Callable[[Optional[Character]], None]] = None
        logger.info("CombatEngine initialisiert.")

    def log(self, message: str):
        logger.info(f"Game Log: {message}")
        if self.on_log:
            self.on_log(message)

    def add_character(self, character: Character):
        self.characters.append(character)
        self.log(f"{character.name} wurde dem Kampf hinzugefügt.")

    def remove_character(self, index: int):
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

    def get_character(self, index: int) -> Optional[Character]:
        if 0 <= index < len(self.characters):
            return self.characters[index]
        return None

    def get_all_characters(self) -> List[Character]:
        return self.characters

    def sort_initiative(self):
        # Sort descending by initiative
        self.characters.sort(key=lambda c: c.init, reverse=True)
        self.log("Initiative sortiert.")

    def roll_all_initiatives(self):
        for char in self.characters:
            char.init = wuerfle_initiative(char.gew)
        self.sort_initiative()
        self.log("Alle Initiativen neu gewürfelt.")

    def next_turn(self) -> Optional[Character]:
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
            return self.next_turn() # Recursively call next turn

        if self.on_turn_change:
            self.on_turn_change(current_char)

        return current_char

    def reset_combat(self):
        self.turn_index = -1
        self.round_number = 1
        self.log("Kampf zurückgesetzt.")

    def insert_character(self, char: Character, surprise: bool = False):
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

    def roll_initiatives(self, reroll_all: bool = False):
        for char in self.characters:
            if reroll_all or char.init == 0:
                char.init = wuerfle_initiative(char.gew)

        self.sort_initiative()
        self.turn_index = 0
        self.round_number = 1
        self.log("Initiative gewürfelt! Reihenfolge erstellt.")
        self.log(f"--- Runde {self.round_number} beginnt ---")

    def get_state(self) -> dict:
        return {
            "characters": [c.to_dict() for c in self.characters],
            "turn_index": self.turn_index,
            "round_number": self.round_number
        }

    def load_state(self, state: dict):
        self.characters = [Character.from_dict(c_data) for c_data in state["characters"]]
        self.turn_index = state["turn_index"]
        self.round_number = state["round_number"]
        self.log("Kampfstatus geladen.")

