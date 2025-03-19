import tkinter as tk
from tkinter import messagebox, filedialog
import random
import json


# Hilfsfunktionen für Würfelmechanik
def roll_with_aces(rang):
    dice_size = {1: 4, 2: 6, 3: 8, 4: 10, 5: 12, 6: 20}.get(rang, 4)
    total = 0
    roll = random.randint(1, dice_size)
    total += roll
    while roll == dice_size:
        roll = random.randint(1, dice_size)
        total += roll
    return total


# Charakter-Klasse für SC und Gegner
class Character:
    def __init__(self, name, lp, rp, sp, initiative):
        self.name = name
        self.lp = lp
        self.rp = rp
        self.sp = sp
        self.initiative = initiative  # INIT wird jetzt manuell gesetzt
        self.status = []
        self.skip_turns = 0

    def apply_damage(self, dmg):
        log = f"{self.name} erleidet {dmg} Schaden!\n"
        if self.sp > 0:
            absorb = min(self.sp, dmg)
            self.sp -= absorb
            dmg -= absorb
            log += f"→ {absorb} Schaden vom Schild absorbiert.\n"
        if dmg > 0 and self.rp > 0:
            absorb = min(self.rp * 2, dmg)
            rp_loss = (absorb + 1) // 2
            self.rp -= rp_loss
            dmg -= absorb
            log += f"→ {absorb} Schaden durch Rüstung abgefangen.\n"
        if dmg > 0:
            self.lp -= dmg
            log += f"→ {dmg} Schaden auf Lebenspunkte!\n"
        if self.lp <= 0:
            log += f"⚔️ {self.name} ist kampfunfähig!\n"
        return log

    def add_status(self, effect, duration):
        self.status.append({"effect": effect, "rounds": duration})

    def update_status(self):
        new_status = []
        for s in self.status:
            s["rounds"] -= 1
            if s["rounds"] > 0:
                new_status.append(s)
        self.status = new_status
        self.skip_turns = sum(1 for s in self.status if s["effect"] == "stunned")

    def heal(self, healing_points):
        """Heilt den Charakter um eine bestimmte Anzahl an Lebenspunkten."""
        self.lp += healing_points
        return f"{self.name} wird um {healing_points} LP geheilt! Aktuelle LP: {self.lp}"


