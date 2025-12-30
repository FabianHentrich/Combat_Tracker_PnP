import random

class Character:
    def __init__(self, name, lp, rp, sp, init, char_type="Gegner"):
        self.name = name
        self.char_type = char_type
        self.max_lp = lp # Speichern der Max LP für Verhältnisse
        self.lp = lp
        self.max_rp = rp
        self.rp = rp
        self.max_sp = sp
        self.sp = sp
        self.init = init
        self.status = []
        self.skip_turns = 0

    def apply_damage(self, dmg, damage_type="Normal", rank=1):
        log = f"{self.name} erleidet {dmg} ({damage_type}) Schaden!\n"

        # Logik basierend auf Schadenstyp
        ignore_shield = False
        ignore_armor = False

        if damage_type == "Durchschlagend":
            ignore_armor = True
            log += "→ Durchschlagender Schaden ignoriert Rüstung.\n"
        elif damage_type == "Direkt":
            ignore_shield = True
            ignore_armor = True
            log += "→ Direktschaden ignoriert Schild und Rüstung.\n"
        elif damage_type == "Verwesung":
            log += f"❓ Chance auf Erosion (Rang {rank})!\n"
        elif damage_type == "Gift":
            log += f"❓ Chance auf Vergiftung (Rang {rank}).\n"
        elif damage_type == "Feuer":
            log += f"❓ Chance auf Verbrennung (Rang {rank}).\n"
        elif damage_type == "Blitz":
            log += f"❓ Chance auf Betäubung (Rang {rank}).\n"
        elif damage_type == "Kälte":
            log += f"❓ Chance auf Unterkühlung (Rang {rank}).\n"

        # Schild Berechnung
        if not ignore_shield and self.sp > 0:
            absorb = min(self.sp, dmg)
            self.sp -= absorb
            dmg -= absorb
            log += f"→ {absorb} Schaden vom Schild absorbiert.\n"

        # Rüstung Berechnung
        if not ignore_armor and dmg > 0 and self.rp > 0:
            absorb = min(self.rp * 2, dmg)
            rp_loss = (absorb + 1) // 2
            self.rp -= rp_loss
            dmg -= absorb
            log += f"→ {absorb} Schaden durch Rüstung abgefangen.\n"

        # LP Berechnung
        if dmg > 0:
            self.lp -= dmg
            log += f"→ {dmg} Schaden auf Lebenspunkte!\n"

        if self.lp <= 0 or self.max_lp <= 0:
            log += f"⚔️ {self.name} ist kampfunfähig!\n"
        return log

    def add_status(self, effect, duration, rank=1):
        if rank > 6: rank = 6
        self.status.append({"effect": effect, "rounds": duration, "rank": rank, "active_rounds": 0})

    def update_status(self):
        log = ""
        new_status = []
        self.skip_turns = 0

        for s in self.status:
            effect = s["effect"]
            rank = s["rank"]
            s["active_rounds"] += 1

            # Effekte anwenden
            if effect == "Vergiftung":
                dmg = rank
                log += self.apply_damage(dmg, "Direkt")
                log += f" (Vergiftung Rang {rank})\n"
            elif effect == "Verbrennung":
                dmg = rank
                log += self.apply_damage(dmg, "Normal") # Oder Direkt? Regelwerk sagt "Schaden".
                log += f" (Verbrennung Rang {rank})\n"
            elif effect == "Blutung":
                # Schaden = Rang/2 + (Runde - 1)
                dmg = int((rank / 2) + (s["active_rounds"] - 1))
                if dmg < 1: dmg = 1
                log += self.apply_damage(dmg, "Normal")
                log += f" (Blutung Rang {rank}, Runde {s['active_rounds']})\n"
            elif effect == "Erosion":
                dmg = rank * random.randint(1, 4)
                self.max_lp -= dmg
                if self.max_lp < 0: self.max_lp = 0
                log += self.apply_damage(dmg, "Direkt") # Erosion ist "Dauerhafter Verlust", also Direkt auf LP
                log += f" (Erosion Rang {rank} - {dmg} Max LP dauerhaft verloren)\n"

            # Info Effekte & Status Flags
            if effect == "Unterkühlung":
                log += f"ℹ️ {self.name} verliert Bonusaktion (Unterkühlung Rang {rank}).\n"
            elif effect == "Betäubung":
                 log += f"🛑 {self.name} ist betäubt und verliert alle Aktionen!\n"
                 self.skip_turns = 1
            elif effect == "Erschöpfung":
                 log += f"ℹ️ {self.name} hat -2 Malus auf GEWANDTHEIT (Erschöpfung).\n"
            elif effect == "Verwirrung":
                 log += f"ℹ️ {self.name} hat -1 Malus auf KAMPF-Probe (Verwirrung).\n"

            s["rounds"] -= 1
            if s["rounds"] > 0:
                new_status.append(s)

        self.status = new_status
        return log

    def heal(self, healing_points):
        """Heilt den Charakter um eine bestimmte Anzahl an Lebenspunkten."""
        self.lp += healing_points
        return f"{self.name} wird um {healing_points} LP geheilt! Aktuelle LP: {self.lp}"

