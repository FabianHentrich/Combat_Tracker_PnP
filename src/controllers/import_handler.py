import tkinter as tk
from tkinter import messagebox, filedialog
import openpyxl
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from src.models.character import Character
from src.core.mechanics import wuerfle_initiative
from src.utils.logger import setup_logging
from src.ui.components.dialogs.import_dialogs import ImportPreviewDialog, ImportDetailDialog
from src.config.defaults import MAX_GEW
from src.utils.localization import translate
from src.models.enums import StatType

if TYPE_CHECKING:
    from src.core.engine import CombatEngine
    from src.core.history import HistoryManager

logger = setup_logging()

class ImportHandler:
    """
    Manages importing character data from external sources (e.g., Excel).
    """
    def __init__(self, engine: 'CombatEngine', history_manager: 'HistoryManager', root: tk.Tk, colors: Dict[str, str]):
        self.engine: 'CombatEngine' = engine
        self.history_manager: 'HistoryManager' = history_manager
        self.root: tk.Tk = root
        self.colors = colors

    def load_from_excel(self, file_path: Optional[str] = None) -> None:
        """
        Loads enemy data from an Excel file.
        Opens a file dialog if no path is provided.
        Validates columns and opens the preview window.
        """
        self.history_manager.save_snapshot()

        if not file_path:
            file_path = filedialog.askopenfilename(title=translate("dialog.file.load_enemy_data_title"), filetypes=[(translate("dialog.file.excel"), "*.xlsx")])
            if not file_path: return

        try:
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            sheet = workbook.active

            headers = [cell.value for cell in sheet[1]]
            col_map = {name: i for i, name in enumerate(headers) if name}

            required_columns = {"Name", "Ruestung", "Schild", "HP"}
            if not required_columns.issubset(col_map.keys()):
                missing = required_columns - set(col_map.keys())
                raise ValueError(f"{translate('messages.excel_missing_columns')}: {missing}")

            data = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                if not row[col_map["Name"]]:
                    continue

                entry = {
                    "Name": row[col_map["Name"]],
                    "HP": row[col_map["HP"]],
                    "Ruestung": row[col_map["Ruestung"]],
                    "Schild": row[col_map["Schild"]],
                    "Gewandtheit": row[col_map.get("Gewandtheit")] if "Gewandtheit" in col_map and row[col_map["Gewandtheit"]] is not None else 1
                }
                data.append(entry)

            logger.info(f"Excel file loaded successfully: {file_path} ({len(data)} rows)")
            ImportPreviewDialog(self.root, data, self.colors, self.on_preview_confirmed)

        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            messagebox.showerror(translate("dialog.error.title"), f"{translate('messages.error_loading_file')}: {e}")

    def on_preview_confirmed(self, expanded_data: List[Dict[str, Any]]) -> None:
        """Callback when the initial preview is confirmed."""
        if not expanded_data:
            return
        ImportDetailDialog(self.root, expanded_data, self.colors, self.on_details_confirmed)

    def on_details_confirmed(self, final_data: List[Dict[str, Any]]) -> None:
        """Callback when the import is finalized."""
        count_imported = 0
        try:
            for entry in final_data:
                name = entry[StatType.NAME.value]
                char_type = entry[StatType.TYPE.value]
                lp = entry[StatType.LP.value]
                rp = entry[StatType.RP.value]
                sp = entry[StatType.SP.value]
                gew = entry[StatType.GEW.value]
                if gew > MAX_GEW:
                    gew = MAX_GEW
                level = entry.get(StatType.LEVEL.value, 0)

                init = wuerfle_initiative(gew)

                new_char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type, level=level)
                self.engine.insert_character(new_char)
                count_imported += 1

            self.engine.log(translate("messages.characters_imported", count=count_imported))

        except Exception as e:
            logger.error(f"Error during import: {e}")
            messagebox.showerror(translate("dialog.error.title"), f"{translate('messages.error_during_import')}: {e}")

    def update_colors(self, colors: Dict[str, str]):
        self.colors = colors
