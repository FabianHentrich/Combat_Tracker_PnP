import tkinter as tk
from tkinter import ttk
import os
import re
import glob
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.utils.logger import setup_logging
from src.config import FONTS, WINDOW_SIZE
from src.utils.library_data_manager import LibraryDataManager
from src.utils.navigation_manager import NavigationManager

from src.controllers.library_import_tab import LibraryImportTab
from src.controllers.library_markdown_tab import LibraryMarkdownTab
from src.utils.enemy_data_loader import EnemyDataLoader

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager

logger = setup_logging()

class LibraryHandler:
    """
    Verwaltet die Gegner-Bibliothek (Presets).
    Erlaubt das Durchsuchen, Auswählen und Hinzufügen von vordefinierten Gegnern.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', root: tk.Tk, colors: Dict[str, str]):
        self.engine = engine
        self.history_manager = history_manager
        self.root = root
        self.colors = colors
        self.lib_window = None
        self.notebook = None
        self._ignore_search_trace = False
        self.import_tab = None
        self.markdown_tabs = {}

        self.data_manager = LibraryDataManager()
        self.dirs = self.data_manager.dirs

        # Tab storage
        self.tabs = {}

        # Navigation Manager
        self.navigator = NavigationManager(self._restore_state, self._update_nav_buttons_ui)
        self.btn_back = None
        self.btn_forward = None

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Gibt die Daten eines Presets zurück."""
        return EnemyDataLoader().get_preset(name)

    def open_library_window(self) -> None:
        """Öffnet das Bibliotheks-Fenster mit Tabs für Gegner und Regelwerk."""
        if self.lib_window and self.lib_window.winfo_exists():
            self.lib_window.lift()
            self.lib_window.focus_force()
            return

        lib_window = tk.Toplevel(self.root)
        self.lib_window = lib_window
        lib_window.title("Bibliothek & Regelwerk")
        lib_window.geometry(WINDOW_SIZE["library"])
        lib_window.configure(bg=self.colors["bg"])

        # --- Navigation & Suche ---
        top_frame = ttk.Frame(lib_window, style="Card.TFrame")
        top_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        # Navigation Buttons
        nav_frame = ttk.Frame(top_frame)
        nav_frame.pack(side=tk.LEFT, padx=5)

        self.btn_back = ttk.Button(nav_frame, text="<", width=3, command=self.navigator.back, state="disabled")
        self.btn_back.pack(side=tk.LEFT, padx=(0, 2))

        self.btn_forward = ttk.Button(nav_frame, text=">", width=3, command=self.navigator.forward, state="disabled")
        self.btn_forward.pack(side=tk.LEFT)

        # Globale Suche
        ttk.Label(top_frame, text="🔍 Globale Suche:", font=FONTS["bold"]).pack(side=tk.LEFT, padx=5)
        self.global_search_var = tk.StringVar()
        self.global_search_var.trace("w", self._on_global_search)
        entry = ttk.Entry(top_frame, textvariable=self.global_search_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(lib_window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._init_tabs()

    def _init_tabs(self):
        """Initialisiert alle Tabs im Notebook."""
        # Tab 1: Gegner (Import)
        tab_enemies_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_enemies_frame, text="Gegner (Import)")

        # Initialize Import Tab Controller
        self.import_tab = LibraryImportTab(tab_enemies_frame, self.engine, self.history_manager, self.colors, self.lib_window.destroy)

        # Generic Markdown Tabs
        self.markdown_tabs = {}
        self._create_markdown_tab("rules", "Regelwerk", self.dirs["rules"])
        self._create_markdown_tab("items", "Gegenstände", self.dirs["items"])
        self._create_markdown_tab("enemies", "Gegner (Info)", self.dirs["enemies"])
        self._create_markdown_tab("npcs", "NPCs", self.dirs["npcs"])
        self._create_markdown_tab("locations", "Orte", self.dirs["locations"])
        self._create_markdown_tab("organizations", "Organisationen", self.dirs["organizations"])
        self._create_markdown_tab("gods", "Götter", self.dirs["gods"])
        self._create_markdown_tab("demons", "Dämonen", self.dirs["demons"])

    def _create_markdown_tab(self, tab_id, title, root_dir):
        """Erstellt einen generischen Tab für Markdown-Dateien."""
        tab = LibraryMarkdownTab(self.notebook, tab_id, title, root_dir, self.colors, self.search_and_open, self.on_navigation_event)
        self.markdown_tabs[tab_id] = tab

    def _get_controller_by_widget_id(self, widget_id: str) -> Optional[Any]:
        """Ermittelt den Controller basierend auf der Widget-ID des Tabs."""
        if self.import_tab and str(self.import_tab.parent) == widget_id:
            return self.import_tab

        for tab in self.markdown_tabs.values():
            if str(tab.frame) == widget_id:
                return tab
        return None

    def search_and_open(self, name):
        """Sucht nach einer Regeldatei mit dem Namen und öffnet sie."""

        # Setze den Suchbegriff in die globale Suche (für Anzeige)
        # Wir setzen ein Flag, damit _on_global_search nicht feuert und die Tabs filtert
        self._ignore_search_trace = True
        self.global_search_var.set(name)
        self._ignore_search_trace = False

        # Reset filters in all tabs to ensure we can find the item
        for tab in self.markdown_tabs.values():
            tab.search_var.set("")

        # Suche über DataManager
        result = self.data_manager.search_file(name)

        if result:
            category, filepath = result
            logger.info(f"Datei gefunden: {filepath} in Kategorie {category}")

            # Tab finden
            if category in self.markdown_tabs:
                tab = self.markdown_tabs[category]

                # Switch to tab
                for i, child in enumerate(self.notebook.tabs()):
                    if self.notebook.nametowidget(child) == tab.frame:
                        self.notebook.select(i)
                        break

                # Datei anzeigen und im Baum selektieren
                tab.display_content(filepath)
                tab.select_file(filepath)
                return

        # Fallback: Wenn nichts gefunden wurde, führe die globale Suche aus,
        # damit der Nutzer wenigstens gefilterte Listen sieht.
        logger.info(f"Kein direkter Treffer für '{name}'. Starte globale Suche.")
        self._ignore_search_trace = False # Trace wieder aktivieren
        self._on_global_search() # Manuell auslösen



    def _on_global_search(self, *args):
        """Handler für die globale Suche."""
        if self._ignore_search_trace:
            return

        query = self.global_search_var.get().lower()
        logger.info(f"Globale Suche gestartet: '{query}'")

        current_tab_id = self.notebook.select()
        current_has_results = False
        first_tab_with_results = None

        # Iterate over tabs in visual order
        all_tabs = self.notebook.tabs()

        for tab_id in all_tabs:
            controller = self._get_controller_by_widget_id(tab_id)

            if controller:
                # Perform search on this tab
                count = controller.search(query)

                if tab_id == current_tab_id:
                    if count > 0:
                        current_has_results = True

                if count > 0 and first_tab_with_results is None:
                    first_tab_with_results = tab_id
            else:
                logger.warning(f"Kein Controller für Tab ID {tab_id} gefunden!")

        # If current tab has no results, but another tab does, switch to it
        if not current_has_results and first_tab_with_results:
            logger.info(f"Wechsle zu Tab: {first_tab_with_results}")
            try:
                self.notebook.select(first_tab_with_results)
            except Exception as e:
                logger.error(f"Fehler beim Wechseln des Tabs: {e}")

    def on_navigation_event(self, tab_id, filepath=None):
        """Wird aufgerufen, wenn der Nutzer navigiert (Tab wechselt oder Datei öffnet)."""
        self.navigator.push({'tab_id': tab_id, 'filepath': filepath})

    def _on_tab_changed(self, event):
        """Handler für Tab-Wechsel."""
        if self.navigator.is_navigating:
            return

        selected_tab_id = self.notebook.select()
        controller = self._get_controller_by_widget_id(selected_tab_id)

        if controller:
            controller_id = getattr(controller, 'tab_id', 'import')
            filepath = getattr(controller, 'current_file', None)
            self.on_navigation_event(controller_id, filepath)

    def go_back(self):
        self.navigator.back()

    def go_forward(self):
        self.navigator.forward()

    def _restore_state(self, state):
        try:
            tab_id = state.get('tab_id')
            filepath = state.get('filepath')

            # Switch tab
            target_controller = None
            if tab_id == "import":
                target_controller = self.import_tab
            elif tab_id in self.markdown_tabs:
                target_controller = self.markdown_tabs[tab_id]

            if target_controller:
                # Select tab
                frame = target_controller.frame if hasattr(target_controller, 'frame') else target_controller.parent

                # Find index
                for i, child in enumerate(self.notebook.tabs()):
                    if self.notebook.nametowidget(child) == frame:
                        self.notebook.select(i)
                        break

                # Restore file if applicable
                if filepath and hasattr(target_controller, 'display_content'):
                    target_controller.display_content(filepath)

        except Exception as e:
            logger.error(f"Fehler bei der Navigation: {e}")

    def _update_nav_buttons_ui(self, can_back, can_forward):
        if self.btn_back:
            self.btn_back.config(state="normal" if can_back else "disabled")
        if self.btn_forward:
            self.btn_forward.config(state="normal" if can_forward else "disabled")
