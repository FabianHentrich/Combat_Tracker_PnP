import uuid
from typing import List, Dict, Any
from src.core.mechanics import calculate_damage, format_damage_log
from src.models.enums import CharacterType
from src.models.status_effects import StatusEffect, EFFECT_CLASSES, GenericStatusEffect
from src.config.rule_manager import get_rules
from src.utils.logger import setup_logging
from src.models.combat_results import DamageResult

logger = setup_logging()

class Character:
    """
    Repräsentiert einen einzelnen Charakter im Kampf (Spieler, Gegner oder NPC).
    Speichert Attribute wie Lebenspunkte (LP), Rüstung (RP), Schild (SP), Initiative und Status-Effekte.
    Diese Klasse sollte primär Daten halten (POPO - Plain Old Python Object).
    """
    def __init__(self, name: str, lp: int, rp: int, sp: int, init: int, gew: int = 1, char_type: str = CharacterType.ENEMY, char_id: str = None, level: int = 0):
        self.id: str = char_id if char_id else str(uuid.uuid4())
        self.name: str = name
        self.char_type: str = char_type
        self.level: int = level
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

    def apply_damage(self, dmg: int, damage_type: str = "Normal", rank: int = 1) -> DamageResult:
        """
        Wendet Schaden auf den Charakter an.
        Berücksichtigt Rüstung, Schild und Schadenstyp.
        Gibt ein DamageResult Objekt zurück.
        """
        return calculate_damage(self, dmg, damage_type, rank)

    def add_status(self, effect_name: str, duration: int, rank: int = 1) -> None:
        """Fügt dem Charakter einen Status-Effekt hinzu."""
        rules = get_rules()
        max_rank = 6
        if effect_name in rules.get("status_effects", {}):
             max_rank = rules["status_effects"][effect_name].get("max_rank", 6)

        if rank > max_rank: rank = max_rank

        effect_class = EFFECT_CLASSES.get(effect_name)
        if effect_class:
            effect = effect_class(duration, rank)
        else:
            effect = GenericStatusEffect(effect_name, duration, rank)

        self.status.append(effect)

    def get_status_string(self) -> str:
        """Gibt eine formatierte Liste der Status-Effekte zurück."""
        if not self.status:
            return ""

        status_list = []
        for s in self.status:
            name = s.name
            if hasattr(name, 'value'):
                name = name.value
            status_list.append(f"{name} (Rang {s.rank}, {s.duration} Rd.)")

        return " | Status: " + ", ".join(status_list)

    def heal(self, healing_points: int) -> str:
        """Heilt den Charakter um eine bestimmte Anzahl an Lebenspunkten."""
        self.lp += healing_points
        return f"{self.name} wird um {healing_points} LP geheilt! Aktuelle LP: {self.lp}"

    def update(self, data: Dict[str, Any]) -> None:
        """Aktualisiert die Attribute des Charakters basierend auf einem Dictionary."""
        self.name = data.get("name", self.name)
        self.char_type = data.get("char_type", self.char_type)
        self.lp = data.get("lp", self.lp)
        self.max_lp = data.get("max_lp", self.max_lp)
        self.rp = data.get("rp", self.rp)
        self.max_rp = data.get("max_rp", self.max_rp)
        self.sp = data.get("sp", self.sp)
        self.max_sp = data.get("max_sp", self.max_sp)
        self.init = data.get("init", self.init)
        self.gew = data.get("gew", self.gew)
        self.level = data.get("level", self.level)

        if "status" in data:
            self.status = data["status"]

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert den Charakter in ein Dictionary (für JSON-Export)."""
        return {
            "id": self.id,
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
            "level": self.level,
            "status": [s.to_dict() for s in self.status],
            "skip_turns": self.skip_turns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Erstellt einen Charakter aus einem Dictionary (für JSON-Import)."""

        # Check for missing critical fields
        required_fields = ["name", "max_lp", "max_rp", "max_sp", "init", "gew", "char_type", "id"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            logger.warning(f"Character Import: Fehlende Felder ersetzt durch Defaults: {', '.join(missing)} (Data: {data.get('name', 'Unknown')})")

        # Robuster Import mit Default-Werten
        char = cls(
            name=data.get("name", "Unknown"),
            lp=data.get("max_lp", 10),
            rp=data.get("max_rp", 0),
            sp=data.get("max_sp", 0),
            init=data.get("init", 0),
            gew=data.get("gew", 1),
            char_type=data.get("char_type", CharacterType.ENEMY),
            char_id=data.get("id"),
            level=data.get("level", 0)
        )
        # Aktuelle Werte setzen (falls abweichend von Max)
        char.lp = data.get("lp", char.max_lp)
        char.rp = data.get("rp", char.max_rp)
        char.sp = data.get("sp", char.max_sp)

        status_data = data.get("status", [])
        char.status = [StatusEffect.from_dict(s) for s in status_data]

        char.skip_turns = data.get("skip_turns", 0)
        return char
