import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import pandas as pd
import json
import os
from .character import Character
from .utils import ToolTip, generate_health_bar
from .import_handler import ImportHandler
from .library_handler import LibraryHandler
from .edit_handler import EditHandler
from .hotkey_handler import HotkeyHandler
from .ui_layout import UILayout
from .config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS, HOTKEYS
from .engine import CombatEngine
from .persistence import PersistenceHandler
from .history import HistoryManager

class CombatTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("PnP Combat Tracker v2.1 - Dark Mode")
        self.root.geometry("1900x1200")

        # --- Modern Dark Theme Configuration ---
        self.colors = COLORS

        self.engine = CombatEngine()
        self.engine.on_log = self.log_message

        self.history_manager = HistoryManager(self.engine)
        self.persistence_handler = PersistenceHandler(self, self.root)
        self.import_handler = ImportHandler(self, self.root, self.colors)
        self.library_handler = LibraryHandler(self, self.root, self.colors)
        self.edit_handler = EditHandler(self, self.root, self.colors)
        self.hotkey_handler = HotkeyHandler(self, self.root, self.colors)
        self.ui_layout = UILayout(self, self.root)

        self.root.configure(bg=self.colors["bg"])

        style = ttk.Style()
        style.theme_use('clam')

        # Allgemeine Styles
        style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"], font=('Segoe UI', 10))
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TButton", background=self.colors["panel"], foreground=self.colors["fg"], borderwidth=1, focuscolor=self.colors["accent"])
        style.map("TButton", background=[('active', self.colors["accent"])])

        style.configure("TEntry", fieldbackground=self.colors["entry_bg"], foreground=self.colors["fg"], insertcolor=self.colors["fg"])
        style.configure("TCombobox", fieldbackground=self.colors["entry_bg"], foreground=self.colors["fg"], arrowcolor=self.colors["fg"])

        # Treeview (Tabelle) Styles
        style.configure("Treeview",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        fieldbackground=self.colors["panel"],
                        rowheight=30,
                        font=('Segoe UI', 10))
        style.configure("Treeview.Heading",
                        background=self.colors["accent"],
                        foreground="#FFFFFF",
                        font=('Segoe UI', 10, 'bold'),
                        borderwidth=0)
        style.map("Treeview", background=[('selected', self.colors["accent"])])

        # Frame Styles (Karten-Look)
        style.configure("Card.TFrame", background=self.colors["panel"], relief="flat")
        style.configure("Card.TLabelframe", background=self.colors["panel"], foreground=self.colors["fg"], relief="flat")
        style.configure("Card.TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["accent"], font=('Segoe UI', 11, 'bold'))

        self.initiative_rolled = False

        # UI Widgets placeholders
        self.tree = None
        self.context_menu = None
        self.entry_name = None
        self.entry_lp = None
        self.entry_rp = None
        self.entry_sp = None
        self.entry_init = None
        self.entry_type = None
        self.var_surprise = None
        self.action_value = None
        self.action_type = None
        self.status_rank = None
        self.status_combobox = None
        self.status_duration = None
        self.round_label = None
        self.log = None

        # Info-Texte für Tooltips
        self.damage_descriptions = DAMAGE_DESCRIPTIONS
        self.status_descriptions = STATUS_DESCRIPTIONS

        self.enemy_presets = {}
        self.enemy_presets_structure = {}
        self.load_presets()

        self.setup_ui()
        self.hotkey_handler.setup_hotkeys()
        # self.load_enemies()

    def open_hotkey_settings(self):
        self.hotkey_handler.open_hotkey_settings()

    def load_presets(self, filename="enemies.json"):
        """Lädt Gegner-Presets aus einer JSON-Datei."""
        # Bestimme den absoluten Pfad basierend auf dem Speicherort von gui.py
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(base_dir, filename)

        if not os.path.exists(filepath):
            print(f"Warnung: {filepath} nicht gefunden.")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.enemy_presets_structure = json.load(f)

            # Flatten for easy lookup
            self.enemy_presets = {}

            def flatten_presets(data):
                for key, value in data.items():
                    if isinstance(value, dict) and "lp" in value: # It's a character entry
                        self.enemy_presets[key] = value
                    elif isinstance(value, dict): # It's a category
                        flatten_presets(value)

            flatten_presets(self.enemy_presets_structure)

        except Exception as e:
            print(f"Fehler beim Laden der Presets: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden der Bibliothek: {e}")

    def apply_preset(self, name):
        """Füllt die Eingabefelder basierend auf der Auswahl."""
        if name in self.enemy_presets:
            data = self.enemy_presets[name]

            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, name)

            self.entry_lp.delete(0, tk.END)
            self.entry_lp.insert(0, str(data.get("lp", 10)))

            self.entry_rp.delete(0, tk.END)
            self.entry_rp.insert(0, str(data.get("rp", 0)))

            self.entry_sp.delete(0, tk.END)
            self.entry_sp.insert(0, str(data.get("sp", 0)))

            self.entry_gew.delete(0, tk.END)
            self.entry_gew.insert(0, str(data.get("gew", 1)))

            self.entry_init.delete(0, tk.END)
            self.entry_init.insert(0, str(data.get("init", 0)))

            self.entry_type.set(data.get("type", "Gegner"))

    def create_tooltip(self, widget, text_func):
        tt = ToolTip(widget, text_func)
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def setup_ui(self):
        self.ui_layout.setup_ui()

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def add_character_quick(self):
        """Fügt einen Charakter aus den Eingabefeldern hinzu."""
        self.history_manager.save_snapshot()
        name = self.entry_name.get()
        if not name:
            messagebox.showwarning("Fehler", "Name ist erforderlich!")
            return
        try:
            lp = int(self.entry_lp.get() or 0)
            rp = int(self.entry_rp.get() or 0)
            sp = int(self.entry_sp.get() or 0)
            init = int(self.entry_init.get() or 0)
            gew = int(self.entry_gew.get() or 1)
        except ValueError:
            messagebox.showerror("Fehler", "Zahlenwerte ungültig.")
            return

        char_type = self.entry_type.get()
        char = Character(name, lp, rp, sp, init, gew=gew, char_type=char_type)

        surprise = self.var_surprise.get()
        self.insert_character(char, surprise=surprise)
        self.update_listbox()

        # Felder leeren
        self.entry_name.delete(0, tk.END)
        self.entry_lp.delete(0, tk.END)
        self.entry_rp.delete(0, tk.END)
        self.entry_sp.delete(0, tk.END)
        self.entry_init.delete(0, tk.END)
        self.entry_gew.delete(0, tk.END)
        self.entry_name.focus()
        # Checkbox zurücksetzen
        self.var_surprise.set(False)

    def insert_character(self, char, surprise=False):
        """Fügt einen Charakter in die Liste ein. Delegiert an Engine."""
        self.engine.insert_character(char, surprise)

    def roll_initiative_all(self):
        """Sorts characters based on their initiative. Rolls for those with 0 init."""
        self.history_manager.save_snapshot()
        self.engine.roll_initiatives()
        self.initiative_rolled = True
        self.update_listbox()

        # Zeige den ersten Charakter als aktiv an
        if self.engine.characters:
            char = self.engine.characters[0]
            self.log_message(f"▶ {char.name} ist am Zug!")

    def reset_initiative(self, target_type="All"):
        """Setzt die Initiative zurück."""
        self.history_manager.save_snapshot()
        count = 0
        for char in self.engine.characters:
            if target_type == "All" or char.char_type == target_type:
                char.init = 0
                count += 1

        self.engine.turn_index = -1
        self.engine.round_number = 1
        self.initiative_rolled = False # Initiative-Modus beenden
        self.update_listbox()

        type_text = "aller Charaktere" if target_type == "All" else f"aller {target_type}s"
        self.log_message(f"Initiative {type_text} wurde zurückgesetzt ({count} betroffen).")

    def next_turn(self):
        """Moves to the next turn, considering status and conditions."""
        self.history_manager.save_snapshot()
        char = self.engine.next_turn()
        if char:
             # Erzeuge Log für den aktuellen Status (Engine logs status updates, but maybe not current status summary)
            status_info = ""
            if char.status:
                status_list = [f"{s['effect']} (Rang {s['rank']}, {s['rounds']} Rd.)" for s in char.status]
                status_info = " | Status: " + ", ".join(status_list)

            if char.lp <= 0 or char.max_lp <= 0:
                self.log_message(f"💀 {char.name} ist kampfunfähig.{status_info}")
            elif char.skip_turns > 0:
                # Engine logs skip turn
                pass
            else:
                self.log_message(f"▶ {char.name} ist am Zug!{status_info}")

        self.update_listbox()

    def highlight_current_char(self, char):
        # Einfache visuelle Markierung (Auswahl)
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == char.name:
                self.tree.selection_set(item)
                self.tree.focus(item)
                break

    def get_action_value(self):
        """Hilfsfunktion: Liest den Wert aus dem Interaktions-Feld."""
        try:
            val = self.action_value.get()
            return int(val) if val else 0
        except ValueError:
            return 0

    def deal_damage(self):
        """Liest Schaden direkt aus dem UI-Feld."""
        char = self.get_selected_char()
        if not char: return

        dmg = self.get_action_value()
        if dmg <= 0:
            messagebox.showinfo("Info", "Bitte einen Schadenswert > 0 im Feld 'Wert' eingeben.")
            return

        dmg_type = self.action_type.get()

        try:
            rank = int(self.status_rank.get())
            if rank > 6: rank = 6
        except ValueError:
            rank = 1

        # Anwenden des Schadens
        self.history_manager.save_snapshot()
        log = char.apply_damage(dmg, dmg_type, rank)
        self.log_message(log)
        self.update_listbox()

    def add_status_to_character(self):
        char = self.get_selected_char()
        if not char: return

        status = self.status_combobox.get()
        duration_str = self.status_duration.get()
        rank_str = self.status_rank.get()

        if not status:
            messagebox.showwarning("Fehler", "Bitte einen Status eingeben oder auswählen.")
            return

        try:
            duration = int(duration_str)
            rank = int(rank_str)
            if duration <= 0 or rank <= 0: raise ValueError
            if rank > 6:
                rank = 6
                messagebox.showinfo("Info", "Maximaler Rang ist 6. Rang wurde auf 6 gesetzt.")
        except ValueError:
            messagebox.showwarning("Fehler", "Bitte gültige Zahlen für Dauer und Rang eingeben.")
            return

        self.history_manager.save_snapshot()
        char.add_status(status, duration, rank)
        self.log_message(f"{char.name} erhält Status '{status}' (Rang {rank}) für {duration} Runden.")
        self.update_listbox()

    def load_enemies(self, pfad: str = None):
        """
        Loads enemy data from an Excel file and opens a preview window for selection and editing.
        """
        self.history_manager.save_snapshot()
        self.import_handler.load_from_excel(pfad)

    def add_single_enemy(self):
        # Veraltet durch Quick-Add, aber kann als Fallback bleiben oder entfernt werden
        pass

    def edit_selected_char(self):
        """Bearbeitet alle Werte des ausgewählten Charakters."""
        self.edit_handler.edit_selected_char()

    def delete_character(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        # Index finden
        item = selection[0]
        # Treeview index corresponds to display order, which might be rotated
        # We need to find the actual character in self.engine.characters

        # Retrieve values from selected item to identify character
        values = self.tree.item(item, "values")
        char_name = values[1] # Name is in column 1

        # Find character in list (assuming unique names or just taking first match which is risky but standard for simple lists)
        # Better: Use the rotation logic to map back if possible, or just search.
        # Since we rotate the display list, the treeview index 0 is self.engine.characters[rot].

        # Let's recalculate rotation to find the correct index
        rot = 0
        if self.initiative_rolled and self.engine.turn_index >= 0:
             if self.engine.turn_index < len(self.engine.characters):
                rot = self.engine.turn_index

        tree_index = self.tree.index(item)
        actual_index = (rot + tree_index) % len(self.engine.characters)

        deleted_char = self.engine.characters[actual_index]

        # Safety check
        if deleted_char.name != char_name:
            # Fallback search if index calculation is off (should not happen if logic is consistent)
            for i, c in enumerate(self.engine.characters):
                if c.name == char_name:
                    actual_index = i
                    deleted_char = c
                    break

        self.history_manager.save_snapshot()
        self.engine.remove_character(actual_index)
        self.update_listbox()
        self.log_message(f"❌ Charakter '{deleted_char.name}' wurde gelöscht.")

    def delete_group(self, char_type):
        if messagebox.askyesno("Bestätigung", f"Alle {char_type} wirklich löschen?"):
            self.history_manager.save_snapshot()
            # Create a new list excluding the type
            self.engine.characters = [c for c in self.engine.characters if c.char_type != char_type]
            # Reset turn index if needed, or just let update_listbox handle it (might be risky if index out of bounds)
            if self.engine.turn_index >= len(self.engine.characters):
                self.engine.turn_index = 0
            self.update_listbox()
            self.log_message(f"Alle {char_type} wurden gelöscht.")

    def manage_edit(self):
        """Handhabt das Bearbeiten basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.management_target_var.get()
        if target == "Ausgewählter Charakter":
            self.edit_selected_char()
        else:
            messagebox.showinfo("Info", "Massenbearbeitung ist derzeit nicht verfügbar.")

    def manage_delete(self):
        """Handhabt das Löschen basierend auf der Auswahl im Verwaltungs-Panel."""
        target = self.management_target_var.get()
        if target == "Ausgewählter Charakter":
            self.delete_character()
        elif target == "Alle Gegner":
            self.delete_group("Gegner")
        elif target == "Alle Spieler":
            self.delete_group("Spieler")
        elif target == "Alle NPCs":
            self.delete_group("NPC")
        elif target == "Alle Charaktere":
            if messagebox.askyesno("Bestätigung", "Wirklich ALLE Charaktere löschen?"):
                self.history_manager.save_snapshot()
                self.engine.characters.clear()
                self.engine.reset_combat()
                self.update_listbox()
                self.log_message("Alle Charaktere wurden gelöscht.")

    def apply_healing(self):
        char = self.get_selected_char()
        if not char: return

        val = self.get_action_value()
        if val <= 0:
            messagebox.showinfo("Info", "Bitte einen Heilwert > 0 im Feld 'Wert' eingeben.")
            return

        self.history_manager.save_snapshot()
        heal_log = char.heal(val)
        self.log_message(heal_log)
        self.update_listbox()

    def apply_shield(self):
        char = self.get_selected_char()
        if not char: return
        val = self.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            char.sp += val
            self.log_message(f"{char.name} erhält {val} Schild.")
            self.update_listbox()

    def apply_armor(self):
        char = self.get_selected_char()
        if not char: return
        val = self.get_action_value()
        if val > 0:
            self.history_manager.save_snapshot()
            char.rp += val
            self.log_message(f"{char.name} erhält {val} Rüstung.")
            self.update_listbox()

    def update_listbox(self):
        # Treeview leeren
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Update Round Label
        if hasattr(self, 'round_label'):
            self.round_label.config(text=f"Runde: {self.engine.round_number}")

        if not self.engine.characters:
            return

        # Rotation berechnen
        rot = 0
        if self.initiative_rolled and self.engine.turn_index >= 0:
            # turn_index ist jetzt immer im gültigen Bereich (0 bis len-1)
            if self.engine.turn_index < len(self.engine.characters):
                rot = self.engine.turn_index
            else:
                # Fallback, falls turn_index durch Löschen ungültig wurde
                rot = 0

        # Liste rotieren für Anzeige (Aktiver Char oben)
        n = len(self.engine.characters)
        display_list = []
        for k in range(n):
            idx = (rot + k) % n
            display_list.append((idx, self.engine.characters[idx]))

        for orig_idx, char in display_list:
            status_str = ", ".join(f"{s['effect']} (Rang {s['rank']}, {s['rounds']} Rd.)" for s in char.status)
            order = str(orig_idx + 1) if self.initiative_rolled else "-"

            # Werte formatieren (Aktuell / Max)
            lp_str = f"{char.lp}/{char.max_lp}"
            rp_str = f"{char.rp}/{char.max_rp}"
            sp_str = f"{char.sp}/{char.max_sp}"

            # Health Bar generieren
            health_bar = generate_health_bar(char.lp, char.max_lp, length=10)

            # Werte einfügen
            item_id = self.tree.insert("", tk.END, values=(order, char.name, char.char_type, health_bar, rp_str, sp_str, char.gew, char.init, status_str))

            # Visuelles Feedback für niedrige LP (optional)
            if char.lp <= 0 or char.max_lp <= 0:
                self.tree.item(item_id, tags=('dead',))
            elif char.lp < (char.max_lp * 0.3): # Unter 30% LP
                self.tree.item(item_id, tags=('low_hp',))

        # Tags für Dark Mode angepasst
        self.tree.tag_configure('dead', background='#5e0000', foreground='#ffcccc') # Dunkelrot Hintergrund
        self.tree.tag_configure('low_hp', foreground='#ff5252')   # Helles Rot Schrift

        # Autosave trigger
        self.persistence_handler.autosave()

    def get_selected_char(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Fehler", "Kein Charakter ausgewählt.")
            return None

        tree_index = self.tree.index(selection[0])

        # Rotation berücksichtigen
        rot = 0
        if self.initiative_rolled and self.engine.turn_index >= 0:
            if self.engine.turn_index < len(self.engine.characters):
                rot = self.engine.turn_index

        # Den tatsächlichen Index in der self.engine.characters Liste berechnen
        actual_index = (rot + tree_index) % len(self.engine.characters)

        return self.engine.characters[actual_index]

    def log_message(self, msg):
        self.log.insert(tk.END, str(msg).strip() + "\n")
        self.log.see(tk.END)

    def undo_action(self):
        if self.history_manager.undo():
            self.update_listbox()
            self.log_message("↩ Undo ausgeführt.")

    def redo_action(self):
        if self.history_manager.redo():
            self.update_listbox()
            self.log_message("↪ Redo ausgeführt.")
