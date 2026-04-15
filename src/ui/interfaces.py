from typing import Protocol, Any, Optional, Dict, Tuple, List, TYPE_CHECKING
from src.models.enums import ScopeType

if TYPE_CHECKING:
    from src.models.character import Character

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
        
    def get_selected_char_ids(self) -> List[str]:
        """Gibt eine Liste aller ausgewählten Item-IDs zurück."""
        ...

    def get_action_value(self) -> int:
        """Gibt den Wert aus dem Aktions-Eingabefeld zurück (z.B. Schaden)."""
        ...

    def get_damage_data(self) -> Tuple[int, str, str]:
        """Gibt (Gesamtschaden, primärer_Schadenstyp, Detail-String) aus dem ActionPanel zurück."""
        ...

    def get_status_input(self) -> Dict[str, Any]:
        """Gibt die Eingaben für Status-Effekte zurück (status, rank, duration)."""
        ...

    def get_overheal(self) -> bool:
        """Gibt zurück, ob Überheilung erlaubt ist."""
        ...

    def get_management_target(self) -> ScopeType:
        """Gibt den ausgewählten Management-Zielbereich zurück."""
        ...

    def update_round_label(self, round_number: int) -> None:
        """Aktualisiert die Anzeige der aktuellen Runde."""
        ...

    def update_colors(self, colors: Dict[str, str]) -> None:
        """Aktualisiert das Farbschema der View."""
        ...

    def focus_damage_input(self) -> None:
        """Setzt den Fokus auf das Schadens-Eingabefeld."""
        ...

    def ask_secondary_effect(self, effect_name: str, chars: List['Character'], max_rank: int = 6) -> Tuple[List['Character'], int, int]:
        """Fragt den DM, welche der gewählten Charaktere vom Sekundäreffekt betroffen sind.
        Gibt (bestätigte Charaktere, rang, dauer) zurück."""
        ...
