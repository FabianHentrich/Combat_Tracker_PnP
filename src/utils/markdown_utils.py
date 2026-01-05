import tkinter as tk
import re
import os
from typing import Dict, Any, Callable
from src.utils.logger import setup_logging
from src.utils.localization import translate
from PIL import Image, ImageTk  # Pillow für Bildverarbeitung

logger = setup_logging()

class MarkdownUtils:
    # Pre-compile regex patterns for better performance
    LINK_PATTERN = re.compile(r'(\[\[.*?\]\])')
    BOLD_PATTERN = re.compile(r'(\*\*.*?\*\*)')
    STAT_PAIR_PATTERN = re.compile(r'^\d+/\d+$')
    IMAGE_PATTERN = re.compile(r'!\[.*?\]\((.*?)\)')
    TABLE_ROW_PATTERN = re.compile(r'^\s*\|.*\|\s*$')

    @staticmethod
    def configure_text_tags(text_widget: tk.Text, link_callback: Callable[[Any], None], colors: Dict[str, str]):
        """Configures the tags for a text widget."""
        text_widget.tag_config("h1", font=("Segoe UI", 16, "bold"), foreground=colors["accent"])
        text_widget.tag_config("h2", font=("Segoe UI", 14, "bold"), foreground=colors["accent"])
        text_widget.tag_config("h3", font=("Segoe UI", 12, "bold"))
        text_widget.tag_config("bold", font=("Segoe UI", 10, "bold"))
        text_widget.tag_config("link", foreground="#4a90e2", underline=True)
        # Tabellenfarben
        text_widget.tag_config("table_border", foreground=colors["fg"])
        text_widget.tag_config("table_header", font=("Segoe UI", 10, "bold"), foreground=colors["fg"])
        text_widget.tag_config("table_cell", font=("Segoe UI", 10), foreground=colors["fg"])

        # Bindings need to know which widget triggered them
        text_widget.tag_bind("link", "<Button-1>", link_callback)
        text_widget.tag_bind("link", "<Enter>", lambda e: text_widget.configure(cursor="hand2"))
        text_widget.tag_bind("link", "<Leave>", lambda e: text_widget.configure(cursor=""))

    @staticmethod
    def parse_markdown(text: str, text_widget: tk.Text, base_path: str = None):
        """Markdown-Parser mit Bild- und Tabellenunterstützung."""
        # Bild-Referenzen müssen am Widget gespeichert werden, sonst werden sie vom GC entfernt
        if not hasattr(text_widget, '_image_refs'):
            text_widget._image_refs = []
        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
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

            # Bild einfügen, falls vorhanden
            img_match = MarkdownUtils.IMAGE_PATTERN.search(line)
            if img_match:
                img_filename = img_match.group(1)
                if base_path:
                    img_path = os.path.join(base_path, img_filename)
                else:
                    img_path = img_filename
                if os.path.exists(img_path):
                    try:
                        # Dynamische Skalierung auf max. 60% der Widget-Breite
                        widget_width = text_widget.winfo_width() or 400
                        max_width = int(widget_width * 0.6)
                        img = Image.open(img_path)
                        ratio = min(1.0, max_width / img.width)
                        new_size = (int(img.width * ratio), int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        tk_img = ImageTk.PhotoImage(img)
                        text_widget.image_create(tk.END, image=tk_img)
                        text_widget._image_refs.append(tk_img)
                        text_widget.insert(tk.END, "\n")
                    except Exception as e:
                        logger.warning(f"Fehler beim Laden des Bildes {img_path}: {e}")
                else:
                    if tags:
                        text_widget.insert(tk.END, f"[Bild nicht gefunden: {img_filename}]\n", tuple(tags))
                    else:
                        text_widget.insert(tk.END, f"[Bild nicht gefunden: {img_filename}]\n")
                i += 1
                continue

            # Tabellen erkennen (mind. 2 Zeilen mit |)
            if MarkdownUtils.TABLE_ROW_PATTERN.match(line):
                table_lines = [line]
                j = i + 1
                while j < len(lines) and MarkdownUtils.TABLE_ROW_PATTERN.match(lines[j]):
                    table_lines.append(lines[j])
                    j += 1
                MarkdownUtils._insert_table(table_lines, text_widget)
                i = j
                continue

            # Process links [[Link]]
            parts = MarkdownUtils.LINK_PATTERN.split(line)
            for part in parts:
                if part.startswith("[[") and part.endswith("]]"):
                    link_text = part[2:-2]
                    text_widget.insert(tk.END, link_text, ("link",))
                else:
                    bold_parts = MarkdownUtils.BOLD_PATTERN.split(part)
                    for b_part in bold_parts:
                        if b_part.startswith("**") and b_part.endswith("**"):
                            text_widget.insert(tk.END, b_part[2:-2], ("bold",) + tuple(tags))
                        else:
                            text_widget.insert(tk.END, b_part, tuple(tags))
            text_widget.insert(tk.END, "\n")
            i += 1

    @staticmethod
    def _insert_table(table_lines, text_widget):
        # Einfache Markdown-Tabelle als ASCII-Tabelle mit Rahmen und Theme-Farbe
        # Zellen splitten
        rows = [ [cell.strip() for cell in row.strip('|').split('|')] for row in table_lines ]
        col_count = max(len(r) for r in rows)
        col_widths = [0]*col_count
        for row in rows:
            for idx, cell in enumerate(row):
                col_widths[idx] = max(col_widths[idx], len(cell))
        # Rahmenzeichen
        h = '─'
        v = '│'
        tl, tr, bl, br, c = '┌', '┐', '└', '┘', '┼'
        # Kopfzeile
        text_widget.insert(tk.END, tl + c.join([h*(w+2) for w in col_widths]) + tr + "\n", ("table_border",))
        for ridx, row in enumerate(rows):
            text_widget.insert(tk.END, v, ("table_border",))
            for idx, cell in enumerate(row):
                tag = "table_header" if ridx == 0 else "table_cell"
                text_widget.insert(tk.END, f" {cell.ljust(col_widths[idx])} ", (tag,))
                text_widget.insert(tk.END, v, ("table_border",))
            text_widget.insert(tk.END, "\n")
            if ridx == 0:
                # Kopf-/Body-Trenner
                text_widget.insert(tk.END, c + c.join([h*(w+2) for w in col_widths]) + c + "\n", ("table_border",))
        text_widget.insert(tk.END, bl + c.join([h*(w+2) for w in col_widths]) + br + "\n", ("table_border",))

    @staticmethod
    def parse_stats_from_markdown(content: str) -> Dict[str, Any]:
        """Parses statistics from Markdown content."""
        lines = content.split("\n")
        stats = {}

        # Simple parsing logic: Assume stats are in a specific order
        # and separated by colons. E.g., "LP: 10", "RP: 5", etc.
        for line in lines:
            if ":" in line:
                try:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Try to convert the value to a number
                    if value.isdigit():
                        value = int(value)
                    elif MarkdownUtils.STAT_PAIR_PATTERN.match(value):  # For values like 10/5 (LP/RP)
                        lp, rp = value.split("/")
                        value = {"lp": int(lp), "rp": int(rp)}
                    else:
                        continue  # Unknown format, skip

                    stats[key] = value
                except Exception as e:
                    logger.warning(f"Error parsing line '{line}': {e}")

        return stats

    @staticmethod
    def display_folder_toc(folder_path: str, text_widget: tk.Text, colors: Dict[str, str]):
        """Displays a table of contents for a folder."""
        if text_widget is None:
            return

        text_widget.config(state="normal")
        text_widget.delete("1.0", tk.END)

        folder_name = os.path.basename(folder_path)

        # Manually insert header since we are outside the class context for tag config if we didn't pass it
        # But tags are configured on the widget.
        text_widget.insert(tk.END, f"# {translate('markdown.contents_of')} {folder_name}\n\n", ("h1",))

        # List subfolders
        try:
            subfolders = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
            subfolders.sort()
            if subfolders:
                text_widget.insert(tk.END, f"## {translate('markdown.folders')}\n", ("h2",))
                for sub in subfolders:
                    text_widget.insert(tk.END, f"- [[{sub}]]\n", ("link",))
                text_widget.insert(tk.END, "\n")

            # List files
            files = [f for f in os.listdir(folder_path) if f.endswith(".md") and os.path.isfile(os.path.join(folder_path, f))]
            files.sort()
            if files:
                text_widget.insert(tk.END, f"## {translate('markdown.files')}\n", ("h2",))
                for f in files:
                    name = os.path.splitext(f)[0]
                    if name != "Start":
                        text_widget.insert(tk.END, f"- [[{name}]]\n", ("link",))
        except OSError as e:
            logger.error(f"Error reading folder {folder_path}: {e}")
            text_widget.insert(tk.END, translate("messages.error_reading_folder"), ("error",))

        text_widget.config(state="disabled")
