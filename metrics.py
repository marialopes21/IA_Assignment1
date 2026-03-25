"""
Performance Metrics & Algorithm Comparison for Water Sort

"""

import os
import time
from state import WaterSortState
from search import bfs, dfs, iddfs, ucs, SearchResult
from search_heuristic import greedy, astar, weighted_astar
from heuristics import h1_unsolved_tubes, h2_color_misplacement, h3_combined
from puzzle_io import load_puzzle, list_puzzles

# Algorithm registry

UNINFORMED = [
    ("BFS",   bfs),
    ("DFS",   dfs),
    ("IDDFS", iddfs),
    ("UCS",   ucs),
]

HEURISTIC = [
    ("Greedy (h1)",        lambda s: greedy(s, h1_unsolved_tubes)),
    ("Greedy (h2)",        lambda s: greedy(s, h2_color_misplacement)),
    ("Greedy (h3)",        lambda s: greedy(s, h3_combined)),
    ("A* (h1)",            lambda s: astar(s, h1_unsolved_tubes)),
    ("A* (h2)",            lambda s: astar(s, h2_color_misplacement)),
    ("A* (h3)",            lambda s: astar(s, h3_combined)),
    ("WA* W=1.5 (h3)",     lambda s: weighted_astar(s, h3_combined, 1.5)),
    ("WA* W=2.0 (h3)",     lambda s: weighted_astar(s, h3_combined, 2.0)),
]

ALL_ALGORITHMS = UNINFORMED + HEURISTIC

SLOW_ALGORITHMS = {"IDDFS"}


def run_algorithm(name: str, fn, state: WaterSortState, skip_slow=False) -> SearchResult | None:
    if skip_slow and name in SLOW_ALGORITHMS:
        print(f"  [{name}] ⏭  Skipped (too slow for this puzzle size)")
        return None

    print(f"  [{name}] Running...", end="\r")
    result = fn(state)
    result.algorithm = name
    print(f"  {result}")
    return result


# Run all algorithms on one puzzle

def benchmark_puzzle(
    state: WaterSortState,
    puzzle_name: str = "puzzle",
    skip_slow: bool = False,
    algorithms=None,
) -> list[SearchResult]:
    algs = algorithms if algorithms is not None else ALL_ALGORITHMS
    results = []

    print(f"\n{'─'*55}")
    print(f"  Benchmarking: {puzzle_name}")
    print(f"  Tubes: {state.num_tubes} | Capacity: {state.capacity}")
    print(f"{'─'*55}")

    for name, fn in algs:
        result = run_algorithm(name, fn, state, skip_slow=skip_slow)
        if result is not None:
            results.append(result)

    return results

# Run all algorithms across multiple puzzles

def benchmark_all_puzzles(
    puzzle_folder: str = "puzzles",
    skip_slow: bool = True,
    algorithms=None,
) -> dict[str, list[SearchResult]]:
    files = list_puzzles(puzzle_folder)
    if not files:
        print(f"No puzzle files found in '{puzzle_folder}/'")
        return {}

    all_results = {}
    for filepath in files:
        name = os.path.basename(filepath)
        try:
            state = load_puzzle(filepath)
            results = benchmark_puzzle(state, name, skip_slow=skip_slow, algorithms=algorithms)
            all_results[name] = results
        except Exception as e:
            print(f"    Failed to load {name}: {e}")

    return all_results


def print_table(results: list[SearchResult], title: str = "Results") -> None:
    if not results:
        print("No results to display.")
        return

    print(f"\n{'═'*72}")
    print(f"  {title}")
    print(f"{'═'*72}")
    print(f"{'Algorithm':<22} {'Solved':<8} {'Moves':<8} {'States':<12} {'Mem(KB)':<12} {'Time(s)'}")
    print("─" * 72)
    for r in results:
        solved_str = " Yes" if r.solved else " No"
        print(
            f"{r.algorithm:<22} "
            f"{solved_str:<8} "
            f"{r.solution_length:<8} "
            f"{r.states_explored:<12} "
            f"{r.max_memory_kb:<12.1f} "
            f"{r.time_seconds:.4f}"
        )
    print("─" * 72)


def save_report(
    results_by_puzzle: dict[str, list[SearchResult]],
    output_path: str = "results/report.txt",
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        f.write("=" * 72 + "\n")
        f.write("  WATER SORT — ALGORITHM BENCHMARK REPORT\n")
        f.write(f"  Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 72 + "\n\n")

        for puzzle_name, results in results_by_puzzle.items():
            f.write(f"\nPuzzle: {puzzle_name}\n")
            f.write("─" * 72 + "\n")
            f.write(
                f"{'Algorithm':<22} {'Solved':<8} {'Moves':<8} "
                f"{'States':<12} {'Mem(KB)':<12} {'Time(s)'}\n"
            )
            f.write("─" * 72 + "\n")
            for r in results:
                solved_str = "Yes" if r.solved else "No"
                f.write(
                    f"{r.algorithm:<22} {solved_str:<8} {r.solution_length:<8} "
                    f"{r.states_explored:<12} {r.max_memory_kb:<12.2f} {r.time_seconds:.4f}\n"
                )
            f.write("\n")

            solved = [r for r in results if r.solved]
            if solved:
                fastest   = min(solved, key=lambda r: r.time_seconds)
                fewest    = min(solved, key=lambda r: r.states_explored)
                optimal   = min(solved, key=lambda r: r.solution_length)
                f.write(f"  Fastest        : {fastest.algorithm} ({fastest.time_seconds:.4f}s)\n")
                f.write(f"  Fewest states  : {fewest.algorithm} ({fewest.states_explored} states)\n")
                f.write(f"  Best solution  : {optimal.algorithm} ({optimal.solution_length} moves)\n")
            f.write("\n")

        f.write("=" * 72 + "\n")
        f.write("END OF REPORT\n")

    print(f"\n Report saved to: {output_path}")
