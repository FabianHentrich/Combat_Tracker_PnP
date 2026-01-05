import pytest
from src.utils.utils import generate_health_bar, format_time

# --- generate_health_bar Tests ---

@pytest.mark.parametrize("current, maximum, expected_bar", [
    (100, 100, "██████████"), # Full health
    (50, 100,  "█████░░░░░"), # Half health
    (0, 100,   "░░░░░░░░░░"), # Zero health
    (1, 100,   "░░░░░░░░░░"), # Almost zero health (still 0 blocks filled)
    (9, 100,   "░░░░░░░░░░"), # Still 0 blocks
    (10, 100,  "█░░░░░░░░░"), # First block filled
])
def test_generate_health_bar_various_levels(current, maximum, expected_bar):
    """Tests the visual representation of the health bar at different levels."""
    result = generate_health_bar(current, maximum, length=10)
    assert result.startswith(expected_bar)
    assert result.endswith(f" {current}/{maximum}")

def test_generate_health_bar_zero_max_hp():
    """Tests the edge case where maximum HP is zero or less."""
    result = generate_health_bar(0, 0)
    assert result == "💀 0/0"
    
    result_neg = generate_health_bar(-10, 0)
    assert result_neg == "💀 -10/0"

def test_generate_health_bar_negative_current_hp():
    """Tests that negative current HP results in an empty bar."""
    result = generate_health_bar(-50, 100)
    assert result.startswith("░░░░░░░░░░")
    assert result.endswith(" -50/100")

# --- format_time Tests ---

@pytest.mark.parametrize("seconds, expected_time", [
    (0, "00:00"),
    (5, "00:05"),   # Single digit seconds
    (59, "00:59"),  # Just under a minute
    (60, "01:00"),  # Exactly one minute
    (95, "01:35"),  # Mixed minutes and seconds
    (600, "10:00"), # Exactly ten minutes
])
def test_format_time(seconds, expected_time):
    """Tests the formatting of seconds into MM:SS format."""
    assert format_time(seconds) == expected_time

def test_format_time_float_input():
    """Tests that floating point seconds are correctly truncated."""
    assert format_time(59.9) == "00:59"
