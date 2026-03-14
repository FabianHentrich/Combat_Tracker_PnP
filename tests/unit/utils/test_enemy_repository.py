import json
import pytest
from unittest.mock import patch, mock_open

from src.utils.db_manager import DatabaseManager
from src.utils.enemy_repository import EnemyRepository


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """Provides a fresh in-memory DatabaseManager for each test."""
    DatabaseManager._instance = None
    manager = DatabaseManager(":memory:")
    yield manager
    manager.close()


@pytest.fixture
def repo(db):
    """Provides a clean EnemyRepository backed by the in-memory DB."""
    EnemyRepository._instance = None
    r = EnemyRepository.__new__(EnemyRepository)
    r._db = db
    r._initialized = True
    yield r
    EnemyRepository._instance = None


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def test_add_and_get_preset(repo):
    repo.add("Goblin", "Tiere", lp=10, rp=0, sp=0, gew=2, char_type="Gegner", level=1)
    preset = repo.get_preset("Goblin")
    assert preset is not None
    assert preset["lp"] == 10
    assert preset["type"] == "Gegner"  # char_type is renamed to 'type' on read


def test_get_preset_not_found(repo):
    assert repo.get_preset("NonExistent") is None


def test_add_returns_id(repo):
    row_id = repo.add("Wolf", "Tiere", lp=15)
    assert isinstance(row_id, int)
    assert row_id > 0


def test_update_preset(repo):
    row_id = repo.add("Goblin", "Tiere", lp=10)
    repo.update(row_id, lp=20, level=2)
    preset = repo.get_preset("Goblin")
    assert preset["lp"] == 20
    assert preset["level"] == 2


def test_update_ignores_unknown_fields(repo):
    """Unknown field names must not cause an error or corrupt the row."""
    row_id = repo.add("Goblin", "Tiere", lp=10)
    repo.update(row_id, lp=99, nonexistent_field="boom")
    assert repo.get_preset("Goblin")["lp"] == 99


def test_delete_preset(repo):
    row_id = repo.add("Goblin", "Tiere", lp=10)
    repo.delete(row_id)
    assert repo.get_preset("Goblin") is None


# ---------------------------------------------------------------------------
# flat_presets property
# ---------------------------------------------------------------------------

def test_flat_presets(repo):
    repo.add("Goblin", "Tiere", lp=10)
    repo.add("Wolf", "Tiere", lp=20)
    flat = repo.flat_presets
    assert "Goblin" in flat
    assert "Wolf" in flat
    assert flat["Goblin"]["lp"] == 10


# ---------------------------------------------------------------------------
# get_all_presets (hierarchical tree reconstruction)
# ---------------------------------------------------------------------------

def test_get_all_presets_flat_category(repo):
    repo.add("Goblin", "Tiere", lp=10)
    repo.add("Wolf", "Tiere", lp=20)
    tree = repo.get_all_presets()
    assert "Tiere" in tree
    assert "Goblin" in tree["Tiere"]
    assert "Wolf" in tree["Tiere"]


def test_get_all_presets_with_subcategory(repo):
    repo.add("Bandit", "Menschen", lp=15, subcategory="Räuber")
    repo.add("Söldner", "Menschen", lp=20, subcategory="Räuber")
    repo.add("Händler", "Menschen", lp=8)
    tree = repo.get_all_presets()
    assert "Räuber" in tree["Menschen"]
    assert "Bandit" in tree["Menschen"]["Räuber"]
    assert "Händler" in tree["Menschen"]


# ---------------------------------------------------------------------------
# get_by_filter
# ---------------------------------------------------------------------------

def test_get_by_filter_by_category(repo):
    repo.add("Goblin", "Tiere", lp=10, level=1)
    repo.add("Wolf", "Tiere", lp=20, level=3)
    repo.add("Bandit", "Menschen", lp=15, level=2)
    results = repo.get_by_filter(category="Tiere")
    names = [r["name"] for r in results]
    assert "Goblin" in names
    assert "Wolf" in names
    assert "Bandit" not in names


def test_get_by_filter_by_level_range(repo):
    repo.add("Goblin", "Tiere", lp=10, level=1)
    repo.add("Wolf", "Tiere", lp=20, level=3)
    repo.add("Dragon", "Drachen", lp=100, level=10)
    results = repo.get_by_filter(level_min=2, level_max=5)
    names = [r["name"] for r in results]
    assert "Wolf" in names
    assert "Goblin" not in names
    assert "Dragon" not in names


def test_get_by_filter_by_char_type(repo):
    repo.add("Goblin", "Tiere", lp=10, char_type="Gegner")
    repo.add("Händler", "Menschen", lp=8, char_type="NPC")
    results = repo.get_by_filter(char_type="NPC")
    assert all(r["type"] == "NPC" for r in results)
    assert len(results) == 1


def test_categories(repo):
    repo.add("Goblin", "Tiere", lp=10)
    repo.add("Wolf", "Tiere", lp=20)
    repo.add("Bandit", "Menschen", lp=15)
    cats = repo.categories()
    assert "Tiere" in cats
    assert "Menschen" in cats
    assert len(cats) == 2


# ---------------------------------------------------------------------------
# Migration from JSON
# ---------------------------------------------------------------------------

def test_import_from_json(repo):
    mock_data = {
        "Gegner": {
            "Tiere": {
                "Wolf": {"lp": 20, "rp": 0, "sp": 0, "gew": 3, "type": "Gegner", "level": 2},
                "Bär": {"lp": 35, "rp": 2, "sp": 0, "gew": 4, "type": "Gegner", "level": 3},
            }
        }
    }
    mock_json = json.dumps(mock_data)
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_json)):
        count = repo.import_from_json("dummy.json")

    assert count == 2
    assert repo.get_preset("Wolf") is not None
    assert repo.get_preset("Bär")["lp"] == 35


def test_import_from_json_skips_existing(repo):
    """Importing twice must not create duplicates."""
    mock_data = {"Gegner": {"Tiere": {"Wolf": {"lp": 20, "type": "Gegner", "level": 1}}}}
    mock_json = json.dumps(mock_data)
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_json)):
        repo.import_from_json("dummy.json")
        second = repo.import_from_json("dummy.json")

    assert second == 0  # no new rows
    assert len(repo.flat_presets) == 1


def test_import_from_json_file_not_found(repo):
    with patch("os.path.exists", return_value=False):
        count = repo.import_from_json("missing.json")
    assert count == 0


def test_import_from_json_bad_json(repo):
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data="not valid json")):
        count = repo.import_from_json("bad.json")
    assert count == 0


def test_import_nested_subcategory(repo):
    """JSON with three nesting levels → preset stored with subcategory."""
    mock_data = {
        "Gegner": {
            "Menschen": {
                "Räuber": {
                    "Bandit": {"lp": 15, "type": "Gegner", "level": 1}
                }
            }
        }
    }
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=json.dumps(mock_data))):
        repo.import_from_json("dummy.json")

    preset = repo.get_preset("Bandit")
    assert preset is not None
    row = repo._db.conn.execute("SELECT * FROM enemies WHERE name='Bandit'").fetchone()
    assert row["category"] == "Menschen"
    assert row["subcategory"] == "Räuber"