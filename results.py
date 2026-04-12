import os
import re
from pathlib import Path

import pandas as pd


RESULTS_DIR = "results"
OUTPUT_CSV = "results/parsed_results.csv"


def parse_result_file(filepath: str) -> dict | None:
    text = Path(filepath).read_text(encoding="utf-8")

    def extract(pattern: str, cast=str, default=None, flags=0):
        m = re.search(pattern, text, flags)
        if not m:
            return default
        value = m.group(1).strip()
        try:
            return cast(value)
        except Exception:
            return default

    puzzle_file = extract(r"Puzzle file\s*:\s*(.+)")
    algorithm = extract(r"Algorithm\s*:\s*(.+)")
    time_seconds = extract(r"time_seconds\s*:\s*([0-9eE\.\-]+)", float)
    states_explored = extract(r"states_explored\s*:\s*(\d+)", int)
    max_memory_kb = extract(r"max_memory_kb\s*:\s*([0-9eE\.\-]+)", float)
    solution_length = extract(r"solution_length\s*:\s*(\d+)", int)
    solved_raw = extract(r"solved\s*:\s*(True|False)")
    solved = solved_raw == "True" if solved_raw is not None else None

    if puzzle_file is None or algorithm is None:
        return None

    puzzle_name = os.path.basename(puzzle_file)
    puzzle_path_lower = puzzle_file.lower()

    if "/easy/" in puzzle_path_lower or "\\easy\\" in puzzle_path_lower:
        difficulty = "Easy"
    elif "/medium/" in puzzle_path_lower or "\\medium\\" in puzzle_path_lower:
        difficulty = "Medium"
    elif "/hard/" in puzzle_path_lower or "\\hard\\" in puzzle_path_lower:
        difficulty = "Hard"
    else:
        difficulty = "Unknown"

    return {
        "source_file": filepath,
        "puzzle_file": puzzle_file,
        "puzzle_name": puzzle_name,
        "difficulty": difficulty,
        "algorithm": algorithm,
        "solved": solved,
        "solution_length": solution_length,
        "states_explored": states_explored,
        "max_memory_kb": max_memory_kb,
        "time_seconds": time_seconds,
    }


def load_all_results(results_dir: str) -> pd.DataFrame:
    rows = []

    for root, _, files in os.walk(results_dir):
        for name in files:
            if not name.endswith(".txt"):
                continue
            filepath = os.path.join(root, name)
            parsed = parse_result_file(filepath)
            if parsed is not None:
                rows.append(parsed)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    return df


def make_summary_table(df: pd.DataFrame, difficulty: str) -> pd.DataFrame:
    sub = df[df["difficulty"] == difficulty].copy()
    if sub.empty:
        return pd.DataFrame()

    summary = (
        sub.groupby("algorithm", dropna=False)
        .agg(
            puzzles_run=("puzzle_name", "count"),
            solved_pct=("solved", lambda s: 100 * s.mean() if len(s) else 0),
            avg_moves=("solution_length", "mean"),
            avg_states=("states_explored", "mean"),
            avg_memory_kb=("max_memory_kb", "mean"),
            avg_time_s=("time_seconds", "mean"),
        )
        .reset_index()
    )

    for col in ["solved_pct", "avg_moves", "avg_states", "avg_memory_kb", "avg_time_s"]:
        summary[col] = summary[col].round(2)

    return summary.sort_values("algorithm").reset_index(drop=True)


def main():
    df = load_all_results(RESULTS_DIR)

    if df.empty:
        print("No result files found.")
        return

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Parsed raw results saved to: {OUTPUT_CSV}\n")

    for difficulty in ["Easy", "Medium", "Hard"]:
        summary = make_summary_table(df, difficulty)
        if summary.empty:
            print(f"No data for {difficulty}.\n")
            continue

        print(f"\n=== {difficulty.upper()} SUMMARY ===")
        print(summary.to_string(index=False))

        out_path = f"results/{difficulty.lower()}_summary.csv"
        summary.to_csv(out_path, index=False)
        print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()