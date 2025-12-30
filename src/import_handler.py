import tkinter as tk
from tkinter import ttk, messagebox
from .character import Character
from .utils import wuerfle_initiative

class ImportHandler:
    def __init__(self, tracker, root, colors):
        self.tracker = tracker
        self.root = root
        self.colors = colors
        self.import_entries = []
        self.detail_entries = []

    def show_import_preview(self, df):
        """Zeigt ein Vorschaufenster für den Import an (Schritt 1: Auswahl & Menge)."""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Import Vorschau & Auswahl")
        preview_window.geometry("900x600")
        preview_window.configure(bg=self.colors["bg"])

        # Header
        ttk.Label(preview_window, text="Gegner auswählen und anpassen", font=('Segoe UI', 14, 'bold'), background=self.colors["bg"]).pack(pady=10)

        # Scrollable Frame für die Liste
        canvas = tk.Canvas(preview_window, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        # Spaltenüberschriften
        headers = ["Name", "Typ", "LP", "RP", "SP", "Gewandtheit", "Anzahl"]
        header_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        widths = [20, 10, 8, 8, 8, 12, 8]
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=('Segoe UI', 10, 'bold'), width=widths[i], anchor="w", background=self.colors["panel"]).pack(side="left", padx=5)

        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=5)

        # Zeilen generieren
        self.import_entries = []

        for _, row in df.iterrows():
            row_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=2)

            # Name
            e_name = ttk.Entry(row_frame, width=20)
            e_name.insert(0, str(row["Name"]))
            e_name.pack(side="left", padx=5)

            # Typ
            e_type = ttk.Combobox(row_frame, values=["Spieler", "Gegner", "NPC"], width=10, state="readonly")
            e_type.set("Gegner")
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

            # Gewandtheit (Init Basis)
            e_gew = ttk.Entry(row_frame, width=12)
            e_gew.insert(0, str(row["Gewandtheit"]))
            e_gew.pack(side="left", padx=5)

            # Anzahl (Spinbox)
            e_count = ttk.Entry(row_frame, width=8)
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
                "count": e_count
            })

        # Import Button
        btn_frame = ttk.Frame(preview_window, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=10, padx=10)

        ttk.Button(btn_frame, text="Weiter zur Detail-Anpassung", command=lambda: self.prepare_detail_view(preview_window)).pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=preview_window.destroy).pack(side="right", padx=10)

    def prepare_detail_view(self, window):
        """Nimmt die Auswahl aus Schritt 1 und bereitet die Detail-Ansicht vor."""
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
                            "Gewandtheit": gew
                        })

            if not expanded_data:
                messagebox.showinfo("Info", "Keine Gegner ausgewählt.")
                return

            # Fensterinhalt löschen für Schritt 2
            for widget in window.winfo_children():
                widget.destroy()

            self.show_detail_preview(window, expanded_data)

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte verwenden.")

    def show_detail_preview(self, window, data):
        """Schritt 2: Zeigt jeden einzelnen Charakter zur Bearbeitung an."""
        window.title("Import - Detail Anpassung")

        # Header
        ttk.Label(window, text="Details anpassen", font=('Segoe UI', 14, 'bold'), background=self.colors["bg"]).pack(pady=10)
        ttk.Label(window, text="Hier können einzelne Charaktere final bearbeitet werden.", font=('Segoe UI', 10), background=self.colors["bg"]).pack(pady=(0, 10))

        # Canvas Setup
        canvas = tk.Canvas(window, bg=self.colors["panel"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style="Card.TFrame")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        # Header Zeile
        headers = ["Name", "Typ", "LP", "RP", "SP", "Gewandtheit"]
        header_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        widths = [20, 10, 8, 8, 8, 12]
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=('Segoe UI', 10, 'bold'), width=widths[i], anchor="w", background=self.colors["panel"]).pack(side="left", padx=5)

        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=5)

        self.detail_entries = []

        for row in data:
            row_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
            row_frame.pack(fill="x", pady=2)

            # Name
            e_name = ttk.Entry(row_frame, width=20)
            e_name.insert(0, str(row["Name"]))
            e_name.pack(side="left", padx=5)

            # Typ
            e_type = ttk.Combobox(row_frame, values=["Spieler", "Gegner", "NPC"], width=10, state="readonly")
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
                "gew": e_gew
            }

            # Command setzen mit Referenz auf das Objekt
            btn_del.configure(command=lambda f=row_frame, obj=entry_obj: self.remove_detail_row(f, obj))

            self.detail_entries.append(entry_obj)

        # Footer Buttons
        btn_frame = ttk.Frame(window, style="Card.TFrame")
        btn_frame.pack(fill="x", pady=10, padx=10)

        ttk.Button(btn_frame, text="Alle Importieren", command=lambda: self.finalize_import(window)).pack(side="right")
        ttk.Button(btn_frame, text="Abbrechen", command=window.destroy).pack(side="right", padx=10)

    def remove_detail_row(self, frame, entry_obj):
        """Entfernt eine Zeile aus der Detailansicht."""
        frame.destroy()
        if entry_obj in self.detail_entries:
            self.detail_entries.remove(entry_obj)

    def finalize_import(self, window):
        """Führt den endgültigen Import durch."""
        count_imported = 0
        try:
            for entry in self.detail_entries:
                name = entry["name"].get()
                char_type = entry["type"].get()
                lp = int(entry["lp"].get())
                rp = int(entry["rp"].get())
                sp = int(entry["sp"].get())
                gew = int(entry["gew"].get())

                # Init würfeln
                init = wuerfle_initiative(gew)

                new_char = Character(name, lp, rp, sp, init, char_type)
                self.tracker.insert_character(new_char)
                count_imported += 1

            self.tracker.update_listbox()
            self.tracker.log_message(f"{count_imported} Charaktere erfolgreich importiert.")
            window.destroy()

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte in den Feldern verwenden.")

