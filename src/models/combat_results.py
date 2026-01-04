from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class DamageResult:
    """
    Hält das Ergebnis einer Schadensberechnung.
    """
    original_damage: int
    damage_type: str
    rank: int
    
    # Ergebnisse
    final_damage_hp: int = 0      # Schaden, der tatsächlich auf LP ging
    absorbed_by_shield: int = 0   # Schaden vom Schild gefressen
    absorbed_by_armor: int = 0    # Schaden von Rüstung gefressen
    armor_loss: int = 0           # Wieviel RP wurden zerstört
    
    # Flags & Infos
    is_dead: bool = False
    ignores_armor: bool = False
    ignores_shield: bool = False
    secondary_effect: Optional[str] = None # Name des möglichen Statuseffekts
    
    # Zusätzliche Nachrichten (für Sonderfälle)
    messages: List[str] = field(default_factory=list)
