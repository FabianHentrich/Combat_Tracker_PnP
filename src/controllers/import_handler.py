import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import openpyxl
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from src.models.character import Character
from src.utils.utils import wuerfle_initiative
from src.utils.logger import setup_logging
from src.models.enums import CharacterType
from src.utils.config import FONTS, WINDOW_SIZE

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager

logger = setup_logging()

class ImportHandler:
    """
    Verwaltet den Import von Charakterdaten aus externen Quellen (z.B. Excel).
    Bietet eine Vorschau- und Bearbeitungs-UI vor dem endgültigen Import.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', root: tk.Tk, colors: Dict[str, str]):
        self.engine = engine
        self.history_manager = history_manager
        self.root = root
        self.colors = colors
        self.import_entries: List[Dict[str, Any]] = []
        self.detail_entries: List[Dict[str, Any]] = []
        self.preview_window = None

    def load_from_excel(self, file_path: Optional[str] = None) -> None:
        """
        Lädt Gegnerdaten aus einer Excel-Datei.
        Öffnet einen Dateidialog, falls kein Pfad angegeben ist.
        Validiert die Spalten und öffnet das Vorschaufenster.
        """
        if not file_path:
            file_path = filedialog.askopenfilename(title="Gegnerdaten laden", filetypes=[("Excel Dateien", "*.xlsx")])
            if not file_path: return

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active

            # Header lesen (erste Zeile)
            headers = [cell.value for cell in sheet[1]]
            col_map = {name: i for i, name in enumerate(headers) if name}

            # Check for required columns
            required_columns = {"Name", "Ruestung", "Schild", "HP"}
            if not required_columns.issubset(col_map.keys()):
                missing = required_columns - set(col_map.keys())
                raise ValueError(f"Excel file is missing columns: {missing}")

            data = []
            # Iteriere ab Zeile 2
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Überspringe leere Zeilen (wenn Name leer ist)
                if not row[col_map["Name"]]:
                    continue

                entry = {
                    "Name": row[col_map["Name"]],
                    "HP": row[col_map["HP"]],
                    "Ruestung": row[col_map["Ruestung"]],
                    "Schild": row[col_map["Schild"]],
                    "Gewandtheit": row[col_map["Gewandtheit"]] if "Gewandtheit" in col_map else 1
                }
                data.append(entry)

            logger.info(f"Excel-Datei erfolgreich geladen: {file_path} ({len(data)} Zeilen)")
            self.show_import_preview(data)

        except Exception as e:
            logger.error(f"Fehler beim Laden der Excel-Datei: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

    def show_import_preview(self, data: List[Dict[str, Any]]) -> None:
        """
        Zeigt ein Vorschaufenster für den Import an (Schritt 1: Auswahl & Menge).
        Erstellt eine Liste basierend auf den geladenen Daten.
        """
        if self.preview_window and self.preview_window.winfo_exists():
            self.preview_window.lift()
            self.preview_window.focus_force()
            return

        preview_window = tk.Toplevel(self.root)
        self.preview_window = preview_window
        preview_window.title("Import Vorschau & Auswahl")
        preview_window.geometry(WINDOW_SIZE["import"])
        preview_window.configure(bg=self.colors["bg"])

        # Header
        ttk.Label(preview_window, text="Auswählen und anpassen", font=FONTS["xl"]).pack(pady=10)

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
        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW", "Anzahl"]
        header_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        widths = [15, 8, 5, 5, 5, 5, 10]
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=FONTS["bold"], width=widths[i], anchor="w").pack(side="left", padx=5)

        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=5)

        # Zeilen generieren
        self.import_entries = []

        for row in data:
            row_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
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

            # Anzahl (Spinbox)
            e_count = ttk.Entry(row_frame, width=widths[6])
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
        """
        Nimmt die Auswahl aus Schritt 1 und bereitet die Detail-Ansicht vor.
        Expandiert die Auswahl basierend auf der "Anzahl"-Spalte in individuelle Einträge.
        """
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
        """
        Schritt 2: Zeigt jeden einzelnen Charakter zur Bearbeitung an.
        Erlaubt das finale Anpassen von Werten vor dem Import.
        """
        window.title("Import - Detail Anpassung")

        # Header
        ttk.Label(window, text="Details anpassen", font=FONTS["xl"], background=self.colors["bg"]).pack(pady=10)
        ttk.Label(window, text="Hier können einzelne Charaktere final bearbeitet werden.", font=FONTS["main"], background=self.colors["bg"]).pack(pady=(0, 10))

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
        headers = ["Name", "Typ", "LP", "RP", "SP", "GEW"]
        header_frame = ttk.Frame(scrollable_frame, style="Card.TFrame")
        header_frame.pack(fill="x", pady=5)

        widths = [20, 10, 5, 5, 5, 5, 5]
        for i, col in enumerate(headers):
            ttk.Label(header_frame, text=col, font=FONTS["bold"], width=widths[i], anchor="w", background=self.colors["panel"]).pack(side="left", padx=5)

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
        """
        Führt den endgültigen Import durch.
        Erstellt Character-Objekte und fügt sie der Engine hinzu.
        """
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

                new_char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type)
                self.engine.insert_character(new_char)
                count_imported += 1

            # self.tracker.update_listbox() # Handled by engine event
            self.engine.log(f"{count_imported} Charaktere erfolgreich importiert.")
            window.destroy()

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Zahlenwerte in den Feldern verwenden.")
