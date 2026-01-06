import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Callable, Dict, Any, Optional, List, Tuple
from src.config import COLORS, FONTS
from src.ui.components.dice_roller import DiceRoller
from src.ui.interfaces import ICombatView
from src.ui.components.audio.audio_player_view import AudioPlayerWidget
from src.ui.components.combat.quick_add_panel import QuickAddPanel
from src.ui.components.combat.action_panel import ActionPanel
from src.ui.components.combat.character_list import CharacterList
from src.ui.styles import StyleManager
from src.ui.components.main_menu import MainMenu
from src.ui.components.combat.bottom_panel import BottomPanel
from src.utils.localization import translate
from src.models.enums import ScopeType
from src.ui.components.dm_notes_panel import DMNotesPanel

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class MainView(ICombatView):
    def __init__(self, controller: 'CombatTracker', root: tk.Tk):
        self.controller = controller
        self.root = root
        self.colors = COLORS
        self.style_manager = StyleManager(root)

        # Components
        self.main_menu: Optional[MainMenu] = None
        self.quick_add_panel: Optional[QuickAddPanel] = None
        self.character_list: Optional[CharacterList] = None
        self.action_panel: Optional[ActionPanel] = None
        self.bottom_panel: Optional[BottomPanel] = None
        self.audio_player: Optional[AudioPlayerWidget] = None
        self.dm_notes_panel: Optional[ttk.Frame] = None  # Panel für DM-Notizen

    def setup_ui(self) -> None:
        # Menübar erstellen
        self.main_menu = MainMenu(self.root, self.controller)

        # Hauptcontainer mit Splitter (PanedWindow)
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Linkes Panel: DM-Notizen (DMNotesPanel)
        self.dm_notes_panel = DMNotesPanel(paned_window, root_dir="data/dm_notes/", colors=self.colors, link_callback=self._open_library_link)
        paned_window.add(self.dm_notes_panel, weight=1)

        # Rechtes Panel: Bisherige Hauptinhalte
        main_frame = ttk.Frame(paned_window, padding="15")
        paned_window.add(main_frame, weight=4)

        # --- OBERER BEREICH: QuickAddPanel (mit Open Library Button) und Musikplayer nebeneinander ---
        top_row = ttk.Frame(main_frame)
        top_row.pack(fill="x", pady=(0, 15))
        # QuickAddPanel mit Bibliotheks-Button oben links
        quickadd_frame = ttk.Frame(top_row)
        quickadd_frame.pack(side="left", fill="both", expand=True)
        btn_library = ttk.Button(quickadd_frame, text=translate("main_view.open_library"), command=self.controller.library_handler.open_library_window)
        btn_library.pack(side="top", anchor="nw", pady=(0, 4))
        self.quick_add_panel = QuickAddPanel(quickadd_frame, self.controller)
        self.quick_add_panel.pack(fill="both", expand=True)
        # Musikplayer dynamisch
        self.audio_player = AudioPlayerWidget(top_row, self.controller.audio_controller, self.controller.open_audio_settings)
        self.audio_player.pack(side="left", fill="both", expand=True, padx=(15, 0))

        # --- MITTLERER BEREICH: Tabelle und Aktionen ---
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Linke Seite: Tabelle (Treeview)
        self.character_list = CharacterList(content_frame, self.controller, self.colors)
        self.character_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Rechte Seite: Container für Player und Aktionen
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))

        # Aktions-Panel
        self.action_panel = ActionPanel(right_frame, self.controller, self.colors)
        self.action_panel.pack(fill=tk.X, ipadx=10)

        # --- UNTERER BEREICH: Kampfsteuerung & Log ---
        self.bottom_panel = BottomPanel(main_frame, self.controller, self.colors)


    # --- Interface Implementation ---

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    def log_message(self, message: str) -> None:
        if self.bottom_panel and self.bottom_panel.log:
            self.bottom_panel.log.config(state="normal")
            self.bottom_panel.log.insert(tk.END, str(message).strip() + "\n")
            self.bottom_panel.log.see(tk.END)
            self.bottom_panel.log.config(state="disabled")

    def get_quick_add_data(self) -> Dict[str, Any]:
        return self.quick_add_panel.get_data()

    def clear_quick_add_fields(self) -> None:
        self.quick_add_panel.clear()

    def set_quick_add_defaults(self) -> None:
        self.quick_add_panel.set_defaults()

    def get_selected_char_id(self) -> Optional[str]:
        return self.character_list.get_selected_id()
        
    def get_selected_char_ids(self) -> List[str]:
        return self.character_list.get_selected_ids()

    def highlight_character(self, char_id: str) -> None:
        self.character_list.highlight(char_id)

    def get_action_value(self) -> int:
        return self.action_panel.get_value()

    def get_action_type(self) -> str:
        return self.action_panel.get_type()
        
    def get_damage_data(self) -> Tuple[int, str]:
        return self.action_panel.get_damage_data()

    def get_status_input(self) -> Dict[str, Any]:
        return self.action_panel.get_status_input()

    def get_management_target(self) -> ScopeType:
        return self.action_panel.get_management_target()

    def focus_damage_input(self) -> None:
        self.action_panel.focus_value_input()

    def update_listbox(self) -> None:
        """
        Aktualisiert die Anzeige der Charakterliste (Treeview).
        """
        self.character_list.update_list()
        self.update_round_label(self.controller.engine.round_number)
        self.controller.autosave()

    def update_round_label(self, round_number: int) -> None:
        if self.bottom_panel and self.bottom_panel.round_label:
            self.bottom_panel.round_label.config(text=f"{translate('main_view.round')}: {round_number}")

    def fill_input_fields(self, data: Dict[str, Any]) -> None:
        self.quick_add_panel.fill_fields(data)

    def update_colors(self, colors: Dict[str, str]) -> None:
        self.colors = colors
        self.root.configure(bg=self.colors["bg"])

        self.style_manager.configure_styles(colors)

        # Update components
        if self.character_list:
            self.character_list.update_colors(colors)
        if self.action_panel:
            self.action_panel.update_colors(colors)
        if self.bottom_panel:
            self.bottom_panel.update_colors(colors)

    def _open_library_link(self, link: str):
        # Öffnet einen Link im Bibliotheks-Markdown-Browser
        try:
            self.controller.library_handler.open_library_window_with_file(link)
        except Exception as e:
            messagebox.showerror(translate("main_view.error_title"), f"Bibliotheks-Link konnte nicht geöffnet werden: {e}")
