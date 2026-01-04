import pytest
from unittest.mock import MagicMock, patch, ANY
from src.controllers.import_handler import ImportHandler
from src.models.character import Character

@pytest.fixture
def mock_dependencies():
    """Erstellt gemockte Abhängigkeiten für den ImportHandler."""
    engine = MagicMock()
    history = MagicMock()
    root = MagicMock()
    colors = {}
    return engine, history, root, colors

@pytest.fixture
def mock_workbook():
    """Erstellt ein gemocktes openpyxl Workbook."""
    mock_sheet = MagicMock()
    # Header-Zeile
    header = [MagicMock(value="Name"), MagicMock(value="HP"), MagicMock(value="Ruestung"), MagicMock(value="Schild"), MagicMock(value="Gewandtheit")]
    # Daten-Zeilen
    row1 = [MagicMock(value="Goblin"), MagicMock(value=10), MagicMock(value=2), MagicMock(value=0), MagicMock(value=2)]
    row2 = [MagicMock(value="Orc"), MagicMock(value=25), MagicMock(value=5), MagicMock(value=0), MagicMock(value=1)]
    
    # Konfiguriere das Verhalten des Sheets
    # iter_rows(values_only=True) wird im Code verwendet
    mock_sheet.iter_rows.return_value = [
        ("Goblin", 10, 2, 0, 2),
        ("Orc", 25, 5, 0, 1)
    ]
    # __getitem__ wird für den Header verwendet
    mock_sheet.__getitem__.return_value = header

    mock_wb = MagicMock()
    mock_wb.active = mock_sheet
    return mock_wb

def test_load_from_excel_success(mock_dependencies, mock_workbook):
    """
    Testet den erfolgreichen Ladevorgang bis zum Aufruf des Preview-Dialogs.
    """
    engine, history, root, colors = mock_dependencies
    handler = ImportHandler(engine, history, root, colors)

    # Korrekte Patch-Ziele: Dort, wo die Funktion aufgerufen wird.
    with patch('src.controllers.import_handler.openpyxl.load_workbook', return_value=mock_workbook) as mock_load_wb, \
         patch('src.controllers.import_handler.filedialog.askopenfilename', return_value="dummy.xlsx") as mock_file_dialog, \
         patch('src.controllers.import_handler.ImportPreviewDialog') as MockPreviewDialog:
        
        handler.load_from_excel()

        # Prüfen, ob der Dateidialog aufgerufen wurde
        mock_file_dialog.assert_called_once()
        
        # Prüfen, ob die Datei geladen wurde
        mock_load_wb.assert_called_once_with("dummy.xlsx", data_only=True)
        
        # Prüfen, ob der History-Manager aufgerufen wurde
        history.save_snapshot.assert_called_once()

        # Prüfen, ob der Preview-Dialog mit den korrekten Daten aufgerufen wurde
        expected_data = [
            {'Name': 'Goblin', 'HP': 10, 'Ruestung': 2, 'Schild': 0, 'Gewandtheit': 2},
            {'Name': 'Orc', 'HP': 25, 'Ruestung': 5, 'Schild': 0, 'Gewandtheit': 1}
        ]
        MockPreviewDialog.assert_called_once_with(root, expected_data, colors, ANY)

def test_load_from_excel_missing_columns(mock_dependencies):
    """
    Testet, ob ein Fehler ausgelöst wird, wenn wichtige Spalten fehlen.
    """
    engine, history, root, colors = mock_dependencies
    handler = ImportHandler(engine, history, root, colors)

    # Erstelle ein Workbook, dem die "HP"-Spalte fehlt
    mock_sheet = MagicMock()
    header = [MagicMock(value="Name"), MagicMock(value="Ruestung")]
    mock_sheet.__getitem__.return_value = header
    mock_wb = MagicMock()
    mock_wb.active = mock_sheet

    # Korrekte Patch-Ziele
    with patch('src.controllers.import_handler.openpyxl.load_workbook', return_value=mock_wb), \
         patch('src.controllers.import_handler.filedialog.askopenfilename', return_value="bad.xlsx"), \
         patch('src.controllers.import_handler.messagebox.showerror') as mock_showerror:
        
        handler.load_from_excel()
        
        # Prüfen, ob eine Fehlermeldung angezeigt wurde
        mock_showerror.assert_called_once()
        # Prüfen, ob der Fehler die fehlenden Spalten erwähnt
        call_args, _ = mock_showerror.call_args
        assert "missing columns" in call_args[1]
        assert "HP" in call_args[1]

def test_on_details_confirmed_imports_characters(mock_dependencies):
    """
    Testet den finalen Schritt: Werden aus den Dialog-Daten Charaktere erstellt?
    """
    engine, history, root, colors = mock_dependencies
    handler = ImportHandler(engine, history, root, colors)

    # Simulierte Daten, die vom Detail-Dialog zurückkommen
    final_data = [
        {'name': 'Goblin', 'type': 'Gegner', 'lp': 10, 'rp': 2, 'sp': 0, 'gew': 2, 'level': 1},
        {'name': 'Orc', 'type': 'Gegner', 'lp': 25, 'rp': 5, 'sp': 0, 'gew': 1, 'level': 3}
    ]

    # Mock für wuerfle_initiative, damit wir einen festen Wert haben
    with patch('src.controllers.import_handler.wuerfle_initiative', return_value=15):
        handler.on_details_confirmed(final_data)

    # Prüfen, ob die Charaktere korrekt an die Engine übergeben wurden
    assert engine.insert_character.call_count == 2
    
    # Erster Charakter
    call_args1, _ = engine.insert_character.call_args_list[0]
    char1 = call_args1[0]
    assert isinstance(char1, Character)
    assert char1.name == "Goblin"
    assert char1.max_lp == 10
    assert char1.gew == 2
    assert char1.level == 1
    assert char1.init == 15 # Gemockter Wert

    # Zweiter Charakter
    call_args2, _ = engine.insert_character.call_args_list[1]
    char2 = call_args2[0]
    assert isinstance(char2, Character)
    assert char2.name == "Orc"
    assert char2.max_lp == 25
    assert char2.gew == 1
    assert char2.level == 3
    assert char2.init == 15 # Gemockter Wert

    # Prüfen, ob eine Erfolgsmeldung geloggt wurde
    engine.log.assert_called_with("2 Charaktere erfolgreich importiert.")
