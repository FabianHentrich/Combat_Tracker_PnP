from typing import List, Dict, Any, Optional
import random
from .mechanics import calculate_damage, process_status_effects

class Character:
    def __init__(self, name: str, lp: int, rp: int, sp: int, init: int, gew: int = 1, char_type: str = "Gegner"):
        self.name: str = name
        self.char_type: str = char_type
        self.max_lp: int = lp # Speichern der Max LP für Verhältnisse
        self.lp: int = lp
        self.max_rp: int = rp
        self.rp: int = rp
        self.max_sp: int = sp
        self.sp: int = sp
        self.gew: int = gew
        self.init: int = init
        self.status: List[Dict[str, Any]] = []
        self.skip_turns: int = 0

    def apply_damage(self, dmg: int, damage_type: str = "Normal", rank: int = 1) -> str:
        return calculate_damage(self, dmg, damage_type, rank)

    def add_status(self, effect: str, duration: int, rank: int = 1) -> None:
        if rank > 6: rank = 6
        self.status.append({"effect": effect, "rounds": duration, "rank": rank, "active_rounds": 0})

    def update_status(self) -> str:
        return process_status_effects(self)

    def heal(self, healing_points: int) -> str:
        """Heilt den Charakter um eine bestimmte Anzahl an Lebenspunkten."""
        self.lp += healing_points
        return f"{self.name} wird um {healing_points} LP geheilt! Aktuelle LP: {self.lp}"

    def to_dict(self) -> Dict[str, Any]:
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
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
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
