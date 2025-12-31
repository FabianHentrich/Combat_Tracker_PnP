from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Type
import random
from .enums import StatusEffectType, DamageType

if TYPE_CHECKING:
    from .character import Character

class StatusEffect(ABC):
    def __init__(self, name: str, duration: int, rank: int = 1):
        self.name = name
        self.duration = duration
        self.rank = rank
        self.active_rounds = 0

    def apply_round_effect(self, character: 'Character') -> str:
        """Wird am Anfang der Runde aufgerufen. Standardmäßig passiert nichts."""
        return ""

    def to_dict(self) -> Dict:
        return {
            "effect": self.name,
            "rounds": self.duration,
            "rank": self.rank,
            "active_rounds": self.active_rounds
        }

    @staticmethod
    def from_dict(data: Dict) -> 'StatusEffect':
        name = data["effect"]
        duration = data["rounds"]
        rank = data["rank"]
        active_rounds = data.get("active_rounds", 0)

        effect_class = EFFECT_CLASSES.get(name)
        if effect_class:
            effect = effect_class(duration, rank)
        else:
            effect = GenericStatusEffect(name, duration, rank)

        effect.active_rounds = active_rounds
        return effect

class GenericStatusEffect(StatusEffect):
    def __init__(self, name: str, duration: int, rank: int = 1):
        super().__init__(name, duration, rank)

class PoisonEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.POISON, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        from .mechanics import calculate_damage
        dmg = self.rank
        log = calculate_damage(character, dmg, DamageType.DIRECT)
        return log + f" (Vergiftung Rang {self.rank}, Runde {self.active_rounds})\n"

class BurnEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.BURN, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        from .mechanics import calculate_damage
        dmg = self.rank
        log = calculate_damage(character, dmg, DamageType.NORMAL)
        return log + f" (Verbrennung Rang {self.rank}, Runde {self.active_rounds})\n"

class BleedEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.BLEED, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        from .mechanics import calculate_damage
        # Schaden = Rang/2 + (Runde - 1)
        dmg = int((self.rank / 2) + (self.active_rounds - 1))
        if dmg < 1: dmg = 1
        log = calculate_damage(character, dmg, DamageType.NORMAL)
        return log + f" (Blutung Rang {self.rank}, Runde {self.active_rounds})\n"

class ErosionEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.EROSION, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        from .mechanics import calculate_damage
        dmg = self.rank * random.randint(1, 4)
        character.max_lp -= dmg
        if character.max_lp < 0: character.max_lp = 0
        log = calculate_damage(character, dmg, DamageType.DIRECT)
        return log + f" (Erosion Rang {self.rank} - {dmg} Max LP dauerhaft verloren)\n"

class FreezeEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.FREEZE, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        return f"ℹ️ {character.name} verliert Bonusaktion (Unterkühlung Rang {self.rank}).\n"

class StunEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.STUN, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        character.skip_turns = 1
        return f"🛑 {character.name} ist betäubt und verliert alle Aktionen!\n"

class ExhaustionEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.EXHAUSTION, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        return f"ℹ️ {character.name} hat -2 Malus auf GEWANDTHEIT (Erschöpfung).\n"

class ConfusionEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.CONFUSION, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        return f"ℹ️ {character.name} hat -1 Malus auf KAMPF-Probe (Verwirrung).\n"

class BlindEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.BLIND, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        if self.rank == 1:
            return f"ℹ️ {character.name} ist geblendet: -1 auf Angriffsprobe (Rang 1).\n"
        elif self.rank == 2:
            return f"ℹ️ {character.name} ist geblendet: -2 auf Angriffsprobe (Rang 2).\n"
        elif self.rank == 3:
            return f"ℹ️ {character.name} ist geblendet: -2 auf alle Aktionen (Rang 3).\n"
        elif self.rank == 4:
            return f"ℹ️ {character.name} ist geblendet: -2 auf alle Aktionen (Rang 4).\n"
        elif self.rank == 5:
            return f"ℹ️ {character.name} ist geblendet: -3 auf alle Aktionen (Rang 5).\n"
        else:
            return f"ℹ️ {character.name} ist geblendet (Rang {self.rank}).\n"

EFFECT_CLASSES: Dict[str, Type[StatusEffect]] = {
    StatusEffectType.POISON: PoisonEffect,
    StatusEffectType.BURN: BurnEffect,
    StatusEffectType.BLEED: BleedEffect,
    StatusEffectType.EROSION: ErosionEffect,
    StatusEffectType.FREEZE: FreezeEffect,
    StatusEffectType.STUN: StunEffect,
    StatusEffectType.EXHAUSTION: ExhaustionEffect,
    StatusEffectType.CONFUSION: ConfusionEffect,
    StatusEffectType.BLIND: BlindEffect
}

