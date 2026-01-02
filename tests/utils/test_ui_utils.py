import pytest
from src.utils.utils import generate_health_bar

def test_generate_health_bar_full():
    """Testet Health Bar bei vollen LP."""
    bar = generate_health_bar(10, 10, length=10)
    assert bar == "██████████ 10/10"

def test_generate_health_bar_half():
    """Testet Health Bar bei halben LP."""
    bar = generate_health_bar(5, 10, length=10)
    assert bar == "█████░░░░░ 5/10"

def test_generate_health_bar_empty():
    """Testet Health Bar bei 0 LP."""
    bar = generate_health_bar(0, 10, length=10)
    assert bar == "░░░░░░░░░░ 0/10"

def test_generate_health_bar_overflow():
    """Testet Health Bar bei mehr LP als Max (Heilung über Max)."""
    bar = generate_health_bar(15, 10, length=10)
    assert bar == "██████████ 15/10"

def test_generate_health_bar_zero_max():
    """Testet Health Bar bei Max LP 0 (sollte leer sein, kein Crash)."""
    bar = generate_health_bar(0, 0, length=10)
    assert bar == "💀 0/0"

