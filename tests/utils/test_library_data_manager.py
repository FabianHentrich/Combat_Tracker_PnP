import pytest
from unittest.mock import MagicMock, patch
from src.utils.library_data_manager import LibraryDataManager

@pytest.fixture
def data_manager():
    # Reset singleton
    LibraryDataManager._instance = None
    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'):
        manager = LibraryDataManager()
        return manager

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

