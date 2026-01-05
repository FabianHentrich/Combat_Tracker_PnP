from enum import Enum


class CharacterType(str, Enum):
    PLAYER = "PLAYER"
    ENEMY = "ENEMY"
    NPC = "NPC"


class DamageType(str, Enum):
    NORMAL = "NORMAL"
    PIERCING = "PIERCING"
    DIRECT = "DIRECT"
    DECAY = "DECAY"
    POISON = "POISON"
    FIRE = "FIRE"
    LIGHTNING = "LIGHTNING"
    COLD = "COLD"


class StatusEffectType(str, Enum):
    POISON = "POISON"
    BURN = "BURN"
    BLEED = "BLEED"
    FREEZE = "FREEZE"
    EXHAUSTION = "EXHAUSTION"
    STUN = "STUN"
    EROSION = "EROSION"
    CONFUSION = "CONFUSION"
    BLIND = "BLIND"


class EventType(str, Enum):
    UPDATE = "update"
    LOG = "log"
    TURN_CHANGE = "turn_change"


class ScopeType(str, Enum):
    SELECTED = "SELECTED"
    ALL_ENEMIES = "ALL_ENEMIES"
    ALL_PLAYERS = "ALL_PLAYERS"
    ALL_NPCS = "ALL_NPCS"
    ALL = "ALL"


class StatType(str, Enum):
    LP = "lp"
    MAX_LP = "max_lp"
    RP = "rp"
    MAX_RP = "max_rp"
    SP = "sp"
    MAX_SP = "max_sp"
    INIT = "init"
    GEW = "gew"
    LEVEL = "level"
    NAME = "name"
    TYPE = "type"
    CHAR_TYPE = "char_type"
    STATUS = "status"
    SKIP_TURNS = "skip_turns"
    ID = "id"


class RuleKey(str, Enum):
    IGNORES_ARMOR = "ignores_armor"
    IGNORES_SHIELD = "ignores_shield"
    SECONDARY_EFFECT = "secondary_effect"
    DESCRIPTION = "description"
    MAX_RANK = "max_rank"
    STACKABLE = "stackable"
    DAMAGE_TYPES = "damage_types"
    STATUS_EFFECTS = "status_effects"


class Language(str, Enum):
    ENGLISH = "en"
    GERMAN = "de"
