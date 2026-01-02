from typing import Protocol, Any, Optional, Dict

class ICombatView(Protocol):
    """Interface für die Haupt-Ansicht des Combat Trackers."""

    def setup_ui(self) -> None:
        """Erstellt die UI-Komponenten."""
        ...

    def show_error(self, title: str, message: str) -> None:
        """Zeigt eine Fehlermeldung an."""
        ...

    def show_info(self, title: str, message: str) -> None:
        """Zeigt eine Informationsmeldung an."""
        ...

    def show_warning(self, title: str, message: str) -> None:
        """Zeigt eine Warnmeldung an."""
        ...

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Zeigt einen Ja/Nein-Dialog an."""
        ...

    def log_message(self, message: str) -> None:
        """Fügt eine Nachricht zum Log hinzu."""
        ...

    def update_listbox(self) -> None:
        """Aktualisiert die Charakterliste."""
        ...

    def get_quick_add_data(self) -> Dict[str, Any]:
        """Liest die Daten aus dem Schnelleingabe-Panel."""
        ...

    def clear_quick_add_fields(self) -> None:
        """Leert die Felder des Schnelleingabe-Panels."""
        ...

    def set_quick_add_defaults(self) -> None:
        """Setzt Standardwerte im Schnelleingabe-Panel."""
        ...

    def get_selected_char_id(self) -> Optional[str]:
        """Gibt die ID des aktuell ausgewählten Charakters zurück."""
        ...

    def highlight_character(self, char_id: str) -> None:
        """Hebt den Charakter mit der angegebenen ID in der Liste hervor."""
        ...

    def get_action_value(self) -> int:
        """Gibt den Wert aus dem Aktions-Eingabefeld zurück (z.B. Schaden)."""
        ...

    def get_action_type(self) -> str:
        """Gibt den ausgewählten Schadenstyp zurück."""
        ...

    def get_status_input(self) -> Dict[str, Any]:
        """Gibt die Eingaben für Status-Effekte zurück (status, rank, duration)."""
        ...

    def update_round_label(self, round_number: int) -> None:
        """Aktualisiert die Anzeige der aktuellen Runde."""
        ...

    def fill_input_fields(self, data: Dict[str, Any]) -> None:
        """Füllt die Eingabefelder mit den übergebenen Daten."""
        ...

    def update_colors(self, colors: Dict[str, str]) -> None:
        """Aktualisiert das Farbschema der View."""
        ...

    def focus_damage_input(self) -> None:
        """Setzt den Fokus auf das Schadens-Eingabefeld."""
        ...
