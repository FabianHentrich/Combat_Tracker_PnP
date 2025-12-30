# Farben für das Dark Theme
COLORS = {
    "bg": "#1a1b26",       # Tiefes Nachtblau
    "fg": "#a9b1d6",       # Weiches Grau-Blau
    "accent": "#7aa2f7",   # Helles Blau
    "panel": "#24283b",    # Panel Hintergrund
    "entry_bg": "#414868", # Eingabefelder
    "danger": "#f7768e",   # Rot
    "success": "#9ece6a",  # Grün
    "warning": "#e0af68"   # Orange/Gelb
}

# Beschreibungen für Tooltips
DAMAGE_DESCRIPTIONS = {
    "Normal": "Waffenschaden.\nSchild (SP) und Rüstung (RP) reduzieren den Schaden.",
    "Durchschlagend": "Ignoriert Rüstung (RP).\nSchild (SP) reduziert den Schaden weiterhin.",
    "Direkt": "Ignoriert Rüstung (RP) und Schild (SP).\nGeht direkt auf die Lebenspunkte (LP).",
    "Verwesung": "Verursacht Schaden und den Status 'Erosion'.",
    "Gift": "Kann Vergiftung verursachen (Chance abhängig vom Rang).",
    "Feuer": "Kann Verbrennung verursachen (Chance abhängig vom Rang).",
    "Blitz": "Kann Betäubung verursachen (Chance abhängig vom Rang).",
    "Kälte": "Kann Unterkühlung verursachen (Chance abhängig vom Rang)."
}

STATUS_DESCRIPTIONS = {
    "Vergiftung": "Direktschaden (Rang) pro Runde.",
    "Verbrennung": "Schaden (Rang) pro Runde.",
    "Blutung": "Schaden (Rang/2) pro Runde.\nSchaden steigt jede Runde um +1.",
    "Unterkühlung": "Verlust der Bonusaktion für (Rang) Runden.",
    "Erschöpfung": "-2 Malus auf GEWANDTHEIT für 1 Runde.",
    "Betäubung": "Ziel verliert für eine Runde alle Aktionen.",
    "Erosion": "Dauerhafter Verlust von RANG * 1W4 Lebenspunkten (LP).",
    "Verwirrung": "-1 Malus auf KAMPF-Probe."
}

