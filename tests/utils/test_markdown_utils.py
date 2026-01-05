import pytest
from unittest.mock import MagicMock, patch, call
from src.utils.markdown_utils import MarkdownUtils

@pytest.fixture
def text_widget():
    """Provides a MagicMock for a tkinter Text widget."""
    return MagicMock()

# --- parse_markdown Tests ---

def test_parse_markdown_headings(text_widget):
    """Tests that headings are correctly parsed and tagged."""
    text = "# Title 1\n## Title 2"
    MarkdownUtils.parse_markdown(text, text_widget)
    
    # Check that insert was called with the correct text and tags
    text_widget.insert.assert_any_call('end', "Title 1", ('h1',))
    text_widget.insert.assert_any_call('end', "Title 2", ('h2',))

def test_parse_markdown_bold_and_links(text_widget):
    """Tests that bold and link formatting are correctly applied."""
    text = "Some **bold** and a [[Link]]."
    MarkdownUtils.parse_markdown(text, text_widget)
    
    # Check the sequence of inserts
    expected_calls = [
        call('end', 'Some ', ()),
        call('end', 'bold', ('bold',)),
        call('end', ' and a ', ()),
        call('end', 'Link', ('link',)),
        call('end', '.', ()),
        call('end', '\n')
    ]
    text_widget.insert.assert_has_calls(expected_calls, any_order=False)

def test_parse_markdown_image(text_widget):
    """Testet, dass ein Bild erkannt und image_create aufgerufen wird."""
    mock_img = MagicMock()
    mock_img.width = 100
    mock_img.height = 100
    mock_img.resize.return_value = mock_img  # resize gibt sich selbst zurück
    with patch("src.utils.markdown_utils.Image.open", return_value=mock_img), \
         patch.object(text_widget, "winfo_width", return_value=500), \
         patch.object(text_widget, "image_create") as mock_image_create:
        text = "![](bild.png)"
        with patch("os.path.exists", return_value=True):
            MarkdownUtils.parse_markdown(text, text_widget, base_path="/fake/path")
        mock_image_create.assert_called_once()
        text_widget.insert.assert_any_call('end', '\n')

def test_parse_markdown_table(text_widget):
    """Testet, dass eine Markdown-Tabelle als ASCII-Tabelle eingefügt wird."""
    table_md = "| Kopf1 | Kopf2 |\n| Wert1 | Wert2 |"
    MarkdownUtils.parse_markdown(table_md, text_widget)
    # Prüfe, ob ASCII-Rahmen eingefügt wurden
    border_calls = [c for c in text_widget.insert.call_args_list if '┌' in c.args[1] or '┐' in c.args[1]]
    assert border_calls, "Tabellenrahmen wurden nicht eingefügt."
    # Prüfe, ob Tabellenzellen eingefügt wurden
    cell_calls = [c for c in text_widget.insert.call_args_list if 'Kopf1' in c.args[1] or 'Wert1' in c.args[1]]
    assert cell_calls, "Tabellenzellen wurden nicht eingefügt."

# --- display_folder_toc Tests ---

@patch('src.utils.markdown_utils.os.listdir')
@patch('src.utils.markdown_utils.os.path.isdir')
@patch('src.utils.markdown_utils.os.path.isfile', return_value=True)
def test_display_folder_toc(mock_isfile, mock_isdir, mock_listdir, text_widget):
    """Tests the creation of a table of contents for a folder."""
    mock_listdir.return_value = ["Subfolder", "File1.md", "Start.md"]
    # Make "Subfolder" a directory and others files
    mock_isdir.side_effect = lambda path: "Subfolder" in path
    
    MarkdownUtils.display_folder_toc("/fake/path", text_widget, {})
    
    # Check that the widget was cleared and state was managed
    text_widget.config.assert_any_call(state="normal")
    text_widget.delete.assert_called_once_with("1.0", "end")
    text_widget.config.assert_any_call(state="disabled")
    
    # Check that headers and links were inserted
    insert_calls = text_widget.insert.call_args_list
    inserted_text = "".join([c.args[1] for c in insert_calls])
    
    assert "Contents of" in inserted_text
    assert "Folders" in inserted_text
    assert "[[Subfolder]]" in inserted_text
    assert "Files" in inserted_text
    assert "[[File1]]" in inserted_text
    # "Start.md" should be ignored
    assert "[[Start]]" not in inserted_text

# --- parse_stats_from_markdown Tests ---

def test_parse_stats_from_markdown_simple():
    """Tests parsing of simple key-value stats."""
    content = "LP: 100\nRP: 20"
    stats = MarkdownUtils.parse_stats_from_markdown(content)
    assert stats["lp"] == 100
    assert stats["rp"] == 20

def test_parse_stats_from_markdown_pair(caplog):
    """
    Tests parsing of 'current/max' style stats.
    This also tests the identified bug where the key is 'lp' but the value is {'lp':..., 'rp':...}.
    This is likely not the intended behavior, but we test the current implementation.
    """
    content = "LP: 80/100"
    stats = MarkdownUtils.parse_stats_from_markdown(content)
    
    assert "lp" in stats
    assert isinstance(stats["lp"], dict)
    assert stats["lp"]["lp"] == 80
    assert stats["lp"]["rp"] == 100
