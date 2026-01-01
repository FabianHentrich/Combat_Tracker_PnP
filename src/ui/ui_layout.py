import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Callable
from src.utils.config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS, FONTS
from src.utils.utils import ToolTip, generate_health_bar
from src.ui.dice_roller import DiceRoller
from src.models.enums import DamageType, StatusEffectType, CharacterType

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class UILayout:
    def __init__(self, tracker: 'CombatTracker', root: tk.Tk):
        self.tracker = tracker
        self.root = root
        self.colors = COLORS

    def setup_ui(self) -> None:
        # Menübar erstellen
        self.create_menu()

        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- OBERER BEREICH: Schnelleingabe ---
        self.create_input_frame(main_frame)

        # --- MITTLERER BEREICH: Tabelle und Aktionen ---
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # Linke Seite: Tabelle (Treeview)
        self.create_treeview(content_frame)

        # Rechte Seite: Aktions-Panel
        self.create_action_panel(content_frame)

        # --- UNTERER BEREICH: Kampfsteuerung & Log ---
        self.create_bottom_area(main_frame)

    def create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)

        file_menu.add_command(label="Kampf speichern...", command=self.tracker.save_session)
        file_menu.add_command(label="Kampf laden...", command=self.tracker.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Bibliothek öffnen", command=self.tracker.library_handler.open_library_window)
        file_menu.add_command(label="Gegner importieren (Excel)...", command=self.tracker.load_enemies)
        file_menu.add_separator()
        file_menu.add_command(label="Einstellungen...", command=self.tracker.open_hotkey_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)

        # Theme Menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)

        from src.utils.config import THEMES
        for theme_name in THEMES.keys():
            theme_menu.add_command(label=theme_name, command=lambda t=theme_name: self.tracker.change_theme(t))

    def create_input_frame(self, parent: tk.Widget) -> None:
        input_frame = ttk.LabelFrame(parent, text="Neuen Charakter hinzufügen", padding="15", style="Card.TLabelframe")
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Zeile 0: Bibliothek (Button) und Excel Import
        ttk.Button(input_frame, text="📚 Bibliothek öffnen...", command=self.tracker.library_handler.open_library_window).grid(row=0, column=0, columnspan=2, padx=5, sticky="ew")
        ttk.Button(input_frame, text="Excel Import", command=lambda: self.tracker.load_enemies(None)).grid(row=0, column=2, columnspan=2, padx=5, sticky="ew")

        # Zeile 1: Eingabefelder (Row Index um 1 erhöht)
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, padx=5, sticky="w")
        self.tracker.entry_name = ttk.Entry(input_frame, width=20)
        self.tracker.entry_name.grid(row=1, column=1, padx=5)

        ttk.Label(input_frame, text="LP:").grid(row=1, column=2, padx=5, sticky="w")
        self.tracker.entry_lp = ttk.Entry(input_frame, width=8)
        self.tracker.entry_lp.grid(row=1, column=3, padx=5)

        ttk.Label(input_frame, text="RP:").grid(row=1, column=4, padx=5, sticky="w")
        self.tracker.entry_rp = ttk.Entry(input_frame, width=8)
        self.tracker.entry_rp.grid(row=1, column=5, padx=5)

        ttk.Label(input_frame, text="SP:").grid(row=1, column=6, padx=5, sticky="w")
        self.tracker.entry_sp = ttk.Entry(input_frame, width=8)
        self.tracker.entry_sp.grid(row=1, column=7, padx=5)

        ttk.Label(input_frame, text="GEW:").grid(row=1, column=10, padx=5, sticky="w")
        self.tracker.entry_gew = ttk.Entry(input_frame, width=8)
        self.tracker.entry_gew.grid(row=1, column=11, padx=5)

        ttk.Label(input_frame, text="INIT:").grid(row=1, column=8, padx=5, sticky="w")
        self.tracker.entry_init = ttk.Entry(input_frame, width=8)
        self.tracker.entry_init.grid(row=1, column=9, padx=5)

        ttk.Label(input_frame, text="Typ:").grid(row=1, column=12, padx=5, sticky="w")
        self.tracker.entry_type = ttk.Combobox(input_frame, values=[t.value for t in CharacterType], width=10, state="readonly")
        self.tracker.entry_type.set(CharacterType.ENEMY.value)
        self.tracker.entry_type.grid(row=1, column=13, padx=5)

        # Checkbox für "Sofort agieren"
        self.tracker.var_surprise = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Sofort dran", variable=self.tracker.var_surprise).grid(row=1, column=14, padx=5)

        ttk.Button(input_frame, text="Hinzufügen", command=self.tracker.add_character_quick).grid(row=1, column=15, padx=10)

    def create_treeview(self, parent: tk.Widget) -> None:
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("Order", "Name", "Typ", "LP", "RP", "SP", "GEW", "INIT", "Status")
        self.tracker.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        # Spalten konfigurieren
        self.tracker.tree.heading("Order", text="#")
        self.tracker.tree.column("Order", width=30, anchor="center", stretch=False)
        self.tracker.tree.heading("Name", text="Name")
        self.tracker.tree.column("Name", width=200, minwidth=100)
        self.tracker.tree.heading("Typ", text="Typ")
        self.tracker.tree.column("Typ", width=80, anchor="center", stretch=False)
        self.tracker.tree.heading("LP", text="LP (Balken)")
        self.tracker.tree.column("LP", width=200, anchor="center", stretch=False)
        self.tracker.tree.heading("RP", text="RP")
        self.tracker.tree.column("RP", width=60, anchor="center", stretch=False)
        self.tracker.tree.heading("SP", text="SP")
        self.tracker.tree.column("SP", width=60, anchor="center", stretch=False)
        self.tracker.tree.heading("GEW", text="GEW")
        self.tracker.tree.column("GEW", width=60, anchor="center", stretch=False)
        self.tracker.tree.heading("INIT", text="INIT")
        self.tracker.tree.column("INIT", width=60, anchor="center", stretch=False)
        self.tracker.tree.heading("Status", text="Status")
        # Status-Spalte breiter machen und stretch=False setzen, damit Scrollen erzwungen wird, wenn nötig
        self.tracker.tree.column("Status", width=700, minwidth=200, stretch=False)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tracker.tree.yview)
        self.tracker.tree.configure(yscroll=scrollbar.set)
        self.tracker.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Kontextmenü für Rechtsklick
        self.tracker.context_menu = tk.Menu(self.root, tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        self.tracker.context_menu.add_command(label="Löschen", command=self.tracker.delete_character)
        self.tracker.tree.bind("<Button-3>", self.tracker.show_context_menu)

    def create_action_panel(self, parent: tk.Widget) -> None:
        action_frame = ttk.LabelFrame(parent, text="Interaktion", padding="15", style="Card.TLabelframe")
        action_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0), ipadx=10)

        # Wert Eingabe (Groß)
        ttk.Label(action_frame, text="Wert:").pack(anchor="w")
        self.tracker.action_value = ttk.Entry(action_frame, font=FONTS["xl"], justify="center")
        self.tracker.action_value.pack(fill=tk.X, pady=(0, 10))
        self.tracker.action_value.insert(0, "0")

        # Typ Auswahl
        ttk.Label(action_frame, text="Typ:").pack(anchor="w")
        self.tracker.action_type = ttk.Combobox(action_frame, values=[t.value for t in DamageType], state="readonly")
        self.tracker.action_type.set(DamageType.NORMAL.value)
        self.tracker.action_type.pack(fill=tk.X, pady=(0, 15))

        # Tooltip für Schadenstyp
        self.create_tooltip(self.tracker.action_type, lambda: DAMAGE_DESCRIPTIONS.get(self.tracker.action_type.get(), ""))

        # Aktions-Buttons Grid
        btn_grid = ttk.Frame(action_frame, style="Card.TFrame")
        btn_grid.pack(fill=tk.X)

        # Zeile 1: Schaden / Heilen
        ttk.Button(btn_grid, text="⚔️ Schaden", command=self.tracker.deal_damage).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="💚 Heilen", command=self.tracker.apply_healing).grid(row=0, column=1, padx=2, pady=2, sticky="ew")

        # Zeile 2: Schild / Rüstung
        ttk.Button(btn_grid, text="🛡️ Schild +", command=self.tracker.apply_shield).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="👕 Rüstung +", command=self.tracker.apply_armor).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # --- Status Sektion (Inline) ---
        ttk.Label(action_frame, text="Status Effekt:").pack(anchor="w")

        status_frame = ttk.Frame(action_frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 5))

        self.tracker.status_combobox = ttk.Combobox(status_frame, values=[t.value for t in StatusEffectType], state="readonly")
        self.tracker.status_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.tracker.status_combobox.set(StatusEffectType.POISON.value)

        # Tooltip für Status
        self.create_tooltip(self.tracker.status_combobox, lambda: f"{self.tracker.status_combobox.get()}:\n{STATUS_DESCRIPTIONS.get(self.tracker.status_combobox.get(), 'Keine Info')}")

        # Rank und Dauer in einer Zeile
        rank_duration_frame = ttk.Frame(action_frame, style="Card.TFrame")
        rank_duration_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(rank_duration_frame, text="Rang:").pack(side=tk.LEFT)
        self.tracker.status_rank = ttk.Entry(rank_duration_frame, width=5)
        self.tracker.status_rank.pack(side=tk.LEFT, padx=(5, 15))
        self.tracker.status_rank.insert(0, "1")

        ttk.Label(rank_duration_frame, text="Dauer:").pack(side=tk.LEFT)
        self.tracker.status_duration = ttk.Entry(rank_duration_frame, width=5)
        self.tracker.status_duration.pack(side=tk.LEFT, padx=(5, 0))
        self.tracker.status_duration.insert(0, "3")

        ttk.Button(action_frame, text="Status hinzufügen", command=self.tracker.add_status_to_character).pack(fill=tk.X, pady=2)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Management Section
        ttk.Label(action_frame, text="Verwaltung:").pack(anchor="w")

        self.tracker.management_target_var = tk.StringVar(value="Ausgewählter Charakter")
        target_cb = ttk.Combobox(action_frame, textvariable=self.tracker.management_target_var,
                                 values=["Ausgewählter Charakter", "Alle Gegner", "Alle Spieler", "Alle NPCs", "Alle Charaktere"],
                                 state="readonly")
        target_cb.pack(fill=tk.X, pady=(0, 5))

        btn_frame = ttk.Frame(action_frame, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        self.tracker.btn_edit = ttk.Button(btn_frame, text="Bearbeiten", command=self.tracker.manage_edit)
        self.tracker.btn_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        ttk.Button(btn_frame, text="Löschen", command=self.tracker.manage_delete).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # Event binding to enable/disable edit button
        def update_edit_state(event):
            if self.tracker.management_target_var.get() == "Ausgewählter Charakter":
                self.tracker.btn_edit.state(["!disabled"])
            else:
                self.tracker.btn_edit.state(["disabled"])

        target_cb.bind("<<ComboboxSelected>>", update_edit_state)

    def create_bottom_area(self, parent: tk.Widget) -> None:
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Button(control_frame, text="🎲 Initiative würfeln & sortieren", command=self.tracker.roll_initiative_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏭ Nächster Zug", command=self.tracker.next_turn).pack(side=tk.LEFT, padx=5)

        # Reset Initiative Menu
        reset_btn = ttk.Menubutton(control_frame, text="🔄 Init Reset")
        reset_menu = tk.Menu(reset_btn, tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        reset_menu.add_command(label="Alle", command=lambda: self.tracker.reset_initiative("All"))
        reset_menu.add_command(label="Nur Gegner", command=lambda: self.tracker.reset_initiative("Gegner"))
        reset_menu.add_command(label="Nur Spieler", command=lambda: self.tracker.reset_initiative("Spieler"))
        reset_menu.add_command(label="Nur NPCs", command=lambda: self.tracker.reset_initiative("NPC"))
        reset_btn.config(menu=reset_menu)
        reset_btn.pack(side=tk.LEFT, padx=5)

        # Undo / Redo Buttons
        ttk.Button(control_frame, text="↩ Undo", command=self.tracker.undo_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="↪ Redo", command=self.tracker.redo_action).pack(side=tk.LEFT, padx=5)

        # Rundenzähler
        self.tracker.round_label = ttk.Label(control_frame, text=f"Runde: {self.tracker.engine.round_number}", font=FONTS["large"], background=self.colors["bg"])
        self.tracker.round_label.pack(side=tk.RIGHT, padx=20)

        # Split Bottom Area: Log (Left) | Dice Roller (Right)
        bottom_content = ttk.Frame(bottom_frame)
        bottom_content.pack(fill=tk.BOTH, expand=True)

        # Log
        log_frame = ttk.LabelFrame(bottom_content, text="Kampfprotokoll", style="Card.TLabelframe")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.tracker.log = tk.Text(log_frame, height=8, state="normal", bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"], font=FONTS["log"])
        self.tracker.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.tracker.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tracker.log.configure(yscrollcommand=scrollbar.set)

        # Dice Roller
        self.tracker.dice_roller = DiceRoller(bottom_content, self.colors)
        self.tracker.dice_roller.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0))

    def create_tooltip(self, widget: tk.Widget, text_func: Callable[[], str]) -> None:
        tt = ToolTip(widget, text_func, color_provider=lambda: (self.colors["tooltip_bg"], self.colors["tooltip_fg"]))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    def update_listbox(self) -> None:
        """
        Aktualisiert die Anzeige der Charakterliste (Treeview).
        Wird automatisch aufgerufen, wenn sich der Zustand in der Engine ändert.
        """
        tree = self.tracker.tree
        engine = self.tracker.engine

        # Treeview leeren
        for item in tree.get_children():
            tree.delete(item)

        # Update Round Label
        if hasattr(self.tracker, 'round_label') and self.tracker.round_label:
            self.tracker.round_label.config(text=f"Runde: {engine.round_number}")

        if not engine.characters:
            return

        # Rotation berechnen
        rot = 0
        if engine.initiative_rolled and engine.turn_index >= 0:
            # turn_index ist jetzt immer im gültigen Bereich (0 bis len-1)
            if engine.turn_index < len(engine.characters):
                rot = engine.turn_index
            else:
                # Fallback, falls turn_index durch Löschen ungültig wurde
                rot = 0

        # Liste rotieren für Anzeige (Aktiver Char oben)
        n = len(engine.characters)
        display_list = []
        for k in range(n):
            idx = (rot + k) % n
            display_list.append((idx, engine.characters[idx]))

        for orig_idx, char in display_list:
            status_items = []
            for s in char.status:
                name = s.name
                if hasattr(name, 'value'):
                    name = name.value
                status_items.append(f"{name} (Rang {s.rank}, {s.duration} Rd.)")

            status_str = ", ".join(status_items)
            order = str(orig_idx + 1) if engine.initiative_rolled else "-"

            # Werte formatieren (Aktuell / Max)
            lp_str = f"{char.lp}/{char.max_lp}"
            rp_str = f"{char.rp}/{char.max_rp}"
            sp_str = f"{char.sp}/{char.max_sp}"

            # Health Bar generieren
            health_bar = generate_health_bar(char.lp, char.max_lp, length=10)

            # Werte einfügen
            item_id = tree.insert("", tk.END, values=(order, char.name, char.char_type, health_bar, rp_str, sp_str, char.gew, char.init, status_str))

            # Visuelles Feedback für niedrige LP (optional)
            if char.lp <= 0 or char.max_lp <= 0:
                tree.item(item_id, tags=('dead',))
            elif char.lp < (char.max_lp * 0.3): # Unter 30% LP
                tree.item(item_id, tags=('low_hp',))

        # Tags für Dark Mode angepasst
        tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
        tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

        # Autosave trigger
        self.tracker.autosave()
