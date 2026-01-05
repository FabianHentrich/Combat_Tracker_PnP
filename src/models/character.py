import uuid
from typing import List, Dict, Any
from src.core.mechanics import calculate_damage, format_damage_log
from src.models.enums import CharacterType, StatType, RuleKey
from src.models.status_effects import StatusEffect, EFFECT_CLASSES, GenericStatusEffect
from src.config.rule_manager import get_rules
from src.utils.logger import setup_logging
from src.models.combat_results import DamageResult
from src.utils.localization import translate

logger = setup_logging()

class Character:
    """
    Represents a single character in combat (player, enemy, or NPC).
    Stores attributes like hit points (LP), armor (RP), shield (SP), initiative, and status effects.
    This class should primarily hold data (POPO - Plain Old Python Object).
    """
    def __init__(self, name: str, lp: int, rp: int, sp: int, init: int, gew: int = 1, char_type: str = CharacterType.ENEMY, char_id: str = None, level: int = 0):
        self.id: str = char_id if char_id else str(uuid.uuid4())
        self.name: str = name
        self.char_type: str = char_type
        self.level: int = level
        self.max_lp: int = lp # Store max LP for ratios
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
        Applies damage to the character.
        Considers armor, shield, and damage type.
        Returns a DamageResult object.
        """
        return calculate_damage(self, dmg, damage_type, rank)

    def add_status(self, effect_name: str, duration: int, rank: int = 1) -> None:
        """Adds a status effect to the character."""
        rules = get_rules()
        max_rank = 6
        if effect_name in rules.get(RuleKey.STATUS_EFFECTS, {}):
             max_rank = rules[RuleKey.STATUS_EFFECTS][effect_name].get(RuleKey.MAX_RANK, 6)

        if rank > max_rank: rank = max_rank

        effect_class = EFFECT_CLASSES.get(effect_name)
        if effect_class:
            effect = effect_class(duration, rank)
        else:
            effect = GenericStatusEffect(effect_name, duration, rank)

        self.status.append(effect)

    def get_status_string(self) -> str:
        """Returns a formatted list of status effects."""
        if not self.status:
            return ""

        status_list = []
        for s in self.status:
            name = s.name
            if hasattr(name, 'value'):
                name = name.value
            
            # Translate the status effect name
            translated_name = translate(f"status_effects.{name}")
            # If translation fails (returns key), use the original name
            if translated_name == f"status_effects.{name}":
                translated_name = name

            status_list.append(f"{translated_name} ({translate('action_panel.rank')} {s.rank}, {s.duration} {translate('common.rounds')})")

        return " | " + translate("character_list.status") + ": " + ", ".join(status_list)

    def heal(self, healing_points: int) -> str:
        """Heals the character by a certain amount of hit points."""
        self.lp += healing_points
        return translate("messages.character_healed", name=self.name, amount=healing_points, lp=self.lp)

    def update(self, data: Dict[str, Any]) -> None:
        """Updates the character's attributes based on a dictionary."""
        self.name = data.get(StatType.NAME, self.name)
        self.char_type = data.get(StatType.CHAR_TYPE, self.char_type)
        self.lp = data.get(StatType.LP, self.lp)
        self.max_lp = data.get(StatType.MAX_LP, self.max_lp)
        self.rp = data.get(StatType.RP, self.rp)
        self.max_rp = data.get(StatType.MAX_RP, self.max_rp)
        self.sp = data.get(StatType.SP, self.sp)
        self.max_sp = data.get(StatType.MAX_SP, self.max_sp)
        self.init = data.get(StatType.INIT, self.init)
        self.gew = data.get(StatType.GEW, self.gew)
        self.level = data.get(StatType.LEVEL, self.level)

        if StatType.STATUS in data:
            self.status = data[StatType.STATUS]

    def to_dict(self) -> Dict[str, Any]:
        """Converts the character to a dictionary (for JSON export)."""
        return {
            StatType.ID: self.id,
            StatType.NAME: self.name,
            StatType.CHAR_TYPE: self.char_type,
            StatType.MAX_LP: self.max_lp,
            StatType.LP: self.lp,
            StatType.MAX_RP: self.max_rp,
            StatType.RP: self.rp,
            StatType.MAX_SP: self.max_sp,
            StatType.SP: self.sp,
            StatType.GEW: self.gew,
            StatType.INIT: self.init,
            StatType.LEVEL: self.level,
            StatType.STATUS: [s.to_dict() for s in self.status],
            StatType.SKIP_TURNS: self.skip_turns
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Creates a character from a dictionary (for JSON import)."""

        # Check for missing critical fields
        required_fields = [StatType.NAME, StatType.MAX_LP, StatType.MAX_RP, StatType.MAX_SP, StatType.INIT, StatType.GEW, StatType.CHAR_TYPE, StatType.ID]
        missing = [f for f in required_fields if f not in data]
        if missing:
            logger.warning(f"Character Import: Missing fields replaced by defaults: {', '.join(missing)} (Data: {data.get(StatType.NAME, 'Unknown')})")

        # Robust import with default values
        char = cls(
            name=data.get(StatType.NAME, "Unknown"),
            lp=data.get(StatType.MAX_LP, 10),
            rp=data.get(StatType.MAX_RP, 0),
            sp=data.get(StatType.MAX_SP, 0),
            init=data.get(StatType.INIT, 0),
            gew=data.get(StatType.GEW, 1),
            char_type=data.get(StatType.CHAR_TYPE, CharacterType.ENEMY),
            char_id=data.get(StatType.ID),
            level=data.get(StatType.LEVEL, 0)
        )
        # Set current values (if different from max)
        char.lp = data.get(StatType.LP, char.max_lp)
        char.rp = data.get(StatType.RP, char.max_rp)
        char.sp = data.get(StatType.SP, char.max_sp)

        status_data = data.get(StatType.STATUS, [])
        char.status = [StatusEffect.from_dict(s) for s in status_data]

        char.skip_turns = data.get(StatType.SKIP_TURNS, 0)
        return char
