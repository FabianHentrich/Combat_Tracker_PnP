from typing import List, Optional, TYPE_CHECKING
from src.models.character import Character
from src.core.mechanics import wuerfle_initiative
from src.models.enums import EventType, CharacterType, ScopeType
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.core.engine import CombatEngine

class TurnManager:
    """
    Manages initiative, rounds, and the current turn.
    """
    def __init__(self, engine: 'CombatEngine'):
        self.engine = engine
        self.turn_index: int = -1
        self.round_number: int = 1
        self.initiative_rolled: bool = False

    def sort_initiative(self) -> None:
        """Sorts characters in descending order of initiative."""
        self.engine.characters.sort(key=lambda c: c.init, reverse=True)
        self.engine.log(translate("messages.initiative_sorted"))
        self.engine.notify(EventType.UPDATE)

    def roll_all_initiatives(self) -> None:
        """Rerolls initiative for all characters."""
        for char in self.engine.characters:
            char.init = wuerfle_initiative(char.gew)
        self.sort_initiative()
        self.engine.log(translate("messages.all_initiatives_rerolled"))
        self.engine.notify(EventType.UPDATE)

    def roll_initiatives(self, reroll_all: bool = False) -> None:
        """
        Rolls initiative for characters with Init 0 (or all).
        Then starts the combat.
        """
        for char in self.engine.characters:
            if reroll_all or char.init == 0:
                char.init = wuerfle_initiative(char.gew)

        self.sort_initiative()
        self.turn_index = 0
        self.round_number = 1
        self.initiative_rolled = True
        self.engine.log(translate("messages.initiative_rolled"))
        self.engine.log(translate("messages.round_begins", round_number=self.round_number))
        self.engine.notify(EventType.UPDATE)

    def reset_initiative(self, target_type: str = ScopeType.ALL.value) -> int:
        """Resets the initiative."""
        count = 0
        for char in self.engine.characters:
            if target_type == ScopeType.ALL.value or char.char_type == target_type:
                char.init = 0
                count += 1

        self.turn_index = -1
        self.round_number = 1
        self.initiative_rolled = False

        type_text = translate("management_targets.all_characters") if target_type == ScopeType.ALL.value else f"{translate('management_targets.all_enemies')}s" if target_type == CharacterType.ENEMY else f"{translate('management_targets.all_players')}s" if target_type == CharacterType.PLAYER else f"{translate('management_targets.all_npcs')}s"
        self.engine.log(translate("messages.initiative_reset", type_text=type_text, count=count))
        self.engine.notify(EventType.UPDATE)
        return count

    def _update_character_status(self, character: Character) -> None:
        """
        Updates all active status effects for a character.
        This method logically belongs to the TurnManager, as it is executed at the beginning of a turn.
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
        Switches to the next character and applies status effects.
        """
        if not self.engine.characters:
            return None

        self.turn_index += 1

        # New round
        if self.turn_index >= len(self.engine.characters):
            self.turn_index = 0
            self.round_number += 1
            self.engine.log(translate("messages.round_begins", round_number=self.round_number))

        current_char = self.engine.characters[self.turn_index]

        # Process status effects
        self._update_character_status(current_char)

        # Process skipping turns
        if current_char.skip_turns > 0:
            self.engine.log(translate("messages.character_skips_turn", name=current_char.name))
            current_char.skip_turns -= 1 # Is set to 0 in _update_character_status, but here in case of multiple rounds
            self.engine.notify(EventType.UPDATE)
            return self.next_turn() # Recursively continue

        # Status info for log
        status_info = current_char.get_status_string()

        if current_char.lp <= 0 or current_char.max_lp <= 0:
             self.engine.log(f"💀 {current_char.name} {translate('messages.is_incapacitated')}{status_info}")
        else:
             self.engine.log(f"▶ {current_char.name}{translate('messages.is_on_turn')}{status_info}")

        self.engine.notify(EventType.TURN_CHANGE, current_char)
        self.engine.notify(EventType.UPDATE)

        return current_char

    def reset_combat(self) -> None:
        self.turn_index = -1
        self.round_number = 1
        self.initiative_rolled = False

    def insert_character(self, char: Character, surprise: bool = False) -> None:
        """
        Inserts a character into the list, considering initiative/surprise.
        """
        if self.turn_index == -1: # Initiative not yet rolled
            self.engine.characters.append(char)
            self.engine.log(translate("messages.character_added", name=char.name))
        else:
            if surprise:
                # Surprise: Insert BEFORE the current turn (or at the current position)
                target_index = max(0, self.turn_index)
                self.engine.characters.insert(target_index, char)
                if self.turn_index < 0:
                    self.turn_index = 0
                self.engine.log(translate("messages.character_jumps_in", name=char.name))
            else:
                # Normal sorting by initiative
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
                self.engine.log(translate("messages.character_sorted_in", name=char.name))

        self.engine.notify(EventType.UPDATE)

    def remove_character(self, index: int) -> None:
        """Removes a character and adjusts the turn index."""
        if 0 <= index < len(self.engine.characters):
            char = self.engine.characters.pop(index)
            self.engine.log(translate("messages.character_removed", name=char.name))

            # Adjust turn index
            if index < self.turn_index:
                self.turn_index -= 1
            elif index == self.turn_index:
                if self.turn_index >= len(self.engine.characters):
                    self.turn_index = 0
                    if not self.engine.characters:
                        self.turn_index = -1

            self.engine.notify(EventType.UPDATE)

    def remove_characters_by_type(self, char_type: str) -> None:
        """Removes all characters of a specific type."""
        self.engine.characters = [c for c in self.engine.characters if c.char_type != char_type]

        # Correct turn index
        if self.turn_index >= len(self.engine.characters):
            self.turn_index = 0
            if not self.engine.characters:
                self.turn_index = -1

        self.engine.log(translate("messages.all_characters_of_type_deleted", type=char_type))
        self.engine.notify(EventType.UPDATE)

    def clear_all_characters(self) -> None:
        """Deletes all characters and resets the combat."""
        self.engine.characters.clear()
        self.reset_combat()
        self.engine.log(translate("messages.all_characters_deleted"))
        self.engine.notify(EventType.UPDATE)
