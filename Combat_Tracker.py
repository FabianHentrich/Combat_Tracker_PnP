import tkinter as tk
import sys
import os
from tkinter import messagebox

# Sicherstellen, dass das Projekt-Root im Pfad ist
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from src.ui.main_window import CombatTracker
    from src.utils.logger import setup_logging
except ImportError as e:
    # Fallback, falls Module fehlen (wichtig für User ohne Konsole)
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Startfehler", f"Kritischer Import-Fehler:\n{e}")
    sys.exit(1)

if __name__ == '__main__':
    logger = setup_logging()
    try:
        root = tk.Tk()
        # Optional: Fenstertitel und Icon hier setzen
        root.title("Combat Tracker")

        # Starte im Vollbildmodus
        try:
            root.state('zoomed')  # Windows
        except Exception:
            root.attributes('-fullscreen', True)  # Fallback für andere Plattformen

        app = CombatTracker(root)
        root.mainloop()
    except Exception as e:
        # Globales Error-Catching für unerwartete Abstürze
        logger.critical("Kritischer unerwarteter Fehler:", exc_info=True)

        # Falls root noch existiert, Fehler anzeigen
        try:
            messagebox.showerror("Kritischer Fehler", f"Ein unerwarteter Fehler ist aufgetreten:\n{e}")
        except:
            pass
