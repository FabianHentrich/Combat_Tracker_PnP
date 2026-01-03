import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional
from src.utils.logger import setup_logging
from src.ui.components.markdown_browser import MarkdownBrowser

logger = setup_logging()

class LibraryMarkdownTab:
    """
    Controller für einen Markdown-Tab in der Bibliothek.
    Delegiert die UI an MarkdownBrowser.
    """
    def __init__(self, notebook: ttk.Notebook, tab_id: str, title: str, root_dir: str, colors: Dict[str, str], link_callback: Callable[[str], None], on_navigate: Optional[Callable[[str, str], None]] = None):
        self.notebook = notebook
        self.tab_id = tab_id
        self.title = title
        self.root_dir = root_dir
        self.colors = colors
        self.link_callback = link_callback
        self.on_navigate = on_navigate

        self.frame = ttk.Frame(notebook)
        self.notebook.add(self.frame, text=title)

        self.browser = MarkdownBrowser(
            self.frame,
            root_dir,
            colors,
            link_callback,
            self._on_browser_navigate
        )
        self.browser.pack(fill=tk.BOTH, expand=True)

        # Expose search_var for global search
        self.search_var = self.browser.search_var

    def _on_browser_navigate(self, filepath: str):
        """Callback vom Browser, wenn navigiert wird."""
        if self.on_navigate:
            self.on_navigate(self.tab_id, filepath)

    @property
    def current_file(self) -> Optional[str]:
        return self.browser.current_file

    def search(self, query: str) -> int:
        """Delegiert die Suche an den Browser."""
        return self.browser.search(query)

    def display_content(self, filepath: str):
        """Delegiert die Anzeige an den Browser."""
        self.browser.display_content(filepath)

    def select_file(self, filepath: str):
        """Delegiert die Selektion an den Browser."""
        self.browser.select_file(filepath)

    def update_colors(self, colors: Dict[str, str]):
        """Aktualisiert die Farben des Tabs."""
        self.colors = colors
        if self.browser:
            self.browser.update_colors(colors)
