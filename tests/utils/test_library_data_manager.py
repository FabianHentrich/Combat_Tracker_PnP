import pytest
from unittest.mock import MagicMock, patch, mock_open
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
    mock_entry = MagicMock(is_dir=lambda: True, name="custom", path="/mock/custom")
    with patch('os.path.exists', return_value=True), \
         patch('os.makedirs'), \
         patch('os.scandir', return_value=iter([mock_entry])):
        manager = LibraryDataManager()
        assert "custom" in manager.dirs

def test_get_files_in_category_caching(data_manager):
    """Tests that file lists are cached after the first access."""
    with patch('glob.glob', return_value=["file1.md"]) as mock_glob:
        # First call should trigger glob
        files1 = data_manager.get_files_in_category("rules")
        assert len(files1) == 1
        mock_glob.assert_called_once()
        
        # Second call should use cache and not trigger glob again
        files2 = data_manager.get_files_in_category("rules")
        assert len(files2) == 1
        mock_glob.assert_called_once() # Still only one call

def test_search_file_priority_exact_vs_partial(data_manager):
    """Tests that an exact match is preferred over a partial match."""
    # Both "Wolf" (exact) and "Dire Wolf" (partial) are potential matches for "Wolf"
    mock_files = ["/path/to/Dire Wolf.md", "/path/to/Wolf.md"]
    
    with patch('glob.glob', return_value=mock_files):
        result = data_manager.search_file("Wolf")
        assert result is not None
        category, path = result
        # It should return the exact match, not the first partial one it finds.
        assert path == "/path/to/Wolf.md"

def test_search_file_priority_filename_vs_content(data_manager):
    """Tests that a filename match is preferred over a content match."""
    # "Goblin" is a partial match in the filename, but an exact match in content.
    mock_files = ["/path/to/Goblin Champion.md", "/path/to/Army.md"]
    
    # Mock open to simulate content
    def open_side_effect(path, *args, **kwargs):
        if "Army.md" in path:
            return mock_open(read_data="This file contains Goblin.").return_value
        return mock_open(read_data="A strong champion.").return_value
        
    with patch('glob.glob', return_value=mock_files), \
         patch('builtins.open', side_effect=open_side_effect):
        
        result = data_manager.search_file("Goblin")
        assert result is not None
        category, path = result
        # It should return the filename match, not the content match.
        assert path == "/path/to/Goblin Champion.md"

def test_search_file_with_parentheses(data_manager):
    """Tests that suffixes in parentheses are correctly ignored for matching."""
    mock_files = ["/path/to/Bandit.md"]
    with patch('glob.glob', return_value=mock_files):
        # Search for "Bandit (Boss)" should find "Bandit.md"
        result = data_manager.search_file("Bandit (Boss)")
        assert result is not None
        _, path = result
        assert path == "/path/to/Bandit.md"

def test_search_file_not_found(data_manager):
    """Tests search with no possible match."""
    with patch('glob.glob', return_value=[]), \
         patch('builtins.open', mock_open(read_data="")):
        result = data_manager.search_file("NonExistent")
        assert result is None
