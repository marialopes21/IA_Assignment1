from __future__ import annotations
from typing import Optional

TUBE_CAPACITY = 4  

class WaterSortState:
    def __init__(self, tubes: list[list[str]], capacity: int = TUBE_CAPACITY):
        self.tubes = tuple(tuple(t) for t in tubes)
        self.capacity = capacity
        self.num_tubes = len(self.tubes)

    def tube_top(self, idx: int) -> Optional[str]:
        t = self.tubes[idx]
        return t[-1] if t else None

    def tube_top_count(self, idx: int) -> int:
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

        return self.capacity - len(self.tubes[idx])

    def is_tube_empty(self, idx: int) -> bool:
        return len(self.tubes[idx]) == 0

    def is_tube_complete(self, idx: int) -> bool:
        t = self.tubes[idx]
        if len(t) == 0:
            return True
        if len(t) == self.capacity and len(set(t)) == 1:
            return True
        return False

    def is_valid_move(self, src: int, dst: int) -> bool:
        if src == dst:
            return False
        if self.is_tube_empty(src):
            return False
        if self.tube_free_space(dst) == 0:
            return False
        if self.is_tube_complete(src) and self.is_tube_empty(dst):
            return False
        top_dst = self.tube_top(dst)
        if top_dst is None:
            return True  
        return self.tube_top(src) == top_dst

    def get_valid_moves(self) -> list[tuple[int, int]]: 
        moves = []
        for src in range(self.num_tubes):
            for dst in range(self.num_tubes):
                if self.is_valid_move(src, dst):
                    moves.append((src, dst))
        return moves

    def apply_move(self, src: int, dst: int) -> "WaterSortState":
        assert self.is_valid_move(src, dst), f"Invalid move: {src} → {dst}"

        tubes = [list(t) for t in self.tubes]

        pour_color = tubes[src][-1]
        amount = min(self.tube_top_count(src), self.tube_free_space(dst))

        for _ in range(amount):
            tubes[src].pop()
            tubes[dst].append(pour_color)

        return WaterSortState(tubes, self.capacity)

    def is_goal(self) -> bool:
        return all(self.is_tube_complete(i) for i in range(self.num_tubes))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WaterSortState):
            return False
        return self.tubes == other.tubes

    def __hash__(self) -> int:
        return hash(self.tubes)

    def __repr__(self) -> str:
        lines = []
        for i, tube in enumerate(self.tubes):
            bar = " | ".join(c[:3].upper() for c in tube) if tube else "(empty)"
            complete = " ✓" if self.is_tube_complete(i) else ""
            lines.append(f"  Tube {i}: [{bar}]{complete}")
        return "WaterSortState:\n" + "\n".join(lines)

    def display(self) -> None:
        print(self)

    def move_cost(self, src: int, dst: int) -> int:
        return 1
