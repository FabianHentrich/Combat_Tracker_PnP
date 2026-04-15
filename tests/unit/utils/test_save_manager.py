import json
import os
import pytest
from src.utils.save_manager import SaveManager, DATA_VERSION


# ---------------------------------------------------------------------------
# Atomic write — temp file is replaced, not left behind
# ---------------------------------------------------------------------------

def test_atomic_write_produces_target_file(tmp_path):
    """save_to_file() must create the target file."""
    target = str(tmp_path / "combat.json")
    SaveManager.save_to_file(target, {"characters": []})
    assert os.path.exists(target)


def test_atomic_write_no_temp_file_remains(tmp_path):
    """The .tmp file must be cleaned up after a successful save."""
    target = str(tmp_path / "combat.json")
    SaveManager.save_to_file(target, {"characters": []})
    assert not os.path.exists(f"{target}.tmp")


def test_atomic_write_overwrites_existing_file(tmp_path):
    """Saving twice to the same path must overwrite without error."""
    target = str(tmp_path / "combat.json")
    SaveManager.save_to_file(target, {"round": 1})
    SaveManager.save_to_file(target, {"round": 2})
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    # The wrapper format is {"version": ..., "state": ...}
    assert data["state"]["round"] == 2


# ---------------------------------------------------------------------------
# Version wrapping
# ---------------------------------------------------------------------------

def test_saved_json_contains_version_key(tmp_path):
    """The raw JSON on disk must contain a top-level 'version' key."""
    target = str(tmp_path / "save.json")
    SaveManager.save_to_file(target, {"hp": 42})
    with open(target, "r", encoding="utf-8") as f:
        raw = json.load(f)
    assert "version" in raw
    assert raw["version"] == DATA_VERSION


def test_saved_json_contains_state_key(tmp_path):
    """The raw JSON on disk must contain a top-level 'state' key."""
    target = str(tmp_path / "save.json")
    payload = {"characters": [{"name": "Hero"}]}
    SaveManager.save_to_file(target, payload)
    with open(target, "r", encoding="utf-8") as f:
        raw = json.load(f)
    assert "state" in raw
    assert raw["state"] == payload


def test_load_unwraps_versioned_format(tmp_path):
    """load_from_file() must return only the 'state' portion of a versioned file."""
    target = str(tmp_path / "save.json")
    inner_state = {"round": 3, "characters": []}
    SaveManager.save_to_file(target, inner_state)
    loaded = SaveManager.load_from_file(target)
    assert loaded == inner_state


# ---------------------------------------------------------------------------
# Legacy (unwrapped) format
# ---------------------------------------------------------------------------

def test_load_handles_old_format_without_version(tmp_path):
    """Files without a 'version'/'state' envelope must be returned as-is."""
    target = str(tmp_path / "old_save.json")
    old_payload = {"characters": [], "turn_index": 0}
    with open(target, "w", encoding="utf-8") as f:
        json.dump(old_payload, f)
    loaded = SaveManager.load_from_file(target)
    assert loaded == old_payload


# ---------------------------------------------------------------------------
# Corrupted / missing files
# ---------------------------------------------------------------------------

def test_load_raises_on_missing_file(tmp_path):
    """load_from_file() must raise FileNotFoundError for a non-existent path."""
    missing = str(tmp_path / "does_not_exist.json")
    with pytest.raises(FileNotFoundError):
        SaveManager.load_from_file(missing)


def test_load_raises_on_corrupted_json(tmp_path):
    """load_from_file() must raise json.JSONDecodeError for invalid JSON content."""
    target = str(tmp_path / "corrupt.json")
    with open(target, "w", encoding="utf-8") as f:
        f.write("{ this is not : valid json !!!")
    with pytest.raises(json.JSONDecodeError):
        SaveManager.load_from_file(target)


# ---------------------------------------------------------------------------
# Directory creation
# ---------------------------------------------------------------------------

def test_save_creates_missing_directory(tmp_path):
    """save_to_file() must create parent directories that do not yet exist."""
    target = str(tmp_path / "subdir" / "nested" / "save.json")
    SaveManager.save_to_file(target, {"ok": True})
    assert os.path.exists(target)
