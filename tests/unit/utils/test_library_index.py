import os
import pytest
from unittest.mock import MagicMock, patch

from src.utils.db_manager import DatabaseManager
from src.utils.library_index import LibraryIndex


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_index(db):
    """Creates a LibraryIndex that uses the given in-memory DB, bypassing sync."""
    LibraryIndex._instance = None
    idx = LibraryIndex.__new__(LibraryIndex)
    idx._db = db
    idx.dirs = {}
    idx._initialized = True
    return idx


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    DatabaseManager._instance = None
    manager = DatabaseManager(":memory:")
    yield manager
    manager.close()


@pytest.fixture
def index(db):
    idx = make_index(db)
    yield idx
    LibraryIndex._instance = None


# ---------------------------------------------------------------------------
# Helper: insert a file row directly
# ---------------------------------------------------------------------------

def insert_file(db, path, filename, category, folder=None, content="", last_modified=0.0, tags=""):
    import hashlib
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    with db.conn:
        db.conn.execute(
            """INSERT INTO library_files
               (path, filename, category, folder, content, content_hash, last_modified, tags)
               VALUES (?,?,?,?,?,?,?,?)""",
            (path, filename, category, folder, content, content_hash, last_modified, tags),
        )
    # Rebuild FTS after direct insert
    with db.conn:
        db.conn.execute("INSERT INTO library_fts(library_fts) VALUES('rebuild')")


# ---------------------------------------------------------------------------
# get_files_in_category
# ---------------------------------------------------------------------------

def test_get_files_in_category_returns_paths(index, db):
    insert_file(db, "/data/items/Sword.md", "Sword", "items")
    insert_file(db, "/data/items/Shield.md", "Shield", "items")
    insert_file(db, "/data/enemies/Wolf.md", "Wolf", "enemies")

    files = index.get_files_in_category("items")
    assert len(files) == 2
    assert all("items" in p for p in files)


def test_get_files_in_category_empty(index):
    assert index.get_files_in_category("nonexistent") == []


# ---------------------------------------------------------------------------
# search_file — exact match
# ---------------------------------------------------------------------------

def test_search_exact_match(index, db):
    insert_file(db, "/data/enemies/Wolf.md", "Wolf", "enemies")
    result = index.search_file("Wolf")
    assert result is not None
    category, path = result
    assert category == "enemies"
    assert path == "/data/enemies/Wolf.md"


def test_search_exact_match_case_insensitive(index, db):
    insert_file(db, "/data/enemies/Wolf.md", "Wolf", "enemies")
    result = index.search_file("wolf")
    assert result is not None
    assert result[1] == "/data/enemies/Wolf.md"


def test_search_exact_preferred_over_partial(index, db):
    """Exact match must win over a partial match with a different name."""
    insert_file(db, "/data/enemies/Dire Wolf.md", "Dire Wolf", "enemies")
    insert_file(db, "/data/enemies/Wolf.md", "Wolf", "enemies")
    category, path = index.search_file("Wolf")
    assert path == "/data/enemies/Wolf.md"


# ---------------------------------------------------------------------------
# search_file — parenthesis stripping
# ---------------------------------------------------------------------------

def test_search_strips_parenthetical_suffix(index, db):
    insert_file(db, "/data/enemies/Bandit.md", "Bandit", "enemies")
    result = index.search_file("Bandit (Boss)")
    assert result is not None
    assert result[1] == "/data/enemies/Bandit.md"


# ---------------------------------------------------------------------------
# search_file — partial match
# ---------------------------------------------------------------------------

def test_search_partial_match(index, db):
    insert_file(db, "/data/enemies/Goblin Champion.md", "Goblin Champion", "enemies")
    result = index.search_file("Goblin")
    assert result is not None
    assert "Goblin Champion" in result[1]


# ---------------------------------------------------------------------------
# search_file — FTS full-text
# ---------------------------------------------------------------------------

def test_search_fts_content_match(index, db):
    """FTS fallback must find a file by content when filename does not match."""
    insert_file(
        db,
        "/data/enemies/Unknown.md",
        "Unknown",
        "enemies",
        content="This creature is known as the Shadowbeast.",
    )
    result = index.search_file("Shadowbeast")
    assert result is not None
    assert result[1] == "/data/enemies/Unknown.md"


def test_search_not_found(index):
    result = index.search_file("CompletelyMissing")
    assert result is None


# ---------------------------------------------------------------------------
# sync — mtime-based incremental update
# ---------------------------------------------------------------------------

def test_sync_indexes_new_files(db):
    """Files not yet in DB are picked up on sync."""
    idx = make_index(db)
    idx.dirs = {"items": "/fake/items"}

    mock_files = ["/fake/items/Sword.md"]
    with patch("glob.glob", return_value=mock_files), \
         patch("os.path.getmtime", return_value=1000.0), \
         patch("os.path.exists", return_value=True), \
         patch("builtins.open", create=True) as mock_open_:
        mock_open_.return_value.__enter__.return_value.read.return_value = "# Sword"
        updated = idx.sync()

    assert updated == 1
    files = idx.get_files_in_category("items")
    assert "/fake/items/Sword.md" in files

    LibraryIndex._instance = None


