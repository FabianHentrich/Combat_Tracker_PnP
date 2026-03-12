"""
PanedWindow Position Logger - Speichert die Regler-Positionen wenn sie manuell angepasst werden
"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime

class PanedWindowLogger:
    """Loggt PanedWindow Positionen für Debugging und Konfiguration"""

    def __init__(self, log_file="paned_positions.log"):
        self.log_file = log_file
        self.logged_positions = {}

    def attach_logger(self, paned_window, name):
        """Hängt einen Logger an ein PanedWindow an"""
        def on_sash_moved(event=None):
            positions = []
            # Lese alle Sash-Positionen
            i = 0
            while True:
                try:
                    pos = paned_window.sashpos(i)
                    if pos == -1:
                        break
                    positions.append(pos)
                    i += 1
                except Exception:
                    break

            if positions:
                self.log_position(name, positions)

        # Binde an das Sash-Move Event
        paned_window.bind('<ButtonRelease-1>', on_sash_moved, add='+')

        return on_sash_moved

    def log_position(self, paned_name, positions):
        """Loggt eine Position in die Datei"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Speichere aktuelle Position
        self.logged_positions[paned_name] = positions

        # Schreibe in Log-Datei
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{timestamp}] {paned_name}:\n")
            for i, pos in enumerate(positions):
                f.write(f"  Sash {i}: {pos}px\n")

        print(f"✓ Logged {paned_name} position: {positions}")

    def get_current_config(self):
        """Gibt die aktuelle Konfiguration als Python-Code zurück"""
        if not self.logged_positions:
            return "# Noch keine Positionen geloggt"

        config = "# Optimale PanedWindow Positionen (manuell angepasst)\n\n"

        for name, positions in self.logged_positions.items():
            config += f"# {name}:\n"
            for i, pos in enumerate(positions):
                config += f"{name}_sash_{i} = {pos}  # px\n"
            config += "\n"

        return config

    def save_config(self, filename="paned_config.py"):
        """Speichert die Konfiguration als Python-Datei"""
        config = self.get_current_config()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(config)
        print(f"✓ Konfiguration gespeichert in {filename}")


# Globale Logger-Instanz
_logger = None

def get_logger():
    """Gibt die globale Logger-Instanz zurück"""
    global _logger
    if _logger is None:
        _logger = PanedWindowLogger()
    return _logger
