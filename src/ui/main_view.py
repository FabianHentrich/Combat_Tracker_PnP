import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Dict, Any, Optional, List, Tuple

from src.config import COLORS
from src.ui.interfaces import ICombatView
from src.ui.components.combat.control_bar import ControlBar
from src.ui.components.combat.combat_tab import CombatTab
from src.ui.components.dm_notes_panel import DMNotesPanel
from src.ui.components.main_menu import MainMenu
from src.ui.styles import StyleManager
from src.utils.localization import translate
from src.models.enums import ScopeType
from src.ui.components.dialogs.secondary_effect_dialog import SecondaryEffectDialog
from src.models.character import Character

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker


class MainView(ICombatView):
    def __init__(self, controller: 'CombatTracker', root: tk.Tk):
        self.controller = controller
        self.root = root
        self.colors = COLORS
        self.style_manager = StyleManager(root)

        # Top-level components (set in setup_ui)
        self.main_menu: Optional[MainMenu] = None
        self.control_bar: Optional[ControlBar] = None
        self.combat_tab: Optional[CombatTab] = None
        self.dm_notes_panel: Optional[DMNotesPanel] = None
        self._notebook: Optional[ttk.Notebook] = None

        # Aliases for ICombatView delegation (set in setup_ui after components created)
        self.quick_add_panel = None
        self.character_list = None
        self.action_panel = None
        self.audio_player = None

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup_ui(self) -> None:
        self.main_menu = MainMenu(self.root, self.controller)

        # Root frame fills the window
        root_frame = ttk.Frame(self.root)
        root_frame.pack(fill=tk.BOTH, expand=True)
        root_frame.rowconfigure(0, weight=0)   # ControlBar — fixed
        root_frame.rowconfigure(1, weight=0)   # Separator
        root_frame.rowconfigure(2, weight=1)   # Notebook — expands
        root_frame.columnconfigure(0, weight=1)

        # ── Control bar (always visible) ──────────────────────────────
        self.control_bar = ControlBar(root_frame, self.controller, self.colors)
        self.control_bar.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))

        ttk.Separator(root_frame, orient=tk.HORIZONTAL).grid(
            row=1, column=0, sticky="ew", pady=(4, 0)
        )

        # ── Notebook with 3 tabs ──────────────────────────────────────
        self._notebook = ttk.Notebook(root_frame)
        self._notebook.grid(row=2, column=0, sticky="nsew", padx=5, pady=(4, 5))

        # Tab 1 — Kampf
        combat_frame = ttk.Frame(self._notebook)
        self._notebook.add(combat_frame, text=f"⚔  {translate('tabs.combat')}")
        self.combat_tab = CombatTab(combat_frame, self.controller, self.colors)
        self.combat_tab.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Tab 2 — Bibliothek (embedded)
        library_frame = ttk.Frame(self._notebook)
        self._notebook.add(library_frame, text=f"📚  {translate('tabs.library')}")
        self.controller.library_handler.build_embedded(
            library_frame,
            tab_switch_callback=lambda: self._notebook.select(1),
            close_callback=lambda: self._notebook.select(0),
        )

        # Tab 3 — DM-Notizen
        dm_frame = ttk.Frame(self._notebook)
        self._notebook.add(dm_frame, text=f"📝  {translate('tabs.dm_notes')}")
        self.dm_notes_panel = DMNotesPanel(
            dm_frame,
            root_dir="data/dm_notes/",
            colors=self.colors,
            link_callback=self._open_library_link,
        )
        self.dm_notes_panel.pack(fill=tk.BOTH, expand=True)

        # ── Aliases so ICombatView methods keep working unchanged ─────
        self.quick_add_panel = self.control_bar.quick_add
        self.character_list = self.combat_tab.character_list
        self.action_panel = self.combat_tab.action_panel
        self.audio_player = self.combat_tab.audio_player

    # ------------------------------------------------------------------
    # ICombatView — dialogs
    # ------------------------------------------------------------------

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    # ------------------------------------------------------------------
    # ICombatView — combat log
    # ------------------------------------------------------------------

    def log_message(self, message: str) -> None:
        log = self.combat_tab.log if self.combat_tab else None
        if log:
            log.config(state="normal")
            log.insert(tk.END, str(message).strip() + "\n")
            log.see(tk.END)
            log.config(state="disabled")

    def get_log_content(self) -> str:
        log = self.combat_tab.log if self.combat_tab else None
        return log.get("1.0", "end-1c") if log else ""

    def set_log_content(self, content: str) -> None:
        log = self.combat_tab.log if self.combat_tab else None
        if log:
            log.config(state="normal")
            log.delete("1.0", tk.END)
            log.insert(tk.END, content)
            log.see(tk.END)
            log.config(state="disabled")

    # ------------------------------------------------------------------
    # ICombatView — quick add
    # ------------------------------------------------------------------

    def get_quick_add_data(self) -> Dict[str, Any]:
        return self.quick_add_panel.get_data()

    def clear_quick_add_fields(self) -> None:
        self.quick_add_panel.clear()

    def set_quick_add_defaults(self) -> None:
        self.quick_add_panel.set_defaults()

    # ------------------------------------------------------------------
    # ICombatView — character list
    # ------------------------------------------------------------------

    def get_selected_char_id(self) -> Optional[str]:
        return self.character_list.get_selected_id()

    def get_selected_char_ids(self) -> List[str]:
        return self.character_list.get_selected_ids()

    def update_listbox(self) -> None:
        self.character_list.update_list()
        self.update_round_label(self.controller.engine.round_number)

    # ------------------------------------------------------------------
    # ICombatView — action panel
    # ------------------------------------------------------------------

    def get_action_value(self) -> int:
        return self.action_panel.get_value()

    def get_damage_data(self) -> Tuple[int, str, str]:
        return self.action_panel.get_damage_data()

    def get_status_input(self) -> Dict[str, Any]:
        return self.action_panel.get_status_input()

    def get_overheal(self) -> bool:
        return self.action_panel.get_overheal()

    def get_management_target(self) -> ScopeType:
        return self.action_panel.get_management_target()

    def focus_damage_input(self) -> None:
        self.action_panel.focus_value_input()

    # ------------------------------------------------------------------
    # ICombatView — round label
    # ------------------------------------------------------------------

    def update_round_label(self, round_number: int) -> None:
        if self.control_bar and self.control_bar.round_label:
            self.control_bar.round_label.config(
                text=f"{translate('main_view.round')}: {round_number}"
            )

    # ------------------------------------------------------------------
    # ICombatView — secondary-effect dialog
    # ------------------------------------------------------------------

    def ask_secondary_effect(self, effect_name: str, chars: List[Character], max_rank: int = 6):
        dialog = SecondaryEffectDialog(self.root, effect_name, chars, self.colors, max_rank=max_rank)
        return dialog.result, dialog.rank, dialog.duration

    # ------------------------------------------------------------------
    # ICombatView — theme
    # ------------------------------------------------------------------

    def update_colors(self, colors: Dict[str, str]) -> None:
        self.colors = colors
        self.root.configure(bg=colors["bg"])
        self.style_manager.configure_styles(colors)

        if self.control_bar:
            self.control_bar.update_colors(colors)
        if self.combat_tab:
            self.combat_tab.update_colors(colors)
        if self.dm_notes_panel and hasattr(self.dm_notes_panel, "update_colors"):
            self.dm_notes_panel.update_colors(colors)
        self.controller.library_handler.update_colors(colors)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _open_library_link(self, link: str):
        try:
            self.controller.library_handler.open_library_window_with_file(link)
        except Exception as e:
            messagebox.showerror(
                translate("dialog.error.title"),
                f"Bibliotheks-Link konnte nicht geöffnet werden: {e}",
            )
