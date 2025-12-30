import tkinter as tk
from tkinter import ttk, messagebox
from .utils import simple_input_dialog

class EditHandler:
    def __init__(self, tracker, root, colors):
        self.tracker = tracker
        self.root = root
        self.colors = colors

    def edit_selected_char(self):
        """Bearbeitet alle Werte des ausgewählten Charakters."""
        char = self.tracker.get_selected_char()
        if not char: return

        self.open_edit_character_window(char)

    def open_edit_character_window(self, char):
        """Öffnet ein Fenster zum Bearbeiten eines Charakters."""
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Bearbeiten: {char.name}")
        edit_window.geometry("400x350")
        edit_window.configure(bg=self.colors["bg"])

        # Container
        frame = ttk.Frame(edit_window, padding="20", style="Card.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        # Grid Layout
        row = 0

        # Name
        ttk.Label(frame, text="Name:", background=self.colors["panel"]).grid(row=row, column=0, sticky="w", pady=5)
        e_name = ttk.Entry(frame, width=25)
        e_name.insert(0, char.name)
        e_name.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # Typ
        ttk.Label(frame, text="Typ:", background=self.colors["panel"]).grid(row=row, column=0, sticky="w", pady=5)
        e_type = ttk.Combobox(frame, values=["Spieler", "Gegner", "NPC"], state="readonly", width=23)
        e_type.set(char.char_type)
        e_type.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        # LP (Aktuell / Max)
        ttk.Label(frame, text="LP (Aktuell / Max):", background=self.colors["panel"]).grid(row=row, column=0, sticky="w", pady=5)
        lp_frame = ttk.Frame(frame, style="Card.TFrame")
        lp_frame.grid(row=row, column=1, sticky="ew", pady=5)

        e_lp = ttk.Entry(lp_frame, width=8)
        e_lp.insert(0, str(char.lp))
        e_lp.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(lp_frame, text="/", background=self.colors["panel"]).pack(side=tk.LEFT)

        e_max_lp = ttk.Entry(lp_frame, width=8)
        e_max_lp.insert(0, str(char.max_lp))
        e_max_lp.pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # RP (Aktuell / Max)
        ttk.Label(frame, text="RP (Aktuell / Max):", background=self.colors["panel"]).grid(row=row, column=0, sticky="w", pady=5)
        rp_frame = ttk.Frame(frame, style="Card.TFrame")
        rp_frame.grid(row=row, column=1, sticky="ew", pady=5)

        e_rp = ttk.Entry(rp_frame, width=8)
        e_rp.insert(0, str(char.rp))
        e_rp.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(rp_frame, text="/", background=self.colors["panel"]).pack(side=tk.LEFT)

        e_max_rp = ttk.Entry(rp_frame, width=8)
        e_max_rp.insert(0, str(char.max_rp))
        e_max_rp.pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # SP (Aktuell / Max)
        ttk.Label(frame, text="SP (Aktuell / Max):", background=self.colors["panel"]).grid(row=row, column=0, sticky="w", pady=5)
        sp_frame = ttk.Frame(frame, style="Card.TFrame")
        sp_frame.grid(row=row, column=1, sticky="ew", pady=5)

        e_sp = ttk.Entry(sp_frame, width=8)
        e_sp.insert(0, str(char.sp))
        e_sp.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(sp_frame, text="/", background=self.colors["panel"]).pack(side=tk.LEFT)

        e_max_sp = ttk.Entry(sp_frame, width=8)
        e_max_sp.insert(0, str(char.max_sp))
        e_max_sp.pack(side=tk.LEFT, padx=(5, 0))
        row += 1

        # Initiative
        ttk.Label(frame, text="Initiative:", background=self.colors["panel"]).grid(row=row, column=0, sticky="w", pady=5)
        e_init = ttk.Entry(frame, width=10)
        e_init.insert(0, str(char.init))
        e_init.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        # Buttons
        btn_frame = ttk.Frame(edit_window, style="Card.TFrame")
        btn_frame.pack(fill=tk.X, pady=10, padx=20)

        entries = {
            "name": e_name, "type": e_type,
            "lp": e_lp, "max_lp": e_max_lp,
            "rp": e_rp, "max_rp": e_max_rp,
            "sp": e_sp, "max_sp": e_max_sp,
            "init": e_init
        }

        ttk.Button(btn_frame, text="Speichern", command=lambda: self.save_character_edits(edit_window, char, entries)).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Abbrechen", command=edit_window.destroy).pack(side=tk.RIGHT, padx=10)

    def save_character_edits(self, window, char, entries):
        """Speichert die Änderungen aus dem Bearbeiten-Fenster."""
        try:
            new_name = entries["name"].get()
            if not new_name:
                raise ValueError("Name darf nicht leer sein.")

            char.name = new_name
            char.char_type = entries["type"].get()

            char.lp = int(entries["lp"].get())
            char.max_lp = int(entries["max_lp"].get())

            char.rp = int(entries["rp"].get())
            char.max_rp = int(entries["max_rp"].get())

            char.sp = int(entries["sp"].get())
            char.max_sp = int(entries["max_sp"].get())

            char.init = int(entries["init"].get())

            self.tracker.update_listbox()
            self.tracker.log_message(f"✏ Charakter '{char.name}' wurde bearbeitet.")
            window.destroy()

        except ValueError as e:
            messagebox.showerror("Fehler", f"Ungültige Eingabe: {e}")
