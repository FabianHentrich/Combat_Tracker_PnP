import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, TYPE_CHECKING
from src.utils.logger import setup_logging
from src.models.enums import CharacterType, EventType
from src.models.status_effects import EFFECT_CLASSES, GenericStatusEffect
from src.utils.config import WINDOW_SIZE

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager
    from src.models.character import Character

logger = setup_logging()

class EditHandler:
    """
    Verwaltet das Bearbeiten von Charakteren.
    Öffnet ein Fenster mit Eingabefeldern für alle Attribute und Status-Effekte.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', root: tk.Tk, colors: Dict[str, str]):
        self.engine = engine
        self.history_manager = history_manager
        self.root = root
        self.colors = colors


    def open_edit_character_window(self, char: 'Character') -> None:
        """Öffnet ein Fenster zum Bearbeiten eines Charakters."""
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Bearbeiten: {char.name}")
        edit_window.geometry(WINDOW_SIZE["edit"]) # Fenster vergrößert für Status-Liste
        edit_window.configure(bg=self.colors["bg"])

        # Container
        frame = ttk.Frame(edit_window, padding="20", style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        # Grid Layout
        row = 0

        # Name
        ttk.Label(frame, text="Name:").grid(row=row, column=0, sticky="w", pady=5)
        e_name = ttk.Entry(frame, width=25)
        e_name.insert(0, char.name)
        e_name.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # Typ
        ttk.Label(frame, text="Typ:").grid(row=row, column=0, sticky="w", pady=5)
        e_type = ttk.Combobox(frame, values=[t.value for t in CharacterType], state="readonly", width=23)
        e_type.set(char.char_type)
        e_type.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # LP (Aktuell / Max)
        ttk.Label(frame, text="LP (Aktuell / Max):").grid(row=row, column=0, sticky="w", pady=5)
        lp_frame = ttk.Frame(frame, style="Card.TFrame")
        lp_frame.grid(row=row, column=1, sticky="ew", pady=5)

        e_lp = ttk.Entry(lp_frame, width=8)
        e_lp.insert(0, str(char.lp))
        e_lp.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(lp_frame, text="/").pack(side=tk.LEFT)

        e_max_lp = ttk.Entry(lp_frame, width=8)
        e_max_lp.insert(0, str(char.max_lp))
        e_max_lp.pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # RP (Aktuell / Max)
        ttk.Label(frame, text="RP (Aktuell / Max):").grid(row=row, column=0, sticky="w", pady=5)
        rp_frame = ttk.Frame(frame, style="Card.TFrame")
        rp_frame.grid(row=row, column=1, sticky="ew", pady=5)

        e_rp = ttk.Entry(rp_frame, width=8)
        e_rp.insert(0, str(char.rp))
        e_rp.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(rp_frame, text="/").pack(side=tk.LEFT)

        e_max_rp = ttk.Entry(rp_frame, width=8)
        e_max_rp.insert(0, str(char.max_rp))
        e_max_rp.pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # SP (Aktuell / Max)
        ttk.Label(frame, text="SP (Aktuell / Max):").grid(row=row, column=0, sticky="w", pady=5)
        sp_frame = ttk.Frame(frame, style="Card.TFrame")
        sp_frame.grid(row=row, column=1, sticky="ew", pady=5)

        e_sp = ttk.Entry(sp_frame, width=8)
        e_sp.insert(0, str(char.sp))
        e_sp.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(sp_frame, text="/").pack(side=tk.LEFT)

        e_max_sp = ttk.Entry(sp_frame, width=8)
        e_max_sp.insert(0, str(char.max_sp))
        e_max_sp.pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # Gewandtheit
        ttk.Label(frame, text="Gewandtheit:").grid(row=row, column=0, sticky="w", pady=5)
        e_gew = ttk.Entry(frame, width=10)
        e_gew.insert(0, str(char.gew))
        e_gew.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Initiative
        ttk.Label(frame, text="Initiative:").grid(row=row, column=0, sticky="w", pady=5)
        e_init = ttk.Entry(frame, width=10)
        e_init.insert(0, str(char.init))
        e_init.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # --- Status Section ---
        ttk.Separator(frame, orient='horizontal').grid(row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1

        ttk.Label(frame, text="Status (Effekt | Rang | Dauer):").grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
        row += 1

        status_container = ttk.Frame(frame, style="Card.TFrame")
        status_container.grid(row=row, column=0, columnspan=2, sticky="ew")
        row += 1

        # Liste für die Status-Einträge (Widgets)
        status_ui_entries = []

        def add_status_row(st_data):
            row_frame = ttk.Frame(status_container, style="Card.TFrame")
            row_frame.pack(fill=tk.X, pady=2)

            # Effekt Name
            # st_data ist jetzt ein StatusEffect Objekt
            effect_name = st_data.name
            # Falls es ein Enum ist, den Wert holen
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

            # Löschen Button
            def delete_row():
                row_frame.destroy()
                if entry_dict in status_ui_entries:
                    status_ui_entries.remove(entry_dict)

            btn_del = ttk.Button(row_frame, text="X", width=3, command=delete_row)
            btn_del.pack(side=tk.LEFT)

            entry_dict = {
                "effect": e_effect,
                "rounds": e_rounds,
                "rank": e_rank
            }
            status_ui_entries.append(entry_dict)

        # Bestehende Statusse laden
        for st in char.status:
            add_status_row(st)

        # Buttons
        btn_frame = ttk.Frame(edit_window, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=10, padx=20)

        entries = {
            "name": e_name, "type": e_type,
            "lp": e_lp, "max_lp": e_max_lp,
            "rp": e_rp, "max_rp": e_max_rp,
            "sp": e_sp, "max_sp": e_max_sp,
            "init": e_init,
            "gew": e_gew
        }

        ttk.Button(btn_frame, text="Speichern", command=lambda: self.save_character_edits(edit_window, char, entries, status_ui_entries)).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Abbrechen", command=edit_window.destroy).pack(side=tk.RIGHT, padx=10)


    def save_character_edits(self, window, char, entries, status_ui_entries):
        """
        Speichert die Änderungen aus dem Bearbeiten-Fenster.
        Validiert die Eingaben und aktualisiert das Character-Objekt.
        """
        try:
            # Snapshot vor Änderungen
            if self.history_manager:
                self.history_manager.save_snapshot()

            new_name = entries["name"].get()
            if not new_name:
                raise ValueError("Name darf nicht leer sein.")

            data = {
                "name": new_name,
                "char_type": entries["type"].get(),
                "lp": int(entries["lp"].get()),
                "max_lp": int(entries["max_lp"].get()),
                "rp": int(entries["rp"].get()),
                "max_rp": int(entries["max_rp"].get()),
                "sp": int(entries["sp"].get()),
                "max_sp": int(entries["max_sp"].get()),
                "init": int(entries["init"].get()),
                "gew": int(entries["gew"].get())
            }

            # Status speichern
            new_status_list = []
            for item in status_ui_entries:
                effect_name = item["effect"].cget("text")
                rounds = int(item["rounds"].get())
                rank = int(item["rank"].get())

                if effect_name: # Nur speichern wenn Name existiert
                    effect_class = EFFECT_CLASSES.get(effect_name)
                    if effect_class:
                        effect = effect_class(rounds, rank)
                    else:
                        effect = GenericStatusEffect(effect_name, rounds, rank)
                    new_status_list.append(effect)

            data["status"] = new_status_list

            self.engine.update_character(char, data)
            window.destroy()

        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")