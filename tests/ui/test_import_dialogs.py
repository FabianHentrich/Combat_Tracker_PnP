import pytest
from unittest.mock import MagicMock, patch
import tkinter as tk
from src.ui.components.dialogs.import_dialogs import ImportPreviewDialog, ImportDetailDialog

@pytest.fixture
def mock_root():
    root = MagicMock()
    return root

@pytest.fixture
def colors():
    return {"bg": "white", "panel": "grey", "fg": "black"}

def test_import_preview_dialog_init(mock_root, colors):
    data = [{"Name": "Test", "HP": 10, "Ruestung": 0, "Schild": 0, "Gewandtheit": 1}]

    with patch('src.ui.components.dialogs.import_dialogs.tk.Toplevel'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Frame'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Label'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Entry'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Combobox'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Button'), \
         patch('src.ui.components.dialogs.import_dialogs.tk.Canvas'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Scrollbar'):

        dialog = ImportPreviewDialog(mock_root, data, colors, lambda x: None)
        assert dialog.data == data

def test_import_detail_dialog_init(mock_root, colors):
    data = [{"Name": "Test", "Typ": "Gegner", "HP": 10, "Ruestung": 0, "Schild": 0, "Gewandtheit": 1}]

    with patch('src.ui.components.dialogs.import_dialogs.tk.Toplevel'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Frame'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Label'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Entry'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Combobox'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Button'), \
         patch('src.ui.components.dialogs.import_dialogs.tk.Canvas'), \
         patch('src.ui.components.dialogs.import_dialogs.ttk.Scrollbar'):

        dialog = ImportDetailDialog(mock_root, data, colors, lambda x: None)
        assert dialog.data == data

