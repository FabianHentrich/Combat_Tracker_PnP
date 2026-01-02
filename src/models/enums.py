from enum import StrEnum

class CharacterType(StrEnum):
    PLAYER = "Spieler"
    ENEMY = "Gegner"
    NPC = "NPC"

class DamageType(StrEnum):
    NORMAL = "Normal"
    PIERCING = "Durchschlagend"
    DIRECT = "Direkt"
    DECAY = "Verwesung"
    POISON = "Gift"
    FIRE = "Feuer"
    LIGHTNING = "Blitz"
    COLD = "Kälte"

class StatusEffectType(StrEnum):
    POISON = "Vergiftung"
    BURN = "Verbrennung"
    BLEED = "Blutung"
    FREEZE = "Unterkühlung"
    STUN = "Betäubung"
    EROSION = "Erosion"
    EXHAUSTION = "Erschöpfung"
    CONFUSION = "Verwirrung"
    BLIND = "Blendung"

class EventType(StrEnum):
    UPDATE = "update"
    LOG = "log"
    TURN_CHANGE = "turn_change"
