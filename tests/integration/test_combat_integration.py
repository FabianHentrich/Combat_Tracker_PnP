"""
Integration tests — no mocking, real objects only.
Tests cross-layer behavior that unit tests with heavy mocking cannot catch.
"""
import pytest
from src.core.engine import CombatEngine
from src.core.history import HistoryManager
from src.models.character import Character
from src.models.enums import StatusEffectType
from src.models.status_effects import PoisonEffect, StunEffect


# ---------------------------------------------------------------------------
# 1. Full combat round progression
# ---------------------------------------------------------------------------

def test_full_combat_round_progression():
    """
    Two characters with preset initiative values.
    Verifies correct turn order and round increment without any mocking.
    """
    engine = CombatEngine()
    alice = Character("Alice", lp=20, rp=0, sp=0, init=20)
    bob   = Character("Bob",   lp=20, rp=0, sp=0, init=10)
    engine.characters = [alice, bob]

    engine.sort_initiative()               # [Alice(20), Bob(10)]
    engine.turn_manager.turn_index = -1
    engine.turn_manager.round_number = 1

    # Round 1 — Alice
    c = engine.next_turn()
    assert c.name == "Alice"
    assert engine.round_number == 1

    # Round 1 — Bob
    c = engine.next_turn()
    assert c.name == "Bob"
    assert engine.round_number == 1

    # Round 2 — wraps back to Alice
    c = engine.next_turn()
    assert c.name == "Alice"
    assert engine.round_number == 2


# ---------------------------------------------------------------------------
# 2. Damage absorption chain: SP → RP → LP
# ---------------------------------------------------------------------------

def test_damage_absorption_chain():
    """
    A character with SP and RP receives a large hit.
    Verifies that damage is absorbed in the correct order with correct math.

    char: lp=100, rp=5, sp=10
    30 damage:
      shield absorbs min(10, 30) = 10  → sp=0,  remaining=20
      armor  absorbs min(10, 20) = 10  → rp_loss=(10+1)//2=5, rp=0, remaining=10
      hp     takes 10                  → lp=90
    """
    engine = CombatEngine()
    char = Character("Tank", lp=100, rp=5, sp=10, init=0)
    engine.characters = [char]

    engine.apply_damage(char, 30, "NORMAL", 1)

    assert char.sp == 0
    assert char.rp == 0
    assert char.lp == 90


# ---------------------------------------------------------------------------
# 3. Status effect lifecycle — Stun skips a turn then expires
# ---------------------------------------------------------------------------

def test_stun_skips_turn_and_expires():
    """
    Alice has a 1-round Stun applied before her first turn.
    When next_turn() is called, Alice is skipped and Bob acts.
    On the next call (new round) Alice acts normally and has no status effects.
    """
    engine = CombatEngine()
    alice = Character("Alice", lp=20, rp=0, sp=0, init=20)
    bob   = Character("Bob",   lp=20, rp=0, sp=0, init=10)
    engine.characters = [alice, bob]
    engine.sort_initiative()               # [Alice, Bob]
    engine.turn_manager.turn_index = -1
    engine.turn_manager.round_number = 1

    alice.status = [StunEffect(duration=1, rank=1)]

    # Alice is stunned → skipped → Bob acts
    result1 = engine.next_turn()
    assert result1.name == "Bob"
    assert engine.round_number == 1

    # Next call: new round, Alice's stun expired
    result2 = engine.next_turn()
    assert result2.name == "Alice"
    assert engine.round_number == 2
    assert len(alice.status) == 0          # Effect consumed


# ---------------------------------------------------------------------------
# 4. Poison deals damage over multiple turns
# ---------------------------------------------------------------------------

def test_poison_damages_over_turns():
    """
    A character with Poison rank=2 duration=3 and no SP/RP.
    After 3 turns, LP should have dropped by 2 per turn = 6 total.
    """
    engine = CombatEngine()
    char = Character("Victim", lp=100, rp=0, sp=0, init=10)
    engine.characters = [char]
    engine.turn_manager.turn_index = -1

    char.status = [PoisonEffect(duration=3, rank=2)]

    engine.next_turn()   # Round 1 — poison fires, 2 dmg
    engine.next_turn()   # Round 2 — poison fires, 2 dmg
    engine.next_turn()   # Round 3 — poison fires, 2 dmg, effect expires

    assert char.lp == 94                   # 100 - 6
    assert len(char.status) == 0           # Poison consumed


# ---------------------------------------------------------------------------
# 5. Save / load state roundtrip
# ---------------------------------------------------------------------------

def test_save_load_state_roundtrip():
    """
    Build a complex engine state (character with status, non-default turn/round),
    serialize it, load it into a fresh engine, and verify exact match.
    """
    engine = CombatEngine()
    char = Character("Hero", lp=80, rp=5, sp=3, init=15)
    char.add_status(StatusEffectType.POISON.value, duration=3, rank=2)
    engine.characters = [char]
    engine.turn_manager.turn_index = 0
    engine.turn_manager.round_number = 3

    state = engine.get_state()

    new_engine = CombatEngine()
    new_engine.load_state(state)

    loaded = new_engine.characters[0]
    assert loaded.name == "Hero"
    assert loaded.lp == 80
    assert loaded.rp == 5
    assert loaded.sp == 3
    assert loaded.init == 15
    assert len(loaded.status) == 1
    assert isinstance(loaded.status[0], PoisonEffect)
    assert loaded.status[0].rank == 2
    assert new_engine.turn_index == 0
    assert new_engine.round_number == 3


# ---------------------------------------------------------------------------
# 6. History undo / redo chain across multiple actions
# ---------------------------------------------------------------------------

def test_history_undo_redo_chain():
    """
    Three sequential damage actions.
    Verifies that undo walks back through each state and redo replays them.
    """
    engine = CombatEngine()
    history = HistoryManager(engine)
    char = Character("Hero", lp=100, rp=0, sp=0, init=0)
    engine.characters = [char]

    # Action 1: lp 100 → 80
    history.save_snapshot()
    engine.characters[0].lp = 80

    # Action 2: lp 80 → 60
    history.save_snapshot()
    engine.characters[0].lp = 60

    # Action 3: lp 60 → 40
    history.save_snapshot()
    engine.characters[0].lp = 40

    history.undo()
    assert engine.characters[0].lp == 60

    history.undo()
    assert engine.characters[0].lp == 80

    # Redo back to 60
    history.redo()
    assert engine.characters[0].lp == 60

    # New action clears redo stack
    history.save_snapshot()
    engine.characters[0].lp = 30
    assert history.redo() is False          # Redo stack cleared


# ---------------------------------------------------------------------------
# 7. Overheal flag — with and without cap at max_lp
# ---------------------------------------------------------------------------

def test_overheal_flag():
    """
    Healing without overheal is capped at max_lp.
    Healing with allow_overheal=True can exceed it.
    """
    engine = CombatEngine()
    char = Character("Hero", lp=90, rp=0, sp=0, init=0)
    char.max_lp = 100
    engine.characters = [char]

    # Default: capped
    engine.apply_healing(char, 20, allow_overheal=False)
    assert char.lp == 100

    # Reset and test overheal
    char.lp = 90
    engine.apply_healing(char, 20, allow_overheal=True)
    assert char.lp == 110
