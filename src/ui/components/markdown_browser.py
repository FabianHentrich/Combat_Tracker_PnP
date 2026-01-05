import tkinter as tk
from tkinter import ttk, filedialog
import os
import glob
from typing import Dict, Callable, Optional
from src.config import FONTS
from src.utils.logger import setup_logging
from src.utils.markdown_utils import MarkdownUtils
from src.utils.localization import translate

logger = setup_logging()

class MarkdownBrowser(ttk.Frame):
    """
    Wiederverwendbare Komponente zum Durchsuchen und Anzeigen von Markdown-Dateien.
    """
    def __init__(self, parent: tk.Widget, root_dir: str, colors: Dict[str, str], link_callback: Callable[[str], None], on_navigate: Optional[Callable[[str], None]] = None):
        super().__init__(parent)
        self.root_dir = root_dir
        self.colors = colors
        self.link_callback = link_callback
        self.on_navigate = on_navigate

        self.tree: Optional[ttk.Treeview] = None
        self.text_widget: Optional[tk.Text] = None
        self.search_var = tk.StringVar()
        self.current_file: Optional[str] = None

        self._setup_ui()
        self.load_tree()

    def _setup_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Linke Seite: Dateiliste / Suche ---
        left_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(left_frame, weight=1)
        self._create_sidebar(left_frame)

        # --- Rechte Seite: Inhalt ---
        right_frame = ttk.Frame(paned, style="Card.TFrame")
        paned.add(right_frame, weight=3)
        self._create_content_area(right_frame)

    def _create_sidebar(self, parent):
        # Suchfeld
        search_frame = ttk.Frame(parent, style="Card.TFrame")
        search_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        ttk.Label(search_frame, text="🔍").pack(side=tk.LEFT, padx=(5, 2))

        self.search_var.trace("w", self._on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Treeview für Dateien
        self.tree = ttk.Treeview(parent, selectmode="browse", show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Button zum Ordner wählen
        ttk.Button(parent, text=translate("library.select_folder"), command=self._select_folder).pack(fill=tk.X, padx=5, pady=5)

    def _create_content_area(self, parent):
        # Text Widget für Markdown-Anzeige
        self.text_widget = tk.Text(parent, wrap=tk.WORD, font=FONTS["text"], bg=self.colors["panel"], fg=self.colors["fg"], padx=10, pady=10)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tags konfigurieren
        MarkdownUtils.configure_text_tags(self.text_widget, self._on_link_click, self.colors)

    def load_tree(self):
        """Lädt die Markdown-Dateien in den Treeview."""
        self.tree.delete(*self.tree.get_children())

        if not os.path.exists(self.root_dir):
            return

        files = glob.glob(os.path.join(self.root_dir, "**/*.md"), recursive=True)
        files.sort()

        folder_nodes = {}

        for filepath in files:
            rel_path = os.path.relpath(filepath, self.root_dir)
            parts = rel_path.split(os.sep)
            filename = parts[-1]
            display_name = os.path.splitext(filename)[0]
            current_parent = ""

            for i in range(len(parts) - 1):
                folder_name = parts[i]
                folder_path = os.path.join(current_parent, folder_name) if current_parent else folder_name
                abs_folder_path = os.path.join(self.root_dir, folder_path)

                if folder_path not in folder_nodes:
                    parent_node = folder_nodes.get(current_parent, "")
                    node_id = self.tree.insert(parent_node, "end", text=folder_name, open=False, tags=("folder",), values=(abs_folder_path,))
                    folder_nodes[folder_path] = node_id

                current_parent = folder_path

            parent_node = folder_nodes.get(current_parent, "")
            self.tree.insert(parent_node, "end", text=display_name, values=(filepath,), tags=("file",))

        start_file = os.path.join(self.root_dir, "Start.md")
        if os.path.exists(start_file):
            self.display_content(start_file)

    def _select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.root_dir, title=translate("dialog.file.select_folder_title"))
        if folder:
            self.root_dir = folder
            self.load_tree()

    def _on_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item.get("values")

        if not values:
            return

        path = values[0]

        if os.path.isfile(path):
            self.display_content(path)
        elif os.path.isdir(path):
            start_file = os.path.join(path, "Start.md")
            if os.path.exists(start_file):
                self.display_content(start_file)
            else:
                MarkdownUtils.display_folder_toc(path, self.text_widget, self.colors)

    def search(self, query: str) -> int:
        """Führt eine Suche durch und gibt die Anzahl der Treffer zurück."""
        self.search_var.set(query)
        return len(self.tree.get_children())

    def _on_search_change(self, *args):
        query = self.search_var.get().lower()
        self.tree.delete(*self.tree.get_children())

        if not os.path.exists(self.root_dir):
            return

        files = glob.glob(os.path.join(self.root_dir, "**/*.md"), recursive=True)

        for filepath in files:
            filename = os.path.basename(filepath)
            display_name = os.path.splitext(filename)[0]
            match = False
            if query in display_name.lower():
                match = True
            else:
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if query in content:
                            match = True
                except:
                    pass

            if match:
                self.tree.insert("", "end", text=display_name, values=(filepath,))

    def display_content(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete("1.0", tk.END)
            MarkdownUtils.parse_markdown(content, self.text_widget, base_path=os.path.dirname(filepath))
            self.text_widget.config(state=tk.DISABLED)

            self.current_file = filepath
            if self.on_navigate:
                self.on_navigate(filepath)

        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")

    def _on_link_click(self, event, text_widget):
        index = text_widget.index(f"@{event.x},{event.y}")
        tags = text_widget.tag_names(index)

        if "link" in tags:
            start = text_widget.tag_prevrange("link", index + "+1c")
            if start:
                link_text = text_widget.get(start[0], start[1])
                self.link_callback(link_text)

    def select_file(self, filepath: str):
        """Wählt eine Datei im Treeview aus und zeigt sie an."""
        item_id = self._find_item_by_value("", filepath)
        if item_id:
            self.select_item(item_id)

    def _find_item_by_value(self, parent, value):
        for item in self.tree.get_children(parent):
            item_values = self.tree.item(item, "values")
            if item_values and item_values[0] == value:
                return item
            found = self._find_item_by_value(item, value)
            if found:
                return found
        return None

    def select_item(self, item_id):
        """Wählt ein Item im Treeview aus und zeigt es an."""
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        parent = self.tree.parent(item_id)
        while parent:
            self.tree.item(parent, open=True)
            parent = self.tree.parent(parent)

        self._on_select(None)

    def update_colors(self, colors: Dict[str, str]):
        """Aktualisiert die Farben der Komponente."""
        self.colors = colors
        if self.text_widget and self.text_widget.winfo_exists():
            self.text_widget.configure(bg=self.colors["panel"], fg=self.colors["fg"])
            MarkdownUtils.configure_text_tags(self.text_widget, self._on_link_click, self.colors)
