import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, TYPE_CHECKING

from src.utils.logger import setup_logging
from src.config import FONTS, WINDOW_SIZE, LIBRARY_TABS
from src.utils.library_data_manager import LibraryDataManager
from src.utils.navigation_manager import NavigationManager
from src.controllers.library_import_tab import LibraryImportTab
from src.controllers.library_markdown_tab import LibraryMarkdownTab
from src.utils.enemy_data_loader import EnemyDataLoader
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager

logger = setup_logging()

class LibraryHandler:
    """
    Manages the preset library, allowing users to browse, search, and add predefined enemies.
    """
    def __init__(self, root: tk.Tk, engine: 'CombatEngine', history_manager: 'HistoryManager', colors: Dict[str, str]):
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
        self.tabs = {}
        self.navigator = NavigationManager(self._restore_state, self._update_nav_buttons_ui)
        self.btn_back = None
        self.btn_forward = None

    def get_preset(self, name: str) -> Optional[Dict[str, Any]]:
        return EnemyDataLoader().get_preset(name)

    def open_library_window(self) -> None:
        if self.lib_window and self.lib_window.winfo_exists():
            self.lib_window.lift()
            self.lib_window.focus_force()
            return

        self.lib_window = tk.Toplevel(self.root)
        self.lib_window.title(translate("library.title"))
        self.lib_window.geometry(WINDOW_SIZE["library"])
        self.lib_window.configure(bg=self.colors["bg"])

        top_frame = ttk.Frame(self.lib_window, style="Card.TFrame")
        top_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        nav_frame = ttk.Frame(top_frame)
        nav_frame.pack(side=tk.LEFT, padx=5)

        self.btn_back = ttk.Button(nav_frame, text="<", width=3, command=self.navigator.back, state="disabled")
        self.btn_back.pack(side=tk.LEFT, padx=(0, 2))
        self.btn_forward = ttk.Button(nav_frame, text=">", width=3, command=self.navigator.forward, state="disabled")
        self.btn_forward.pack(side=tk.LEFT)

        ttk.Label(top_frame, text=translate("library.global_search"), font=FONTS["bold"]).pack(side=tk.LEFT, padx=5)
        self.global_search_var = tk.StringVar()
        self.global_search_var.trace("w", self._on_global_search)
        entry = ttk.Entry(top_frame, textvariable=self.global_search_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.notebook = ttk.Notebook(self.lib_window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._init_tabs()

    def _init_tabs(self):
        tab_enemies_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_enemies_frame, text=translate("library.enemies_tab"))
        self.import_tab = LibraryImportTab(tab_enemies_frame, self.engine, self.history_manager, self.colors, self.lib_window.destroy)

        self.markdown_tabs = {}
        for tab_config in LIBRARY_TABS:
            tab_id, title, dir_name = tab_config["id"], tab_config["title"], tab_config["dir"]
            if dir_name in self.dirs:
                self._create_markdown_tab(tab_id, title, self.dirs[dir_name])
            else:
                logger.warning(f"Directory for tab '{title}' ({dir_name}) not found.")

    def _create_markdown_tab(self, tab_id, title, root_dir):
        tab = LibraryMarkdownTab(self.notebook, tab_id, title, root_dir, self.colors, self.search_and_open, self.on_navigation_event)
        self.markdown_tabs[tab_id] = tab

    def _get_controller_by_widget_id(self, widget_id: str) -> Optional[Any]:
        if self.import_tab and str(self.import_tab.parent) == widget_id:
            return self.import_tab
        for tab in self.markdown_tabs.values():
            if str(tab.frame) == widget_id:
                return tab
        return None

    def search_and_open(self, name):
        self._ignore_search_trace = True
        self.global_search_var.set(name)
        self._ignore_search_trace = False

        for tab in self.markdown_tabs.values():
            tab.search_var.set("")

        result = self.data_manager.search_file(name)
        if result:
            category, filepath = result
            logger.info(f"File found: {filepath} in category {category}")
            if category in self.markdown_tabs:
                tab = self.markdown_tabs[category]
                for i, child in enumerate(self.notebook.tabs()):
                    if self.notebook.nametowidget(child) == tab.frame:
                        self.notebook.select(i)
                        break
                tab.display_content(filepath)
                tab.select_file(filepath)
                return

        logger.info(f"No direct hit for '{name}'. Starting global search.")
        self._ignore_search_trace = False
        self._on_global_search()

    def _on_global_search(self, *args):
        if self._ignore_search_trace: return
        query = self.global_search_var.get().lower()
        logger.info(f"Global search started: '{query}'")

        current_tab_id = self.notebook.select()
        current_has_results = False
        first_tab_with_results = None

        for tab_id in self.notebook.tabs():
            controller = self._get_controller_by_widget_id(tab_id)
            if controller:
                count = controller.search(query)
                if tab_id == current_tab_id and count > 0:
                    current_has_results = True
                if count > 0 and first_tab_with_results is None:
                    first_tab_with_results = tab_id
            else:
                logger.warning(f"No controller for Tab ID {tab_id} found!")

        if not current_has_results and first_tab_with_results:
            logger.info(f"Switching to tab: {first_tab_with_results}")
            try:
                self.notebook.select(first_tab_with_results)
            except Exception as e:
                logger.error(f"Error switching tabs: {e}")

    def on_navigation_event(self, tab_id, filepath=None):
        self.navigator.push({'tab_id': tab_id, 'filepath': filepath})

    def _on_tab_changed(self, event):
        if self.navigator.is_navigating: return
        selected_tab_id = self.notebook.select()
        controller = self._get_controller_by_widget_id(selected_tab_id)
        if controller:
            controller_id = getattr(controller, 'tab_id', 'import')
            filepath = getattr(controller, 'current_file', None)
            self.on_navigation_event(controller_id, filepath)

    def _restore_state(self, state):
        try:
            tab_id, filepath = state.get('tab_id'), state.get('filepath')
            target_controller = self.import_tab if tab_id == "import" else self.markdown_tabs.get(tab_id)
            if target_controller:
                frame = getattr(target_controller, 'frame', target_controller.parent)
                for i, child in enumerate(self.notebook.tabs()):
                    if self.notebook.nametowidget(child) == frame:
                        self.notebook.select(i)
                        break
                if filepath and hasattr(target_controller, 'display_content'):
                    target_controller.display_content(filepath)
        except Exception as e:
            logger.error(f"Navigation error: {e}")

    def _update_nav_buttons_ui(self, can_back, can_forward):
        if self.btn_back: self.btn_back.config(state="normal" if can_back else "disabled")
        if self.btn_forward: self.btn_forward.config(state="normal" if can_forward else "disabled")

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if self.lib_window and self.lib_window.winfo_exists():
            self.lib_window.configure(bg=colors["bg"])
        if self.import_tab: self.import_tab.update_colors(colors)
        for tab in self.markdown_tabs.values():
            if hasattr(tab.browser, 'update_colors'):
                tab.browser.update_colors(colors)
