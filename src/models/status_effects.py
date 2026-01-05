from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, Type
import random
from src.models.enums import StatusEffectType, DamageType
from src.core.mechanics import calculate_damage, format_damage_log
from src.utils.localization import translate

if TYPE_CHECKING:
    from src.models.character import Character

class StatusEffect(ABC):
    def __init__(self, name: str, duration: int, rank: int = 1):
        self.name = name
        self.duration = duration
        self.rank = rank
        self.active_rounds = 0

    def apply_round_effect(self, character: 'Character') -> str:
        """Called at the beginning of the round. By default, nothing happens."""
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
        name = data.get("effect", "Unknown")
        duration = data.get("rounds", 0)
        rank = data.get("rank", 1)
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
        dmg = self.rank
        result = calculate_damage(character, dmg, DamageType.DIRECT)
        result.messages.append(translate("messages.status.poison", rank=self.rank, round=self.active_rounds))
        return format_damage_log(character, result)

class BurnEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.BURN, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        dmg = self.rank
        result = calculate_damage(character, dmg, DamageType.NORMAL)
        result.messages.append(translate("messages.status.burn", rank=self.rank, round=self.active_rounds))
        return format_damage_log(character, result)

class BleedEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.BLEED, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        # Damage = Rank/2 + (Round - 1)
        dmg = int((self.rank / 2) + (self.active_rounds - 1))
        if dmg < 1: dmg = 1
        result = calculate_damage(character, dmg, DamageType.NORMAL)
        result.messages.append(translate("messages.status.bleed", rank=self.rank, round=self.active_rounds))
        return format_damage_log(character, result)

class ErosionEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.EROSION, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        dmg = self.rank * random.randint(1, 4)
        character.max_lp -= dmg
        if character.max_lp < 0: character.max_lp = 0
        result = calculate_damage(character, dmg, DamageType.DIRECT)
        result.messages.append(translate("messages.status.erosion", rank=self.rank, dmg=dmg))
        return format_damage_log(character, result)

class FreezeEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.FREEZE, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        return translate("messages.status.freeze", name=character.name, rank=self.rank)

class StunEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.STUN, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        character.skip_turns = 1
        return translate("messages.status.stun", name=character.name)

class ExhaustionEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.EXHAUSTION, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        return translate("messages.status.exhaustion", name=character.name)

class ConfusionEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.CONFUSION, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        return translate("messages.status.confusion", name=character.name)

class BlindEffect(StatusEffect):
    def __init__(self, duration: int, rank: int = 1):
        super().__init__(StatusEffectType.BLIND, duration, rank)

    def apply_round_effect(self, character: 'Character') -> str:
        if self.rank == 1:
            return translate("messages.status.blind_rank1", name=character.name)
        elif self.rank == 2:
            return translate("messages.status.blind_rank2", name=character.name)
        elif self.rank == 3:
            return translate("messages.status.blind_rank3", name=character.name)
        elif self.rank == 4:
            return translate("messages.status.blind_rank4", name=character.name)
        elif self.rank == 5:
            return translate("messages.status.blind_rank5", name=character.name)
        else:
            return translate("messages.status.blind_generic", name=character.name, rank=self.rank)

EFFECT_CLASSES: Dict[str, Type[StatusEffect]] = {
    StatusEffectType.POISON.value: PoisonEffect,
    StatusEffectType.BURN.value: BurnEffect,
    StatusEffectType.BLEED.value: BleedEffect,
    StatusEffectType.EROSION.value: ErosionEffect,
    StatusEffectType.FREEZE.value: FreezeEffect,
    StatusEffectType.STUN.value: StunEffect,
    StatusEffectType.EXHAUSTION.value: ExhaustionEffect,
    StatusEffectType.CONFUSION.value: ConfusionEffect,
    StatusEffectType.BLIND.value: BlindEffect
}
