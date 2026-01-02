from typing import List, Dict, Any, Callable, Optional
from src.config import MAX_HISTORY

class NavigationManager:
    """
    Verwaltet eine Navigations-Historie (Vor/Zurück).
    """
    def __init__(self, on_restore: Callable[[Dict[str, Any]], None], on_update_ui: Optional[Callable[[bool, bool], None]] = None):
        self.history: List[Dict[str, Any]] = []
        self.index: int = -1
        self.is_navigating: bool = False
        self.on_restore = on_restore
        self.on_update_ui = on_update_ui

    def push(self, state: Dict[str, Any]) -> None:
        """Fügt einen neuen Zustand zur Historie hinzu."""
        if self.is_navigating:
            return

        # Vermeide Duplikate des aktuellen Zustands
        if self.index >= 0 and self.history:
            current = self.history[self.index]
            if current == state:
                return

        # Schneide Zukunft ab, wenn wir uns in der Mitte befinden und was neues machen
        self.history = self.history[:self.index+1]

        self.history.append(state)
        self.index += 1

        # Begrenze Historie auf MAX_HISTORY
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
            self.index -= 1

        self._notify_ui()

    def back(self) -> None:
        """Geht einen Schritt zurück."""
        if self.index > 0:
            self.index -= 1
            self._trigger_restore()

    def forward(self) -> None:
        """Geht einen Schritt vorwärts."""
        if self.index < len(self.history) - 1:
            self.index += 1
            self._trigger_restore()

    def _trigger_restore(self) -> None:
        self.is_navigating = True
        try:
            self.on_restore(self.history[self.index])
        finally:
            self.is_navigating = False
            self._notify_ui()

    def _notify_ui(self) -> None:
        if self.on_update_ui:
            can_back = self.index > 0
            can_forward = self.index < len(self.history) - 1
            self.on_update_ui(can_back, can_forward)
