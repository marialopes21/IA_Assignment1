"""
puzzle_io.py - Load and save Water Sort puzzles from/to text files.

──────────────────────────────────────────────
FILE FORMAT  (puzzles/*.txt)
──────────────────────────────────────────────

Lines starting with '#' are comments and are ignored.
The first non-comment line must be:
    capacity=<int>

Each subsequent non-comment line defines one tube (bottom → top),
with colors separated by spaces. An empty line or the word "empty"
means an empty tube.

Example file (easy_1.txt):
─────────────────────────────
# Easy puzzle 1
capacity=4
red blue blue red
blue red red blue
empty
empty
─────────────────────────────

Color names can be anything (e.g., red, blue, R, B, 1, 2 …).
"""

import os
from state import WaterSortState


# ──────────────────────────────────────────────
# Load
# ──────────────────────────────────────────────

def load_puzzle(filepath: str) -> WaterSortState:
    """
    Read a puzzle text file and return a WaterSortState.
    Raises ValueError on bad format.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Puzzle file not found: {filepath}")

    tubes = []
    capacity = None

    with open(filepath, "r") as f:
        for raw_line in f:
            line = raw_line.strip()

            # Skip comments and blank lines between sections
            if not line or line.startswith("#"):
                continue

            # Capacity declaration
            if line.lower().startswith("capacity="):
                try:
                    capacity = int(line.split("=")[1].strip())
                except ValueError:
                    raise ValueError(f"Invalid capacity line: '{line}'")
                continue

            # Tube definition
            if line.lower() == "empty":
                tubes.append([])
            else:
                colors = line.split()
                tubes.append(colors)

    if capacity is None:
        raise ValueError("Missing 'capacity=<int>' in puzzle file.")
    if not tubes:
        raise ValueError("No tubes found in puzzle file.")

    # Validate tube lengths
    for i, tube in enumerate(tubes):
        if len(tube) > capacity:
            raise ValueError(
                f"Tube {i} has {len(tube)} layers but capacity is {capacity}."
            )

    return WaterSortState(tubes, capacity)


# ──────────────────────────────────────────────
# Save puzzle (for creating new levels)
# ──────────────────────────────────────────────

def save_puzzle(state: WaterSortState, filepath: str, comment: str = "") -> None:
    """
    Write a WaterSortState to a text file in the standard format.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None

    with open(filepath, "w") as f:
        if comment:
            f.write(f"# {comment}\n")
        f.write(f"capacity={state.capacity}\n")
        for tube in state.tubes:
            if tube:
                f.write(" ".join(tube) + "\n")
            else:
                f.write("empty\n")

    print(f"Puzzle saved to: {filepath}")


# ──────────────────────────────────────────────
# Save results (solution + stats)
# ──────────────────────────────────────────────

def save_results(
    filepath: str,
    puzzle_file: str,
    algorithm: str,
    solution_moves: list[tuple[int, int]],
    stats: dict,
    initial_state: WaterSortState,
) -> None:
    """
    Save algorithm results to a text file.

    stats dict should contain keys like:
        time_seconds, states_explored, max_memory, solution_length
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None

    with open(filepath, "w") as f:
        f.write("=" * 50 + "\n")
        f.write("WATER SORT - RESULTS\n")
        f.write("=" * 50 + "\n\n")

        f.write(f"Puzzle file  : {puzzle_file}\n")
        f.write(f"Algorithm    : {algorithm}\n\n")

        # Initial state
        f.write("Initial State:\n")
        for i, tube in enumerate(initial_state.tubes):
            content = " ".join(tube) if tube else "(empty)"
            f.write(f"  Tube {i}: {content}\n")
        f.write("\n")

        # Stats
        f.write("Performance:\n")
        for key, value in stats.items():
            f.write(f"  {key:<22}: {value}\n")
        f.write("\n")

        # Solution
        if solution_moves:
            f.write(f"Solution ({len(solution_moves)} moves):\n")
            for step, (src, dst) in enumerate(solution_moves, 1):
                f.write(f"  Step {step:>3}: Pour tube {src} → tube {dst}\n")
        else:
            f.write("No solution found.\n")

    print(f"Results saved to: {filepath}")


# ──────────────────────────────────────────────
# List available puzzles
# ──────────────────────────────────────────────

def list_puzzles(folder: str = "puzzles") -> list[str]:
    """Return all .txt puzzle files in a folder."""
    if not os.path.isdir(folder):
        return []
    return sorted(
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.endswith(".txt")
    )
