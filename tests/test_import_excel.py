import pytest
from unittest.mock import MagicMock, patch
from src.controllers.import_handler import ImportHandler

def test_load_from_excel_success():
    with patch('openpyxl.load_workbook') as mock_load:
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_load.return_value = mock_wb
        mock_wb.active = mock_sheet

        # Mock Header Row (sheet[1])
        # sheet[1] returns a tuple of cells
        cell1 = MagicMock(); cell1.value = "Name"
        cell2 = MagicMock(); cell2.value = "HP"
        cell3 = MagicMock(); cell3.value = "Ruestung"
        cell4 = MagicMock(); cell4.value = "Schild"
        cell5 = MagicMock(); cell5.value = "Gewandtheit"

        mock_sheet.__getitem__.return_value = (cell1, cell2, cell3, cell4, cell5)

        # Mock Data Rows (iter_rows)
        # values_only=True returns tuples of values
        mock_sheet.iter_rows.return_value = [
            ("Goblin", 10, 2, 0, 3)
        ]

        handler = ImportHandler(MagicMock(), MagicMock(), MagicMock(), {})
        handler.show_import_preview = MagicMock()

        handler.load_from_excel("dummy.xlsx")

        handler.show_import_preview.assert_called_once()
        data = handler.show_import_preview.call_args[0][0]
        assert len(data) == 1
        assert data[0]["Name"] == "Goblin"
        assert data[0]["HP"] == 10
        assert data[0]["Gewandtheit"] == 3

def test_load_from_excel_missing_columns():
    with patch('openpyxl.load_workbook') as mock_load:
        mock_wb = MagicMock()
        mock_sheet = MagicMock()
        mock_load.return_value = mock_wb
        mock_wb.active = mock_sheet

        # Missing HP
        cell1 = MagicMock(); cell1.value = "Name"

        mock_sheet.__getitem__.return_value = (cell1,)

        handler = ImportHandler(MagicMock(), MagicMock(), MagicMock(), {})
        # Mock messagebox to avoid popup during test
        with patch('src.controllers.import_handler.messagebox.showerror') as mock_error:
            handler.load_from_excel("dummy.xlsx")
            mock_error.assert_called()

