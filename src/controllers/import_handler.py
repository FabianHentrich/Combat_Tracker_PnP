import tkinter as tk
from tkinter import messagebox, filedialog
import openpyxl
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from src.models.character import Character
from src.core.mechanics import wuerfle_initiative
from src.utils.logger import setup_logging
from src.ui.components.dialogs.import_dialogs import ImportPreviewDialog, ImportDetailDialog
from src.config.defaults import MAX_GEW

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager

logger = setup_logging()

class ImportHandler:
    """
    Verwaltet den Import von Charakterdaten aus externen Quellen (z.B. Excel).
    Nutzt separate Dialog-Klassen für die UI.
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', root: tk.Tk, colors: Dict[str, str]):
        self.engine = engine
        self.history_manager = history_manager
        self.root = root
        self.colors = colors

    def load_from_excel(self, file_path: Optional[str] = None) -> None:
        """
        Lädt Gegnerdaten aus einer Excel-Datei.
        Öffnet einen Dateidialog, falls kein Pfad angegeben ist.
        Validiert die Spalten und öffnet das Vorschaufenster.
        """
        self.history_manager.save_snapshot()

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

            # Öffne Vorschau-Dialog
            ImportPreviewDialog(self.root, data, self.colors, self.on_preview_confirmed)

        except Exception as e:
            logger.error(f"Fehler beim Laden der Excel-Datei: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

    def on_preview_confirmed(self, expanded_data: List[Dict[str, Any]]) -> None:
        """Callback, wenn die erste Vorschau bestätigt wurde."""
        if not expanded_data:
            return

        # Öffne Detail-Dialog
        ImportDetailDialog(self.root, expanded_data, self.colors, self.on_details_confirmed)

    def on_details_confirmed(self, final_data: List[Dict[str, Any]]) -> None:
        """Callback, wenn der Import finalisiert wird."""
        count_imported = 0
        try:
            for entry in final_data:
                name = entry["name"]
                char_type = entry["type"]
                lp = entry["lp"]
                rp = entry["rp"]
                sp = entry["sp"]
                gew = entry["gew"]
                if gew > MAX_GEW:
                    gew = MAX_GEW
                level = entry.get("level", 0)

                # Init würfeln
                init = wuerfle_initiative(gew)

                new_char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type, level=level)
                self.engine.insert_character(new_char)
                count_imported += 1

            self.engine.log(f"{count_imported} Charaktere erfolgreich importiert.")

        except Exception as e:
            logger.error(f"Fehler beim Importieren: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Importieren: {e}")
