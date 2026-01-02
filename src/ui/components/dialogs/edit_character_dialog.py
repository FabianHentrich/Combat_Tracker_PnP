import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Callable, List, Optional
from src.models.character import Character
from src.models.enums import CharacterType
from src.models.status_effects import EFFECT_CLASSES, GenericStatusEffect
from src.config import WINDOW_SIZE

class EditCharacterDialog:
    """
    Dialog-Fenster zum Bearbeiten eines Charakters.
    """
    def __init__(self, parent: tk.Tk, char: Character, colors: Dict[str, str], on_save: Callable[[Dict[str, Any]], None]):
        self.parent = parent
        self.char = char
        self.colors = colors
        self.on_save = on_save

        self.window = tk.Toplevel(parent)
        self.window.title(f"Bearbeiten: {char.name}")
        self.window.geometry(WINDOW_SIZE["edit"])
        self.window.configure(bg=self.colors["bg"])

        self.entries: Dict[str, Any] = {}
        self.status_ui_entries: List[Dict[str, Any]] = []
        self.status_container: Optional[ttk.Frame] = None

        self._setup_ui()

    def lift(self):
        self.window.lift()

    def focus_force(self):
        self.window.focus_force()

    def destroy(self):
        self.window.destroy()

    def winfo_exists(self) -> bool:
        return self.window.winfo_exists()

    def _setup_ui(self):
        # Container
        frame = ttk.Frame(self.window, padding="20", style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        # Grid Layout
        row = 0

        # Name
        self._create_entry_row(frame, "Name:", "name", self.char.name, row, width=25)
        row += 1

        # Typ
        ttk.Label(frame, text="Typ:").grid(row=row, column=0, sticky="w", pady=5)
        e_type = ttk.Combobox(frame, values=[t.value for t in CharacterType], state="readonly", width=23)
        e_type.set(self.char.char_type)
        e_type.grid(row=row, column=1, sticky="ew", pady=5)
        self.entries["type"] = e_type
        row += 1

        # LP, RP, SP (Dual Entries)
        self._create_dual_entry_row(frame, "LP (Aktuell / Max):", "lp", self.char.lp, "max_lp", self.char.max_lp, row)
        row += 1
        self._create_dual_entry_row(frame, "RP (Aktuell / Max):", "rp", self.char.rp, "max_rp", self.char.max_rp, row)
        row += 1
        self._create_dual_entry_row(frame, "SP (Aktuell / Max):", "sp", self.char.sp, "max_sp", self.char.max_sp, row)
        row += 1

        # Gewandtheit & Initiative
        self._create_entry_row(frame, "Gewandtheit:", "gew", self.char.gew, row, width=10)
        row += 1
        self._create_entry_row(frame, "Initiative:", "init", self.char.init, row, width=10)
        row += 1

        # --- Status Section ---
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        ttk.Label(frame, text="Status (Effekt | Rang | Dauer):").grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1

        self.status_container = ttk.Frame(frame, style="Card.TFrame")
        self.status_container.grid(row=row, column=0, columnspan=2, sticky="ew")
        row += 1

        # Bestehende Statusse laden
        for st in self.char.status:
            self._add_status_row(st)

        # Buttons
        btn_frame = ttk.Frame(self.window, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=10, padx=20)

        ttk.Button(btn_frame, text="Speichern", command=self._on_save_click).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Abbrechen", command=self.window.destroy).pack(side=tk.RIGHT, padx=10)

    def _create_entry_row(self, parent, label, key, value, row, width=20):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, width=width)
        entry.insert(0, str(value))
        entry.grid(row=row, column=1, sticky="w", pady=5)
        self.entries[key] = entry

    def _create_dual_entry_row(self, parent, label, key1, val1, key2, val2, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=5)
        container = ttk.Frame(parent, style="Card.TFrame")
        container.grid(row=row, column=1, sticky="ew", pady=5)

        e1 = ttk.Entry(container, width=8)
        e1.insert(0, str(val1))
        e1.pack(side=tk.LEFT, padx=(0, 5))
        self.entries[key1] = e1

        ttk.Label(container, text="/").pack(side=tk.LEFT)

        e2 = ttk.Entry(container, width=8)
        e2.insert(0, str(val2))
        e2.pack(side=tk.LEFT, padx=(5, 0))
        self.entries[key2] = e2

    def _add_status_row(self, st_data):
        row_frame = ttk.Frame(self.status_container, style="Card.TFrame")
        row_frame.pack(fill=tk.X, pady=2)

        # Effekt Name
        effect_name = st_data.name
        if hasattr(effect_name, 'value'):
            effect_name = effect_name.value

        e_effect = ttk.Label(row_frame, text=str(effect_name), width=18, anchor="w")
        e_effect.pack(side=tk.LEFT, padx=(0, 5))

        # Rang
        e_rank = ttk.Entry(row_frame, width=5)
        e_rank.insert(0, str(st_data.rank))
        e_rank.pack(side=tk.LEFT, padx=(0, 5))

        # Dauer
        e_rounds = ttk.Entry(row_frame, width=5)
        e_rounds.insert(0, str(st_data.duration))
        e_rounds.pack(side=tk.LEFT, padx=(0, 5))

        entry_dict = {
            "effect": e_effect,
            "rounds": e_rounds,
            "rank": e_rank,
            "frame": row_frame
        }

        # Löschen Button
        btn_del = ttk.Button(row_frame, text="X", width=3, command=lambda: self._delete_status_row(entry_dict))
        btn_del.pack(side=tk.LEFT)

        self.status_ui_entries.append(entry_dict)

    def _delete_status_row(self, entry_dict):
        entry_dict["frame"].destroy()
        if entry_dict in self.status_ui_entries:
            self.status_ui_entries.remove(entry_dict)

    def _on_save_click(self):
        """Sammelt Daten, validiert und ruft Callback auf."""
        try:
            new_name = self.entries["name"].get()
            if not new_name:
                raise ValueError("Name darf nicht leer sein.")

            data = {
                "name": new_name,
                "char_type": self.entries["type"].get(),
                "lp": int(self.entries["lp"].get()),
                "max_lp": int(self.entries["max_lp"].get()),
                "rp": int(self.entries["rp"].get()),
                "max_rp": int(self.entries["max_rp"].get()),
                "sp": int(self.entries["sp"].get()),
                "max_sp": int(self.entries["max_sp"].get()),
                "init": int(self.entries["init"].get()),
                "gew": int(self.entries["gew"].get())
            }

            # Status speichern
            new_status_list = []
            for item in self.status_ui_entries:
                effect_name = item["effect"].cget("text")
                rounds = int(item["rounds"].get())
                rank = int(item["rank"].get())

                if effect_name:
                    effect_class = EFFECT_CLASSES.get(effect_name)
                    if effect_class:
                        effect = effect_class(rounds, rank)
                    else:
                        effect = GenericStatusEffect(effect_name, rounds, rank)
                    new_status_list.append(effect)

            data["status"] = new_status_list

            self.on_save(data)
            self.window.destroy()

        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")

