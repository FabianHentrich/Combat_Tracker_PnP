import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any, Optional
from src.config import FONTS
from src.models.enums import CharacterType

class StagingArea(ttk.Frame):
    """
    Widget zur Verwaltung der ausgewählten Gegner vor dem Import.
    """
    def __init__(self, parent: tk.Widget, colors: Dict[str, str]):
        super().__init__(parent, style="Card.TFrame")
        self.colors = colors
        self.staging_entries: List[Dict[str, Any]] = []
        self.scrollable_frame: Optional[ttk.Frame] = None

        self._setup_ui()

    def _setup_ui(self):
        # Header Label
        ttk.Label(self, text="Ausgewählte Gegner (Anzahl & Werte anpassen)", font=FONTS["large"]).pack(pady=5)

        # Canvas für scrollbare Liste
        canvas = tk.Canvas(self, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        self._create_headers()

    def _create_headers(self):
        header_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW", "Anzahl", "Sofort", ""]
        widths = [30, 10, 5, 5, 5, 5, 5, 5, 5]
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=FONTS["small"], width=widths[i], anchor="w").pack(side="left", padx=2)

    def add_entry(self, name: str, data: Dict[str, Any]):
        """Fügt einen neuen Eintrag zur Staging Area hinzu."""
        row_frame = ttk.Frame(self.scrollable_frame, style="Card.TFrame")
        row_frame.pack(fill="x", pady=5)

        # Name
        e_name = ttk.Entry(row_frame, width=30)
        e_name.insert(0, name)
        e_name.pack(side="left", padx=5)

        # Typ
        e_type = ttk.Combobox(row_frame, values=[t.value for t in CharacterType], width=10, state="readonly")
        e_type.set(data.get("type", CharacterType.ENEMY.value))
        e_type.pack(side="left", padx=5)

        # Numerische Felder
        e_lp = self._create_numeric_entry(row_frame, data.get("lp", 10))
        e_rp = self._create_numeric_entry(row_frame, data.get("rp", 0))
        e_sp = self._create_numeric_entry(row_frame, data.get("sp", 0))
        e_gew = self._create_numeric_entry(row_frame, data.get("gew", 1))
        e_count = self._create_numeric_entry(row_frame, "1")

        # Sofort Checkbox
        var_surprise = tk.BooleanVar()
        cb_surprise = ttk.Checkbutton(row_frame, variable=var_surprise)
        cb_surprise.pack(side="left", padx=5)

        # Löschen Button
        btn_del = ttk.Button(row_frame, text="X", width=3)
        btn_del.pack(side="left", padx=5)

        entry_obj = {
            "frame": row_frame,
            "name": e_name,
            "type": e_type,
            "lp": e_lp,
            "rp": e_rp,
            "sp": e_sp,
            "gew": e_gew,
            "count": e_count,
            "surprise": var_surprise
        }

        btn_del.configure(command=lambda: self._remove_entry(row_frame, entry_obj))
        self.staging_entries.append(entry_obj)

    def _create_numeric_entry(self, parent, value, width=5):
        entry = ttk.Entry(parent, width=width)
        entry.insert(0, str(value))
        entry.pack(side="left", padx=5)
        return entry

    def _remove_entry(self, frame: ttk.Frame, entry_obj: Dict[str, Any]):
        frame.destroy()
        if entry_obj in self.staging_entries:
            self.staging_entries.remove(entry_obj)

    def get_data(self) -> List[Dict[str, Any]]:
        """
        Sammelt die Daten aus allen Einträgen und gibt sie als Liste zurück.
        Wirft ValueError bei ungültigen Eingaben.
        """
        result = []
        for entry in self.staging_entries:
            try:
                count = int(entry["count"].get())
            except ValueError:
                count = 1

            if count <= 0: continue

            data = {
                "name_base": entry["name"].get(),
                "type": entry["type"].get(),
                "lp": int(entry["lp"].get()),
                "rp": int(entry["rp"].get()),
                "sp": int(entry["sp"].get()),
                "gew": int(entry["gew"].get()),
                "surprise": entry["surprise"].get(),
                "count": count
            }
            result.append(data)
        return result

