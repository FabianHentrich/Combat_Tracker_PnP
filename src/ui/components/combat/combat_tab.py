import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, TYPE_CHECKING
from src.config import FONTS
from src.utils.localization import translate
from src.ui.components.combat.character_list import CharacterList
from src.ui.components.combat.action_panel import ActionPanel
from src.ui.components.audio.audio_player_view import AudioPlayerWidget
from src.ui.components.dice_roller import DiceRoller

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker


class CombatTab(ttk.Frame):
    """
    Content for the '⚔ Kampf' tab.
    Left pane:  CharacterList (top, expands) + Combat Log + DiceRoller (bottom, fixed).
    Right pane: ActionPanel (expands) + AudioPlayerWidget (fixed).
    """

    def __init__(self, parent: tk.Widget, controller: 'CombatTracker', colors: Dict[str, str]):
        super().__init__(parent)
        self.controller = controller
        self.colors = colors

        self.character_list: Optional[CharacterList] = None
        self.action_panel: Optional[ActionPanel] = None
        self.audio_player: Optional[AudioPlayerWidget] = None
        self.log: Optional[tk.Text] = None
        self.dice_roller: Optional[DiceRoller] = None
        self._content_paned: Optional[ttk.PanedWindow] = None

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self._setup_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self._content_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self._content_paned.grid(row=0, column=0, sticky="nsew")

        # ── Left column ──────────────────────────────────────────────
        left_col = ttk.Frame(self._content_paned)
        self._content_paned.add(left_col, weight=1)

        left_col.rowconfigure(0, weight=1)   # CharacterList expands
        left_col.rowconfigure(1, weight=0)   # Log + dice fixed
        left_col.columnconfigure(0, weight=1)

        self.character_list = CharacterList(left_col, self.controller, self.colors)
        self.character_list.grid(row=0, column=0, sticky="nsew")

        # Log + dice row
        log_row = ttk.Frame(left_col)
        log_row.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        log_row.columnconfigure(0, weight=1)
        log_row.columnconfigure(1, weight=0)

        log_frame = ttk.LabelFrame(
            log_row, text=translate("bottom_panel.combat_log_label"),
            style="Card.TLabelframe",
        )
        log_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log = tk.Text(
            log_frame, height=7, state="disabled",
            bg=self.colors["entry_bg"], fg=self.colors["fg"],
            insertbackground=self.colors["fg"],
            font=FONTS["log"], wrap=tk.WORD,
        )
        self.log.grid(row=0, column=0, sticky="nsew")

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log.configure(yscrollcommand=log_scroll.set)

        self.dice_roller = DiceRoller(log_row, self.colors)
        self.dice_roller.grid(row=0, column=1, sticky="ns")

        # ── Right column ─────────────────────────────────────────────
        right_col = ttk.Frame(self._content_paned)
        self._content_paned.add(right_col, weight=0)

        right_col.rowconfigure(0, weight=1)   # ActionPanel expands
        right_col.rowconfigure(1, weight=0)   # Audio fixed
        right_col.columnconfigure(0, weight=1)

        self.action_panel = ActionPanel(right_col, self.controller, self.colors)
        self.action_panel.grid(row=0, column=0, sticky="nsew", padx=(6, 0))

        self.audio_player = AudioPlayerWidget(
            right_col,
            self.controller.audio_controller,
            self.controller.open_audio_settings,
        )
        self.audio_player.grid(row=1, column=0, sticky="ew", padx=(6, 0), pady=(6, 0))

        # Set sash after the UI has had time to render
        self.after(800, self._init_sash)

    def _init_sash(self):
        try:
            self.update_idletasks()
            total = self._content_paned.winfo_width()
            if total > 100:
                self._content_paned.sashpos(0, int(total * 0.65))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self.character_list:
            self.character_list.update_colors(colors)
        if self.action_panel:
            self.action_panel.update_colors(colors)
        if self.dice_roller:
            self.dice_roller.update_colors(colors)
        if self.log and self.log.winfo_exists():
            self.log.configure(
                bg=colors["entry_bg"], fg=colors["fg"],
                insertbackground=colors["fg"],
            )
