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
from src.utils.paned_logger import get_logger

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

        # Logger für PanedWindow-Positionen aktivieren
        logger = get_logger()
        logger.attach_logger(paned_window, "PanedWindow_1_DM_vs_Main")

        # Linkes Panel: DM-Notizen (DMNotesPanel)
        self.dm_notes_panel = DMNotesPanel(paned_window, root_dir="data/dm_notes/", colors=self.colors, link_callback=self._open_library_link)
        paned_window.add(self.dm_notes_panel, weight=0)  # weight=0 damit sashpos() Kontrolle hat!

        # Rechtes Panel: Bisherige Hauptinhalte
        main_frame = ttk.Frame(paned_window, padding="15")
        paned_window.add(main_frame, weight=0)  # weight=0 damit sashpos() Kontrolle hat!

        # Erzwinge UI-Update damit winfo_screenwidth() korrekte Werte liefert
        self.root.update_idletasks()

        # Bildschirmbreite für optimale Positionierung ermitteln
        screen_width = self.root.winfo_screenwidth()

        # Setze optimale Sash-Position für DM-Notizen basierend auf Bildschirmbreite
        self._set_optimal_paned_positions(paned_window, screen_width)

        # Configure main_frame grid: Nur 2 Zeilen (Content + Bottom)
        main_frame.rowconfigure(0, weight=1)  # Content area (expandiert)
        main_frame.rowconfigure(1, weight=0)  # Bottom panel (fixed)
        main_frame.columnconfigure(0, weight=1)

        # --- ZWEITES PANEDWINDOW für Character List und Interaction Panel ---
        content_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        content_paned.grid(row=0, column=0, sticky="nsew")

        # Speichere für spätere Positionierung
        self.content_paned = content_paned

        # Logger für content_paned aktivieren
        logger.attach_logger(content_paned, "PanedWindow_2_CharList_vs_Interaction")

        # --- LINKE SEITE des content_paned: Library Button, QuickAdd+Audio, CharList ---
        left_column = ttk.Frame(content_paned)
        content_paned.add(left_column, weight=0)  # weight=0 damit sashpos() Kontrolle hat!

        # Configure left column rows
        left_column.rowconfigure(0, weight=0)  # Library Button
        left_column.rowconfigure(1, weight=0)  # QuickAdd + Audio (nebeneinander)
        left_column.rowconfigure(2, weight=1)  # Character List (expandiert!)
        left_column.columnconfigure(0, weight=1)

        # Library Button (oben)
        btn_library = ttk.Button(left_column, text=translate("main_view.open_library"),
                                command=self.controller.library_handler.open_library_window)
        btn_library.grid(row=0, column=0, sticky="w", pady=(0, 8))

        # Container für QuickAdd + Audio (nebeneinander)
        top_panels = ttk.Frame(left_column)
        top_panels.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        top_panels.columnconfigure(0, weight=2)  # QuickAdd bekommt mehr Platz
        top_panels.columnconfigure(1, weight=1)  # Audio kompakter

        # QuickAdd Panel (links)
        self.quick_add_panel = QuickAddPanel(top_panels, self.controller)
        self.quick_add_panel.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Audio Player (rechts)
        self.audio_player = AudioPlayerWidget(top_panels, self.controller.audio_controller,
                                              self.controller.open_audio_settings)
        self.audio_player.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Character List (expandiert vertikal)
        self.character_list = CharacterList(left_column, self.controller, self.colors)
        self.character_list.grid(row=2, column=0, sticky="nsew")

        # --- RECHTE SEITE des content_paned: Interaction Panel (VOLLE HÖHE!) ---
        self.action_panel = ActionPanel(content_paned, self.controller, self.colors)
        content_paned.add(self.action_panel, weight=0)  # weight=0 damit sashpos() Kontrolle hat!

        # Setze optimale Position für content_paned nach einem längeren Delay (damit UI vollständig gerendert ist)
        # Nutze die bereits ermittelte screen_width Variable
        # WICHTIG: Delay MUSS größer sein als das Delay vom ersten PanedWindow (1000ms)!
        self.root.after(1500, lambda: self._set_content_paned_position(content_paned, screen_width))

        # --- UNTERER BEREICH: Kampfsteuerung & Log (spans gesamte Breite) ---
        self.bottom_panel = BottomPanel(main_frame, self.controller, self.colors)
        self.bottom_panel.grid(row=1, column=0, sticky="ew", pady=(10, 0))


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

    def get_log_content(self) -> str:
        """Gibt den Inhalt des Kampfprotokolls zurück."""
        if self.bottom_panel and self.bottom_panel.log:
             return self.bottom_panel.log.get("1.0", "end-1c")
        return ""

    def set_log_content(self, content: str) -> None:
        """Setzt den Inhalt des Kampfprotokolls."""
        if self.bottom_panel and self.bottom_panel.log:
            self.bottom_panel.log.config(state="normal")
            self.bottom_panel.log.delete("1.0", tk.END)
            self.bottom_panel.log.insert(tk.END, content)
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

    def get_overheal(self) -> bool:
        return self.action_panel.get_overheal()

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
        if self.dm_notes_panel and hasattr(self.dm_notes_panel, "update_colors"):
            self.dm_notes_panel.update_colors(colors)

    def _open_library_link(self, link: str):
        # Öffnet einen Link im Bibliotheks-Markdown-Browser
        try:
            self.controller.library_handler.open_library_window_with_file(link)
        except Exception as e:
            messagebox.showerror(translate("main_view.error_title"), f"Bibliotheks-Link konnte nicht geöffnet werden: {e}")

    def _set_optimal_paned_positions(self, paned_window, screen_width):
        """Setzt optimale PanedWindow Positionen basierend auf Bildschirmauflösung."""
        # Optimale DM-Notizen Breite basierend auf Auflösung
        if screen_width <= 1366:  # Kleine Laptops (1366x768)
            dm_notes_width = int(screen_width * 0.25)  # 25% (1/4)
        elif screen_width <= 1600:  # Laptop mit Skalierung (1536x864 typisch)
            dm_notes_width = 438  # Manuell optimiert für 1536px
        elif screen_width <= 1920:  # Full HD Desktop (1920x1080)
            dm_notes_width = 250  # Normal für Desktop
        elif screen_width <= 2560:  # WQHD Desktop (2560x1440)
            dm_notes_width = 350
        else:  # 4K und größer (3840x2160+)
            dm_notes_width = 400

        # Setze Position mit längerem Delay (damit UI vollständig gerendert ist)
        def set_pos():
            self.root.update_idletasks()
            paned_window.sashpos(0, dm_notes_width)

        self.root.after(1000, set_pos)  # 1 Sekunde Delay!

    def _set_content_paned_position(self, content_paned, screen_width):
        """Setzt optimale Position für das innere PanedWindow (CharList vs Interaction)."""
        # Ziel: DM=1/4, CharList=2/4, Interaction=1/4 vom GESAMTBILDSCHIRM
        # Aber content_paned hat nur den Platz NACH DM-Notizen!
        # Also müssen wir CharList als Anteil des verfügbaren Platzes berechnen

        if screen_width <= 1366:  # Kleine Laptops (1366x768)
            # DM = 25% (341px), verfügbar = ~1025px
            # Wir wollen: CharList = 2/4 vom Gesamtbildschirm = 683px
            # Das sind 2/3 vom verfügbaren Platz (683/1025 ≈ 0.66)
            dm_width = int(screen_width * 0.25)
            available_width = screen_width - dm_width - 50  # Abzug Padding
            char_list_width = int(available_width * 0.66)  # 2/3 der verfügbaren Breite
        elif screen_width <= 1600:  # Laptop mit Skalierung (1536x864)
            char_list_width = 744  # Manuell optimiert für 1536px
        elif screen_width <= 1920:  # Full HD Desktop (1920x1080)
            char_list_width = 550
        elif screen_width <= 2560:  # WQHD Desktop (2560x1440)
            char_list_width = 700
        else:  # 4K und größer (3840x2160+)
            char_list_width = 900

        content_paned.sashpos(0, char_list_width)
