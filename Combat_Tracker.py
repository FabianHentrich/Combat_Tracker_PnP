import tkinter as tk
from src.gui import CombatTracker

if __name__ == '__main__':
    root = tk.Tk()
    app = CombatTracker(root)
    root.mainloop()

# Problem: nach init-reset kann keine neue init automatzsich zu gewiesen werden (gew muss gespeichert werden)
# Verbesserung: nicht nur den Schaden, welcher durch Rüstung aufgefangen wird anzeigen sondern auch wie viel RÜstung dadurch reduziert wurde.
