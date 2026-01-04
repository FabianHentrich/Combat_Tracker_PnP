import random
from typing import Tuple, List, Dict, Any, TYPE_CHECKING
from src.config.defaults import GEW_TO_DICE
from src.config.rule_manager import get_rules
from src.models.enums import DamageType, StatusEffectType
from src.models.combat_results import DamageResult

if TYPE_CHECKING:
    from src.models.character import Character

def roll_exploding_dice(sides: int) -> Tuple[int, List[int]]:
    """
    Simuliert einen explodierenden Würfelwurf.
    Wenn die höchste Augenzahl gewürfelt wird, darf erneut gewürfelt werden.
    Gibt die Summe und die Liste der Einzelwürfe zurück.
    """
    rolls = []
    while True:
        roll = random.randint(1, sides)
        rolls.append(roll)
        if roll != sides:
            break
        # Safety break to prevent infinite loops
        if len(rolls) > 20:
            break
    return sum(rolls), rolls

def get_wuerfel_from_gewandtheit(gewandtheit: int) -> int:
    # Einfache Validierung, um Abstürze zu vermeiden
    if gewandtheit < 1: return 4
    if gewandtheit > 6: return 20
    return GEW_TO_DICE.get(gewandtheit, 20)

def wuerfle_initiative(gewandtheit: int) -> int:
    """Würfelt Initiative basierend auf Gewandtheit (mit explodierenden Würfeln). Rückgabe des Wurfwerts."""
    wuerfel = get_wuerfel_from_gewandtheit(gewandtheit)
    total, _ = roll_exploding_dice(wuerfel)
    return total

def calculate_damage(character: 'Character', dmg: int, damage_type: str = DamageType.NORMAL, rank: int = 1) -> DamageResult:
    """
    Berechnet den Schaden für einen Charakter unter Berücksichtigung von Rüstung, Schild und Schadenstyp.
    Gibt ein DamageResult Objekt zurück.
    """
    # Ensure damage_type is a string (value of Enum)
    if hasattr(damage_type, 'value'):
        damage_type = damage_type.value

    result = DamageResult(
        original_damage=dmg,
        damage_type=damage_type,
        rank=rank
    )

    # Logik basierend auf Schadenstyp aus Regeln laden
    rules = get_rules()
    damage_rules = rules.get("damage_types", {})
    
    if damage_type in damage_rules:
        rule = damage_rules[damage_type]
        result.ignores_shield = rule.get("ignores_shield", False)
        result.ignores_armor = rule.get("ignores_armor", False)
        result.secondary_effect = rule.get("secondary_effect")
    else:
        # Fallback für unbekannte Typen
        if damage_type == DamageType.PIERCING:
            result.ignores_armor = True
        elif damage_type == DamageType.DIRECT:
            result.ignores_shield = True
            result.ignores_armor = True
        elif damage_type in [DamageType.DECAY, DamageType.POISON, DamageType.FIRE, DamageType.LIGHTNING, DamageType.COLD]:
             mapping = {
                 DamageType.DECAY: StatusEffectType.EROSION,
                 DamageType.POISON: StatusEffectType.POISON,
                 DamageType.FIRE: StatusEffectType.BURN,
                 DamageType.LIGHTNING: StatusEffectType.STUN,
                 DamageType.COLD: StatusEffectType.FREEZE
             }
             result.secondary_effect = mapping.get(damage_type)

    current_dmg = dmg

    # Schild Berechnung
    if not result.ignores_shield and character.sp > 0:
        absorb = min(character.sp, current_dmg)
        character.sp -= absorb
        current_dmg -= absorb
        result.absorbed_by_shield = absorb

    # Rüstung Berechnung
    if not result.ignores_armor and current_dmg > 0 and character.rp > 0:
        absorb = min(character.rp * 2, current_dmg)
        rp_loss = (absorb + 1) // 2
        character.rp -= rp_loss
        current_dmg -= absorb
        result.absorbed_by_armor = absorb
        result.armor_loss = rp_loss

    # LP Berechnung
    if current_dmg > 0:
        character.lp -= current_dmg
        result.final_damage_hp = current_dmg

    if character.lp <= 0 or character.max_lp <= 0:
        result.is_dead = True

    return result

def format_damage_log(character: 'Character', result: DamageResult) -> str:
    """
    Erstellt einen lesbaren Log-String aus einem DamageResult.
    """
    log = f"{character.name} erleidet {result.original_damage} ({result.damage_type}) Schaden!\n"

    if result.ignores_armor and result.ignores_shield:
        log += f"→ {result.damage_type} Schaden ignoriert Schild und Rüstung.\n"
    elif result.ignores_armor:
        log += f"→ {result.damage_type} Schaden ignoriert Rüstung.\n"
    elif result.ignores_shield:
        log += f"→ {result.damage_type} Schaden ignoriert Schild.\n"

    if result.secondary_effect:
        log += f"❓ Chance auf {result.secondary_effect} (Rang {result.rank})!\n"

    if result.absorbed_by_shield > 0:
        log += f"→ {result.absorbed_by_shield} Schaden vom Schild absorbiert.\n"

    if result.absorbed_by_armor > 0:
        log += f"→ {result.absorbed_by_armor} Schaden durch Rüstung abgefangen ({result.armor_loss} RP verloren).\n"

    if result.final_damage_hp > 0:
        log += f"→ {result.final_damage_hp} Schaden auf Lebenspunkte!\n"

    if result.is_dead:
        log += f"⚔️ {character.name} ist kampfunfähig!\n"
        
    for msg in result.messages:
        log += f"{msg}\n"

    return log
