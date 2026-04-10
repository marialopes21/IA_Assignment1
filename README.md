# IA_Assignment1

## main.py
Run the game.
´´´bash 
python main.py
´´´

## ui.py
File for the water sort game user interface.

## puzzle_io.py
Load and save Water Sort puzzles from/to text files.
Each subsequent line of code defines one tube (bottom -> top),
with colors separated by spaces. An empty line or the word "empty"
means an empty tube.

## state.py
A WaterSortState holds a list of tubes.
Each tube is a list of color strings, where:
  - Index 0 = BOTTOM of the tube
  - Index -1 = TOP of the tube (poured from/to here)

## test_state.py
File responsible for state testing.
´´´bash 
python test_state.py
´´´

## search.py
Algorithms implemented:
  - BFS   : Breadth-First Search       (optimal: fewest moves)
  - DFS   : Depth-First Search         (fast, not optimal)
  - IDDFS : Iterative Deepening DFS    (optimal + memory efficient)
  - UCS   : Uniform Cost Search        (optimal with weighted costs)

All algorithms return a SearchResult object containing:
  - solution  : list of (src, dst) moves, or None if unsolvable
  - stats     : dict with time, memory, states explored

## test_search.py
File responsible for search testing.
´´´bash 
python test_search.py
´´´

## heuristics.py
Heuristic Functions for Water Sort Puzzle.
Heuristics 1 - Number of tubes not yet complete
Heuristics 2 - Color misplacement: counts total units in incomplete tubes. Penalises states where colours are spread across many units in wrong tubes. 
Heuristics 3 - within-tube discontinuities: adjacent cells of different colour each require at least one pour to separate and cross-tube fragmentation: for each colour split across k tubes, at least k−1 pours are needed to consolidate it. 

## search_heuristic.py
Heuristic Search Algorithms for Water Sort Puzzle.
Algorithms implemented:
  - Greedy Best-First Search  (fast, not optimal)
  - A*                        (optimal + complete)
  - Weighted A*               (faster than A*, trades optimality for speed)

## test_heuristics.py
File responsible for heuristics testing
´´´bash 
python test_heuristics.py
´´´

## metrics.py
Performance Metrics & Algorithm Comparison for Water Sort.

## test_metrics.py
File responsible for metrics testing
´´´bash 
python test_metrics.py
´´´