import pytest
import sys
import os
from unittest.mock import patch

# Füge das src Verzeichnis zum Pfad hinzu
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils import get_wuerfel_from_gewandtheit, wuerfle_initiative, roll_exploding_dice

def test_gewandtheit_mapping():
    """
    Testet das Mapping von Gewandtheit zu Würfelgröße.
    """
    assert get_wuerfel_from_gewandtheit(1) == 4
    assert get_wuerfel_from_gewandtheit(2) == 6
    assert get_wuerfel_from_gewandtheit(3) == 8
    assert get_wuerfel_from_gewandtheit(4) == 10
    assert get_wuerfel_from_gewandtheit(5) == 12
    assert get_wuerfel_from_gewandtheit(6) == 20

    # Randfälle
    assert get_wuerfel_from_gewandtheit(0) == 4 # Fallback Min
    assert get_wuerfel_from_gewandtheit(7) == 20 # Fallback Max

def test_initiative_roll_range():
    """
    Testet, ob der Initiative-Wurf im korrekten Bereich liegt.
    """
    # Teste 100 Würfe um sicherzustellen, dass Range stimmt
    for _ in range(100):
        result = wuerfle_initiative(2) # W6
        assert result >= 1
        # Mit explodierenden Würfeln kann das Ergebnis > 6 sein, daher keine Obergrenze prüfen

def test_exploding_dice_logic():
    # Test normal roll (no explosion)
    with patch('random.randint', return_value=3):
        total, rolls = roll_exploding_dice(6)
        assert total == 3
        assert rolls == [3]

    # Test exploding roll
    with patch('random.randint', side_effect=[6, 2]):
        total, rolls = roll_exploding_dice(6)
        assert total == 8
        assert rolls == [6, 2]

    # Test double explosion
    with patch('random.randint', side_effect=[6, 6, 1]):
        total, rolls = roll_exploding_dice(6)
        assert total == 13
        assert rolls == [6, 6, 1]
