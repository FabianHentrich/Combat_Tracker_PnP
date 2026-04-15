import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Callable, Optional, List
import tkinter.simpledialog

from src.ui.components.markdown_browser import MarkdownBrowser
from src.config import COLORS
from src.utils.localization import translate

# ---------------------------------------------------------------------------
# Note templates (#7)
# ---------------------------------------------------------------------------
_TEMPLATES: Dict[str, str] = {
    "npc":      "# {name}\n\n## Beschreibung\n\n## Persönlichkeit\n\n## Motivation\n\n## Verbindungen\n",
    "location": "# {name}\n\n## Beschreibung\n\n## Atmosphäre\n\n## Wichtige Details\n\n## Verbundene Orte\n",
    "quest":    "# {name}\n\n## Aufgabe\n\n## Hintergrund\n\n## Ziele\n\n## Belohnung\n",
    "faction":  "# {name}\n\n## Ziel\n\n## Mitglieder\n\n## Geschichte\n",
    "empty":    "",
}


class _TemplateDialog(tk.Toplevel):
    """Simple modal dialog to pick a note template."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self.title(translate("dm_notes.template_label"))
        self.resizable(False, False)
        self.result: Optional[str] = None

        options = [
            ("empty",    translate("dm_notes.template_none")),
            ("npc",      "NPC"),
            ("location", translate("dm_notes.template_location")),
            ("quest",    "Quest"),
            ("faction",  translate("dm_notes.template_faction")),
        ]
        self._var = tk.StringVar(value="empty")

        ttk.Label(self, text=translate("dm_notes.template_label"), padding=(10, 10, 10, 5)).pack()
        for key, label in options:
            ttk.Radiobutton(self, text=label, variable=self._var, value=key).pack(anchor=tk.W, padx=20)

        ttk.Button(self, text=translate("common.ok"), command=self._ok).pack(pady=10)

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._ok)
        parent.wait_window(self)

    def _ok(self):
        self.result = self._var.get()
        self.destroy()


class DMNotesPanel(ttk.Frame):
    """
    Panel für DM-Notizen.

    Features:
      #1  DM-Notizen werden durch LibraryIndex indiziert → globale Suche findet Inhalte
      #2  "Neue Notiz"-Button mit Namens- und Ordnereingabe
      #3  Autosave nach 3 s Inaktivität im Bearbeitungsmodus
      #4  Kursiv-Rendering (in MarkdownUtils)
      #5  Backlinks-Panel: zeigt Dateien, die auf die aktuelle Notiz verweisen
      #6  Tag-Filter: filtert den Dateibaum nach YAML-Frontmatter-Tags
      #7  Vorlagen-Auswahl beim Erstellen neuer Notizen
    """

    def __init__(
        self,
        parent: tk.Widget,
        root_dir: str,
        colors: Dict[str, str],
        link_callback: Callable[[str], None],
        collapse_callback: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self._dm_notes_dir = root_dir
        self.root_dir = self._resolve_default_dir(root_dir)
        self.colors = colors
        self.link_callback = link_callback
        self.collapse_callback = collapse_callback

        self.recent_files: List[str] = []
        self.edit_mode = False
        self.max_recent = 5
        self.recent_buttons: List[ttk.Button] = []
        self._autosave_job: Optional[str] = None
        self._collapsed = False
        self._collapse_btn: Optional[ttk.Button] = None

        self._setup_ui()

    # ------------------------------------------------------------------
    # Startup: resolve which dir to show first
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_default_dir(dm_notes_dir: str) -> str:
        """Returns PnP-Welt if dm_notes is absent/empty, otherwise dm_notes."""
        from src.config import DATA_DIR
        pnp_dir = os.path.join(DATA_DIR, "PnP-Welt")
        dm_empty = not os.path.isdir(dm_notes_dir) or not os.listdir(dm_notes_dir)
        if dm_empty and os.path.isdir(pnp_dir):
            return pnp_dir
        return dm_notes_dir

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        # --- Top: collapse button + recent files + edit toggle ---
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        if self.collapse_callback:
            self._collapse_btn = ttk.Button(
                top_frame, text="◀", width=2, command=self._on_collapse_click
            )
            self._collapse_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.recent_label = ttk.Label(top_frame, text=translate("dm_notes.recent"))
        self.recent_label.pack(side=tk.LEFT)
        self.recent_buttons_frame = ttk.Frame(top_frame)
        self.recent_buttons_frame.pack(side=tk.LEFT, padx=(5, 0))
        self._update_recent_buttons()

        self.mode_var = tk.BooleanVar(value=self.edit_mode)
        ttk.Checkbutton(
            top_frame,
            text=translate("dm_notes.edit_mode"),
            variable=self.mode_var,
            command=self._toggle_mode,
        ).pack(side=tk.RIGHT)

        # --- Folder switcher (DM Notizen ↔ PnP-Welt) ---
        self._folder_frame = ttk.Frame(self)
        self._folder_frame.pack(fill=tk.X, padx=5, pady=(0, 2))
        ttk.Label(self._folder_frame, text=translate("dm_notes.folder_label")).pack(side=tk.LEFT)
        self._folder_var = tk.StringVar(value=translate("dm_notes.folder_dm_notes"))
        self._folder_combo = ttk.Combobox(
            self._folder_frame,
            textvariable=self._folder_var,
            state="readonly",
            width=20,
        )
        self._folder_combo.pack(side=tk.LEFT, padx=(4, 0))
        self._folder_combo.bind("<<ComboboxSelected>>", self._on_folder_change)
        self._refresh_folder_list()

        # --- Tag filter (#6) ---
        tag_frame = ttk.Frame(self)
        tag_frame.pack(fill=tk.X, padx=5, pady=(0, 2))
        ttk.Label(tag_frame, text=translate("dm_notes.tag_filter_label")).pack(side=tk.LEFT)
        self._tag_var = tk.StringVar(value=translate("dm_notes.tag_filter_all"))
        self._tag_combo = ttk.Combobox(
            tag_frame,
            textvariable=self._tag_var,
            state="readonly",
            width=20,
        )
        self._tag_combo.pack(side=tk.LEFT, padx=(4, 0))
        self._tag_combo.bind("<<ComboboxSelected>>", self._on_tag_filter)
        self._refresh_tags()

        # --- Main browser ---
        self.markdown_browser = MarkdownBrowser(
            self,
            self.root_dir,
            self.colors,
            self.link_callback,
            on_navigate=self._on_note_navigate,
        )
        self.markdown_browser.pack(fill=tk.BOTH, expand=True)
        # Apply Geschichte filter if starting in PnP-Welt
        initial_filter = self._geschichte_filter(self.root_dir)
        if initial_filter is not None:
            self.markdown_browser.load_tree(filter_paths=initial_filter)

        # --- Backlinks panel (#5) ---
        backlinks_outer = ttk.LabelFrame(self, text=translate("dm_notes.backlinks_label"))
        backlinks_outer.pack(fill=tk.X, padx=5, pady=(2, 0))
        self._backlinks_frame = ttk.Frame(backlinks_outer)
        self._backlinks_frame.pack(fill=tk.X, padx=4, pady=2)
        self._backlinks_placeholder = ttk.Label(
            self._backlinks_frame, text=translate("dm_notes.no_backlinks"), foreground="gray"
        )
        self._backlinks_placeholder.pack(side=tk.LEFT)

        # --- Bottom buttons ---
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(bottom_frame, text=translate("dm_notes.new_note"), command=self._new_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text=translate("dm_notes.delete"), command=self._delete_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text=translate("dm_notes.rename"), command=self._rename_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text=translate("dm_notes.save"), command=self._save_note).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text=translate("dm_notes.undo"), command=self._undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom_frame, text=translate("dm_notes.redo"), command=self._redo).pack(side=tk.LEFT, padx=2)

    # ------------------------------------------------------------------
    # Edit mode + Autosave (#3)
    # ------------------------------------------------------------------

    def _toggle_mode(self):
        self.edit_mode = self.mode_var.get()
        self.markdown_browser.set_edit_mode(self.edit_mode)
        if self.edit_mode:
            tw = self.markdown_browser.text_widget
            if tw:
                tw.bind("<<Modified>>", self._on_text_modified)
        else:
            tw = self.markdown_browser.text_widget
            if tw:
                tw.unbind("<<Modified>>")
            self._cancel_autosave()

    def _on_text_modified(self, event=None):
        tw = self.markdown_browser.text_widget
        if tw and tw.edit_modified():
            tw.edit_modified(False)
            self._schedule_autosave()

    def _schedule_autosave(self):
        self._cancel_autosave()
        self._autosave_job = self.after(3000, self._do_autosave)

    def _cancel_autosave(self):
        if self._autosave_job:
            self.after_cancel(self._autosave_job)
            self._autosave_job = None

    def _do_autosave(self):
        self._autosave_job = None
        if self.edit_mode:
            self.markdown_browser.save_current_file()
            self._sync_index()

    # ------------------------------------------------------------------
    # New note (#2 + #7)
    # ------------------------------------------------------------------

    def _new_note(self):
        name = tkinter.simpledialog.askstring(
            translate("dm_notes.new_note"),
            translate("dm_notes.new_note_name_prompt"),
            parent=self,
        )
        if not name:
            return
        name = name.strip()
        if not name:
            return

        folder = tkinter.simpledialog.askstring(
            translate("dm_notes.new_note"),
            translate("dm_notes.new_note_folder_prompt"),
            parent=self,
        )
        folder = (folder or "").strip()

        target_dir = os.path.join(self.root_dir, folder) if folder else self.root_dir
        os.makedirs(target_dir, exist_ok=True)

        filepath = os.path.join(target_dir, f"{name}.md")
        if os.path.exists(filepath):
            messagebox.showerror(
                translate("dm_notes.error_title"),
                translate("dm_notes.new_note_exists"),
                parent=self,
            )
            return

        # Template selection (#7)
        dlg = _TemplateDialog(self)
        template_key = dlg.result or "empty"
        content = _TEMPLATES.get(template_key, "").format(name=name)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror(
                translate("dm_notes.error_title"),
                f"{translate('dm_notes.new_note_error')}: {e}",
                parent=self,
            )
            return

        self.markdown_browser.load_tree()
        self.markdown_browser.open_file(filepath)
        self.add_to_recent(filepath)
        self._sync_index()

        # Enter edit mode for the freshly created note
        self.mode_var.set(True)
        self.edit_mode = True
        self.markdown_browser.set_edit_mode(True)

    # ------------------------------------------------------------------
    # File operations (delete / rename / save)
    # ------------------------------------------------------------------

    def _delete_note(self):
        file_path = self.markdown_browser.current_file
        if not file_path:
            messagebox.showwarning(
                translate("dm_notes.no_selection_title"),
                translate("dm_notes.no_selection"),
                parent=self,
            )
            return
        if messagebox.askyesno(
            translate("dm_notes.delete_confirm_title"),
            translate("dm_notes.delete_confirm").format(file=file_path),
            parent=self,
        ):
            try:
                os.remove(file_path)
                self.markdown_browser.load_tree()
                self.recent_files = [f for f in self.recent_files if f != file_path]
                self._update_recent_buttons()
                self._sync_index()
                messagebox.showinfo(translate("dm_notes.deleted_title"), translate("dm_notes.deleted"), parent=self)
            except Exception as e:
                messagebox.showerror(
                    translate("dm_notes.error_title"),
                    f"{translate('dm_notes.delete_error')}: {e}",
                    parent=self,
                )

    def _rename_note(self):
        file_path = self.markdown_browser.current_file
        if not file_path:
            messagebox.showwarning(
                translate("dm_notes.no_selection_title"),
                translate("dm_notes.no_selection"),
                parent=self,
            )
            return
        dirname, old_name = os.path.split(file_path)
        new_name = tkinter.simpledialog.askstring(
            translate("dm_notes.rename_title"),
            translate("dm_notes.rename_prompt"),
            initialvalue=os.path.splitext(old_name)[0],
            parent=self,
        )
        if not new_name:
            return
        if not new_name.endswith(".md"):
            new_name += ".md"
        new_path = os.path.join(dirname, new_name)
        if os.path.exists(new_path):
            messagebox.showerror(translate("dm_notes.error_title"), translate("dm_notes.rename_exists"), parent=self)
            return
        try:
            os.rename(file_path, new_path)
            self.markdown_browser.load_tree()
            self.markdown_browser.open_file(new_path)
            self.recent_files = [new_path if f == file_path else f for f in self.recent_files]
            self._update_recent_buttons()
            self._sync_index()
            messagebox.showinfo(translate("dm_notes.renamed_title"), translate("dm_notes.renamed"), parent=self)
        except Exception as e:
            messagebox.showerror(
                translate("dm_notes.error_title"),
                f"{translate('dm_notes.rename_error')}: {e}",
                parent=self,
            )

    def _save_note(self):
        if self.edit_mode:
            self._cancel_autosave()
            success = self.markdown_browser.save_current_file()
            if success:
                self._sync_index()
                messagebox.showinfo(translate("dm_notes.saved_title"), translate("dm_notes.saved"), parent=self)
            else:
                messagebox.showerror(translate("dm_notes.error_title"), translate("dm_notes.save_error"), parent=self)

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

    # ------------------------------------------------------------------
    # Recent files
    # ------------------------------------------------------------------

    def _update_recent_buttons(self):
        for btn in self.recent_buttons:
            btn.destroy()
        self.recent_buttons.clear()
        for file_path in self.recent_files[: self.max_recent]:
            file_name = os.path.basename(file_path)
            btn = ttk.Button(
                self.recent_buttons_frame,
                text=file_name,
                width=18,
                command=lambda p=file_path: self.open_recent(p),
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.recent_buttons.append(btn)

    def open_recent(self, file_path: str):
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
            self.recent_files = self.recent_files[: self.max_recent]
        self._update_recent_buttons()

    # ------------------------------------------------------------------
    # Navigation → backlinks + recent
    # ------------------------------------------------------------------

    def _on_note_navigate(self, filepath: str):
        self.add_to_recent(filepath)
        self._refresh_backlinks(filepath)

    # ------------------------------------------------------------------
    # Backlinks (#5)
    # ------------------------------------------------------------------

    def _refresh_backlinks(self, filepath: str):
        for widget in self._backlinks_frame.winfo_children():
            widget.destroy()

        try:
            from src.utils.library_index import LibraryIndex
            backlinks = LibraryIndex().get_backlinks(filepath)
        except Exception:
            backlinks = []

        if not backlinks:
            ttk.Label(
                self._backlinks_frame,
                text=translate("dm_notes.no_backlinks"),
                foreground="gray",
            ).pack(side=tk.LEFT)
            return

        for bl in backlinks:
            lbl = bl["filename"]
            path = bl["path"]
            btn = ttk.Button(
                self._backlinks_frame,
                text=lbl,
                command=lambda p=path: self.markdown_browser.open_file(p),
            )
            btn.pack(side=tk.LEFT, padx=2)

    # ------------------------------------------------------------------
    # Tag filter (#6)
    # ------------------------------------------------------------------

    def _refresh_tags(self):
        try:
            from src.utils.library_index import LibraryIndex
            tags = LibraryIndex().get_all_tags()
        except Exception:
            tags = []
        all_label = translate("dm_notes.tag_filter_all")
        values = [all_label] + tags
        self._tag_combo.configure(values=values)
        if self._tag_var.get() not in values:
            self._tag_var.set(all_label)

    def _on_tag_filter(self, event=None):
        selected = self._tag_var.get()
        all_label = translate("dm_notes.tag_filter_all")
        if selected == all_label:
            self.markdown_browser.load_tree(filter_paths=None)
        else:
            try:
                from src.utils.library_index import LibraryIndex
                paths = LibraryIndex().get_files_by_tag(selected)
                self.markdown_browser.load_tree(filter_paths=set(paths))
            except Exception:
                self.markdown_browser.load_tree(filter_paths=None)

    # ------------------------------------------------------------------
    # LibraryIndex sync helper (#1)
    # ------------------------------------------------------------------

    def _sync_index(self):
        """Re-indexes dm_notes after a filesystem change so the FTS index stays current."""
        try:
            from src.utils.library_index import LibraryIndex
            LibraryIndex().sync()
            self._refresh_tags()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Folder switcher (DM Notizen ↔ PnP-Welt)
    # ------------------------------------------------------------------

    def _refresh_folder_list(self):
        from src.config import DATA_DIR
        label_dm = translate("dm_notes.folder_dm_notes")
        label_pnp = translate("dm_notes.folder_pnp_welt")
        pnp_dir = os.path.join(DATA_DIR, "PnP-Welt")
        self._folder_map = {label_dm: self._dm_notes_dir}
        if os.path.isdir(pnp_dir):
            self._folder_map[label_pnp] = pnp_dir
        self._folder_combo.configure(values=list(self._folder_map.keys()))
        # Sync combobox label with whichever dir is currently active
        active_label = next(
            (lbl for lbl, path in self._folder_map.items() if path == self.root_dir),
            label_dm,
        )
        self._folder_var.set(active_label)

    def _on_folder_change(self, event=None):
        selected = self._folder_var.get()
        new_dir = self._folder_map.get(selected, self._dm_notes_dir)
        self.root_dir = new_dir
        self.markdown_browser.root_dir = new_dir
        self.markdown_browser.load_tree(filter_paths=self._geschichte_filter(new_dir))
        self._refresh_tags()

    @staticmethod
    def _geschichte_filter(root_dir: str):
        """Returns filter_paths for PnP-Welt (Geschichte folders only), or None for plain dm_notes."""
        import glob as _glob
        from src.config import DATA_DIR
        pnp_dir = os.path.join(DATA_DIR, "PnP-Welt")
        if os.path.abspath(root_dir) != os.path.abspath(pnp_dir):
            return None
        all_files = _glob.glob(os.path.join(root_dir, "**/*.md"), recursive=True)
        result = set()
        for f in all_files:
            parts = os.path.relpath(f, root_dir).split(os.sep)
            if any(p.startswith(".") for p in parts):
                continue
            if parts[0].startswith("Geschichte"):
                result.add(f)
        return result

    # ------------------------------------------------------------------
    # Collapse toggle
    # ------------------------------------------------------------------

    def _on_collapse_click(self):
        if self.collapse_callback:
            self.collapse_callback()

    def set_collapsed(self, collapsed: bool):
        """Called by MainView after the sash has moved to update the button icon."""
        self._collapsed = collapsed
        if self._collapse_btn and self._collapse_btn.winfo_exists():
            self._collapse_btn.config(text="▶" if collapsed else "◀")

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
        if hasattr(self, "markdown_browser"):
            self.markdown_browser.update_colors(colors)
