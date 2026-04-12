from state import WaterSortState
from puzzle_io import load_puzzle, list_puzzles
from metrics import benchmark_puzzle, benchmark_all_puzzles, print_table, save_report, UNINFORMED, HEURISTIC, ALL_ALGORITHMS

def separator(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print(f"{'═'*55}")

# TEST 1: Benchmark a single easy puzzle
separator("TEST 1: Single puzzle benchmark (easy_1)")

state = load_puzzle("puzzles/easy_1.txt")
results = benchmark_puzzle(state, "easy_1.txt", skip_slow=False)
print_table(results, "Easy Puzzle 1 — All Algorithms")

# TEST 2: Uninformed only on medium
separator("TEST 2: Uninformed algorithms on medium_1")

state = load_puzzle("puzzles/medium_1.txt")
results = benchmark_puzzle(state, "medium_1.txt", skip_slow=True, algorithms=UNINFORMED)
print_table(results, "Medium Puzzle 1 — Uninformed Only")

# TEST 3: Heuristic only on medium
separator("TEST 3: Heuristic algorithms on medium_1")

state = load_puzzle("puzzles/medium_1.txt")
results = benchmark_puzzle(state, "medium_1.txt", skip_slow=False, algorithms=HEURISTIC)
print_table(results, "Medium Puzzle 1 — Heuristic Only")

# TEST 4: Full benchmark across all puzzle files
separator("TEST 4: Full benchmark — all puzzles (IDDFS skipped on large)")

all_results = benchmark_all_puzzles("puzzles", skip_slow=True)

for puzzle_name, results in all_results.items():
    print_table(results, puzzle_name)

# TEST 5: Save full report
separator("TEST 5: Save report to file")

save_report(all_results, output_path="results/benchmark_report.txt")
print("   Report saved!")

print("\n All metrics tests complete!")