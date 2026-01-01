import tkinter as tk
from tkinter import ttk
from src.controllers.audio_controller import AudioController
from src.utils.config import FONTS

class AudioPlayerWidget(ttk.LabelFrame):
    def __init__(self, parent, controller: AudioController, open_settings_callback):
        super().__init__(parent, text="Musik-Player", style="Card.TLabelframe", padding=5)
        self.controller = controller
        self.open_settings_callback = open_settings_callback

        self.lbl_title = None
        self.lbl_time = None
        self.btn_play_pause = None
        self.btn_mute = None
        self.lbl_volume = None
        self.is_muted = False
        self.last_volume = self.controller.volume * 100

        self.setup_ui()
        self.update_ui_loop()

    def setup_ui(self):
        # Top row: Title and Settings button
        top_frame = ttk.Frame(self, style="Card.TFrame")
        top_frame.pack(fill=tk.X)

        self.lbl_title = ttk.Label(top_frame, text="Kein Titel", font=FONTS["main"], width=15, anchor="w", style="Card.TLabel")
        self.lbl_title.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(top_frame, text="⚙", width=3, command=self.open_settings_callback).pack(side=tk.RIGHT)

        # Middle row: Controls
        ctrl_frame = ttk.Frame(self, style="Card.TFrame")
        ctrl_frame.pack(fill=tk.X, pady=2)

        ttk.Button(ctrl_frame, text="⏮", width=3, command=self.controller.prev_track).pack(side=tk.LEFT)
        self.btn_play_pause = ttk.Button(ctrl_frame, text="▶", width=3, command=self.toggle_play)
        self.btn_play_pause.pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl_frame, text="⏭", width=3, command=self.controller.next_track).pack(side=tk.LEFT)

        # Time display
        self.lbl_time = ttk.Label(ctrl_frame, text="00:00", font=FONTS["small"], style="Card.TLabel")
        self.lbl_time.pack(side=tk.RIGHT)

        # Loop Controls
        loop_frame = ttk.Frame(self, style="Card.TFrame")
        loop_frame.pack(fill=tk.X, pady=2)

        # Determine initial state from controller
        init_loop_active = self.controller.loop_single or (self.controller.loop_count_target > 1)
        init_count = "Inf" if self.controller.loop_single else str(self.controller.loop_count_target)

        self.var_loop_active = tk.BooleanVar(value=init_loop_active)
        cb_loop = ttk.Checkbutton(loop_frame, text="Loop", variable=self.var_loop_active, command=self.update_loop_state, style="Card.TCheckbutton")
        cb_loop.pack(side=tk.LEFT, padx=2)

        ttk.Label(loop_frame, text="x", style="Card.TLabel").pack(side=tk.LEFT)

        self.var_loop_count = tk.StringVar(value=init_count)
        self.spin_loop = ttk.Spinbox(loop_frame, values=("Inf",) + tuple(range(1, 100)), width=4, textvariable=self.var_loop_count, command=self.update_loop_state)
        self.spin_loop.pack(side=tk.LEFT, padx=2)
        self.spin_loop.bind("<Return>", lambda e: self.update_loop_state())
        self.spin_loop.bind("<FocusOut>", lambda e: self.update_loop_state())

        # Volume Control
        vol_frame = ttk.Frame(self, style="Card.TFrame")
        vol_frame.pack(fill=tk.X, pady=2)

        self.btn_mute = ttk.Button(vol_frame, text="🔊", width=3, command=self.toggle_mute)
        self.btn_mute.pack(side=tk.LEFT, padx=2)

        self.vol_var = tk.DoubleVar(value=self.controller.volume * 100)
        self.scale_vol = ttk.Scale(vol_frame, from_=0, to=100, orient=tk.HORIZONTAL, variable=self.vol_var, command=self.update_volume)
        self.scale_vol.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.lbl_volume = ttk.Label(vol_frame, text=f"{int(self.vol_var.get())}%", width=4, style="Card.TLabel")
        self.lbl_volume.pack(side=tk.LEFT, padx=2)

    def update_volume(self, value):
        vol = float(value)

        if self.lbl_volume:
            self.lbl_volume.config(text=f"{int(vol)}%")

        if self.is_muted and vol > 0:
            self.is_muted = False
            self.btn_mute.config(text="🔊")

        if vol == 0:
            self.btn_mute.config(text="🔇")
        elif not self.is_muted:
            self.btn_mute.config(text="🔊")

        self.controller.set_volume(vol / 100.0)

    def toggle_mute(self):
        if self.is_muted:
            self.is_muted = False
            vol = self.last_volume
            if vol <= 0: vol = 50
            self.vol_var.set(vol)
            self.controller.set_volume(vol / 100.0)
            self.btn_mute.config(text="🔊")
            if self.lbl_volume:
                self.lbl_volume.config(text=f"{int(vol)}%")
        else:
            self.is_muted = True
            current_vol = self.vol_var.get()
            if current_vol > 0:
                self.last_volume = current_vol
            self.vol_var.set(0)
            self.controller.set_volume(0)
            self.btn_mute.config(text="🔇")
            if self.lbl_volume:
                self.lbl_volume.config(text="0%")

    def update_loop_state(self):
        is_looping = self.var_loop_active.get()
        count_str = self.var_loop_count.get()

        if not is_looping:
            self.controller.loop_single = False
            self.controller.loop_count_target = 1
        else:
            if count_str == "Inf":
                self.controller.loop_single = True
            else:
                try:
                    count = int(count_str)
                    self.controller.loop_single = False
                    self.controller.loop_count_target = count
                except ValueError:
                    # Fallback if invalid input
                    self.controller.loop_single = True
                    self.var_loop_count.set("Inf")

    def toggle_play(self):
        if self.controller.is_playing and not self.controller.is_paused:
            self.controller.pause()
            self.btn_play_pause.config(text="▶")
        elif self.controller.is_paused:
            self.controller.pause() # unpause
            self.btn_play_pause.config(text="⏸")
        else:
            if self.controller.current_index == -1 and self.controller.playlist:
                self.controller.play(0)
            else:
                self.controller.play()

            if self.controller.is_playing:
                self.btn_play_pause.config(text="⏸")

    def update_ui_loop(self):
        # Update time and title
        track = self.controller.get_current_track_info()
        if track:
            idx = self.controller.current_index + 1
            self.lbl_title.config(text=f"{idx}. {track['title']}")
        else:
            # Show first track if available but not playing
            if self.controller.playlist:
                self.lbl_title.config(text=f"1. {self.controller.playlist[0]['title']}")
            else:
                self.lbl_title.config(text="Kein Titel")

        # Determine if we should show time
        show_time = False
        if self.controller.is_playing:
            show_time = True
        elif self.controller.is_paused and self.controller.get_current_track_info():
             # Special case: Loaded state but not playing yet (or paused)
             show_time = True

        if show_time:
            if not self.controller.is_paused:
                self.btn_play_pause.config(text="⏸")
            else:
                self.btn_play_pause.config(text="▶")

            seconds = int(self.controller.get_playback_time())
            m, s = divmod(seconds, 60)

            total_seconds = int(self.controller.get_total_duration())
            tm, ts = divmod(total_seconds, 60)

            self.lbl_time.config(text=f"{m:02d}:{s:02d} / {tm:02d}:{ts:02d}")
        else:
            self.btn_play_pause.config(text="▶")
            self.lbl_time.config(text="00:00 / 00:00")

        # Check for audio events (track end)
        self.controller.check_events()

        # Sync Volume (e.g. changed by hotkey)
        current_vol_ctrl = self.controller.volume * 100
        if abs(self.vol_var.get() - current_vol_ctrl) > 1:
            self.vol_var.set(current_vol_ctrl)
            self.lbl_volume.config(text=f"{int(current_vol_ctrl)}%")
            if current_vol_ctrl == 0:
                self.btn_mute.config(text="🔇")
                self.is_muted = True
            else:
                self.btn_mute.config(text="🔊")
                self.is_muted = False

        self.after(100, self.update_ui_loop)

