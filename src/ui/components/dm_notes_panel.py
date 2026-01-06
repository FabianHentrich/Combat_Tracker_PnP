import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable, Optional, List
from src.ui.components.markdown_browser import MarkdownBrowser
from src.config import COLORS
import tkinter.simpledialog
from src.utils.localization import translate

class DMNotesPanel(ttk.Frame):
    """
    Panel für DM-Notizen und Pläne mit Dateibaum, zuletzt geöffneten Notizen, Modus-Schalter,
    Löschen/Umbenennen, Drag & Drop, Undo/Redo, Autosave und Volltextsuche.
    """
    def __init__(self, parent: tk.Widget, root_dir: str, colors: Dict[str, str], link_callback: Callable[[str], None]):
        super().__init__(parent)
        self.root_dir = root_dir
        self.colors = colors
        self.link_callback = link_callback

        # Platzhalter für weitere Features
        self.recent_files: List[str] = []
        self.edit_mode = False
        self.max_recent = 5  # TODO: Wert dynamisch aus Config laden
        self.recent_buttons: List[ttk.Button] = []

        self._setup_ui()

    def _setup_ui(self):
        # Oben: Liste der zuletzt geöffneten Notizen und Modus-Schalter
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        self.recent_label = ttk.Label(top_frame, text=translate("dm_notes.recent"))
        self.recent_label.pack(side=tk.LEFT)
        self.recent_buttons_frame = ttk.Frame(top_frame)
        self.recent_buttons_frame.pack(side=tk.LEFT, padx=(5, 0))
        self._update_recent_buttons()

        self.mode_var = tk.BooleanVar(value=self.edit_mode)
        self.mode_switch = ttk.Checkbutton(top_frame, text=translate("dm_notes.edit_mode"), variable=self.mode_var, command=self._toggle_mode)
        self.mode_switch.pack(side=tk.RIGHT)

        # Mitte: MarkdownBrowser (Dateibaum, Suche, Anzeige)
        self.markdown_browser = MarkdownBrowser(self, self.root_dir, self.colors, self.link_callback, on_navigate=self._on_note_navigate)
        self.markdown_browser.pack(fill=tk.BOTH, expand=True)

        # Unten: Platz für Buttons (Löschen, Umbenennen, Drag & Drop, Speichern, Undo/Redo)
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        self.delete_btn = ttk.Button(bottom_frame, text=translate("dm_notes.delete"), command=self._delete_note)
        self.delete_btn.pack(side=tk.LEFT, padx=2)
        self.rename_btn = ttk.Button(bottom_frame, text=translate("dm_notes.rename"), command=self._rename_note)
        self.rename_btn.pack(side=tk.LEFT, padx=2)
        self.save_btn = ttk.Button(bottom_frame, text=translate("dm_notes.save"), command=self._save_note)
        self.save_btn.pack(side=tk.LEFT, padx=2)
        self.undo_btn = ttk.Button(bottom_frame, text=translate("dm_notes.undo"), command=self._undo)
        self.undo_btn.pack(side=tk.LEFT, padx=2)
        self.redo_btn = ttk.Button(bottom_frame, text=translate("dm_notes.redo"), command=self._redo)
        self.redo_btn.pack(side=tk.LEFT, padx=2)
        # TODO: Drag & Drop-Integration

    def _toggle_mode(self):
        self.edit_mode = self.mode_var.get()
        self.markdown_browser.set_edit_mode(self.edit_mode)

    def _delete_note(self):
        file_path = self.markdown_browser.current_file
        if not file_path:
            messagebox.showwarning(translate("dm_notes.no_selection_title"), translate("dm_notes.no_selection"))
            return
        if messagebox.askyesno(translate("dm_notes.delete_confirm_title"), translate("dm_notes.delete_confirm").format(file=file_path)):
            try:
                import os
                os.remove(file_path)
                self.markdown_browser.load_tree()
                self.recent_files = [f for f in self.recent_files if f != file_path]
                self._update_recent_buttons()
                messagebox.showinfo(translate("dm_notes.deleted_title"), translate("dm_notes.deleted"))
            except Exception as e:
                messagebox.showerror(translate("dm_notes.error_title"), f"{translate('dm_notes.delete_error')}: {e}")

    def _rename_note(self):
        file_path = self.markdown_browser.current_file
        if not file_path:
            messagebox.showwarning(translate("dm_notes.no_selection_title"), translate("dm_notes.no_selection"))
            return
        import os
        dirname, old_name = os.path.split(file_path)
        new_name = tkinter.simpledialog.askstring(translate("dm_notes.rename_title"), translate("dm_notes.rename_prompt"), initialvalue=os.path.splitext(old_name)[0])
        if new_name:
            if not new_name.endswith(".md"):
                new_name += ".md"
            new_path = os.path.join(dirname, new_name)
            if os.path.exists(new_path):
                messagebox.showerror(translate("dm_notes.error_title"), translate("dm_notes.rename_exists"))
                return
            try:
                os.rename(file_path, new_path)
                self.markdown_browser.load_tree()
                self.markdown_browser.open_file(new_path)
                self.recent_files = [new_path if f == file_path else f for f in self.recent_files]
                self._update_recent_buttons()
                messagebox.showinfo(translate("dm_notes.renamed_title"), translate("dm_notes.renamed"))
            except Exception as e:
                messagebox.showerror(translate("dm_notes.error_title"), f"{translate('dm_notes.rename_error')}: {e}")

    def _save_note(self):
        if self.edit_mode:
            success = self.markdown_browser.save_current_file()
            if success:
                messagebox.showinfo(translate("dm_notes.saved_title"), translate("dm_notes.saved"))
            else:
                messagebox.showerror(translate("dm_notes.error_title"), translate("dm_notes.save_error"))

    def _undo(self):
        if self.edit_mode and self.markdown_browser.text_widget:
            try:
                self.markdown_browser.text_widget.edit_undo()
            except tk.TclError:
                pass

    def _redo(self):
        if self.edit_mode and self.markdown_browser.text_widget:
            try:
                self.markdown_browser.text_widget.edit_redo()
            except tk.TclError:
                pass

    def _update_recent_buttons(self):
        # Entferne alte Buttons
        for btn in self.recent_buttons:
            btn.destroy()
        self.recent_buttons.clear()
        # Erstelle neue Buttons für die zuletzt geöffneten Notizen
        for file_path in self.recent_files[:self.max_recent]:
            file_name = file_path.split("/")[-1]
            btn = ttk.Button(self.recent_buttons_frame, text=file_name, width=18, command=lambda p=file_path: self.open_recent(p))
            btn.pack(side=tk.LEFT, padx=2)
            self.recent_buttons.append(btn)

    def open_recent(self, file_path: str):
        # Öffne die Notiz im MarkdownBrowser und verschiebe sie nach vorne in der Liste
        self.markdown_browser.open_file(file_path)
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        self._update_recent_buttons()

    def add_to_recent(self, file_path: str):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        self.recent_files.insert(0, file_path)
        if len(self.recent_files) > self.max_recent:
            self.recent_files = self.recent_files[:self.max_recent]
        self._update_recent_buttons()

    def _on_note_navigate(self, filepath: str):
        self.add_to_recent(filepath)


    # TODO: Methoden für Undo/Redo, Autosave, Scroll-Position, Volltextsuche, Drag & Drop, Highlighting
