from enum import Enum

class CharacterType(str, Enum):
    PLAYER = "Spieler"
    ENEMY = "Gegner"
    NPC = "NPC"

class DamageType(str, Enum):
    NORMAL = "Normal"
    PIERCING = "Durchschlagend"
    DIRECT = "Direkt"
    DECAY = "Verwesung"
    POISON = "Gift"
    FIRE = "Feuer"
    LIGHTNING = "Blitz"
    COLD = "Kälte"

class StatusEffectType(str, Enum):
    POISON = "Vergiftung"
    BURN = "Verbrennung"
    BLEED = "Blutung"
    FREEZE = "Unterkühlung"
    STUN = "Betäubung"
    EROSION = "Erosion"
    EXHAUSTION = "Erschöpfung"
    CONFUSION = "Verwirrung"
    BLIND = "Blendung"

class EventType(str, Enum):
    UPDATE = "update"
    LOG = "log"
    TURN_CHANGE = "turn_change"
