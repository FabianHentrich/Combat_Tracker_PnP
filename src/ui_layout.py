import tkinter as tk
from tkinter import ttk
from .config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS
from .utils import ToolTip

class UILayout:
    def __init__(self, tracker, root):
        self.tracker = tracker
        self.root = root
        self.colors = COLORS

    def setup_ui(self):
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

    def create_input_frame(self, parent):
        input_frame = ttk.LabelFrame(parent, text="Neuen Charakter hinzufügen", padding="15", style="Card.TLabelframe")
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Grid Layout für Eingabe
        ttk.Label(input_frame, text="Name:", background=self.colors["panel"]).grid(row=0, column=0, padx=5, sticky="w")
        self.tracker.entry_name = ttk.Entry(input_frame, width=20)
        self.tracker.entry_name.grid(row=0, column=1, padx=5)

        ttk.Label(input_frame, text="LP:", background=self.colors["panel"]).grid(row=0, column=2, padx=5, sticky="w")
        self.tracker.entry_lp = ttk.Entry(input_frame, width=8)
        self.tracker.entry_lp.grid(row=0, column=3, padx=5)

        ttk.Label(input_frame, text="RP:", background=self.colors["panel"]).grid(row=0, column=4, padx=5, sticky="w")
        self.tracker.entry_rp = ttk.Entry(input_frame, width=8)
        self.tracker.entry_rp.grid(row=0, column=5, padx=5)

        ttk.Label(input_frame, text="SP:", background=self.colors["panel"]).grid(row=0, column=6, padx=5, sticky="w")
        self.tracker.entry_sp = ttk.Entry(input_frame, width=8)
        self.tracker.entry_sp.grid(row=0, column=7, padx=5)

        ttk.Label(input_frame, text="INIT:", background=self.colors["panel"]).grid(row=0, column=8, padx=5, sticky="w")
        self.tracker.entry_init = ttk.Entry(input_frame, width=8)
        self.tracker.entry_init.grid(row=0, column=9, padx=5)

        ttk.Label(input_frame, text="Typ:", background=self.colors["panel"]).grid(row=0, column=10, padx=5, sticky="w")
        self.tracker.entry_type = ttk.Combobox(input_frame, values=["Spieler", "Gegner", "NPC"], width=10, state="readonly")
        self.tracker.entry_type.set("Gegner")
        self.tracker.entry_type.grid(row=0, column=11, padx=5)

        # Checkbox für "Sofort agieren"
        self.tracker.var_surprise = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Sofort dran", variable=self.tracker.var_surprise).grid(row=0, column=12, padx=5)

        ttk.Button(input_frame, text="Hinzufügen", command=self.tracker.add_character_quick).grid(row=0, column=13, padx=10)
        ttk.Button(input_frame, text="Excel Import", command=lambda: self.tracker.load_enemies(None)).grid(row=0, column=14, padx=10)

    def create_treeview(self, parent):
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("Order", "Name", "Typ", "LP", "RP", "SP", "INIT", "Status")
        self.tracker.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        # Spalten konfigurieren
        self.tracker.tree.heading("Order", text="#")
        self.tracker.tree.column("Order", width=30, anchor="center")
        self.tracker.tree.heading("Name", text="Name")
        self.tracker.tree.column("Name", width=150)
        self.tracker.tree.heading("Typ", text="Typ")
        self.tracker.tree.column("Typ", width=80, anchor="center")
        self.tracker.tree.heading("LP", text="LP")
        self.tracker.tree.column("LP", width=60, anchor="center")
        self.tracker.tree.heading("RP", text="RP")
        self.tracker.tree.column("RP", width=60, anchor="center")
        self.tracker.tree.heading("SP", text="SP")
        self.tracker.tree.column("SP", width=60, anchor="center")
        self.tracker.tree.heading("INIT", text="INIT")
        self.tracker.tree.column("INIT", width=60, anchor="center")
        self.tracker.tree.heading("Status", text="Status")
        self.tracker.tree.column("Status", width=250)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tracker.tree.yview)
        self.tracker.tree.configure(yscroll=scrollbar.set)
        self.tracker.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Kontextmenü für Rechtsklick
        self.tracker.context_menu = tk.Menu(self.root, tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        self.tracker.context_menu.add_command(label="Löschen", command=self.tracker.delete_character)
        self.tracker.tree.bind("<Button-3>", self.tracker.show_context_menu)

    def create_action_panel(self, parent):
        action_frame = ttk.LabelFrame(parent, text="Interaktion", padding="15", style="Card.TLabelframe")
        action_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0), ipadx=10)

        # Wert Eingabe (Groß)
        ttk.Label(action_frame, text="Wert:", background=self.colors["panel"]).pack(anchor="w")
        self.tracker.action_value = ttk.Entry(action_frame, font=('Segoe UI', 14), justify="center")
        self.tracker.action_value.pack(fill=tk.X, pady=(0, 10))
        self.tracker.action_value.insert(0, "0")

        # Typ Auswahl
        ttk.Label(action_frame, text="Typ:", background=self.colors["panel"]).pack(anchor="w")
        self.tracker.action_type = ttk.Combobox(action_frame, values=["Normal", "Durchschlagend", "Direkt", "Verwesung", "Gift", "Feuer", "Blitz", "Kälte"], state="readonly")
        self.tracker.action_type.set("Normal")
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
        ttk.Label(action_frame, text="Status Effekt:", background=self.colors["panel"]).pack(anchor="w")

        status_frame = ttk.Frame(action_frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 5))

        self.tracker.status_combobox = ttk.Combobox(status_frame, values=[
            "Vergiftung", "Verbrennung", "Blutung", "Unterkühlung",
            "Betäubung", "Erosion", "Erschöpfung", "Verwirrung"
        ], state="normal")
        self.tracker.status_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.tracker.status_combobox.set("Vergiftung")

        # Tooltip für Status
        self.create_tooltip(self.tracker.status_combobox, lambda: f"{self.tracker.status_combobox.get()}:\n{STATUS_DESCRIPTIONS.get(self.tracker.status_combobox.get(), 'Keine Info')}")

        # Rank und Dauer in einer Zeile
        rank_duration_frame = ttk.Frame(action_frame, style="Card.TFrame")
        rank_duration_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(rank_duration_frame, text="Rang:", background=self.colors["panel"]).pack(side=tk.LEFT)
        self.tracker.status_rank = ttk.Entry(rank_duration_frame, width=5)
        self.tracker.status_rank.pack(side=tk.LEFT, padx=(5, 15))
        self.tracker.status_rank.insert(0, "1")

        ttk.Label(rank_duration_frame, text="Dauer:", background=self.colors["panel"]).pack(side=tk.LEFT)
        self.tracker.status_duration = ttk.Entry(rank_duration_frame, width=5)
        self.tracker.status_duration.pack(side=tk.LEFT, padx=(5, 0))
        self.tracker.status_duration.insert(0, "3")

        ttk.Button(action_frame, text="Status hinzufügen", command=self.tracker.add_status_to_character).pack(fill=tk.X, pady=2)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Management Buttons
        ttk.Button(action_frame, text="Bearbeiten", command=self.tracker.edit_selected_char).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="❌ Löschen", command=self.tracker.delete_character).pack(fill=tk.X, pady=2)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        ttk.Label(action_frame, text="Gruppen löschen:", background=self.colors["panel"]).pack(anchor="w")
        ttk.Button(action_frame, text="Alle Gegner", command=lambda: self.tracker.delete_group("Gegner")).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Alle NPCs", command=lambda: self.tracker.delete_group("NPC")).pack(fill=tk.X, pady=2)
        ttk.Button(action_frame, text="Alle Spieler", command=lambda: self.tracker.delete_group("Spieler")).pack(fill=tk.X, pady=2)

    def create_bottom_area(self, parent):
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

        # Rundenzähler
        self.tracker.round_label = ttk.Label(control_frame, text=f"Runde: {self.tracker.round_number}", font=('Segoe UI', 12, 'bold'), background=self.colors["bg"])
        self.tracker.round_label.pack(side=tk.RIGHT, padx=20)

        # Log
        log_frame = ttk.LabelFrame(bottom_frame, text="Kampfprotokoll", style="Card.TLabelframe")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.tracker.log = tk.Text(log_frame, height=8, width=80, state='normal', font=("Consolas", 9),
                           bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"], relief="flat")
        log_scroll = ttk.Scrollbar(log_frame, command=self.tracker.log.yview)
        self.tracker.log.config(yscrollcommand=log_scroll.set)

        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tracker.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def create_tooltip(self, widget, text_func):
        tt = ToolTip(widget, text_func)
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)
