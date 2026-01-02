import pytest
import tkinter as tk
from unittest.mock import MagicMock
from src.utils.markdown_utils import MarkdownUtils

def test_parse_stats_from_markdown():
    """Testet das Parsen von Stats aus Markdown-Text."""
    content = """
    # Boss
    LP: 100
    RP: 20
    SP: 10
    GEW: 5
    """
    stats = MarkdownUtils.parse_stats_from_markdown(content)

    assert stats["lp"] == 100
    assert stats["rp"] == 20
    assert stats["sp"] == 10
    assert stats["gew"] == 5

def test_parse_stats_complex_format():
    """Testet das Parsen von Stats im Format '10/10'."""
    content = """
    LP: 100/100
    """
    stats = MarkdownUtils.parse_stats_from_markdown(content)
    # Der Parser nimmt aktuell nur einfache Zahlen oder ignoriert komplexe Formate,
    # oder hat spezielle Logik für x/y. Prüfen wir die Implementierung:
    # Implementierung: elif MarkdownUtils.STAT_PAIR_PATTERN.match(value): lp, rp = value.split("/")

    # Wenn der Input "LP: 100/100" ist, wird das als LP und RP interpretiert?
    # Laut Code: value = {"lp": int(lp), "rp": int(rp)}

    assert "lp" in stats
    assert isinstance(stats["lp"], dict)
    assert stats["lp"]["lp"] == 100
    assert stats["lp"]["rp"] == 100

def test_parse_markdown_links():
    """Testet, ob Links korrekt erkannt und ins Widget eingefügt werden."""
    text_widget = MagicMock()
    text = "Ein [[Link]] im Text."

    MarkdownUtils.parse_markdown(text, text_widget)

    # Check calls
    # "Ein " -> normal
    # "Link" -> link tag
    # " im Text." -> normal

    # Wir prüfen nur, ob insert mit "link" tag aufgerufen wurde
    calls = text_widget.insert.call_args_list

    link_inserted = False
    for call in calls:
        args = call[0]
        if len(args) >= 3 and "link" in args[2]:
            if args[1] == "Link":
                link_inserted = True

    assert link_inserted

