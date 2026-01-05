import pytest
from unittest.mock import MagicMock, patch, mock_open

# Mock tkinter before import
@patch('tkinter.ttk.Frame')
def get_markdown_browser(MockFrame):
    from src.ui.components.markdown_browser import MarkdownBrowser
    
    mock_parent = MagicMock()
    mock_colors = {}
    mock_link_callback = MagicMock()
    
    with patch.object(MarkdownBrowser, '_setup_ui'):
        browser = MarkdownBrowser(mock_parent, "/fake/dir", mock_colors, mock_link_callback)
        # Manually mock UI elements the logic depends on
        browser.tree = MagicMock()
        browser.text_widget = MagicMock()
        browser.search_var = MagicMock()
        
    return browser

@pytest.fixture
def browser():
    """Provides a MarkdownBrowser instance with mocked UI elements."""
    return get_markdown_browser()

# --- load_tree Tests ---

@patch('src.ui.components.markdown_browser.glob.glob')
@patch('os.path.exists', return_value=True)
def test_load_tree_builds_hierarchy(mock_exists, mock_glob, browser):
    """Tests that load_tree correctly builds a nested structure in the treeview."""
    mock_files = [
        "/fake/dir/root.md",
        "/fake/dir/subdir/nested.md"
    ]
    mock_glob.return_value = mock_files
    
    # Mock the insert method to track calls
    insert_calls = []
    def mock_insert(*args, **kwargs):
        # Store a simplified representation of the call
        call_info = {
            "parent": args[0],
            "text": kwargs.get("text"),
            "values": kwargs.get("values")
        }
        insert_calls.append(call_info)
        # Return a unique ID for each item so it can be a parent
        return f"I{len(insert_calls)}"
        
    browser.tree.insert.side_effect = mock_insert
    
    browser.load_tree()
    
    assert len(insert_calls) == 3 # folder, nested file, root file
    
    # Check that the root file was inserted correctly
    root_file_call = next(c for c in insert_calls if c["text"] == "root")
    assert root_file_call["parent"] == ""
    assert root_file_call["values"][0] == "/fake/dir/root.md"
    
    # Check that the folder was created
    subdir_call = next(c for c in insert_calls if c["text"] == "subdir")
    assert subdir_call["parent"] == ""
    
    # Check that the nested file was inserted inside the folder
    nested_file_call = next(c for c in insert_calls if c["text"] == "nested")
    assert nested_file_call["parent"] == "I1" # Assumes subdir was the first item inserted

# --- _on_search_change Tests ---

@patch('src.ui.components.markdown_browser.glob.glob')
@patch('os.path.exists', return_value=True)
def test_on_search_change_matches_filename(mock_exists, mock_glob, browser):
    """Tests that the search finds files by matching their filename."""
    mock_glob.return_value = ["/fake/dir/MyTopic.md", "/fake/dir/Another.md"]
    browser.search_var.get.return_value = "topic" # Search query
    
    browser._on_search_change()
    
    browser.tree.delete.assert_called()
    # Should only insert the matching file
    browser.tree.insert.assert_called_once_with("", "end", text="MyTopic", values=("/fake/dir/MyTopic.md",))

@patch('src.ui.components.markdown_browser.glob.glob')
@patch('os.path.exists', return_value=True)
def test_on_search_change_matches_content(mock_exists, mock_glob, browser):
    """Tests that the search finds files by matching their content."""
    mock_glob.return_value = ["/fake/dir/File1.md", "/fake/dir/File2.md"]
    browser.search_var.get.return_value = "secret" # Search query
    
    # Simulate file content using mock_open
    m = mock_open(read_data="some content")
    m.side_effect = [
        mock_open(read_data="this file contains the secret word").return_value,
        mock_open(read_data="this one does not").return_value
    ]

    with patch('builtins.open', m):
        browser._on_search_change()
        
    browser.tree.delete.assert_called()
    # Should only insert File1 which contains the secret word
    browser.tree.insert.assert_called_once_with("", "end", text="File1", values=("/fake/dir/File1.md",))

# --- display_content Test ---

@patch('src.ui.components.markdown_browser.MarkdownUtils')
def test_display_content(MockMarkdownUtils, browser):
    """Tests that display_content reads a file and uses MarkdownUtils to parse it."""
    filepath = "/fake/dir/test.md"
    mock_content = "# Title\nSome text."
    
    m = mock_open(read_data=mock_content)
    with patch('builtins.open', m):
        browser.display_content(filepath)
        
    m.assert_called_once_with(filepath, "r", encoding="utf-8")
    
    # Check that the text widget was updated
    browser.text_widget.config.assert_any_call(state="normal")
    browser.text_widget.delete.assert_called_once_with("1.0", "end")
    MockMarkdownUtils.parse_markdown.assert_called_once_with(mock_content, browser.text_widget)
    browser.text_widget.config.assert_any_call(state="disabled")
    
    # Check that the current file is set
    assert browser.current_file == filepath
