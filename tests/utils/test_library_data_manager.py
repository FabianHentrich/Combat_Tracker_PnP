import pytest
from unittest.mock import MagicMock, patch
from src.utils.library_data_manager import LibraryDataManager

@pytest.fixture
def data_manager():
    # Reset singleton
    LibraryDataManager._instance = None

    # Mock DirEntries for default folders so tests relying on them work
    default_folders = ["rules", "items", "enemies"]
    mock_entries = []
    for folder in default_folders:
        entry = MagicMock()
        entry.is_dir.return_value = True
        entry.name = folder
        entry.path = f"/mock/path/{folder}"
        mock_entries.append(entry)

    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('os.scandir', return_value=iter(mock_entries)):
        manager = LibraryDataManager()
        yield manager

def test_dynamic_directory_scanning():
    """Testet, ob neue Ordner dynamisch erkannt werden."""
    LibraryDataManager._instance = None

    mock_entry = MagicMock()
    mock_entry.is_dir.return_value = True
    mock_entry.name = "custom_category"
    mock_entry.path = "/mock/path/custom_category"

    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('os.scandir', return_value=iter([mock_entry])):

        manager = LibraryDataManager()
        assert "custom_category" in manager.dirs
        assert manager.dirs["custom_category"] == "/mock/path/custom_category"

def test_get_files_in_category(data_manager):
    """Testet das Abrufen von Dateien in einer Kategorie."""
    with patch('glob.glob', return_value=["path/to/file1.md", "path/to/file2.md"]):
        files = data_manager.get_files_in_category("rules")
        assert len(files) == 2
        assert "path/to/file1.md" in files

def test_search_file_exact(data_manager):
    """Testet die exakte Suche nach einer Datei."""
    with patch('glob.glob', return_value=["path/to/TestFile.md"]):
        # Mock get_files_in_category indirectly via glob
        result = data_manager.search_file("TestFile")
        assert result is not None
        category, path = result
        assert path == "path/to/TestFile.md"

def test_search_file_partial(data_manager):
    """Testet die Teilstring-Suche."""
    with patch('glob.glob', return_value=["path/to/LongFileName.md"]):
        result = data_manager.search_file("LongFile")
        assert result is not None
        _, path = result
        assert path == "path/to/LongFileName.md"

def test_search_file_not_found(data_manager):
    """Testet Suche ohne Treffer."""
    with patch('glob.glob', return_value=[]):
        result = data_manager.search_file("NonExistent")
        assert result is None

