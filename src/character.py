import random
from .mechanics import calculate_damage, process_status_effects

class Character:
    def __init__(self, name, lp, rp, sp, init, gew=1, char_type="Gegner"):
        self.name = name
        self.char_type = char_type
        self.max_lp = lp # Speichern der Max LP für Verhältnisse
        self.lp = lp
        self.max_rp = rp
        self.rp = rp
        self.max_sp = sp
        self.sp = sp
        self.gew = gew
        self.init = init
        self.status = []
        self.skip_turns = 0

    def apply_damage(self, dmg, damage_type="Normal", rank=1):
        return calculate_damage(self, dmg, damage_type, rank)

    def add_status(self, effect, duration, rank=1):
        if rank > 6: rank = 6
        self.status.append({"effect": effect, "rounds": duration, "rank": rank, "active_rounds": 0})

    def update_status(self):
        return process_status_effects(self)

    def heal(self, healing_points):
        """Heilt den Charakter um eine bestimmte Anzahl an Lebenspunkten."""
        self.lp += healing_points
        return f"{self.name} wird um {healing_points} LP geheilt! Aktuelle LP: {self.lp}"

    def to_dict(self):
        return {
            "name": self.name,
            "char_type": self.char_type,
            "max_lp": self.max_lp,
            "lp": self.lp,
            "max_rp": self.max_rp,
            "rp": self.rp,
            "max_sp": self.max_sp,
            "sp": self.sp,
            "gew": self.gew,
            "init": self.init,
            "status": self.status,
            "skip_turns": self.skip_turns
        }

    @classmethod
    def from_dict(cls, data):
        char = cls(
            name=data["name"],
            lp=data["max_lp"],
            rp=data["max_rp"],
            sp=data["max_sp"],
            init=data["init"],
            gew=data.get("gew", 1),
            char_type=data["char_type"]
        )
        char.lp = data["lp"]
        char.rp = data["rp"]
        char.sp = data["sp"]
        char.status = data.get("status", [])
        char.skip_turns = data.get("skip_turns", 0)
        return char
