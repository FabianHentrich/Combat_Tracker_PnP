import random
from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from .config import RULES
from .enums import DamageType, StatusEffectType

if TYPE_CHECKING:
    from .character import Character

def calculate_damage(character: 'Character', dmg: int, damage_type: str = DamageType.NORMAL, rank: int = 1) -> str:
    """
    Berechnet den Schaden für einen Charakter unter Berücksichtigung von Rüstung, Schild und Schadenstyp.
    Gibt einen formatierten Log-String zurück.
    """
    # Ensure damage_type is a string (value of Enum)
    if hasattr(damage_type, 'value'):
        damage_type = damage_type.value

    log = f"{character.name} erleidet {dmg} ({damage_type}) Schaden!\n"

    # Logik basierend auf Schadenstyp aus Regeln laden
    ignore_shield = False
    ignore_armor = False

    damage_rules = RULES.get("damage_types", {})
    if damage_type in damage_rules:
        rule = damage_rules[damage_type]
        ignore_shield = rule.get("ignores_shield", False)
        ignore_armor = rule.get("ignores_armor", False)

        if ignore_armor:
            log += f"→ {damage_type} Schaden ignoriert Rüstung.\n"
        if ignore_shield:
            log += f"→ {damage_type} Schaden ignoriert Schild.\n"

        # Sekundäreffekte (Chance auf Status)
        sec_effect = rule.get("secondary_effect")
        if sec_effect:
            log += f"❓ Chance auf {sec_effect} (Rang {rank})!\n"
    else:
        # Fallback für unbekannte Typen (oder alte Logik falls RULES leer)
        if damage_type == DamageType.PIERCING:
            ignore_armor = True
            log += f"→ {damage_type} Schaden ignoriert Rüstung.\n"
        elif damage_type == DamageType.DIRECT:
            ignore_shield = True
            ignore_armor = True
            log += f"→ {damage_type} Schaden ignoriert Schild und Rüstung.\n"
        elif damage_type in [DamageType.DECAY, DamageType.POISON, DamageType.FIRE, DamageType.LIGHTNING, DamageType.COLD]:
             # Mapping für alte Logik falls nicht in JSON
             mapping = {
                 DamageType.DECAY: StatusEffectType.EROSION,
                 DamageType.POISON: StatusEffectType.POISON,
                 DamageType.FIRE: StatusEffectType.BURN,
                 DamageType.LIGHTNING: StatusEffectType.STUN,
                 DamageType.COLD: StatusEffectType.FREEZE
             }
             effect = mapping.get(damage_type)
             if effect:
                 log += f"❓ Chance auf {effect} (Rang {rank})!\n"

    # Schild Berechnung

    # Schild Berechnung
    if not ignore_shield and character.sp > 0:
        absorb = min(character.sp, dmg)
        character.sp -= absorb
        dmg -= absorb
        log += f"→ {absorb} Schaden vom Schild absorbiert.\n"

    # Rüstung Berechnung
    if not ignore_armor and dmg > 0 and character.rp > 0:
        absorb = min(character.rp * 2, dmg)
        rp_loss = (absorb + 1) // 2
        character.rp -= rp_loss
        dmg -= absorb
        log += f"→ {absorb} Schaden durch Rüstung abgefangen ({rp_loss} RP verloren).\n"

    # LP Berechnung
    if dmg > 0:
        character.lp -= dmg
        log += f"→ {dmg} Schaden auf Lebenspunkte!\n"

    if character.lp <= 0 or character.max_lp <= 0:
        log += f"⚔️ {character.name} ist kampfunfähig!\n"

    return log
