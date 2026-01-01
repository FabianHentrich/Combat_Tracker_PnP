from typing import List, Dict, Any
from src.core.mechanics import calculate_damage
from src.models.enums import CharacterType
from src.models.status_effects import StatusEffect, EFFECT_CLASSES, GenericStatusEffect
from src.utils.config import RULES

class Character:
    """
    Repräsentiert einen einzelnen Charakter im Kampf (Spieler, Gegner oder NPC).
    Speichert Attribute wie Lebenspunkte (LP), Rüstung (RP), Schild (SP), Initiative und Status-Effekte.
    """
    def __init__(self, name: str, lp: int, rp: int, sp: int, init: int, gew: int = 1, char_type: str = CharacterType.ENEMY):
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
        self.status: List[StatusEffect] = []
        self.skip_turns: int = 0

    def apply_damage(self, dmg: int, damage_type: str = "Normal", rank: int = 1) -> str:
        """
        Wendet Schaden auf den Charakter an.
        Berücksichtigt Rüstung, Schild und Schadenstyp.
        Gibt einen Log-String zurück.
        """
        return calculate_damage(self, dmg, damage_type, rank)

    def add_status(self, effect_name: str, duration: int, rank: int = 1) -> None:
        """Fügt dem Charakter einen Status-Effekt hinzu."""
        max_rank = 6
        if effect_name in RULES.get("status_effects", {}):
             max_rank = RULES["status_effects"][effect_name].get("max_rank", 6)

        if rank > max_rank: rank = max_rank

        effect_class = EFFECT_CLASSES.get(effect_name)
        if effect_class:
            effect = effect_class(duration, rank)
        else:
            effect = GenericStatusEffect(effect_name, duration, rank)

        self.status.append(effect)

    def update_status(self) -> str:
        """
        Aktualisiert alle aktiven Status-Effekte (z.B. Schaden über Zeit).
        Reduziert die Dauer und entfernt abgelaufene Effekte.
        Gibt einen Log-String zurück.
        """
        log = ""
        new_status = []
        self.skip_turns = 0

        for s in self.status:
            s.active_rounds += 1
            log += s.apply_round_effect(self)

            s.duration -= 1
            if s.duration > 0:
                new_status.append(s)

        self.status = new_status
        return log

    def heal(self, healing_points: int) -> str:
        """Heilt den Charakter um eine bestimmte Anzahl an Lebenspunkten."""
        self.lp += healing_points
        return f"{self.name} wird um {healing_points} LP geheilt! Aktuelle LP: {self.lp}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialisiert den Charakter in ein Dictionary (für JSON-Export)."""
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
            "status": [s.to_dict() for s in self.status],
            "skip_turns": self.skip_turns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Erstellt einen Charakter aus einem Dictionary (für JSON-Import)."""
        char = cls(
            name=data["name"],
            lp=data["max_lp"],
            rp=data["max_rp"],
            sp=data["max_sp"],
            init=data["init"],
            gew=data.get("gew", 1),
            char_type=data.get("char_type", CharacterType.ENEMY)
        )
        char.lp = data["lp"]
        char.rp = data["rp"]
        char.sp = data["sp"]

        status_data = data.get("status", [])
        char.status = [StatusEffect.from_dict(s) for s in status_data]

        char.skip_turns = data.get("skip_turns", 0)
        return char