def test_sync_skips_unchanged_files(db):
    """Files whose mtime matches the DB are not re-read."""
    insert_file(db, "/fake/items/Sword.md", "Sword", "items", last_modified=1000.0)
    idx = make_index(db)
    idx.dirs = {"items": "/fake/items"}

    with patch("glob.glob", return_value=["/fake/items/Sword.md"]), \
         patch("os.path.getmtime", return_value=1000.0), \
         patch("builtins.open", create=True) as mock_open_:
        updated = idx.sync()

    mock_open_.assert_not_called()
    assert updated == 0

    LibraryIndex._instance = None


def test_sync_removes_stale_entries(db):
    """Files deleted from disk are removed from the DB index."""
    insert_file(db, "/fake/items/Deleted.md", "Deleted", "items", last_modified=999.0)
    idx = make_index(db)
    idx.dirs = {"items": "/fake/items"}

    # Filesystem shows no files
    with patch("glob.glob", return_value=[]), \
         patch("os.path.getmtime", return_value=999.0):
        idx.sync()

    assert idx.get_files_in_category("items") == []

    LibraryIndex._instance = None


def test_sync_reindexes_modified_files(db):
    """Files with a changed mtime are re-read and their content updated."""
    insert_file(db, "/fake/items/Sword.md", "Sword", "items", last_modified=1000.0)
    idx = make_index(db)
    idx.dirs = {"items": "/fake/items"}

    with patch("glob.glob", return_value=["/fake/items/Sword.md"]), \
         patch("os.path.getmtime", return_value=2000.0), \
         patch("builtins.open", create=True) as mock_open_:
        mock_open_.return_value.__enter__.return_value.read.return_value = "# Updated content"
        updated = idx.sync()

    assert updated == 1
    row = db.conn.execute(
        "SELECT content FROM library_files WHERE path = ?", ("/fake/items/Sword.md",)
    ).fetchone()
    assert row["content"] == "# Updated content"

    LibraryIndex._instance = None


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------

def test_parse_frontmatter_extracts_tags(index):
    body, tags = index._parse_frontmatter("---\ntags: boss, undead\n---\n# Content")
    assert tags == "boss, undead"
    assert body.startswith("# Content")


def test_parse_frontmatter_no_frontmatter(index):
    body, tags = index._parse_frontmatter("# Just content")
    assert body == "# Just content"
    assert tags == ""


def test_parse_frontmatter_missing_tags_key(index):
    body, tags = index._parse_frontmatter("---\nauthor: me\n---\n# Content")
    assert tags == ""
    assert "# Content" in body


def test_parse_frontmatter_unclosed(index):
    """Unclosed frontmatter is treated as no frontmatter."""
    text = "---\ntags: boss\n# Content"
    body, tags = index._parse_frontmatter(text)
    assert body == text
    assert tags == ""


# ---------------------------------------------------------------------------
# get_backlinks
# ---------------------------------------------------------------------------

def test_get_backlinks_finds_references(index, db):
    insert_file(db, "/data/npcs/Merlin.md", "Merlin", "npcs")
    insert_file(db, "/data/quests/TheWizard.md", "TheWizard", "quests",
                content="You must find [[Merlin]] in the tower.")
    insert_file(db, "/data/locations/Tower.md", "Tower", "locations",
                content="[[Merlin]] lives here.")

    backlinks = index.get_backlinks("/data/npcs/Merlin.md")
    paths = [b["path"] for b in backlinks]
    assert "/data/quests/TheWizard.md" in paths
    assert "/data/locations/Tower.md" in paths


def test_get_backlinks_excludes_self(index, db):
    insert_file(db, "/data/npcs/Merlin.md", "Merlin", "npcs",
                content="[[Merlin]] is a legend.")
    backlinks = index.get_backlinks("/data/npcs/Merlin.md")
    assert backlinks == []


def test_get_backlinks_none_found(index, db):
    insert_file(db, "/data/npcs/Nobody.md", "Nobody", "npcs")
    assert index.get_backlinks("/data/npcs/Nobody.md") == []


# ---------------------------------------------------------------------------
# get_all_tags / get_files_by_tag
# ---------------------------------------------------------------------------

def test_get_all_tags_returns_sorted_unique(index, db):
    insert_file(db, "/a.md", "a", "items", tags="boss, undead")
    insert_file(db, "/b.md", "b", "items", tags="undead, dragon")
    tags = index.get_all_tags()
    assert tags == sorted({"boss", "undead", "dragon"})


def test_get_all_tags_empty(index):
    assert index.get_all_tags() == []


def test_get_files_by_tag_exact_match(index, db):
    insert_file(db, "/a.md", "a", "items", tags="boss, undead")
    insert_file(db, "/b.md", "b", "items", tags="undead")
    insert_file(db, "/c.md", "c", "items", tags="dragon")

    result = index.get_files_by_tag("undead")
    assert "/a.md" in result
    assert "/b.md" in result
    assert "/c.md" not in result


def test_get_files_by_tag_no_partial_match(index, db):
    """'boss' must not match a file tagged 'miniboss'."""
    insert_file(db, "/a.md", "a", "items", tags="miniboss")
    result = index.get_files_by_tag("boss")
    assert "/a.md" not in result