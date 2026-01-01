import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING, Callable, Dict, Any, Optional, List
from src.utils.config import COLORS, DAMAGE_DESCRIPTIONS, STATUS_DESCRIPTIONS, FONTS
from src.utils.utils import ToolTip, generate_health_bar
from src.ui.dice_roller import DiceRoller
from src.models.enums import DamageType, StatusEffectType, CharacterType
from src.ui.interfaces import ICombatView
from src.ui.audio_player_view import AudioPlayerWidget

if TYPE_CHECKING:
    from src.ui.main_window import CombatTracker

class MainView(ICombatView):
    def __init__(self, controller: 'CombatTracker', root: tk.Tk):
        self.controller = controller
        self.root = root
        self.colors = COLORS

        # Widgets
        self.entry_name: Optional[ttk.Entry] = None
        self.entry_lp: Optional[ttk.Entry] = None
        self.entry_rp: Optional[ttk.Entry] = None
        self.entry_sp: Optional[ttk.Entry] = None
        self.entry_init: Optional[ttk.Entry] = None
        self.entry_gew: Optional[ttk.Entry] = None
        self.entry_type: Optional[ttk.Combobox] = None
        self.var_surprise: Optional[tk.BooleanVar] = None

        self.tree: Optional[ttk.Treeview] = None
        self.context_menu: Optional[tk.Menu] = None

        self.action_value: Optional[ttk.Entry] = None
        self.action_type: Optional[ttk.Combobox] = None
        self.status_combobox: Optional[ttk.Combobox] = None
        self.status_rank: Optional[ttk.Entry] = None
        self.status_duration: Optional[ttk.Entry] = None

        self.management_target_var: Optional[tk.StringVar] = None
        self.btn_edit: Optional[ttk.Button] = None

        self.round_label: Optional[ttk.Label] = None
        self.log: Optional[tk.Text] = None
        self.dice_roller: Optional[DiceRoller] = None

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

        # Rechte Seite: Container für Player und Aktionen
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))

        # Player
        self.create_audio_player(right_frame)

        # Aktions-Panel
        self.create_action_panel(right_frame)

        # --- UNTERER BEREICH: Kampfsteuerung & Log ---
        self.create_bottom_area(main_frame)

    def create_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Datei", menu=file_menu)

        file_menu.add_command(label="Kampf speichern...", command=self.controller.save_session)
        file_menu.add_command(label="Kampf laden...", command=self.controller.load_session)
        file_menu.add_separator()
        file_menu.add_command(label="Bibliothek öffnen", command=self.controller.library_handler.open_library_window)
        file_menu.add_command(label="Gegner importieren (Excel)...", command=self.controller.load_enemies)
        file_menu.add_separator()
        file_menu.add_command(label="Einstellungen...", command=self.controller.open_hotkey_settings)
        file_menu.add_command(label="Musikeinstellungen...", command=self.controller.open_audio_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.root.quit)

        # Theme Menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)

        from src.utils.config import THEMES
        for theme_name in THEMES.keys():
            theme_menu.add_command(label=theme_name, command=lambda t=theme_name: self.controller.change_theme(t))

    def create_input_frame(self, parent: tk.Widget) -> None:
        input_frame = ttk.LabelFrame(parent, text="Neuen Charakter hinzufügen", padding="15", style="Card.TLabelframe")
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Zeile 0: Bibliothek (Button) und Excel Import
        ttk.Button(input_frame, text="📚 Bibliothek öffnen...", command=self.controller.library_handler.open_library_window).grid(row=0, column=0, columnspan=2, padx=5, sticky="ew")
        ttk.Button(input_frame, text="Excel Import", command=lambda: self.controller.load_enemies(None)).grid(row=0, column=2, columnspan=2, padx=5, sticky="ew")

        # Zeile 1: Eingabefelder
        ttk.Label(input_frame, text="Name:").grid(row=1, column=0, padx=5, sticky="w")
        self.entry_name = ttk.Entry(input_frame, width=20)
        self.entry_name.grid(row=1, column=1, padx=5)

        ttk.Label(input_frame, text="LP:").grid(row=1, column=2, padx=5, sticky="w")
        self.entry_lp = ttk.Entry(input_frame, width=8)
        self.entry_lp.grid(row=1, column=3, padx=5)

        ttk.Label(input_frame, text="RP:").grid(row=1, column=4, padx=5, sticky="w")
        self.entry_rp = ttk.Entry(input_frame, width=8)
        self.entry_rp.grid(row=1, column=5, padx=5)

        ttk.Label(input_frame, text="SP:").grid(row=1, column=6, padx=5, sticky="w")
        self.entry_sp = ttk.Entry(input_frame, width=8)
        self.entry_sp.grid(row=1, column=7, padx=5)

        ttk.Label(input_frame, text="GEW:").grid(row=1, column=10, padx=5, sticky="w")
        self.entry_gew = ttk.Entry(input_frame, width=8)
        self.entry_gew.grid(row=1, column=11, padx=5)

        ttk.Label(input_frame, text="INIT:").grid(row=1, column=8, padx=5, sticky="w")
        self.entry_init = ttk.Entry(input_frame, width=8)
        self.entry_init.grid(row=1, column=9, padx=5)

        ttk.Label(input_frame, text="Typ:").grid(row=1, column=12, padx=5, sticky="w")
        self.entry_type = ttk.Combobox(input_frame, values=[t.value for t in CharacterType], width=10, state="readonly")
        self.entry_type.set(CharacterType.ENEMY.value)
        self.entry_type.grid(row=1, column=13, padx=5)

        # Checkbox für "Sofort agieren"
        self.var_surprise = tk.BooleanVar()
        ttk.Checkbutton(input_frame, text="Sofort dran", variable=self.var_surprise).grid(row=1, column=14, padx=5)

        ttk.Button(input_frame, text="Hinzufügen", command=self.controller.add_character_quick).grid(row=1, column=15, padx=10)

    def create_treeview(self, parent: tk.Widget) -> None:
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        columns = ("Order", "Name", "Typ", "LP", "RP", "SP", "GEW", "INIT", "Status")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        # Spalten konfigurieren
        self.tree.heading("Order", text="#")
        self.tree.column("Order", width=30, anchor="center", stretch=False)
        self.tree.heading("Name", text="Name")
        self.tree.column("Name", width=200, minwidth=100)
        self.tree.heading("Typ", text="Typ")
        self.tree.column("Typ", width=80, anchor="center", stretch=False)
        self.tree.heading("LP", text="LP (Balken)")
        self.tree.column("LP", width=200, anchor="center", stretch=False)
        self.tree.heading("RP", text="RP")
        self.tree.column("RP", width=60, anchor="center", stretch=False)
        self.tree.heading("SP", text="SP")
        self.tree.column("SP", width=60, anchor="center", stretch=False)
        self.tree.heading("GEW", text="GEW")
        self.tree.column("GEW", width=60, anchor="center", stretch=False)
        self.tree.heading("INIT", text="INIT")
        self.tree.column("INIT", width=60, anchor="center", stretch=False)
        self.tree.heading("Status", text="Status")
        self.tree.column("Status", width=700, minwidth=200, stretch=False)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Kontextmenü für Rechtsklick
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        self.context_menu.add_command(label="Löschen", command=self.controller.delete_character)
        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event: tk.Event) -> None:
        """Zeigt das Kontextmenü bei Rechtsklick auf die Tabelle."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def create_audio_player(self, parent: tk.Widget) -> None:
        player_frame = AudioPlayerWidget(parent, self.controller.audio_controller, self.controller.open_audio_settings)
        player_frame.pack(fill=tk.X, pady=(0, 15))

    def create_action_panel(self, parent: tk.Widget) -> None:
        action_frame = ttk.LabelFrame(parent, text="Interaktion", padding="15", style="Card.TLabelframe")
        action_frame.pack(fill=tk.X, ipadx=10)

        # Wert Eingabe (Groß)
        ttk.Label(action_frame, text="Wert:").pack(anchor="w")
        self.action_value = ttk.Entry(action_frame, font=FONTS["xl"], justify="center")
        self.action_value.pack(fill=tk.X, pady=(0, 10))
        self.action_value.insert(0, "0")

        # Typ Auswahl
        ttk.Label(action_frame, text="Typ:").pack(anchor="w")
        self.action_type = ttk.Combobox(action_frame, values=[t.value for t in DamageType], state="readonly")
        self.action_type.set(DamageType.NORMAL.value)
        self.action_type.pack(fill=tk.X, pady=(0, 15))

        self.create_tooltip(self.action_type, lambda: DAMAGE_DESCRIPTIONS.get(self.action_type.get(), ""))

        # Aktions-Buttons Grid
        btn_grid = ttk.Frame(action_frame, style="Card.TFrame")
        btn_grid.pack(fill=tk.X)

        ttk.Button(btn_grid, text="⚔️ Schaden", command=self.controller.deal_damage).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="💚 Heilen", command=self.controller.apply_healing).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="🛡️ Schild +", command=self.controller.apply_shield).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        ttk.Button(btn_grid, text="👕 Rüstung +", command=self.controller.apply_armor).grid(row=1, column=1, padx=2, pady=2, sticky="ew")

        btn_grid.columnconfigure(0, weight=1)
        btn_grid.columnconfigure(1, weight=1)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # --- Status Sektion (Inline) ---
        ttk.Label(action_frame, text="Status Effekt:").pack(anchor="w")

        status_frame = ttk.Frame(action_frame, style="Card.TFrame")
        status_frame.pack(fill=tk.X, pady=(0, 5))

        self.status_combobox = ttk.Combobox(status_frame, values=[t.value for t in StatusEffectType], state="readonly")
        self.status_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.status_combobox.set(StatusEffectType.POISON.value)

        self.create_tooltip(self.status_combobox, lambda: f"{self.status_combobox.get()}:\n{STATUS_DESCRIPTIONS.get(self.status_combobox.get(), 'Keine Info')}")

        rank_duration_frame = ttk.Frame(action_frame, style="Card.TFrame")
        rank_duration_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(rank_duration_frame, text="Rang:").pack(side=tk.LEFT)
        self.status_rank = ttk.Entry(rank_duration_frame, width=5)
        self.status_rank.pack(side=tk.LEFT, padx=(5, 15))
        self.status_rank.insert(0, "1")

        ttk.Label(rank_duration_frame, text="Dauer:").pack(side=tk.LEFT)
        self.status_duration = ttk.Entry(rank_duration_frame, width=5)
        self.status_duration.pack(side=tk.LEFT, padx=(5, 0))
        self.status_duration.insert(0, "3")

        ttk.Button(action_frame, text="Status hinzufügen", command=self.controller.add_status_to_character).pack(fill=tk.X, pady=2)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # Management Section
        ttk.Label(action_frame, text="Verwaltung:").pack(anchor="w")

        self.management_target_var = tk.StringVar(value="Ausgewählter Charakter")
        target_cb = ttk.Combobox(action_frame, textvariable=self.management_target_var,
                                 values=["Ausgewählter Charakter", "Alle Gegner", "Alle Spieler", "Alle NPCs", "Alle Charaktere"],
                                 state="readonly")
        target_cb.pack(fill=tk.X, pady=(0, 5))

        btn_frame = ttk.Frame(action_frame, style="Card.TFrame")
        btn_frame.pack(fill=tk.X)

        self.btn_edit = ttk.Button(btn_frame, text="Bearbeiten", command=self.controller.manage_edit)
        self.btn_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        ttk.Button(btn_frame, text="Löschen", command=self.controller.manage_delete).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        def update_edit_state(event):
            if self.management_target_var.get() == "Ausgewählter Charakter":
                self.btn_edit.state(["!disabled"])
            else:
                self.btn_edit.state(["disabled"])

        target_cb.bind("<<ComboboxSelected>>", update_edit_state)

    def create_bottom_area(self, parent: tk.Widget) -> None:
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        control_frame = ttk.Frame(bottom_frame)
        control_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Button(control_frame, text="🎲 Initiative würfeln & sortieren", command=self.controller.roll_initiative_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏭ Nächster Zug", command=self.controller.next_turn).pack(side=tk.LEFT, padx=5)

        reset_btn = ttk.Menubutton(control_frame, text="🔄 Init Reset")
        reset_menu = tk.Menu(reset_btn, tearoff=0, bg=self.colors["panel"], fg=self.colors["fg"])
        reset_menu.add_command(label="Alle", command=lambda: self.controller.reset_initiative("All"))
        reset_menu.add_command(label="Nur Gegner", command=lambda: self.controller.reset_initiative("Gegner"))
        reset_menu.add_command(label="Nur Spieler", command=lambda: self.controller.reset_initiative("Spieler"))
        reset_menu.add_command(label="Nur NPCs", command=lambda: self.controller.reset_initiative("NPC"))
        reset_btn.config(menu=reset_menu)
        reset_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="↩ Undo", command=self.controller.undo_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="↪ Redo", command=self.controller.redo_action).pack(side=tk.LEFT, padx=5)

        self.round_label = ttk.Label(control_frame, text=f"Runde: 1", font=FONTS["large"], background=self.colors["bg"])
        self.round_label.pack(side=tk.RIGHT, padx=20)

        bottom_content = ttk.Frame(bottom_frame)
        bottom_content.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(bottom_content, text="Kampfprotokoll", style="Card.TLabelframe")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.log = tk.Text(log_frame, height=8, state="normal", bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"], font=FONTS["log"])
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log.configure(yscrollcommand=scrollbar.set)

        self.dice_roller = DiceRoller(bottom_content, self.colors)
        self.dice_roller.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0))

    def create_tooltip(self, widget: tk.Widget, text_func: Callable[[], str]) -> None:
        tt = ToolTip(widget, text_func, color_provider=lambda: (self.colors["tooltip_bg"], self.colors["tooltip_fg"]))
        widget.bind('<Enter>', tt.showtip)
        widget.bind('<Leave>', tt.hidetip)

    # --- Interface Implementation ---

    def show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str) -> None:
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    def log_message(self, message: str) -> None:
        if self.log:
            self.log.insert(tk.END, str(message).strip() + "\n")
            self.log.see(tk.END)

    def get_quick_add_data(self) -> Dict[str, Any]:
        return {
            "name": self.entry_name.get(),
            "lp": self.entry_lp.get(),
            "rp": self.entry_rp.get(),
            "sp": self.entry_sp.get(),
            "init": self.entry_init.get(),
            "gew": self.entry_gew.get(),
            "type": self.entry_type.get(),
            "surprise": self.var_surprise.get()
        }

    def clear_quick_add_fields(self) -> None:
        self.entry_name.delete(0, tk.END)
        self.entry_lp.delete(0, tk.END)
        self.entry_rp.delete(0, tk.END)
        self.entry_sp.delete(0, tk.END)
        self.entry_init.delete(0, tk.END)
        self.entry_gew.delete(0, tk.END)
        self.entry_name.focus()
        self.var_surprise.set(False)

    def set_quick_add_defaults(self) -> None:
        self.var_surprise.set(False)

    def get_selected_char_id(self) -> Optional[str]:
        selection = self.tree.selection()
        if not selection:
            return None
        return selection[0]

    def highlight_character(self, char_id: str) -> None:
        if self.tree.exists(char_id):
            self.tree.selection_set(char_id)
            self.tree.focus(char_id)
            self.tree.see(char_id)

    def get_action_value(self) -> int:
        try:
            val = self.action_value.get()
            return int(val) if val else 0
        except ValueError:
            return 0

    def get_action_type(self) -> str:
        return self.action_type.get()

    def get_status_input(self) -> Dict[str, Any]:
        return {
            "status": self.status_combobox.get(),
            "rank": self.status_rank.get(),
            "duration": self.status_duration.get()
        }

    def get_management_target(self) -> str:
        return self.management_target_var.get()

    def update_round_label(self, round_number: int) -> None:
        if self.round_label:
            self.round_label.config(text=f"Runde: {round_number}")

    def fill_input_fields(self, data: Dict[str, Any]) -> None:
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, data.get("name", ""))

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

        self.entry_type.set(data.get("type", CharacterType.ENEMY.value))

    def update_colors(self, colors: Dict[str, str]) -> None:
        self.colors = colors
        # Update Root
        self.root.configure(bg=self.colors["bg"])

        # Update Styles
        style = ttk.Style()
        style.theme_use('clam') # Ensure we are modifying the active theme

        # Ensure we are configuring the current theme
        style.configure(".", background=self.colors["bg"], foreground=self.colors["fg"], font=FONTS["main"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])

        # Button Style Update
        style.configure("TButton",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        borderwidth=1,
                        focuscolor=self.colors["accent"],
                        lightcolor=self.colors["panel"],
                        darkcolor=self.colors["panel"],
                        bordercolor=self.colors["fg"])

        style.map("TButton",
                  background=[('pressed', self.colors["accent"]), ('active', self.colors["accent"]), ('!disabled', self.colors["panel"])],
                  foreground=[('disabled', '#888888'), ('!disabled', self.colors["fg"])],
                  relief=[('pressed', 'sunken'), ('!pressed', 'raised')])

        style.configure("TCheckbutton",
                        background=self.colors["bg"],
                        foreground=self.colors["fg"],
                        indicatorbackground=self.colors["entry_bg"],
                        indicatorforeground=self.colors["fg"])

        style.map("TCheckbutton",
                  background=[('active', self.colors["bg"])],
                  indicatorbackground=[('active', self.colors["entry_bg"])])

        # Entry Style Update
        # 'clam' theme uses fieldbackground for the entry area
        style.configure("TEntry",
                        fieldbackground=self.colors["entry_bg"],
                        background=self.colors["entry_bg"],
                        foreground=self.colors["fg"],
                        insertcolor=self.colors["fg"],
                        lightcolor=self.colors["entry_bg"],
                        darkcolor=self.colors["entry_bg"],
                        bordercolor=self.colors["fg"])

        style.map("TEntry",
                  fieldbackground=[('readonly', self.colors["entry_bg"]), ('!disabled', self.colors["entry_bg"])],
                  foreground=[('!disabled', self.colors["fg"])])

        # Combobox Style Update
        style.configure("TCombobox",
                        fieldbackground=self.colors["entry_bg"],
                        background=self.colors["entry_bg"],
                        foreground=self.colors["fg"],
                        arrowcolor=self.colors["fg"],
                        lightcolor=self.colors["entry_bg"],
                        darkcolor=self.colors["entry_bg"],
                        bordercolor=self.colors["fg"])

        style.map("TCombobox",
                  fieldbackground=[('readonly', self.colors["entry_bg"]), ('!readonly', self.colors["entry_bg"])],
                  selectbackground=[('readonly', self.colors["entry_bg"]), ('!readonly', self.colors["entry_bg"])],
                  selectforeground=[('readonly', self.colors["fg"]), ('!readonly', self.colors["fg"])],
                  background=[('readonly', self.colors["entry_bg"]), ('!readonly', self.colors["entry_bg"])],
                  foreground=[('readonly', self.colors["fg"]), ('!readonly', self.colors["fg"])])

        self.root.option_add('*TCombobox*Listbox.background', self.colors["entry_bg"])
        self.root.option_add('*TCombobox*Listbox.foreground', self.colors["fg"])
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.colors["accent"])
        self.root.option_add('*TCombobox*Listbox.selectForeground', self.colors["bg"])

        # Spinbox Style Update
        style.configure("TSpinbox",
                        fieldbackground=self.colors["entry_bg"],
                        background=self.colors["entry_bg"],
                        foreground=self.colors["fg"],
                        arrowcolor=self.colors["fg"],
                        lightcolor=self.colors["entry_bg"],
                        darkcolor=self.colors["entry_bg"],
                        bordercolor=self.colors["fg"])

        style.map("TSpinbox",
                  fieldbackground=[('readonly', self.colors["entry_bg"]), ('!disabled', self.colors["entry_bg"])],
                  foreground=[('!disabled', self.colors["fg"])],
                  background=[('!disabled', self.colors["entry_bg"])])

        # Scale Style Update
        style.configure("Horizontal.TScale",
                        background=self.colors["accent"],
                        troughcolor=self.colors["entry_bg"],
                        bordercolor=self.colors["fg"],
                        lightcolor=self.colors["accent"],
                        darkcolor=self.colors["accent"])

        style.map("Horizontal.TScale",
                  background=[('pressed', self.colors["fg"]), ('active', self.colors["accent"])])

        # Treeview Style Update
        style.configure("Treeview",
                        background=self.colors["panel"],
                        foreground=self.colors["fg"],
                        fieldbackground=self.colors["panel"],
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background=self.colors["panel"],
                        foreground=self.colors["accent"],
                        borderwidth=1)
        style.map("Treeview", background=[('selected', self.colors["accent"])])

        # Card/Frame Style Update
        style.configure("Card.TFrame", background=self.colors["panel"])
        style.configure("Card.TLabelframe", background=self.colors["panel"], foreground=self.colors["fg"], bordercolor=self.colors["fg"])
        style.configure("Card.TLabelframe.Label", background=self.colors["panel"], foreground=self.colors["accent"])
        style.configure("Card.TLabel", background=self.colors["panel"], foreground=self.colors["fg"])
        style.configure("Card.TCheckbutton", background=self.colors["panel"], foreground=self.colors["fg"],
                        indicatorbackground=self.colors["entry_bg"], indicatorforeground=self.colors["fg"])
        style.map("Card.TCheckbutton",
                  background=[('active', self.colors["panel"])],
                  indicatorbackground=[('active', self.colors["entry_bg"])])

        # Manuelle Updates für Widgets
        if self.log:
            self.log.configure(bg=self.colors["entry_bg"], fg=self.colors["fg"], insertbackground=self.colors["fg"])

        if self.round_label:
            self.round_label.configure(background=self.colors["bg"], foreground=self.colors["fg"])

        if self.dice_roller:
            self.dice_roller.update_colors(self.colors)

        # Force update of context menu
        if self.context_menu:
            self.context_menu.configure(bg=self.colors["panel"], fg=self.colors["fg"])

        # Update Treeview Tags
        if self.tree:
            self.tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
            self.tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

    def focus_damage_input(self) -> None:
        if self.action_value:
            self.action_value.focus_set()

    def update_listbox(self) -> None:
        """
        Aktualisiert die Anzeige der Charakterliste (Treeview).
        """
        tree = self.tree
        if not tree:
            return

        engine = self.controller.engine

        # Treeview leeren
        for item in tree.get_children():
            tree.delete(item)

        # Update Round Label
        self.update_round_label(engine.round_number)

        if not engine.characters:
            return

        # Rotation berechnen
        rot = 0
        if engine.initiative_rolled and engine.turn_index >= 0:
            if engine.turn_index < len(engine.characters):
                rot = engine.turn_index
            else:
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
            item_id = tree.insert("", tk.END, iid=char.id, values=(order, char.name, char.char_type, health_bar, rp_str, sp_str, char.gew, char.init, status_str))

            # Visuelles Feedback für niedrige LP
            tags = []
            if char.lp <= 0 or char.max_lp <= 0:
                tags.append('dead')
            elif char.lp < (char.max_lp * 0.3): # Unter 30% LP
                tags.append('low_hp')

            if tags:
                tree.item(item_id, tags=tuple(tags))

        # Tags für Dark Mode angepasst
        tree.tag_configure('dead', background=self.colors["dead_bg"], foreground=self.colors["dead_fg"])
        tree.tag_configure('low_hp', foreground=self.colors["low_hp_fg"])

        # Autosave trigger (via Controller)
        self.controller.autosave()