# Hauptklasse für den Kampf-Tracker
class CombatTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("PnP Combat Tracker")
        self.characters = []
        self.turn_index = 0
        self.enemy_data = {}
        self.setup_ui()
        self.load_enemy_data()

    def setup_ui(self):
        # Charakter-Eingabe oben
        self.frame_top = tk.Frame(self.root)
        self.frame_top.pack()

        tk.Button(self.frame_top, text="Einzelcharakter hinzufügen",
                  command=self.add_single_enemy).pack(side=tk.LEFT, padx=10, pady=5)
        tk.Button(self.frame_top, text="Charakter löschen",
                  command=self.delete_character).pack(side=tk.LEFT, padx=10, pady=5)

        # Liste der Charaktere
        self.listbox = tk.Listbox(self.root, width=80)
        self.listbox.pack()

        # Steuerungselemente unter der Liste
        self.frame_controls = tk.Frame(self.root)
        self.frame_controls.pack()

        # links
        tk.Button(self.frame_controls, text="Name ändern", command=self.edit_name).grid(row=0, column=0, padx=10, pady=5)
        tk.Button(self.frame_controls, text="LP ändern", command=self.edit_lp).grid(row=1, column=0, padx=10, pady=5)
        tk.Button(self.frame_controls, text="RP ändern", command=self.edit_rp).grid(row=2, column=0, padx=10, pady=5)
        tk.Button(self.frame_controls, text="SP ändern", command=self.edit_sp).grid(row=3, column=0, padx=10, pady=5)

        # mitte
        tk.Button(self.frame_controls, text="Schaden zufügen", command=self.deal_damage).grid(row=0, column=1, padx=10, pady=5)
        tk.Button(self.frame_controls, text="Heilung anwenden", command=self.apply_healing).grid(row=1, column=1, padx=10, pady=5)
        tk.Button(self.frame_controls, text="Schild anwenden", command=self.apply_shield).grid(row=2, column=1, padx=10, pady=5)
        tk.Button(self.frame_controls, text="Rüstung anwenden", command=self.apply_armor).grid(row=3, column=1, padx=10, pady=5)

        # rechts
        tk.Button(self.frame_controls, text="Status hinzufügen", command=self.add_status_to_character).grid(row=0, column=2, padx=10, pady=5)
        tk.Button(self.frame_controls, text="Gegnergruppe laden", command=self.load_enemy_group).grid(row=1, column=2, padx=10, pady=5)
        tk.Button(self.frame_controls, text="Initiative ordnen", command=self.roll_initiative_all).grid(row=2, column=2, padx=10, pady=5)
        tk.Button(self.frame_controls, text="Nächster Zug", command=self.next_turn).grid(row=3, column=2, padx=10, pady=5)

        # Log-Anzeige mit Scrollbar
        log_frame = tk.Frame(self.root)
        log_frame.pack()

        self.log = tk.Text(log_frame, height=10, width=80)
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.config(command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log.config(yscrollcommand=scrollbar.set)
        self.log.pack()

    def roll_initiative_all(self):
        """Sorts characters based on their initiative."""
        for char in self.characters:
            char.update_status()
        self.characters.sort(key=lambda c: c.initiative, reverse=True)
        self.turn_index = 0
        self.update_listbox()
        self.log.insert(tk.END, "Initiative-Reihenfolge erstellt!\n")

    def next_turn(self):
        """Moves to the next turn, considering status and conditions."""
        if not self.characters:
            return
        char = self.characters[self.turn_index % len(self.characters)]
        char.update_status()
        if char.lp <= 0:
            self.log.insert(tk.END, f"{char.name} ist kampfunfähig.\n")
        elif char.skip_turns > 0:
            self.log.insert(tk.END, f"{char.name} setzt diese Runde aus!\n")
        else:
            self.log.insert(tk.END, f"{char.name} ist am Zug!\n")
        self.turn_index += 1
        self.update_listbox()

    def deal_damage(self):
        """Allows dealing damage to the selected character."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return
        index = selection[0]
        char = self.characters[index]
        dmg = simple_input_dialog(self.root, "Schaden eingeben", "Schaden:")
        if dmg is None:
            return
        try:
            dmg = int(dmg)
        except ValueError:
            messagebox.showerror("Fehler", "Ungültiger Schaden.")
            return
        log_text = char.apply_damage(dmg)
        self.log.insert(tk.END, log_text + "\n")
        self.update_listbox()

    def add_status_to_character(self):
        """Adds a status effect to the selected character."""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return
        index = selection[0]
        char = self.characters[index]
        status = simple_input_dialog(self.root, "Status hinzufügen", "Status:")
        duration = simple_input_dialog(self.root, "Rundenanzahl", "Dauer in Runden:")
        if status is None or duration is None:
            return
        try:
            duration = int(duration)
        except ValueError:
            messagebox.showerror("Fehler", "Ungültige Rundenzahl.")
            return
        char.add_status(status, duration)
        self.log.insert(tk.END, f"{char.name} erhält Status '{status}' für {duration} Runden.\n")
        self.update_listbox()

    def load_enemy_group(self):
        """Loads a group of enemies from a file."""
        file_path = filedialog.askopenfilename(title="Gegnergruppe laden", filetypes=[("JSON Dateien", "*.json")])
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                enemy_group = json.load(file)
                for enemy in enemy_group:
                    name = enemy.get("name", "Unbenannter Gegner")
                    lp = enemy.get("lp", 10)
                    rp = enemy.get("rp", 5)
                    sp = enemy.get("sp", 5)
                    init = enemy.get("init", 10)
                    char = Character(name, lp, rp, sp, init)
                    self.characters.append(char)
                self.update_listbox()
                self.log.insert(tk.END, f"Gegnergruppe aus '{file_path}' geladen!\n")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Gegnergruppe:\n{e}")

    def add_single_enemy(self):
        """Adds a single enemy to the list with all attributes in one dialog."""
        # Combine all the inputs into a single dialog
        user_input = simple_input_dialog(self.root, "Einzelgegner hinzufügen",
                                         "Gib die Werte für den Gegner im Format: Name, LP, RP, SP, INIT (z.B. Goblin, 30, 10, 5, 12):")

        # Parse the user input
        if user_input:
            try:
                # Split the input and assign values
                inputs = user_input.split(',')
                name = inputs[0].strip()
                lp = int(inputs[1].strip())
                rp = int(inputs[2].strip())
                sp = int(inputs[3].strip())
                init = int(inputs[4].strip())

                # Create the enemy character
                enemy = Character(name, lp, rp, sp, init)
                self.characters.append(enemy)
                self.update_listbox()
                self.log.insert(tk.END, f"{name} wurde als Einzelgegner hinzugefügt!\n")
            except (ValueError, IndexError):
                messagebox.showerror("Fehler",
                                     "Ungültige Eingabe. Stelle sicher, dass du alle Werte im richtigen Format eingibst.")

    def load_enemy_data(self):
        # Open file dialog to load only .txt files
        file_path = filedialog.askopenfilename(title="Gegnerdaten laden", filetypes=[("Text Dateien", "*.txt")])
        if not file_path:
            return

        try:
            # Open the file and read its contents
            with open(file_path, "r", encoding="utf-8") as file:
                file_content = file.read()  # Read the content of the file

                # Here, you can either store the data to use it later or process it
                # For now, we just store it in a dictionary or class for later use.
                self.enemy_data = file_content  # Store file content

                # Create a button dynamically to activate this content
                tk.Button(self.frame_controls, text=f"Aktiviere {file_path.split('/')[-1]}",
                          command=lambda: self.activate_enemy_data(file_content)).pack(side=tk.LEFT)

                # Inform the user
                messagebox.showinfo("Erfolg",
                                    f"Gegnerdaten aus '{file_path}' geladen und Button zum Aktivieren erstellt!")

        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden der Datei:\n{e}")

    def activate_enemy_data(self, data):
        # This function will activate the loaded enemy data
        # For now, we'll just display it in the log
        self.log.insert(tk.END, f"Gegnerdaten aktiviert:\n{data}\n")

    def add_character(self):
        name = self.entry_name.get()
        try:
            lp = int(self.entry_lp.get())
            rp = int(self.entry_rp.get())
            sp = int(self.entry_sp.get())
            init = int(self.entry_init.get())  # Manuelle INIT Eingabe
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Werte eingeben.")
            return
        char = Character(name, lp, rp, sp, init)  # INIT wird nun mit übergeben
        self.characters.append(char)
        self.update_listbox()

    def edit_name(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        index = selection[0]
        char = self.characters[index]
        name = simple_input_dialog(self.root, "Name bearbeiten", "Neuen Namen eingeben:", char.name)
        char.name = name or char.name
        self.update_listbox()
        self.log.insert(tk.END, f"Name von {char.name} geändert.\n")

    def edit_lp(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        index = selection[0]
        char = self.characters[index]

        lp = simple_input_dialog(self.root, "LP bearbeiten", "Neue LP Eingabe:", str(char.lp))

        try:
            char.lp = int(lp) if lp else char.lp
            messagebox.showinfo("Erfolg", "LP erfolgreich geändert!")

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Werte eingeben.")
        self.update_listbox()
        self.log.insert(tk.END, f"LP von {char.name} auf {char.lp} geändert.\n")

    def edit_rp(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        index = selection[0]
        char = self.characters[index]

        rp = simple_input_dialog(self.root, "RP bearbeiten", "Neue RP Eingabe:", str(char.rp))

        try:
            char.rp = int(rp) if rp else char.rp
            messagebox.showinfo("Erfolg", "RP erfolgreich geändert!")

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Werte eingeben.")
        self.update_listbox()
        self.log.insert(tk.END, f"RP von {char.name} auf {char.rp} geändert.\n")

    def edit_sp(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        index = selection[0]
        char = self.characters[index]

        sp = simple_input_dialog(self.root, "SP bearbeiten", "Neue SP Eingabe:", str(char.sp))

        try:
            char.sp = int(sp) if sp else char.sp
            messagebox.showinfo("Erfolg", "SP erfolgreich geändert!")

        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige Werte eingeben.")
        self.update_listbox()
        self.log.insert(tk.END, f"SP von {char.name} auf {char.sp} geändert.\n")

    def delete_character(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showerror("Fehler", "Wähle zuerst einen Charakter aus.")
            return

        index = selection[0]
        del self.characters[index]
        self.update_listbox()
        self.log.insert(tk.END, "Charakter gelöscht.\n")

    def apply_healing(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Fehler", "Wähle mindestens einen Charakter aus.")
            return

        healing_value = simple_input_dialog(self.root, "Heilungswert", "Heilungswert für ausgewählte Charaktere:")
        if healing_value:
            try:
                healing_value = int(healing_value)
            except ValueError:
                messagebox.showerror("Fehler", "Ungültiger Heilungswert.")
                return

            for idx in selected_indices:
                char = self.characters[idx]
                heal_log = char.heal(healing_value)
                self.log.insert(tk.END, heal_log + "\n")
            self.update_listbox()

    def apply_shield(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Fehler", "Wähle mindestens einen Charakter aus.")
            return
        shield_value = simple_input_dialog(self.root, "Schildpunkte hinzufügen",
                                           "Schildpunkte für ausgewählte Charaktere:")
        if shield_value:
            try:
                shield_value = int(shield_value)
            except ValueError:
                messagebox.showerror("Fehler", "Ungültiger Wert für Schildpunkte.")
                return

            for idx in selected_indices:
                char = self.characters[idx]
                char.sp += shield_value
                self.log.insert(tk.END, f"{char.name} erhält {shield_value} zusätzliche SP! Aktuelle SP: {char.sp}\n")

            self.update_listbox()

    def apply_armor(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showerror("Fehler", "Wähle mindestens einen Charakter aus.")
            return
        armor_value = simple_input_dialog(self.root, "Rüstungspunkte hinzufügen",
                                          "Rüstungspunkte für ausgewählte Charaktere:")
        if armor_value:
            try:
                armor_value = int(armor_value)
            except ValueError:
                messagebox.showerror("Fehler", "Ungültiger Wert für Rüstungspunkte.")
                return

            for idx in selected_indices:
                char = self.characters[idx]
                char.rp += armor_value
                self.log.insert(tk.END, f"{char.name} erhält {armor_value} zusätzliche RP! Aktuelle RP: {char.rp}\n")

            self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for char in self.characters:
            status_list = ", ".join(f"{s['effect']} ({s['rounds']})" for s in char.status)
            self.listbox.insert(tk.END,
                                f"{char.name} | INIT: {char.initiative} | LP: {char.lp} | RP: {char.rp} | SP: {char.sp} | Status: {status_list}")


# Helper function for input dialogs
def simple_input_dialog(root, title, prompt, default_value=""):
    def on_ok():
        nonlocal value
        value = entry.get()
        dialog.destroy()

    value = default_value
    dialog = tk.Toplevel(root)
    dialog.title(title)

    tk.Label(dialog, text=prompt).pack()
    entry = tk.Entry(dialog)
    entry.insert(0, default_value)
    entry.pack()
    tk.Button(dialog, text="OK", command=on_ok).pack()

    dialog.transient(root)
    dialog.grab_set()
    root.wait_window(dialog)

    return value


if __name__ == "__main__":
    root = tk.Tk()
    app = CombatTracker(root)
    root.mainloop()
