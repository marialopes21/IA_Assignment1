from state import WaterSortState
from heuristics import h1_unsolved_tubes, h2_color_misplacement, h3_combined, HEURISTICS
from search import bfs
from search_heuristic import greedy, astar, weighted_astar, compare_heuristic_algorithms

def separator(title):
    print(f"\n{'═'*50}")
    print(f"  {title}")
    print('═'*50)

def verify_solution(initial_state, moves, algorithm):
    state = initial_state
    for i, (src, dst) in enumerate(moves):
        assert state.is_valid_move(src, dst), f"[{algorithm}] Move {i+1} invalid!"
        state = state.apply_move(src, dst)
    assert state.is_goal(), f"[{algorithm}] Final state is NOT goal!"
    print(f"   Solution verified ({len(moves)} moves)")

solved = WaterSortState([
    ['red', 'red', 'red', 'red'],
    ['blue', 'blue', 'blue', 'blue'],
    [],
])

easy = WaterSortState([
    ['red', 'blue', 'red', 'blue'],
    ['blue', 'red', 'blue', 'red'],
    [],
    [],
])

medium = WaterSortState([
    ['red', 'blue', 'green', 'red'],
    ['blue', 'green', 'red', 'blue'],
    ['green', 'red', 'blue', 'green'],
    [],
    [],
])


# TEST 1: Heuristic values on solved state (must be 0)
separator("TEST 1: Heuristics on solved state (all must = 0)")

for name, h in HEURISTICS.items():
    val = h(solved)
    status = "Correct!" if val == 0 else "Wrong"
    print(f"  {status} {name}: {val}")

# TEST 2: Heuristic values on easy puzzle (must be > 0)
separator("TEST 2: Heuristics on easy puzzle (all must be > 0)")

for name, h in HEURISTICS.items():
    val = h(easy)
    status = "Correct!" if val > 0 else "Wrong"
    print(f"  {status} {name}: {val}")

# TEST 3: H3 is more informed than H1
separator("TEST 3: H3 >= H1 (more informed heuristic)")

for puzzle_name, puzzle in [("easy", easy), ("medium", medium)]:
    h1 = h1_unsolved_tubes(puzzle)
    h3 = h3_combined(puzzle)
    status = "Correct!" if h3 >= h1 else "Warning "
    print(f"  {status} {puzzle_name}: h1={h1}, h3={h3}")

# TEST 4: Greedy — all heuristics
separator("TEST 4: Greedy with all heuristics (easy puzzle)")

for name, h in HEURISTICS.items():
    result = greedy(easy, heuristic=h)
    print(f"  [{name}] {result}")
    if result.solved:
        verify_solution(easy, result.solution, f"Greedy+{name}")

# TEST 5: A* — all heuristics
separator("TEST 5: A* with all heuristics (easy puzzle)")

bfs_result = bfs(easy)
print(f"  [BFS baseline] {bfs_result}")

for name, h in HEURISTICS.items():
    result = astar(easy, heuristic=h)
    optimal = "Correct optimal" if result.solution_length == bfs_result.solution_length else "Warning  suboptimal"
    print(f"  [{name}] {result} → {optimal}")
    if result.solved:
        verify_solution(easy, result.solution, f"A*+{name}")

# TEST 6: Weighted A* — different weights
separator("TEST 6: Weighted A* with different weights (easy puzzle)")

print(f"  BFS optimal length: {bfs_result.solution_length} moves\n")
for w in [1.0, 1.2, 1.5, 2.0, 3.0]:
    result = weighted_astar(easy, heuristic=h3_combined, weight=w)
    diff = result.solution_length - bfs_result.solution_length
    tag = "= optimal" if diff == 0 else f"+{diff} moves"
    print(f"  W={w:.1f}: {result} → {tag}")

# TEST 7: Medium puzzle — A* vs BFS
separator("TEST 7: Medium puzzle — A* (h3) vs BFS")

bfs_med = bfs(medium)
astar_med = astar(medium, heuristic=h3_combined)

print(f"  BFS  : {bfs_med}")
print(f"  A*   : {astar_med}")

speedup = bfs_med.states_explored / max(astar_med.states_explored, 1)
print(f"\n  A* explored {astar_med.states_explored} states vs BFS {bfs_med.states_explored}")
print(f"  → A* is ~{speedup:.1f}x more efficient on states explored")

if astar_med.solved:
    verify_solution(medium, astar_med.solution, "A* medium")

# TEST 8: Full comparison table
separator("TEST 8: Full comparison — all algorithms on medium puzzle")

from search import compare_algorithms

print("── Uninformed ──")
uninformed = compare_algorithms(medium)

print("\n── Heuristic (h3_combined) ──")
heuristic_results = compare_heuristic_algorithms(medium, heuristic=h3_combined)

all_results = uninformed + heuristic_results
print("\n── Full Summary Table ──")
print(f"{'Algorithm':<26} {'Moves':<8} {'States':<12} {'Memory(KB)':<14} {'Time(s)'}")
print("─" * 72)
for r in all_results:
    print(
        f"{r.algorithm:<26} "
        f"{r.solution_length:<8} "
        f"{r.states_explored:<12} "
        f"{r.max_memory_kb:<14.1f} "
        f"{r.time_seconds:.4f}"
    )

print("\n All heuristic tests complete!")