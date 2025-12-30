import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import pandas as pd
from .character import Character
from .utils import ToolTip
from .import_handler import ImportHandler
from .edit_handler import EditHandler
from .ui_layout import UILayout
from .config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS

class CombatTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("PnP Combat Tracker v2.1 - Dark Mode")
        self.root.geometry("1200x800")

        # --- Modern Dark Theme Configuration ---
        self.colors = COLORS

        self.import_handler = ImportHandler(self, self.root, self.colors)
        self.edit_handler = EditHandler(self, self.root, self.colors)
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

        self.characters = []
        self.turn_index = -1 # Start bei -1, damit erster Klick auf "Nächster Zug" Index 0 wählt
        self.round_number = 1
        self.enemy_data = {}
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

        self.setup_ui()
        # self.load_enemies()

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
        name = self.entry_name.get()
        if not name:
            messagebox.showwarning("Fehler", "Name ist erforderlich!")
            return
        try:
            lp = int(self.entry_lp.get() or 0)
            rp = int(self.entry_rp.get() or 0)
            sp = int(self.entry_sp.get() or 0)
            init = int(self.entry_init.get() or 0)
        except ValueError:
            messagebox.showerror("Fehler", "Zahlenwerte ungültig.")
            return

        char_type = self.entry_type.get()
        char = Character(name, lp, rp, sp, init, char_type)

        surprise = self.var_surprise.get()
        self.insert_character(char, surprise=surprise)
        self.update_listbox()

        # Felder leeren
        self.entry_name.delete(0, tk.END)
        self.entry_lp.delete(0, tk.END)
        self.entry_rp.delete(0, tk.END)
        self.entry_sp.delete(0, tk.END)
        self.entry_init.delete(0, tk.END)
        self.entry_name.focus()
        # Checkbox zurücksetzen
        self.var_surprise.set(False)

    def insert_character(self, char, surprise=False):
        """Fügt einen Charakter in die Liste ein. Sortiert ein, falls Initiative aktiv."""
        if not self.initiative_rolled:
            self.characters.append(char)
        else:
            if surprise:
                # An aktueller Position einfügen (Vordrängeln)
                # Der aktuelle turn_index zeigt auf den Charakter, der gerade dran ist.
                # Wenn wir hier einfügen, rutscht der aktuelle nach hinten.
                # Der Neue ist dann an turn_index und somit "aktiv".

                # Falls turn_index ungültig ist (z.B. -1), setzen wir ihn auf 0
                target_index = max(0, self.turn_index)

                # Einfügen
                self.characters.insert(target_index, char)

                # Wenn wir genau an der aktuellen Position einfügen, ist der Neue jetzt der Aktive.
                # Wir müssen turn_index NICHT erhöhen, damit er auf den Neuen zeigt.
                # Aber wir müssen sicherstellen, dass turn_index im gültigen Bereich ist.
                if self.turn_index < 0:
                    self.turn_index = 0

                self.log_message(f"⚠ {char.name} springt überraschend in den Kampf!")
            else:
                # Finde Einfügeposition für absteigende Sortierung nach Initiative
                inserted = False
                for i, c in enumerate(self.characters):
                    if char.init > c.init:
                        self.characters.insert(i, char)
                        # Wenn vor dem aktuellen Zug eingefügt wird, muss der Index verschoben werden
                        # damit der aktuell aktive Charakter aktiv bleibt.
                        if i <= self.turn_index:
                            self.turn_index += 1
                        inserted = True
                        break
                if not inserted:
                    self.characters.append(char)

    def roll_initiative_all(self):
        """Sorts characters based on their initiative."""
        # Status update removed to prevent damage tick on init roll
        self.characters.sort(key=lambda c: c.init, reverse=True)
        self.turn_index = 0  # Setze auf 0, damit der erste Charakter direkt aktiv ist
        self.round_number = 1
        self.initiative_rolled = True
        self.update_listbox()
        self.log_message("🎲 Initiative gewürfelt! Reihenfolge erstellt.")
        self.log_message(f"--- Runde {self.round_number} beginnt ---")

        # Zeige den ersten Charakter als aktiv an
        if self.characters:
            char = self.characters[0]
            self.log_message(f"▶ {char.name} ist am Zug!")

    def reset_initiative(self, target_type="All"):
        """Setzt die Initiative zurück."""
        count = 0
        for char in self.characters:
            if target_type == "All" or char.char_type == target_type:
                char.init = 0
                count += 1

        self.initiative_rolled = False # Initiative-Modus beenden
        self.turn_index = -1
        self.round_number = 1
        self.update_listbox()

        type_text = "aller Charaktere" if target_type == "All" else f"aller {target_type}s"
        self.log_message(f"Initiative {type_text} wurde zurückgesetzt ({count} betroffen).")

    def next_turn(self):
        """Moves to the next turn, considering status and conditions."""
        if not self.characters:
            return

        # Index erhöhen
        self.turn_index += 1

        # Runden-Update prüfen (Wrap-Around)
        if self.turn_index >= len(self.characters):
            self.turn_index = 0
            self.round_number += 1
            self.log_message(f"--- Runde {self.round_number} beginnt ---")

        # Hole aktuellen Charakter
        char = self.characters[self.turn_index]

        # Update Status (z. B. Runden reduzieren, Stun prüfen, etc.)
        status_log = char.update_status()
        if status_log:
            self.log_message(status_log)

        # Erzeuge Log für den aktuellen Status
        status_info = ""
        if char.status:
            status_list = [f"{s['effect']} (Rang {s['rank']}, {s['rounds']} Rd.)" for s in char.status]
            status_info = " | Status: " + ", ".join(status_list)

        # Prüfe Zustand des Charakters
        if char.lp <= 0 or char.max_lp <= 0:
            self.log_message(f"💀 {char.name} ist kampfunfähig.{status_info}")
        elif char.skip_turns > 0:
            self.log_message(f"⏳ {char.name} setzt diese Runde aus!{status_info}")
        else:
            self.log_message(f"▶ {char.name} ist am Zug!{status_info}")
            # Highlight removed because rotation handles visibility
            # self.highlight_current_char(char)

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

        char.add_status(status, duration, rank)
        self.log_message(f"{char.name} erhält Status '{status}' (Rang {rank}) für {duration} Runden.")
        self.update_listbox()

    def load_enemies(self, pfad: str = None):
        """
        Loads enemy data from an Excel file and opens a preview window for selection and editing.
        """
        if not pfad:
            # Open file dialog to load only .xlsx files
            file_path = filedialog.askopenfilename(title="Gegnerdaten laden", filetypes=[("Excel Dateien", "*.xlsx")])
            if not file_path: return
        else:
            file_path = pfad

        try:
            # Load the Excel file into a DataFrame
            df = pd.read_excel(file_path)

            # Check for required columns
            required_columns = {"Name", "Ruestung", "Schild", "HP", "Gewandtheit"}
            if not required_columns.issubset(df.columns):
                missing = required_columns - set(df.columns)
                raise ValueError(f"Excel file is missing columns: {missing}")

            # Öffne Vorschaufenster über ImportHandler
            self.import_handler.show_import_preview(df)

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden: {e}")

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
        # We need to find the actual character in self.characters

        # Retrieve values from selected item to identify character
        values = self.tree.item(item, "values")
        char_name = values[1] # Name is in column 1

        # Find character in list (assuming unique names or just taking first match which is risky but standard for simple lists)
        # Better: Use the rotation logic to map back if possible, or just search.
        # Since we rotate the display list, the treeview index 0 is self.characters[rot].

        # Let's recalculate rotation to find the correct index
        rot = 0
        if self.initiative_rolled and self.turn_index >= 0:
             if self.turn_index < len(self.characters):
                rot = self.turn_index

        tree_index = self.tree.index(item)
        actual_index = (rot + tree_index) % len(self.characters)

        deleted_char = self.characters[actual_index]

        # Safety check
        if deleted_char.name != char_name:
            # Fallback search if index calculation is off (should not happen if logic is consistent)
            for i, c in enumerate(self.characters):
                if c.name == char_name:
                    actual_index = i
                    deleted_char = c
                    break

        del self.characters[actual_index]

        # Adjust turn_index if necessary
        if self.initiative_rolled:
            if actual_index < self.turn_index:
                self.turn_index -= 1
            elif actual_index == self.turn_index:
                # If we deleted the active character, turn_index now points to the next one (which is correct for "next" in list),
                # but we might want to handle it carefully.
                # If we deleted the last character in list, turn_index might be out of bounds.
                if self.turn_index >= len(self.characters):
                    self.turn_index = 0

        self.update_listbox()
        self.log_message(f"❌ Charakter '{deleted_char.name}' wurde gelöscht.")

    def delete_group(self, char_type):
        if messagebox.askyesno("Bestätigung", f"Alle {char_type} wirklich löschen?"):
            self.characters = [c for c in self.characters if c.char_type != char_type]
            self.update_listbox()
            self.log_message(f"Alle {char_type} wurden gelöscht.")

    def apply_healing(self):
        char = self.get_selected_char()
        if not char: return

        val = self.get_action_value()
        if val <= 0:
            messagebox.showinfo("Info", "Bitte einen Heilwert > 0 im Feld 'Wert' eingeben.")
            return

        heal_log = char.heal(val)
        self.log_message(heal_log)
        self.update_listbox()

    def apply_shield(self):
        char = self.get_selected_char()
        if not char: return
        val = self.get_action_value()
        if val > 0:
            char.sp += val
            self.log_message(f"{char.name} erhält {val} Schild.")
            self.update_listbox()

    def apply_armor(self):
        char = self.get_selected_char()
        if not char: return
        val = self.get_action_value()
        if val > 0:
            char.rp += val
            self.log_message(f"{char.name} erhält {val} Rüstung.")
            self.update_listbox()

    def update_listbox(self):
        # Treeview leeren
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Update Round Label
        if hasattr(self, 'round_label'):
            self.round_label.config(text=f"Runde: {self.round_number}")

        if not self.characters:
            return

        # Rotation berechnen
        rot = 0
        if self.initiative_rolled and self.turn_index >= 0:
            # turn_index ist jetzt immer im gültigen Bereich (0 bis len-1)
            if self.turn_index < len(self.characters):
                rot = self.turn_index
            else:
                # Fallback, falls turn_index durch Löschen ungültig wurde
                rot = 0

        # Liste rotieren für Anzeige (Aktiver Char oben)
        n = len(self.characters)
        display_list = []
        for k in range(n):
            idx = (rot + k) % n
            display_list.append((idx, self.characters[idx]))

        for orig_idx, char in display_list:
            status_str = ", ".join(f"{s['effect']} (Rang {s['rank']}, {s['rounds']} Rd.)" for s in char.status)
            order = str(orig_idx + 1) if self.initiative_rolled else "-"

            # Werte formatieren (Aktuell / Max)
            lp_str = f"{char.lp}/{char.max_lp}"
            rp_str = f"{char.rp}/{char.max_rp}"
            sp_str = f"{char.sp}/{char.max_sp}"

            # Werte einfügen
            item_id = self.tree.insert("", tk.END, values=(order, char.name, char.char_type, lp_str, rp_str, sp_str, char.init, status_str))

            # Visuelles Feedback für niedrige LP (optional)
            if char.lp <= 0 or char.max_lp <= 0:
                self.tree.item(item_id, tags=('dead',))
            elif char.lp < (char.max_lp * 0.3): # Unter 30% LP
                self.tree.item(item_id, tags=('low_hp',))

        # Tags für Dark Mode angepasst
        self.tree.tag_configure('dead', background='#5e0000', foreground='#ffcccc') # Dunkelrot Hintergrund
        self.tree.tag_configure('low_hp', foreground='#ff5252')   # Helles Rot Schrift

    def get_selected_char(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showerror("Fehler", "Kein Charakter ausgewählt.")
            return None

        tree_index = self.tree.index(selection[0])

        # Rotation berücksichtigen
        rot = 0
        if self.initiative_rolled and self.turn_index >= 0:
            if self.turn_index < len(self.characters):
                rot = self.turn_index

        # Den tatsächlichen Index in der self.characters Liste berechnen
        actual_index = (rot + tree_index) % len(self.characters)

        return self.characters[actual_index]

    def log_message(self, msg):
        self.log.insert(tk.END, str(msg).strip() + "\n")
        self.log.see(tk.END)

