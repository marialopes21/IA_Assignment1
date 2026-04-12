"""
heuristics.py - Heuristic Functions for Water Sort Puzzle
"""

from state import WaterSortState

# H1 — Unsolved Tubes
def h1_unsolved_tubes(state: WaterSortState) -> int:
    return sum(
        1 for i in range(state.num_tubes)
        if not state.is_tube_complete(i)
    )

# H2 — Color Misplacement
def h2_color_misplacement(state: WaterSortState) -> int:
    count = 0
    for i in range(state.num_tubes):
        tube = state.tubes[i]
        if not tube:
            continue
        if len(set(tube)) == 1 and len(tube) == state.capacity:
            continue
        count += len(tube)
    return count

# H3 — Combined Heuristic 
def h3_combined(state: WaterSortState) -> int:
    total = 0

    for i in range(state.num_tubes):
        tube = state.tubes[i]
        if len(tube) < 2:
            continue
        for j in range(1, len(tube)):
            if tube[j] != tube[j - 1]:
                total += 1

    color_tubes: dict[str, set[int]] = {}
    for i, tube in enumerate(state.tubes):
        for color in set(tube):
            if color not in color_tubes:
                color_tubes[color] = set()
            color_tubes[color].add(i)

    for color, tube_set in color_tubes.items():
        if len(tube_set) > 1:
            total += len(tube_set) - 1 

    return total

# Heuristic
HEURISTICS = {
    "h1_unsolved_tubes"   : h1_unsolved_tubes,
    "h2_color_misplacement": h2_color_misplacement,
    "h3_combined"         : h3_combined,
}

def get_heuristic(name: str):
    if name not in HEURISTICS:
        raise KeyError(f"Unknown heuristic '{name}'. Available: {list(HEURISTICS)}")
    return HEURISTICS[name]
