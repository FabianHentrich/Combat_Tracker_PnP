from typing import TYPE_CHECKING, List
from src.models.character import Character
from src.config.rule_manager import get_rules
from src.models.enums import EventType, ScopeType, RuleKey
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager
    from src.ui.interfaces import ICombatView

class CombatActionHandler:
    """
    Controller for combat actions like damage, healing, status, and initiative.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', view: 'ICombatView'):
        self.engine: 'CombatEngine' = engine
        self.history_manager: 'HistoryManager' = history_manager
        self.view = view

    def roll_initiative_all(self) -> None:
        """Sorts characters based on initiative, rolling for those with 0."""
        self.history_manager.save_snapshot()
        self.engine.roll_initiatives()

        if self.engine.characters:
            char = self.engine.characters[0]
            self.engine.notify(EventType.LOG, f"▶ {char.name}'s turn!")

    def reset_initiative(self, target_type: str = ScopeType.ALL.value) -> None:
        """Resets the initiative."""
        self.history_manager.save_snapshot()
        self.engine.reset_initiative(target_type)

    def next_turn(self) -> None:
        """Proceeds to the next turn."""
        self.history_manager.save_snapshot()
        self.engine.next_turn()

    def deal_damage(self) -> None:
        """Reads damage from the UI panel and applies it to all selected characters."""
        chars = self._get_selected_chars()
        if not chars: return

        damage_amount, damage_details = self.view.get_damage_data()
        
        if damage_amount <= 0:
            self.view.show_info(translate("dialog.info.title"), translate("messages.enter_damage_value"))
            return

        first_part = damage_details.split(",")[0].strip()
        parts = first_part.split(" ", 1)
        main_type = parts[1] if len(parts) > 1 else "Normal"

        rules = get_rules()
        max_rank = 6
        if main_type in rules.get(RuleKey.DAMAGE_TYPES, {}):
            sec_effect = rules[RuleKey.DAMAGE_TYPES][main_type].get(RuleKey.SECONDARY_EFFECT)
            if sec_effect and sec_effect in rules.get(RuleKey.STATUS_EFFECTS, {}):
                max_rank = rules[RuleKey.STATUS_EFFECTS][sec_effect].get(RuleKey.MAX_RANK, 6)

        status_input = self.view.get_status_input()
        try:
            rank = int(status_input["rank"])
            if rank > max_rank: rank = max_rank
        except ValueError:
            rank = 1

        self.history_manager.save_snapshot()
        
        for char in chars:
            self.engine.apply_damage(char, damage_amount, main_type, rank, damage_details)
        
        if "," in damage_details:
            self.engine.log(f"{translate('common.details')}: {damage_details}")
        
        if len(chars) > 1:
            self.engine.log(translate("messages.damage_applied_to_targets", count=len(chars)))

    def add_status_to_character(self) -> None:
        """Adds a status effect to all selected characters."""
        chars = self._get_selected_chars()
        if not chars: return

        status_input = self.view.get_status_input()
        status = status_input["status"]
        duration_str = status_input["duration"]
        rank_str = status_input["rank"]

        if not status:
            self.view.show_warning(translate("dialog.error.title"), translate("messages.enter_or_select_status"))
            return

        rules = get_rules()
        max_rank = 6
        if status in rules.get(RuleKey.STATUS_EFFECTS, {}):
             max_rank = rules[RuleKey.STATUS_EFFECTS][status].get(RuleKey.MAX_RANK, 6)

        try:
            duration = int(duration_str)
            rank = int(rank_str)
            if duration <= 0 or rank <= 0: raise ValueError

            if rank > max_rank:
                rank = max_rank
                self.view.show_info(translate("dialog.info.title"), translate("messages.max_rank_adjusted", status=status, max_rank=max_rank))
        except ValueError:
            self.view.show_warning(translate("dialog.error.title"), translate("messages.enter_valid_numbers_duration_rank"))
            return

        self.history_manager.save_snapshot()
        for char in chars:
            self.engine.add_status_effect(char, status, duration, rank)
            
        if len(chars) > 1:
            self.engine.log(translate("messages.status_applied_to_targets", status=status, count=len(chars)))

    def apply_healing(self) -> None:
        """Applies healing to all selected characters."""
        chars = self._get_selected_chars()
        if not chars: return

        val = self.view.get_action_value()
        if val <= 0:
            self.view.show_info(translate("dialog.info.title"), translate("messages.enter_healing_value"))
            return

        self.history_manager.save_snapshot()
        for char in chars:
            self.engine.apply_healing(char, val)

    def apply_shield(self) -> None:
        """Increases the shield value of all selected characters."""
        chars = self._get_selected_chars()
        if not chars: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            for char in chars:
                self.engine.apply_shield(char, val)

    def apply_armor(self) -> None:
        """Increases the armor value of all selected characters."""
        chars = self._get_selected_chars()
        if not chars: return
        val = self.view.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            for char in chars:
                self.engine.apply_armor(char, val)

    def _get_selected_chars(self) -> List[Character]:
        """Helper method: Fetches all selected characters via the view."""
        char_ids = self.view.get_selected_char_ids()
        if not char_ids:
            self.view.show_error(translate("dialog.error.title"), translate("messages.no_character_selected"))
            return []
        
        chars = [self.engine.get_character_by_id(cid) for cid in char_ids]
        return [c for c in chars if c is not None]
