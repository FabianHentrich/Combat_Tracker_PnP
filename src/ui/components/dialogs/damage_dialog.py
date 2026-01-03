import tkinter as tk
from tkinter import ttk
from src.config.defaults import DEFAULT_RULES

class DamageDialog(tk.Toplevel):
    def __init__(self, parent, title="Schaden zufügen"):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        self.rows = [] # Speichert Referenzen auf die Widgets jeder Zeile
        
        # Schadenstypen aus DEFAULT_RULES laden
        self.damage_types = list(DEFAULT_RULES["damage_types"].keys())
        
        # Haupt-Container
        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill="both", expand=True)
        
        # Container für die dynamischen Zeilen
        self.rows_frame = ttk.Frame(self.main_frame)
        self.rows_frame.pack(fill="x", pady=(0, 10))
        
        # Buttons
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="+ Typ hinzufügen", command=self.add_row).pack(side="left")
        
        # Summen-Anzeige
        self.lbl_total = ttk.Label(self.main_frame, text="Gesamt: 0", font=("Arial", 10, "bold"))
        self.lbl_total.pack(pady=10)
        
        # OK / Abbrechen
        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill="x", pady=(10, 0))
        ttk.Button(action_frame, text="Abbrechen", command=self.destroy).pack(side="right", padx=5)
        ttk.Button(action_frame, text="OK", command=self.on_ok).pack(side="right")
        
        # Erste Zeile initial hinzufügen
        self.add_row()
        
        # Fenster zentrieren
        self.update_idletasks()
        width = 350
        height = self.winfo_reqheight()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def add_row(self):
        row_frame = ttk.Frame(self.rows_frame)
        row_frame.pack(fill="x", pady=2)
        
        # Eingabefeld für Menge
        amount_var = tk.StringVar(value="0")
        amount_var.trace_add("write", self.calculate_total)
        entry = ttk.Entry(row_frame, textvariable=amount_var, width=8)
        entry.pack(side="left", padx=(0, 5))
        
        # Dropdown für Typ
        type_var = tk.StringVar(value=self.damage_types[0] if self.damage_types else "")
        combo = ttk.Combobox(row_frame, textvariable=type_var, values=self.damage_types, state="readonly", width=12)
        combo.pack(side="left", padx=(0, 5))
        
        # Löschen Button (nur wenn nicht die erste Zeile)
        if len(self.rows) > 0:
            btn_del = ttk.Button(row_frame, text="X", width=3, command=lambda: self.remove_row(row_frame))
            btn_del.pack(side="left")
        
        self.rows.append({
            "frame": row_frame,
            "amount": amount_var,
            "type": type_var
        })
        
        entry.focus_set()
        entry.select_range(0, tk.END)

    def remove_row(self, frame):
        # Zeile aus Liste und GUI entfernen
        self.rows = [r for r in self.rows if r["frame"] != frame]
        frame.destroy()
        self.calculate_total()

    def calculate_total(self, *args):
        total = 0
        for row in self.rows:
            try:
                val = int(row["amount"].get())
                total += val
            except ValueError:
                pass
        self.lbl_total.config(text=f"Gesamt: {total}")
        return total

    def on_ok(self):
        total = self.calculate_total()
        details = []
        
        for row in self.rows:
            try:
                val = int(row["amount"].get())
                if val > 0:
                    t = row["type"].get()
                    details.append(f"{val} {t}")
            except ValueError:
                pass
        
        detail_str = ", ".join(details) if details else "0 Normal"
        
        # Rückgabe: (Gesamtschaden, Beschreibungs-String)
        self.result = (total, detail_str)
        self.destroy()
