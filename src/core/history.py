import copy
from typing import List, Dict, Any, TYPE_CHECKING
from src.utils.logger import setup_logging
from src.config import MAX_HISTORY
from src.models.enums import EventType
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.core.engine import CombatEngine

logger = setup_logging()

class HistoryManager:
    def __init__(self, engine: 'CombatEngine'):
        self.engine = engine
        self.undo_stack: List[Dict[str, Any]] = []
        self.redo_stack: List[Dict[str, Any]] = []
        self.max_history: int = MAX_HISTORY

    def save_snapshot(self) -> None:
        """Called before every action (damage, next turn, etc.)"""
        state = self.engine.get_state()
        # Deep copy is usually safer for state snapshots if get_state returns references
        # But get_state returns dicts with new lists, so it should be fine if Character.to_dict returns values.
        # Character.to_dict returns values and a list of status dicts.
        # Let's use deepcopy just to be safe against mutable objects in the dict.
        state_copy = copy.deepcopy(state)

        self.undo_stack.append(state_copy)
        self.redo_stack.clear() # Clear redo stack on new action

        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        logger.debug("Snapshot saved. Undo stack size: %d", len(self.undo_stack))

    def undo(self) -> bool:
        if not self.undo_stack:
            logger.info("Cannot undo: stack empty.")
            return False

        current_state = self.engine.get_state()
        self.redo_stack.append(copy.deepcopy(current_state))

        prev_state = self.undo_stack.pop()
        self.engine.load_state(prev_state)
        logger.info("Undo executed.")
        self.engine.notify(EventType.LOG, translate("messages.undo_executed"))
        return True

    def redo(self) -> bool:
        if not self.redo_stack:
            logger.info("Cannot redo: stack empty.")
            return False

        current_state = self.engine.get_state()
        self.undo_stack.append(copy.deepcopy(current_state))

        next_state = self.redo_stack.pop()
        self.engine.load_state(next_state)
        logger.info("Redo executed.")
        self.engine.notify(EventType.LOG, translate("messages.redo_executed"))
        return True
