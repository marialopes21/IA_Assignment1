"""
search_heuristic.py - Heuristic Search Algorithms for Water Sort Puzzle
"""

import time
import tracemalloc
import heapq
from state import WaterSortState
from search import SearchResult  
from heuristics import h3_combined

# Internal helpers 
def _start_tracking():
    tracemalloc.start()
    return time.perf_counter()

def _stop_tracking(start_time):
    elapsed = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / 1024

# Greedy Best-First Search
def greedy(initial_state: WaterSortState, heuristic=h3_combined) -> SearchResult:
    start_time = _start_tracking()
    states_explored = 0
    counter = 0

    heap = [(heuristic(initial_state), counter, initial_state, [])]
    visited = set()

    while heap:
        h, _, state, path = heapq.heappop(heap)

        if state in visited:
            continue
        visited.add(state)
        states_explored += 1

        if state.is_goal():
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(path, states_explored, mem, elapsed, "Greedy")

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            if next_state not in visited:
                counter += 1
                heapq.heappush(heap, (
                    heuristic(next_state),
                    counter,
                    next_state,
                    path + [(src, dst)]
                ))

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, states_explored, mem, elapsed, "Greedy")

# A* Search
def astar(initial_state: WaterSortState, heuristic=h3_combined) -> SearchResult:
    start_time = _start_tracking()
    states_explored = 0
    counter = 0

    h0 = heuristic(initial_state)
    heap = [(h0, counter, initial_state, 0, [])]
    best_g = {initial_state: 0}

    while heap:
        f, _, state, g, path = heapq.heappop(heap)

        if best_g.get(state, float('inf')) < g:
            continue

        states_explored += 1

        if state.is_goal():
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(path, states_explored, mem, elapsed, "A*")

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            new_g = g + state.move_cost(src, dst)

            if new_g < best_g.get(next_state, float('inf')):
                best_g[next_state] = new_g
                f_new = new_g + heuristic(next_state)
                counter += 1
                heapq.heappush(heap, (f_new, counter, next_state, new_g, path + [(src, dst)]))

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, states_explored, mem, elapsed, "A*")

# Weighted A*
def weighted_astar(
    initial_state: WaterSortState,
    heuristic=h3_combined,
    weight: float = 1.5
) -> SearchResult:
    algorithm_name = f"Weighted A* (W={weight})"
    start_time = _start_tracking()
    states_explored = 0
    counter = 0

    h0 = heuristic(initial_state)
    heap = [(h0 * weight, counter, initial_state, 0, [])]
    best_g = {initial_state: 0}

    while heap:
        f, _, state, g, path = heapq.heappop(heap)

        if best_g.get(state, float('inf')) < g:
            continue

        states_explored += 1

        if state.is_goal():
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(path, states_explored, mem, elapsed, algorithm_name)

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            new_g = g + state.move_cost(src, dst)

            if new_g < best_g.get(next_state, float('inf')):
                best_g[next_state] = new_g
                f_new = new_g + weight * heuristic(next_state)
                counter += 1
                heapq.heappush(heap, (f_new, counter, next_state, new_g, path + [(src, dst)]))

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, states_explored, mem, elapsed, algorithm_name)

def compare_heuristic_algorithms(
    initial_state: WaterSortState,
    heuristic=h3_combined,
    weights: list[float] = [1.2, 1.5, 2.0]
) -> list[SearchResult]:
    print("Running all heuristic search algorithms...\n")
    results = []

    for fn in [greedy, astar]:
        result = fn(initial_state, heuristic)
        print(result)
        results.append(result)

    for w in weights:
        result = weighted_astar(initial_state, heuristic, weight=w)
        print(result)
        results.append(result)

    return results
