"""
test_state.py - Manual tests for state.py and puzzle_io.py
Run with: python test_state.py
"""

from state import WaterSortState
from puzzle_io import load_puzzle, save_puzzle, save_results


def separator(title):
    print(f"\n{'─'*40}")
    print(f"  {title}")
    print('─'*40)


# ──────────────────────────────────────────────
# TEST 1: Basic state creation & display
# ──────────────────────────────────────────────
separator("TEST 1: State creation")

state = WaterSortState([
    ['red', 'blue', 'red', 'blue'],
    ['blue', 'red', 'blue', 'red'],
    [],
    []
])
state.display()


# ──────────────────────────────────────────────
# TEST 2: Tube queries
# ──────────────────────────────────────────────
separator("TEST 2: Tube queries")

print(f"Tube 0 top      : {state.tube_top(0)}")           # blue
print(f"Tube 0 top count: {state.tube_top_count(0)}")     # 1
print(f"Tube 0 free     : {state.tube_free_space(0)}")    # 0
print(f"Tube 2 empty?   : {state.is_tube_empty(2)}")      # True
print(f"Tube 0 complete?: {state.is_tube_complete(0)}")   # False
print(f"Tube 2 complete?: {state.is_tube_complete(2)}")   # True (empty = complete)


# ──────────────────────────────────────────────
# TEST 3: Valid moves
# ──────────────────────────────────────────────
separator("TEST 3: Valid moves")

moves = state.get_valid_moves()
print(f"Valid moves: {moves}")
# Tube 0 top = blue, Tube 1 top = red → they don't match, only empty tubes are valid dst


# ──────────────────────────────────────────────
# TEST 4: Apply a move
# ──────────────────────────────────────────────
separator("TEST 4: Apply move (tube 0 → tube 2)")

new_state = state.apply_move(0, 2)
print("After move:")
new_state.display()
print(f"Original state unchanged? {state.tubes[0] == ('red', 'blue', 'red', 'blue')}")


# ──────────────────────────────────────────────
# TEST 5: Win detection
# ──────────────────────────────────────────────
separator("TEST 5: Win detection")

winning_state = WaterSortState([
    ['red', 'red', 'red', 'red'],
    ['blue', 'blue', 'blue', 'blue'],
    [],
])
print(f"Winning state goal?: {winning_state.is_goal()}")   # True
print(f"Normal state goal? : {state.is_goal()}")           # False


# ──────────────────────────────────────────────
# TEST 6: Hashing (for search visited sets)
# ──────────────────────────────────────────────
separator("TEST 6: Hashing")

s1 = WaterSortState([['red', 'blue'], ['blue', 'red'], []])
s2 = WaterSortState([['red', 'blue'], ['blue', 'red'], []])
s3 = WaterSortState([['blue', 'red'], ['red', 'blue'], []])

print(f"s1 == s2: {s1 == s2}")   # True
print(f"s1 == s3: {s1 == s3}")   # False
print(f"Can use in set: {len({s1, s2, s3}) == 2}")  # True


# ──────────────────────────────────────────────
# TEST 7: Load puzzle from file
# ──────────────────────────────────────────────
separator("TEST 7: Load puzzle from file")

try:
    loaded = load_puzzle("puzzles/easy_1.txt")
    print("Loaded puzzle:")
    loaded.display()
except FileNotFoundError as e:
    print(f"File not found (run from water_sort/ directory): {e}")


# ──────────────────────────────────────────────
# TEST 8: Save puzzle & results
# ──────────────────────────────────────────────
separator("TEST 8: Save puzzle & results")

save_puzzle(winning_state, "puzzles/test_output.txt", comment="Auto-generated test puzzle")

save_results(
    filepath="results/test_results.txt",
    puzzle_file="puzzles/easy_1.txt",
    algorithm="BFS",
    solution_moves=[(0, 2), (1, 3), (0, 2)],
    stats={
        "time_seconds"   : 0.004,
        "states_explored": 42,
        "max_memory"     : "2.1 MB",
        "solution_length": 3,
    },
    initial_state=state,
)

print("\n✅ All tests complete!")
