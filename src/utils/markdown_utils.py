import tkinter as tk
import re
import os
from typing import Dict, Any, Callable
from src.utils.logger import setup_logging

logger = setup_logging()

class MarkdownUtils:
    # Pre-compile regex patterns for better performance
    LINK_PATTERN = re.compile(r"(\[\[.*?\]\])")
    BOLD_PATTERN = re.compile(r"(\*\*.*?\*\*)")
    STAT_PAIR_PATTERN = re.compile(r"^\d+/\d+$")

    @staticmethod
    def configure_text_tags(text_widget: tk.Text, link_callback: Callable[[Any], None], colors: Dict[str, str]):
        """Konfiguriert die Tags für ein Text-Widget."""
        text_widget.tag_config("h1", font=("Segoe UI", 16, "bold"), foreground=colors["accent"])
        text_widget.tag_config("h2", font=("Segoe UI", 14, "bold"), foreground=colors["accent"])
        text_widget.tag_config("h3", font=("Segoe UI", 12, "bold"))
        text_widget.tag_config("bold", font=("Segoe UI", 10, "bold"))
        text_widget.tag_config("link", foreground="#4a90e2", underline=True)

        # Bindings need to know which widget triggered them
        # We wrap the callback to pass the event and widget if needed, or just use the event in the callback
        text_widget.tag_bind("link", "<Button-1>", lambda e: link_callback(e, text_widget))
        text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.configure(cursor="hand2"))
        text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.configure(cursor=""))

    @staticmethod
    def parse_markdown(text: str, text_widget: tk.Text):
        """Einfacher Markdown-Parser für die Anzeige."""
        lines = text.split("\n")
        for line in lines:
            tags = []
            if line.startswith("# "):
                tags.append("h1")
                line = line[2:]
            elif line.startswith("## "):
                tags.append("h2")
                line = line[3:]
            elif line.startswith("### "):
                tags.append("h3")
                line = line[4:]

            # Links verarbeiten [[Link]]
            parts = MarkdownUtils.LINK_PATTERN.split(line)
            for part in parts:
                if part.startswith("[[") and part.endswith("]]"):
                    link_text = part[2:-2]
                    # Link einfügen
                    text_widget.insert(tk.END, link_text, ("link",))
                else:
                    # Normaler Text (hier könnte man noch **bold** parsen)
                    # Einfaches Bold Parsing
                    bold_parts = MarkdownUtils.BOLD_PATTERN.split(part)
                    for b_part in bold_parts:
                        if b_part.startswith("**") and b_part.endswith("**"):
                            text_widget.insert(tk.END, b_part[2:-2], ("bold",) + tuple(tags))
                        else:
                            text_widget.insert(tk.END, b_part, tuple(tags))

            text_widget.insert(tk.END, "\n")

    @staticmethod
    def parse_stats_from_markdown(content: str) -> Dict[str, Any]:
        """Parst die Statistiken aus dem Markdown-Inhalt."""
        lines = content.split("\n")
        stats = {}

        # Einfache Parsing-Logik: Wir gehen davon aus, dass die Stats in einer bestimmten Reihenfolge kommen
        # und durch Doppelpunkte getrennt sind. Z.B. "LP: 10", "RP: 5", etc.
        for line in lines:
            if ":" in line:
                try:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Versuchen, den Wert in eine Zahl zu konvertieren
                    if value.isdigit():
                        value = int(value)
                    elif MarkdownUtils.STAT_PAIR_PATTERN.match(value):  # Für Werte wie 10/5 (LP/RP)
                        lp, rp = value.split("/")
                        value = {"lp": int(lp), "rp": int(rp)}
                    else:
                        continue  # Unbekanntes Format, überspringen

                    stats[key] = value
                except Exception as e:
                    logger.warning(f"Fehler beim Parsen der Zeile '{line}': {e}")

        return stats

    @staticmethod
    def display_folder_toc(folder_path: str, text_widget: tk.Text, colors: Dict[str, str]):
        """Zeigt ein Inhaltsverzeichnis für einen Ordner an."""
        if text_widget is None:
            return

        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)

        folder_name = os.path.basename(folder_path)

        # Manually insert header since we are outside the class context for tag config if we didn't pass it
        # But tags are configured on the widget.
        text_widget.insert(tk.END, f"# Inhalt von {folder_name}\n\n", ("h1",))

        # List subfolders
        try:
            subfolders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
            subfolders.sort()
            if subfolders:
                text_widget.insert(tk.END, "## Ordner\n", ("h2",))
                for sub in subfolders:
                    text_widget.insert(tk.END, f"- [[{sub}]]\n", ("link",))
                text_widget.insert(tk.END, "\n")

            # List files
            files = [f for f in os.listdir(folder_path) if f.endswith(".md") and os.path.isfile(os.path.join(folder_path, f))]
            files.sort()
            if files:
                text_widget.insert(tk.END, "## Dateien\n", ("h2",))
                for f in files:
                    name = os.path.splitext(f)[0]
                    if name != "Start":
                        text_widget.insert(tk.END, f"- [[{name}]]\n", ("link",))
        except OSError as e:
            logger.error(f"Fehler beim Lesen des Ordners {folder_path}: {e}")
            text_widget.insert(tk.END, "Fehler beim Lesen des Ordners.", ("error",))

        text_widget.config(state=tk.DISABLED)

