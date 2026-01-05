import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Callable
from src.config import FONTS, WINDOW_SIZE
from src.models.enums import CharacterType, StatType
from src.utils.localization import translate

class BaseImportDialog:
    """Basisklasse für Import-Dialoge mit scrollbarem Bereich."""
    def __init__(self, parent: tk.Tk, title: str, colors: Dict[str, str]):
        self.colors = colors
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry(WINDOW_SIZE["import"])
        self.window.configure(bg=self.colors["bg"])
        self.scrollable_frame = None

    def _setup_scrollable_area(self):
        canvas = tk.Canvas(self.window, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)
        return self.scrollable_frame

    def _create_header_row(self, parent, headers, widths):
        header_frame = ttk.Frame(parent, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=FONTS["bold"], width=widths[i], anchor="w").pack(side="left", padx=5)
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=5)

class ImportPreviewDialog(BaseImportDialog):
    """
    Dialog für Schritt 1 des Imports: Auswahl der Zeilen und Anzahl.
    """
    def __init__(self, parent: tk.Tk, data: List[Dict[str, Any]], colors: Dict[str, str], on_confirm: Callable[[List[Dict[str, Any]]], None]):
        super().__init__(parent, translate("dialog.import_preview.title"), colors)
        self.data = data
        self.on_confirm = on_confirm
        self.import_entries = []
        self._setup_ui()

    def _setup_ui(self):
        # Header
        ttk.Label(self.window, text=translate("dialog.import_preview.header"), font=FONTS["xl"]).pack(pady=10)

        scroll_frame = self._setup_scrollable_area()

        # Spaltenüberschriften
        headers = [translate("character_attributes.name"), translate("character_attributes.type"), translate("character_attributes.lp"), translate("character_attributes.rp"), translate("character_attributes.sp"), translate("character_attributes.gew"), translate("character_attributes.level"), translate("dialog.import_preview.count")]
        widths = [15, 8, 5, 5, 5, 5, 5, 10]
        self._create_header_row(scroll_frame, headers, widths)

        # Zeilen generieren
        self.import_entries = []
        self.translated_types = {translate(f"character_types.{t.name}"): t.value for t in CharacterType}

        for row in self.data:
            row_frame = ttk.Frame(scroll_frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=2)

            # Name
            e_name = ttk.Entry(row_frame, width=widths[0])
            e_name.insert(0, str(row["Name"]))
            e_name.pack(side="left", padx=5)

            # Typ
            e_type = ttk.Combobox(row_frame, values=list(self.translated_types.keys()), width=widths[1], state="readonly")
            e_type.set(translate(f"character_types.{CharacterType.ENEMY.name}"))
            e_type.pack(side="left", padx=5)

            # LP
            e_lp = ttk.Entry(row_frame, width=widths[2])
            e_lp.insert(0, str(row["HP"]))
            e_lp.pack(side="left", padx=5)

            # RP
            e_rp = ttk.Entry(row_frame, width=widths[3])
            e_rp.insert(0, str(row["Ruestung"]))
            e_rp.pack(side="left", padx=5)

            # SP
            e_sp = ttk.Entry(row_frame, width=widths[4])
            e_sp.insert(0, str(row["Schild"]))
            e_sp.pack(side="left", padx=5)

            # Gewandtheit (Init Basis)
            e_gew = ttk.Entry(row_frame, width=widths[5])
            e_gew.insert(0, str(row["Gewandtheit"]))
            e_gew.pack(side="left", padx=5)

            # Level
            e_level = ttk.Entry(row_frame, width=widths[6])
            e_level.insert(0, str(row.get("level", 0)))
            e_level.pack(side="left", padx=5)

            # Anzahl (Spinbox)
            e_count = ttk.Entry(row_frame, width=widths[7])
            e_count.insert(0, "1") # Standardmäßig 1
            e_count.pack(side="left", padx=5)

            # Speichere Referenzen
            self.import_entries.append({
                "name": e_name,
                "type": e_type,
                "lp": e_lp,
                "rp": e_rp,
                "sp": e_sp,
                "gew": e_gew,
                "level": e_level,
                "count": e_count
            })

        # Footer Buttons
        btn_frame = ttk.Frame(self.window, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=10, padx=10)

        ttk.Button(btn_frame, text=translate("dialog.import_preview.next_btn"), command=self._on_next).pack(side="right")
        ttk.Button(btn_frame, text=translate("common.cancel"), command=self.window.destroy).pack(side="right", padx=10)

    def _on_next(self):
        """Sammelt Daten und ruft den Callback auf."""
        expanded_data = []
        try:
            for entry in self.import_entries:
                try:
                    count = int(entry["count"].get())
                except ValueError:
                    count = 0

                if count > 0:
                    name_base = entry["name"].get()
                    selected_type_display = entry["type"].get()
                    char_type_value = self.translated_types.get(selected_type_display, CharacterType.ENEMY.value)
                    
                    lp = entry["lp"].get()
                    rp = entry["rp"].get()
                    sp = entry["sp"].get()
                    gew = entry["gew"].get()
                    level = entry["level"].get()

                    for i in range(count):
                        final_name = name_base
                        if count > 1:
                            final_name = f"{name_base} {i+1}"

                        expanded_data.append({
                            StatType.NAME.value: final_name,
                            StatType.TYPE.value: char_type_value,
                            StatType.LP.value: lp,
                            StatType.RP.value: rp,
                            StatType.SP.value: sp,
                            StatType.GEW.value: gew,
                            StatType.LEVEL.value: level
                        })

            if not expanded_data:
                messagebox.showinfo(translate("dialog.info.title"), translate("messages.no_enemies_selected"))
                return

            self.window.destroy()
            self.on_confirm(expanded_data)

        except ValueError:
            messagebox.showerror(translate("dialog.error.title"), translate("messages.use_valid_numbers"))


