import tkinter as tk
from tkinter import ttk
import os
import glob
from typing import Dict, Optional
from src.ui.components.pdf_viewer import PDFViewer
from src.utils.logger import setup_logging

logger = setup_logging()

class LibraryPDFTab:
    """
    Controller for a PDF Tab in the Library.
    Replaces Markdown content with a PDF Viewer.
    """
    def __init__(self, notebook: ttk.Notebook, tab_id: str, title: str, root_dir: str, colors: Dict[str, str]):
        self.notebook = notebook
        self.tab_id = tab_id
        self.title = title
        self.root_dir = root_dir
        self.colors = colors

        self.frame = ttk.Frame(notebook)
        self.notebook.add(self.frame, text=title)

        # Find PDF file
        self.pdf_path = self._find_pdf_in_dir(root_dir)

        if self.pdf_path:
            # Toolbar for external actions
            top_bar = ttk.Frame(self.frame)
            top_bar.pack(fill=tk.X, padx=5, pady=2)

            ttk.Label(top_bar, text=f"Datei: {os.path.basename(self.pdf_path)}").pack(side=tk.LEFT)
            ttk.Button(top_bar, text="↗ Extern öffnen", command=self._open_external).pack(side=tk.RIGHT)

            self.viewer = PDFViewer(self.frame, colors, self.pdf_path)
            self.viewer.pack(fill=tk.BOTH, expand=True)
        else:
            self._show_placeholder()

    def _open_external(self):
        if self.pdf_path and os.path.exists(self.pdf_path):
            try:
                os.startfile(self.pdf_path)
            except Exception as e:
                logger.error(f"Failed to open PDF externaly: {e}")

    def _find_pdf_in_dir(self, directory: str) -> Optional[str]:
        """Finds the first PDF file in the directory or its subdirectories."""
        if not os.path.exists(directory):
            return None

        # Prioritize "Regelwerk.pdf" or "Rules.pdf"
        priority_files = ["Regelwerk.pdf", "Rules.pdf", "rules.pdf", "regelwerk.pdf"]
        for f in priority_files:
            path = os.path.join(directory, f)
            if os.path.isfile(path):
                return path

        # Fallback: any pdf
        pdfs = glob.glob(os.path.join(directory, "*.pdf"))
        if pdfs:
            return pdfs[0]

        return None

    def _show_placeholder(self):
        """Shows a placeholder message if no PDF is found."""
        container = ttk.Frame(self.frame)
        container.pack(fill=tk.BOTH, expand=True)

        msg = (
            f"Keine PDF-Datei gefunden in:\n{self.root_dir}\n\n"
            "Bitte platziere eine PDF-Datei (z.B. 'Regelwerk.pdf') in diesem Ordner,\n"
            "um das Regelwerk anzuzeigen."
        )
        ttk.Label(container, text=msg, font=("Segoe UI", 12), justify=tk.CENTER).pack(expand=True)

        # Open folder button
        btn = ttk.Button(container, text="Ordner öffnen", command=lambda: os.startfile(self.root_dir) if os.name == 'nt' else None)
        btn.pack(pady=10)

    def jump_to_page(self, page_num: int):
        if hasattr(self, 'viewer') and self.viewer:
            self.viewer.jump_to_page(page_num)

    def search(self, query: str) -> int:
        """
        Executes search on the PDF viewer.
        Returns the number of matches.
        """
        if hasattr(self, 'viewer') and self.viewer:
            self.viewer.search_var.set(query)
            return self.viewer.search(query)
        return 0

    def display_content(self, filepath: str):
        """
        Displays the content of the file.
        If it's a PDF, loads it.
        If it matches the current PDF, does nothing.
        """
        if not filepath:
            return

        if filepath.lower().endswith(".pdf"):
            if self.pdf_path != filepath:
                self.pdf_path = filepath
                if hasattr(self, 'viewer') and self.viewer:
                    self.viewer.load_file(filepath)
        else:
            logger.warning(f"LibraryPDFTab cannot display non-PDF file: {filepath}")

    def select_file(self, filepath: str):
        """
        Highlight or select the file in the interface.
        For PDF Tab, this might update the label or do nothing if no tree view exists.
        """
        # No file tree in PDF tab to select from
        pass

    @property
    def current_file(self) -> Optional[str]:
        return self.pdf_path

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        # Helper to update viewer colors if supported in future
        if hasattr(self, 'viewer') and hasattr(self.viewer, 'update_colors'):
             self.viewer.update_colors(colors)
