"""
search.py - Search Algorithms for Water Sort Puzzle

Algorithms implemented:
  - BFS   : Breadth-First Search       (optimal: fewest moves)
  - DFS   : Depth-First Search         (fast, not optimal)
  - IDDFS : Iterative Deepening DFS    (optimal + memory efficient)
  - UCS   : Uniform Cost Search        (optimal with weighted costs)

All algorithms return a SearchResult object containing:
  - solution  : list of (src, dst) moves, or None if unsolvable
  - stats     : dict with time, memory, states explored
"""

import time
import tracemalloc
from collections import deque
import heapq
from state import WaterSortState


# SearchResult

class SearchResult:
    def __init__(self, solution, states_explored, max_memory_kb, time_seconds, algorithm):
        self.solution       = solution          # list of (src,dst) or None
        self.states_explored = states_explored  # int
        self.max_memory_kb  = max_memory_kb     # float
        self.time_seconds   = time_seconds      # float
        self.algorithm      = algorithm         # str

    @property
    def solved(self):
        return self.solution is not None

    @property
    def solution_length(self):
        return len(self.solution) if self.solution else 0

    def __repr__(self):
        if self.solved:
            status = f"Solved in {self.solution_length} moves"
        else:
            status = " No solution found"
        return (
            f"[{self.algorithm}] {status} | "
            f"States: {self.states_explored} | "
            f"Memory: {self.max_memory_kb:.1f} KB | "
            f"Time: {self.time_seconds:.4f}s"
        )

    def to_dict(self):
        return {
            "algorithm"      : self.algorithm,
            "solved"         : self.solved,
            "solution_length": self.solution_length,
            "states_explored": self.states_explored,
            "max_memory_kb"  : round(self.max_memory_kb, 2),
            "time_seconds"   : round(self.time_seconds, 4),
        }


# Internal helpers

def _reconstruct_path(parent: dict, state: WaterSortState) -> list[tuple[int, int]]:
    path = []
    while parent[state][0] is not None:
        prev_state, move = parent[state]
        path.append(move)
        state = prev_state
    path.reverse()
    return path


def _start_tracking():
    tracemalloc.start()
    return time.perf_counter()


def _stop_tracking(start_time):
    elapsed = time.perf_counter() - start_time
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return elapsed, peak / 1024  


# BFS 

def bfs(initial_state: WaterSortState) -> SearchResult:
    start_time = _start_tracking()
    states_explored = 0

    parent = {initial_state: (None, None)}
    queue = deque([initial_state])

    while queue:
        state = queue.popleft()
        states_explored += 1

        if state.is_goal():
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(
                solution=_reconstruct_path(parent, state),
                states_explored=states_explored,
                max_memory_kb=mem,
                time_seconds=elapsed,
                algorithm="BFS"
            )

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            if next_state not in parent:
                parent[next_state] = (state, (src, dst))
                queue.append(next_state)

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, states_explored, mem, elapsed, "BFS")


# DFS

def dfs(initial_state: WaterSortState, max_depth: int = 200) -> SearchResult:
    start_time = _start_tracking()
    states_explored = 0

    stack = [(initial_state, [], 0)]
    visited = set()

    while stack:
        state, path, depth = stack.pop()

        if state in visited:
            continue
        visited.add(state)
        states_explored += 1

        if state.is_goal():
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(path, states_explored, mem, elapsed, "DFS")

        if depth >= max_depth:
            continue

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            if next_state not in visited:
                stack.append((next_state, path + [(src, dst)], depth + 1))

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, states_explored, mem, elapsed, "DFS")


# IDDFS

def iddfs(initial_state: WaterSortState, max_depth: int = 200) -> SearchResult:
    start_time = _start_tracking()
    total_states = 0

    def depth_limited_search(state, path, depth_limit, visited):
        nonlocal total_states
        total_states += 1

        if state.is_goal():
            return path

        if len(path) >= depth_limit:
            return None 

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            if next_state not in visited:
                visited.add(next_state)
                result = depth_limited_search(
                    next_state, path + [(src, dst)], depth_limit, visited
                )
                if result is not None:
                    return result
                visited.discard(next_state)

        return None

    for limit in range(1, max_depth + 1):
        visited = {initial_state}
        result = depth_limited_search(initial_state, [], limit, visited)
        if result is not None:
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(result, total_states, mem, elapsed, "IDDFS")

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, total_states, mem, elapsed, "IDDFS")


# UCS

def ucs(initial_state: WaterSortState) -> SearchResult:
    start_time = _start_tracking()
    states_explored = 0

    counter = 0  
    heap = [(0, counter, initial_state, [])]
    visited = {} 

    while heap:
        cost, _, state, path = heapq.heappop(heap)
        states_explored += 1

        if state in visited and visited[state] <= cost:
            continue
        visited[state] = cost

        if state.is_goal():
            elapsed, mem = _stop_tracking(start_time)
            return SearchResult(path, states_explored, mem, elapsed, "UCS")

        for (src, dst) in state.get_valid_moves():
            next_state = state.apply_move(src, dst)
            move_cost = state.move_cost(src, dst)
            new_cost = cost + move_cost

            if next_state not in visited or visited[next_state] > new_cost:
                counter += 1
                heapq.heappush(heap, (new_cost, counter, next_state, path + [(src, dst)]))

    elapsed, mem = _stop_tracking(start_time)
    return SearchResult(None, states_explored, mem, elapsed, "UCS")



def compare_algorithms(initial_state: WaterSortState) -> list[SearchResult]:
    print("Running all uninformed search algorithms...\n")
    results = []
    for fn in [bfs, dfs, iddfs, ucs]:
        result = fn(initial_state)
        print(result)
        results.append(result)
    return results