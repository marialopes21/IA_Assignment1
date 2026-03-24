
from state import WaterSortState
from search import bfs, dfs, iddfs, ucs, compare_algorithms
from puzzle_io import load_puzzle


def separator(title):
    print(f"\n{'═'*50}")
    print(f"  {title}")
    print('═'*50)


def verify_solution(initial_state: WaterSortState, moves: list, algorithm: str):
    """Replay the solution moves and confirm it reaches a goal state."""
    state = initial_state
    for i, (src, dst) in enumerate(moves):
        assert state.is_valid_move(src, dst), \
            f"[{algorithm}] Move {i+1} ({src}→{dst}) is invalid!"
        state = state.apply_move(src, dst)
    assert state.is_goal(), f"[{algorithm}] Final state is NOT a goal!"
    print(f"   Solution verified ({len(moves)} moves)")



# Puzzle definitions

# already solved
trivial = WaterSortState([
    ['red', 'red', 'red', 'red'],
    ['blue', 'blue', 'blue', 'blue'],
    [],
])

# Easy: 2 colors, needs a few moves
easy = WaterSortState([
    ['red', 'blue', 'red', 'blue'],
    ['blue', 'red', 'blue', 'red'],
    [],
    [],
])

# Medium: 3 colors
medium = WaterSortState([
    ['red', 'blue', 'green', 'red'],
    ['blue', 'green', 'red', 'blue'],
    ['green', 'red', 'blue', 'green'],
    [],
    [],
])


# TEST 1: Trivial
separator("TEST 1: Trivial puzzle (already solved)")

for fn in [bfs, dfs, iddfs, ucs]:
    result = fn(trivial)
    print(result)
    assert result.solved, f"{result.algorithm} should solve trivial puzzle!"
    assert result.solution_length == 0, "Trivial puzzle needs 0 moves"
print("  All algorithms handle trivially solved state")


# TEST 2: Easy puzzle — all algorithms
separator("TEST 2: Easy puzzle")

for fn in [bfs, dfs, iddfs, ucs]:
    result = fn(easy)
    print(result)
    if result.solved:
        verify_solution(easy, result.solution, result.algorithm)
    else:
        print(f"  {result.algorithm} failed to solve easy puzzle!")


# TEST 3: Medium puzzle
separator("TEST 3: Medium puzzle")

for fn in [bfs, dfs, iddfs, ucs]:
    result = fn(medium)
    print(result)
    if result.solved:
        verify_solution(medium, result.solution, result.algorithm)
    else:
        print(f"   {result.algorithm} did not solve medium puzzle")


# TEST 4: BFS vs UCS solution length (should match)
separator("TEST 4: BFS and UCS should give same solution length")

bfs_result = bfs(easy)
ucs_result = ucs(easy)
print(f"  BFS solution length : {bfs_result.solution_length}")
print(f"  UCS solution length : {ucs_result.solution_length}")
assert bfs_result.solution_length == ucs_result.solution_length, \
    "BFS and UCS should find equally optimal solutions!"
print("   Match confirmed")


# TEST 5: Load from file and solve
separator("TEST 5: Load puzzle from file and solve with BFS")

try:
    file_puzzle = load_puzzle("puzzles/easy_1.txt")
    print("Loaded puzzle:")
    file_puzzle.display()
    result = bfs(file_puzzle)
    print(result)
    if result.solved:
        verify_solution(file_puzzle, result.solution, "BFS")
except FileNotFoundError as e:
    print(f"   {e} (run from water_sort/ directory)")


# TEST 6: Full comparison table
separator("TEST 6: Full algorithm comparison on easy puzzle")

results = compare_algorithms(easy)

print("\n── Summary Table ──")
print(f"{'Algorithm':<8} {'Solved':<8} {'Moves':<8} {'States':<10} {'Memory(KB)':<12} {'Time(s)'}")
print("─" * 60)
for r in results:
    print(
        f"{r.algorithm:<8} "
        f"{'Yes' if r.solved else 'No':<8} "
        f"{r.solution_length:<8} "
        f"{r.states_explored:<10} "
        f"{r.max_memory_kb:<12.1f} "
        f"{r.time_seconds:.4f}"
    )

print("\n All search tests complete!")