class ImportDetailDialog(BaseImportDialog):
    """
    Dialog für Schritt 2 des Imports: Finale Bearbeitung einzelner Einträge.
    """
    def __init__(self, parent: tk.Tk, data: List[Dict[str, Any]], colors: Dict[str, str], on_finish: Callable[[List[Dict[str, Any]]], None]):
        super().__init__(parent, translate("dialog.import_detail.title"), colors)
        self.data = data
        self.on_finish = on_finish
        self.detail_entries = []
        self._setup_ui()

    def _setup_ui(self):
        # Header
        ttk.Label(self.window, text=translate("dialog.import_detail.header"), font=FONTS["xl"], background=self.colors["bg"]).pack(pady=10)
        ttk.Label(self.window, text=translate("dialog.import_detail.subheader"), font=FONTS["main"], background=self.colors["bg"]).pack(pady=(0, 10))

        scroll_frame = self._setup_scrollable_area()

        # Header Zeile
        headers = [translate("character_attributes.name"), translate("character_attributes.type"), translate("character_attributes.lp"), translate("character_attributes.rp"), translate("character_attributes.sp"), translate("character_attributes.gew"), translate("character_attributes.level")]
        widths = [20, 10, 5, 5, 5, 5, 5, 5]
        self._create_header_row(scroll_frame, headers, widths)

        self.detail_entries = []
        self.translated_types = {translate(f"character_types.{t.name}"): t.value for t in CharacterType}

        for row in self.data:
            row_frame = ttk.Frame(scroll_frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=2)

            # Name
            e_name = ttk.Entry(row_frame, width=20)
            e_name.insert(0, str(row[StatType.NAME.value]))
            e_name.pack(side="left", padx=5)

            # Typ
            e_type = ttk.Combobox(row_frame, values=list(self.translated_types.keys()), width=10, state="readonly")
            current_type_display = translate(f"character_types.{row[StatType.TYPE.value]}")
            e_type.set(current_type_display)
            e_type.pack(side="left", padx=5)

            # LP
            e_lp = ttk.Entry(row_frame, width=8)
            e_lp.insert(0, str(row[StatType.LP.value]))
            e_lp.pack(side="left", padx=5)

            # RP
            e_rp = ttk.Entry(row_frame, width=8)
            e_rp.insert(0, str(row[StatType.RP.value]))
            e_rp.pack(side="left", padx=5)

            # SP
            e_sp = ttk.Entry(row_frame, width=8)
            e_sp.insert(0, str(row[StatType.SP.value]))
            e_sp.pack(side="left", padx=5)

            # Gewandtheit
            e_gew = ttk.Entry(row_frame, width=12)
            e_gew.insert(0, str(row[StatType.GEW.value]))
            e_gew.pack(side="left", padx=5)

            # Level
            e_level = ttk.Entry(row_frame, width=8)
            e_level.insert(0, str(row.get(StatType.LEVEL.value, 0)))
            e_level.pack(side="left", padx=5)

            # Löschen Button für einzelne Zeile
            btn_del = ttk.Button(row_frame, text="X", width=3)
            btn_del.pack(side="left", padx=5)

            # Eintrag speichern
            entry_obj = {
                "frame": row_frame,
                "name": e_name,
                "type": e_type,
                "lp": e_lp,
                "rp": e_rp,
                "sp": e_sp,
                "gew": e_gew,
                "level": e_level
            }

            # Command setzen mit Referenz auf das Objekt
            btn_del.configure(command=lambda f=row_frame, obj=entry_obj: self.remove_detail_row(f, obj))

            self.detail_entries.append(entry_obj)

        # Footer Buttons
        btn_frame = ttk.Frame(self.window, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=10, padx=10)

        ttk.Button(btn_frame, text=translate("dialog.import_detail.import_all_btn"), command=self._on_finish).pack(side="right")
        ttk.Button(btn_frame, text=translate("common.cancel"), command=self.window.destroy).pack(side="right", padx=10)

    def remove_detail_row(self, frame, entry_obj):
        """Entfernt eine Zeile aus der Detailansicht."""
        frame.destroy()
        if entry_obj in self.detail_entries:
            self.detail_entries.remove(entry_obj)

    def _on_finish(self):
        """Sammelt finale Daten und ruft Callback auf."""
        final_data = []
        try:
            for entry in self.detail_entries:
                selected_type_display = entry["type"].get()
                char_type_value = self.translated_types.get(selected_type_display, CharacterType.ENEMY.value)
                
                data = {
                    StatType.NAME.value: entry["name"].get(),
                    StatType.TYPE.value: char_type_value,
                    StatType.LP.value: int(entry["lp"].get()),
                    StatType.RP.value: int(entry["rp"].get()),
                    StatType.SP.value: int(entry["sp"].get()),
                    StatType.GEW.value: int(entry["gew"].get()),
                    StatType.LEVEL.value: int(entry["level"].get())
                }
                final_data.append(data)

            self.window.destroy()
            self.on_finish(final_data)

        except ValueError:
            messagebox.showerror(translate("dialog.error.title"), translate("messages.use_valid_numbers"))
