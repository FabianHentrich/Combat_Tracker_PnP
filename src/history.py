import copy
from .logger import setup_logging

logger = setup_logging()

class HistoryManager:
    def __init__(self, engine):
        self.engine = engine
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 20

    def save_snapshot(self):
        """Wird vor jeder Aktion aufgerufen (Schaden, Next Turn, etc.)"""
        state = self.engine.get_state()
        # Deep copy is usually safer for state snapshots if get_state returns references
        # But get_state returns dicts with new lists, so it should be fine if Character.to_dict returns values.
        # Character.to_dict returns values and a list of status dicts.
        # Let's use deepcopy just to be safe against mutable objects in the dict.
        state_copy = copy.deepcopy(state)

        self.undo_stack.append(state_copy)
        self.redo_stack.clear() # Redo leeren bei neuer Aktion

        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        logger.debug("Snapshot gespeichert. Undo Stack Größe: %d", len(self.undo_stack))

    def undo(self):
        if not self.undo_stack:
            logger.info("Undo nicht möglich: Stack leer.")
            return False

        current_state = self.engine.get_state()
        self.redo_stack.append(copy.deepcopy(current_state))

        prev_state = self.undo_stack.pop()
        self.engine.load_state(prev_state)
        logger.info("Undo ausgeführt.")
        return True

    def redo(self):
        if not self.redo_stack:
            logger.info("Redo nicht möglich: Stack leer.")
            return False

        current_state = self.engine.get_state()
        self.undo_stack.append(copy.deepcopy(current_state))

        next_state = self.redo_stack.pop()
        self.engine.load_state(next_state)
        logger.info("Redo ausgeführt.")
        return True

