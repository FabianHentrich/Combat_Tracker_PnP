import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any, Callable
from src.config import FONTS, WINDOW_SIZE
from src.models.enums import CharacterType

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
        super().__init__(parent, "Import Vorschau & Auswahl", colors)
        self.data = data
        self.on_confirm = on_confirm
        self.import_entries = []
        self._setup_ui()

    def _setup_ui(self):
        # Header
        ttk.Label(self.window, text="Auswählen und anpassen", font=FONTS["xl"]).pack(pady=10)

        scroll_frame = self._setup_scrollable_area()

        # Spaltenüberschriften
        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW", "Level", "Anzahl"]
        widths = [15, 8, 5, 5, 5, 5, 5, 10]
        self._create_header_row(scroll_frame, headers, widths)

        # Zeilen generieren
        self.import_entries = []

        for row in self.data:
            row_frame = ttk.Frame(scroll_frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=2)

            # Name
            e_name = ttk.Entry(row_frame, width=widths[0])
            e_name.insert(0, str(row["Name"]))
            e_name.pack(side="left", padx=5)

            # Typ
            e_type = ttk.Combobox(row_frame, values=[t.value for t in CharacterType], width=widths[1], state="readonly")
            e_type.set(CharacterType.ENEMY.value)
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

        ttk.Button(btn_frame, text="Weiter zur Detail-Anpassung", command=self._on_next).pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=self.window.destroy).pack(side="right", padx=10)

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
                    char_type = entry["type"].get()
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
                            "Name": final_name,
                            "Typ": char_type,
                            "HP": lp,
                            "Ruestung": rp,
                            "Schild": sp,
                            "Gewandtheit": gew,
                            "Level": level
                        })

            if not expanded_data:
                messagebox.showinfo("Info", "Keine Gegner ausgewählt.")
                return

            self.window.destroy()
            self.on_confirm(expanded_data)

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte verwenden.")


class ImportDetailDialog(BaseImportDialog):
    """
    Dialog für Schritt 2 des Imports: Finale Bearbeitung einzelner Einträge.
    """
    def __init__(self, parent: tk.Tk, data: List[Dict[str, Any]], colors: Dict[str, str], on_finish: Callable[[List[Dict[str, Any]]], None]):
        super().__init__(parent, "Import - Detail Anpassung", colors)
        self.data = data
        self.on_finish = on_finish
        self.detail_entries = []
        self._setup_ui()

    def _setup_ui(self):
        # Header
        ttk.Label(self.window, text="Details anpassen", font=FONTS["xl"], background=self.colors["bg"]).pack(pady=10)
        ttk.Label(self.window, text="Hier können einzelne Charaktere final bearbeitet werden.", font=FONTS["main"], background=self.colors["bg"]).pack(pady=(0, 10))

        scroll_frame = self._setup_scrollable_area()

        # Header Zeile
        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW", "Level"]
        widths = [20, 10, 5, 5, 5, 5, 5, 5]
        self._create_header_row(scroll_frame, headers, widths)

        self.detail_entries = []

        for row in self.data:
            row_frame = ttk.Frame(scroll_frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=2)

            # Name
            e_name = ttk.Entry(row_frame, width=20)
            e_name.insert(0, str(row["Name"]))
            e_name.pack(side="left", padx=5)

            # Typ
            e_type = ttk.Combobox(row_frame, values=[t.value for t in CharacterType], width=10, state="readonly")
            e_type.set(row["Typ"])
            e_type.pack(side="left", padx=5)

            # LP
            e_lp = ttk.Entry(row_frame, width=8)
            e_lp.insert(0, str(row["HP"]))
            e_lp.pack(side="left", padx=5)

            # RP
            e_rp = ttk.Entry(row_frame, width=8)
            e_rp.insert(0, str(row["Ruestung"]))
            e_rp.pack(side="left", padx=5)

            # SP
            e_sp = ttk.Entry(row_frame, width=8)
            e_sp.insert(0, str(row["Schild"]))
            e_sp.pack(side="left", padx=5)

            # Gewandtheit
            e_gew = ttk.Entry(row_frame, width=12)
            e_gew.insert(0, str(row["Gewandtheit"]))
            e_gew.pack(side="left", padx=5)

            # Level
            e_level = ttk.Entry(row_frame, width=8)
            e_level.insert(0, str(row.get("level", 0)))
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

        ttk.Button(btn_frame, text="Alle Importieren", command=self._on_finish).pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=self.window.destroy).pack(side="right", padx=10)

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
                data = {
                    "name": entry["name"].get(),
                    "type": entry["type"].get(),
                    "lp": int(entry["lp"].get()),
                    "rp": int(entry["rp"].get()),
                    "sp": int(entry["sp"].get()),
                    "gew": int(entry["gew"].get()),
                    "level": int(entry["level"].get())
                }
                final_data.append(data)

            self.window.destroy()
            self.on_finish(final_data)

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte in den Feldern verwenden.")
