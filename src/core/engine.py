from typing import List, Optional, Callable, Dict, Any
import random
from src.models.character import Character
from src.core.mechanics import wuerfle_initiative, format_damage_log
from src.utils.logger import setup_logging
from src.models.enums import EventType
from src.core.event_manager import EventManager
from src.core.turn_manager import TurnManager
from src.utils.localization import translate

logger = setup_logging()

class CombatEngine:
    """
    Core logic of the Combat Tracker.
    Manages the list of characters and delegates turn management.
    """
    def __init__(self):
        self.characters: List[Character] = []
        self.event_manager = EventManager()
        self.turn_manager = TurnManager(self)
        logger.info("CombatEngine initialized.")

    # --- Delegate properties ---
    @property
    def turn_index(self) -> int:
        return self.turn_manager.turn_index

    @turn_index.setter
    def turn_index(self, value: int):
        self.turn_manager.turn_index = value

    @property
    def round_number(self) -> int:
        return self.turn_manager.round_number

    @round_number.setter
    def round_number(self, value: int):
        self.turn_manager.round_number = value

    @property
    def initiative_rolled(self) -> bool:
        return self.turn_manager.initiative_rolled

    @initiative_rolled.setter
    def initiative_rolled(self, value: bool):
        self.turn_manager.initiative_rolled = value

    # --- Event Management ---
    def subscribe(self, event_type: EventType, callback: Callable[..., None]) -> None:
        self.event_manager.subscribe(event_type, callback)

    def notify(self, event_type: EventType, *args: Any, **kwargs: Any) -> None:
        self.event_manager.notify(event_type, *args, **kwargs)

    def log(self, message: str) -> None:
        logger.info(f"Game Log: {message}")
        self.notify(EventType.LOG, message)

    # --- Character Management ---
    def add_character(self, character: Character) -> None:
        self.characters.append(character)
        self.log(translate("messages.character_added_to_combat", name=character.name))
        self.notify(EventType.UPDATE)

    def remove_character(self, index: int) -> None:
        self.turn_manager.remove_character(index)

    def get_character(self, index: int) -> Optional[Character]:
        if 0 <= index < len(self.characters):
            return self.characters[index]
        return None

    def get_character_by_id(self, char_id: str) -> Optional[Character]:
        for char in self.characters:
            if char.id == char_id:
                return char
        return None

    def get_all_characters(self) -> List[Character]:
        return self.characters

    # --- Turn & Initiative Management (Delegation) ---
    def sort_initiative(self) -> None:
        self.turn_manager.sort_initiative()

    def roll_all_initiatives(self) -> None:
        self.turn_manager.roll_all_initiatives()

    def roll_initiatives(self, reroll_all: bool = False) -> None:
        self.turn_manager.roll_initiatives(reroll_all)

    def reset_initiative(self, target_type: str = "All") -> int:
        return self.turn_manager.reset_initiative(target_type)

    def next_turn(self) -> Optional[Character]:
        return self.turn_manager.next_turn()

    def reset_combat(self) -> None:
        self.turn_manager.reset_combat()
        self.log(translate("messages.combat_reset"))
        self.notify(EventType.UPDATE)

    def insert_character(self, char: Character, surprise: bool = False) -> None:
        """
        Inserts a character into the list.
        """
        self.turn_manager.insert_character(char, surprise)

    # --- State Management ---
    def get_state(self) -> dict:
        return {
            "characters": [c.to_dict() for c in self.characters],
            "turn_index": self.turn_index,
            "round_number": self.round_number
        }

    def load_state(self, state: dict) -> None:
        self.characters = [Character.from_dict(c_data) for c_data in state.get("characters", [])]
        self.turn_index = state.get("turn_index", -1)
        self.round_number = state.get("round_number", 1)
        self.log(translate("messages.combat_status_loaded"))
        self.notify(EventType.UPDATE)

    # --- Combat Actions ---
    def apply_damage(self, char: Character, amount: int, damage_type: str, rank: int, damage_details: Optional[str] = None) -> str:
        result = char.apply_damage(amount, damage_type, rank)
        has_details = damage_details is not None and "," in damage_details
        log = format_damage_log(char, result, has_details=has_details)
        self.log(log)
        self.notify(EventType.UPDATE)
        return log

    def apply_healing(self, char: Character, amount: int) -> str:
        log = char.heal(amount)
        self.log(log)
        self.notify(EventType.UPDATE)
        return log

    def apply_shield(self, char: Character, amount: int) -> str:
        char.sp += amount
        log = translate("messages.character_receives_shield", name=char.name, amount=amount)
        self.log(log)
        self.notify(EventType.UPDATE)
        return log

    def apply_armor(self, char: Character, amount: int) -> str:
        char.rp += amount
        log = translate("messages.character_receives_armor", name=char.name, amount=amount)
        self.log(log)
        self.notify(EventType.UPDATE)
        return log

    def add_status_effect(self, char: Character, effect_name: str, duration: int, rank: int) -> str:
        char.add_status(effect_name, duration, rank)
        log = translate("messages.character_receives_status", name=char.name, effect_name=effect_name, rank=rank, duration=duration)
        self.log(log)
        self.notify(EventType.UPDATE)
        return log

    def remove_characters_by_type(self, char_type: str) -> None:
        self.turn_manager.remove_characters_by_type(char_type)

    def clear_all_characters(self) -> None:
        self.turn_manager.clear_all_characters()

    def update_character(self, char: Character, data: dict) -> None:
        char.update(data)
        self.log(translate("messages.character_edited", name=char.name))
        self.notify(EventType.UPDATE)
