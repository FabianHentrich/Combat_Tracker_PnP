import random
from typing import Tuple, List, Dict, Any
from .config import RULES

def calculate_damage(character, dmg: int, damage_type: str = "Normal", rank: int = 1) -> str:
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
            log += f"→ {damage_type} ignoriert Rüstung.\n"
        if ignore_shield:
            log += f"→ {damage_type} ignoriert Schild.\n"

        # Sekundäreffekte (Chance auf Status)
        sec_effect = rule.get("secondary_effect")
        if sec_effect:
            log += f"❓ Chance auf {sec_effect} (Rang {rank})!\n"
    else:
        # Fallback für unbekannte Typen (oder alte Logik falls RULES leer)
        if damage_type == "Durchschlagend":
            ignore_armor = True
            log += "→ Durchschlagender Schaden ignoriert Rüstung.\n"
        elif damage_type == "Direkt":
            ignore_shield = True
            ignore_armor = True
            log += "→ Direktschaden ignoriert Schild und Rüstung.\n"
        elif damage_type in ["Verwesung", "Gift", "Feuer", "Blitz", "Kälte"]:
             # Mapping für alte Logik falls nicht in JSON
             mapping = {
                 "Verwesung": "Erosion", "Gift": "Vergiftung", "Feuer": "Verbrennung",
                 "Blitz": "Betäubung", "Kälte": "Unterkühlung"
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

def process_status_effects(character) -> str:
    log = ""
    new_status = []
    character.skip_turns = 0

    for s in character.status:
        effect = s["effect"]
        rank = s["rank"]
        s["active_rounds"] += 1

        # Effekte anwenden
        if effect == "Vergiftung":
            dmg = rank
            log += calculate_damage(character, dmg, "Direkt")
            log += f" (Vergiftung Rang {rank}, Runde {s['active_rounds']})\n"
        elif effect == "Verbrennung":
            dmg = rank
            log += calculate_damage(character, dmg, "Normal")
            log += f" (Verbrennung Rang {rank}, Runde {s['active_rounds']})\n"
        elif effect == "Blutung":
            # Schaden = Rang/2 + (Runde - 1)
            dmg = int((rank / 2) + (s["active_rounds"] - 1))
            if dmg < 1: dmg = 1
            log += calculate_damage(character, dmg, "Normal")
            log += f" (Blutung Rang {rank}, Runde {s['active_rounds']})\n"
        elif effect == "Erosion":
            dmg = rank * random.randint(1, 4)
            character.max_lp -= dmg
            if character.max_lp < 0: character.max_lp = 0
            log += calculate_damage(character, dmg, "Direkt") # Erosion ist "Dauerhafter Verlust", also Direkt auf LP
            log += f" (Erosion Rang {rank} - {dmg} Max LP dauerhaft verloren)\n"

        # Info Effekte & Status Flags
        if effect == "Unterkühlung":
            log += f"ℹ️ {character.name} verliert Bonusaktion (Unterkühlung Rang {rank}).\n"
        elif effect == "Betäubung":
                log += f"🛑 {character.name} ist betäubt und verliert alle Aktionen!\n"
                character.skip_turns = 1
        elif effect == "Erschöpfung":
                log += f"ℹ️ {character.name} hat -2 Malus auf GEWANDTHEIT (Erschöpfung).\n"
        elif effect == "Verwirrung":
                log += f"ℹ️ {character.name} hat -1 Malus auf KAMPF-Probe (Verwirrung).\n"

        s["rounds"] -= 1
        if s["rounds"] > 0:
            new_status.append(s)

    character.status = new_status
    return log

