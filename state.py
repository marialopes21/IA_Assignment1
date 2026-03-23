"""
state.py - Water Sort Puzzle: Game State Representation & Logic

A WaterSortState holds a list of tubes.
Each tube is a list of color strings, where:
  - Index 0 = BOTTOM of the tube
  - Index -1 = TOP of the tube (poured from/to here)

Example tube (capacity 4):
  ['red', 'blue', 'blue', 'red']
   ^bottom                 ^top
"""

from __future__ import annotations
from typing import Optional


# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

TUBE_CAPACITY = 4  # Standard Water Sort tube size


# ──────────────────────────────────────────────
# WaterSortState
# ──────────────────────────────────────────────

class WaterSortState:
    """
    Immutable-friendly representation of a Water Sort puzzle state.
    
    tubes: tuple of tuples  (hashable → can be used in visited sets)
    Each inner tuple represents one tube (bottom → top order).
    """

    def __init__(self, tubes: list[list[str]], capacity: int = TUBE_CAPACITY):
        # Store as tuple of tuples for hashability & immutability
        self.tubes = tuple(tuple(t) for t in tubes)
        self.capacity = capacity
        self.num_tubes = len(self.tubes)

    # ── Tube queries ──────────────────────────

    def tube_top(self, idx: int) -> Optional[str]:
        """Return the top color of tube idx, or None if empty."""
        t = self.tubes[idx]
        return t[-1] if t else None

    def tube_top_count(self, idx: int) -> int:
        """How many consecutive same-color layers are at the top of tube idx."""
        t = self.tubes[idx]
        if not t:
            return 0
        top_color = t[-1]
        count = 0
        for color in reversed(t):
            if color == top_color:
                count += 1
            else:
                break
        return count

    def tube_free_space(self, idx: int) -> int:
        """How many more layers can fit in tube idx."""
        return self.capacity - len(self.tubes[idx])

    def is_tube_empty(self, idx: int) -> bool:
        return len(self.tubes[idx]) == 0

    def is_tube_complete(self, idx: int) -> bool:
        """
        A tube is complete if:
          - It is empty, OR
          - It is full and contains only one color.
        """
        t = self.tubes[idx]
        if len(t) == 0:
            return True
        if len(t) == self.capacity and len(set(t)) == 1:
            return True
        return False

    # ── Move logic ────────────────────────────

    def is_valid_move(self, src: int, dst: int) -> bool:
        """
        A pour from tube src → tube dst is valid iff:
          1. src != dst
          2. src is not empty
          3. dst is not full
          4. dst is empty  OR  top color of dst == top color of src
        """
        if src == dst:
            return False
        if self.is_tube_empty(src):
            return False
        if self.tube_free_space(dst) == 0:
            return False
        # Pouring a complete tube into an empty tube is pointless
        if self.is_tube_complete(src) and self.is_tube_empty(dst):
            return False
        top_dst = self.tube_top(dst)
        if top_dst is None:
            return True  # dst is empty → always ok (unless caught above)
        return self.tube_top(src) == top_dst

    def get_valid_moves(self) -> list[tuple[int, int]]:
        """Return all (src, dst) pairs that are currently valid moves."""
        moves = []
        for src in range(self.num_tubes):
            for dst in range(self.num_tubes):
                if self.is_valid_move(src, dst):
                    moves.append((src, dst))
        return moves

    def apply_move(self, src: int, dst: int) -> "WaterSortState":
        """
        Return a NEW WaterSortState after pouring src → dst.
        Pours as many layers as possible (matching color, fitting in dst).
        Does NOT modify self.
        """
        assert self.is_valid_move(src, dst), f"Invalid move: {src} → {dst}"

        tubes = [list(t) for t in self.tubes]  # mutable copy

        pour_color = tubes[src][-1]
        amount = min(self.tube_top_count(src), self.tube_free_space(dst))

        for _ in range(amount):
            tubes[src].pop()
            tubes[dst].append(pour_color)

        return WaterSortState(tubes, self.capacity)

    # ── Win/loss detection ────────────────────

    def is_goal(self) -> bool:
        """The puzzle is solved when every tube is complete."""
        return all(self.is_tube_complete(i) for i in range(self.num_tubes))

    # ── Hashing & equality (needed for search) ─

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WaterSortState):
            return False
        return self.tubes == other.tubes

    def __hash__(self) -> int:
        return hash(self.tubes)

    # ── Display ───────────────────────────────

    def __repr__(self) -> str:
        lines = []
        for i, tube in enumerate(self.tubes):
            bar = " | ".join(c[:3].upper() for c in tube) if tube else "(empty)"
            complete = " ✓" if self.is_tube_complete(i) else ""
            lines.append(f"  Tube {i}: [{bar}]{complete}")
        return "WaterSortState:\n" + "\n".join(lines)

    def display(self) -> None:
        """Pretty-print the current state to the console."""
        print(self)

    # ── Cost ──────────────────────────────────

    def move_cost(self, src: int, dst: int) -> int:
        """
        Cost of a move. Default = 1 (uniform cost).
        Override for weighted variants.
        """
        return 1
