from __future__ import annotations

import math
import os
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, Future
import pygame

from state import WaterSortState
from search import bfs, dfs, iddfs, ucs
from search_heuristic import greedy, astar, weighted_astar
from heuristics import h3_combined
from puzzle_io import save_results


SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60

BACKGROUND = (28, 30, 38)
PANEL = (40, 44, 54)
WHITE = (250, 250, 250)
SUBTLE = (170, 175, 185)
SUCCESS = (120, 230, 150)
WARNING = (255, 215, 120)
ERROR_COLOR = (255, 130, 130)

BUTTON = (70, 100, 170)
BUTTON_HOVER = (90, 125, 205)
BUTTON_DISABLED = (90, 95, 105)

POUR_DURATION = 1.05
WASTAR_WEIGHT = 1.5
SOLVER_TIMEOUT_SECONDS = 8.0

COLOR_MAP = {
    "red": (220, 70, 70),
    "blue": (75, 135, 245),
    "green": (80, 200, 120),
    "yellow": (240, 215, 70),
    "purple": (170, 100, 220),
    "orange": (250, 150, 70),
    "pink": (245, 120, 180),
    "cyan": (80, 210, 220),
    "brown": (145, 95, 60),
    "gray": (145, 145, 145),
    "grey": (145, 145, 145),
    "lime": (150, 225, 70),
    "magenta": (220, 80, 220),
    "teal": (50, 170, 160),
    "navy": (70, 90, 180),
    "gold": (225, 180, 40),
    "maroon": (145, 45, 60),
}


def clamp(x: float) -> int:
    return max(0, min(255, int(x)))


def lighten(color: tuple[int, int, int], amount: int = 30) -> tuple[int, int, int]:
    r, g, b = color
    return (clamp(r + amount), clamp(g + amount), clamp(b + amount))


def darken(color: tuple[int, int, int], amount: int = 30) -> tuple[int, int, int]:
    r, g, b = color
    return (clamp(r - amount), clamp(g - amount), clamp(b - amount))


def get_color(name: str) -> tuple[int, int, int]:
    if name in COLOR_MAP:
        return COLOR_MAP[name]
    h = abs(hash(name))
    r = 60 + (h % 160)
    g = 60 + ((h // 13) % 160)
    b = 60 + ((h // 29) % 160)
    return (r, g, b)


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def get_color_runs(tube: tuple[str, ...] | list[str]) -> list[tuple[str, int, int]]:
    if not tube:
        return []

    runs: list[tuple[str, int, int]] = []
    start = 0
    current = tube[0]

    for i in range(1, len(tube)):
        if tube[i] != current:
            runs.append((current, start, i - start))
            current = tube[i]
            start = i

    runs.append((current, start, len(tube) - start))
    return runs


def _run_solver_job(job_kind: str, state: WaterSortState):
    """
    Runs in a separate process.
    Must stay top-level to be pickleable.
    """
    if job_kind == "solve_bfs":
        result = bfs(state)
        return {"kind": job_kind, "label": "BFS", "result": result}

    if job_kind == "solve_dfs":
        result = dfs(state)
        return {"kind": job_kind, "label": "DFS", "result": result}

    if job_kind == "solve_iddfs":
        result = iddfs(state)
        return {"kind": job_kind, "label": "IDDFS", "result": result}

    if job_kind == "solve_ucs":
        result = ucs(state)
        return {"kind": job_kind, "label": "UCS", "result": result}

    if job_kind == "solve_greedy":
        result = greedy(state, h3_combined)
        return {"kind": job_kind, "label": "Greedy", "result": result}

    if job_kind == "solve_astar":
        result = astar(state, h3_combined)
        return {"kind": job_kind, "label": "A*", "result": result}

    if job_kind == "solve_wastar":
        result = weighted_astar(state, h3_combined, WASTAR_WEIGHT)
        return {"kind": job_kind, "label": f"WA* (W={WASTAR_WEIGHT})", "result": result}

    if job_kind == "hint":
        candidates = [
            ("Greedy", greedy(state, h3_combined)),
            ("A*", astar(state, h3_combined)),
            (f"WA* (W={WASTAR_WEIGHT})", weighted_astar(state, h3_combined, WASTAR_WEIGHT)),
        ]
        solved = [(name, res) for name, res in candidates if res.solution is not None]
        if not solved:
            return {"kind": job_kind, "label": "Hint", "result": None, "hint": None}

        best_name, best_result = min(
            solved,
            key=lambda item: (item[1].time_seconds, item[1].states_explored, item[1].solution_length)
        )
        hint_move = best_result.solution[0] if best_result.solution else None
        return {
            "kind": job_kind,
            "label": "Hint",
            "result": best_result,
            "hint": hint_move,
            "hint_algorithm": best_name,
        }

    raise ValueError(f"Unknown solver job: {job_kind}")


class Button:
    def __init__(self, rect: pygame.Rect, text: str, action: str):
        self.rect = rect
        self.text = text
        self.action = action
        self.enabled = True

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]) -> None:
        if not self.enabled:
            color = BUTTON_DISABLED
        elif self.rect.collidepoint(mouse_pos):
            color = BUTTON_HOVER
        else:
            color = BUTTON

        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        pygame.draw.rect(screen, WHITE, self.rect, width=2, border_radius=12)

        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, pos: tuple[int, int]) -> bool:
        return self.enabled and self.rect.collidepoint(pos)


class WaterSortUI:
    def __init__(
        self,
        screen: pygame.Surface,
        initial_state: WaterSortState,
        puzzle_file: str = "unknown_puzzle.txt",
        results_folder: str = "results",
    ):
        self.screen = screen
        self.initial_state = initial_state
        self.state = initial_state
        self.puzzle_file = puzzle_file
        self.results_folder = results_folder

        self.history: list[WaterSortState] = [initial_state]
        self.selected_tube: int | None = None
        self.solution_queue: list[tuple[int, int]] = []
        self.status_text = "Click a tube, then click another tube to pour."
        self.status_style = "normal"
        self.animation: dict | None = None
        self.pending_action: str | None = None

        self.tube_rects: list[pygame.Rect] = []
        self.buttons: list[Button] = []

        self.executor = self._create_executor()
        self.solver_future: Future | None = None
        self.solver_started_at: float | None = None
        self.solver_job_kind: str | None = None

        self.refresh_layout()

    # ----------------------------
    # Process management
    # ----------------------------

    def _create_executor(self) -> ProcessPoolExecutor:
        return ProcessPoolExecutor(max_workers=1)

    def _reset_executor(self) -> None:
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
        self.executor = self._create_executor()

    def close(self) -> None:
        self.cancel_solver()
        try:
            self.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    # ----------------------------
    # Report saving
    # ----------------------------

    def save_solver_report(self, algorithm_name: str, result) -> None:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            puzzle_name = os.path.splitext(os.path.basename(self.puzzle_file))[0]

            safe_algorithm = (
                algorithm_name.replace(" ", "_")
                .replace("*", "star")
                .replace("(", "")
                .replace(")", "")
                .replace("=", "_")
                .replace(".", "_")
            )

            output_path = os.path.join(
                self.results_folder,
                f"{puzzle_name}_{safe_algorithm}_{timestamp}.txt"
            )

            stats = {
                "time_seconds": result.time_seconds,
                "states_explored": result.states_explored,
                "max_memory_kb": result.max_memory_kb,
                "solution_length": len(result.solution) if result.solution is not None else 0,
                "solved": result.solution is not None,
            }

            save_results(
                filepath=output_path,
                puzzle_file=self.puzzle_file,
                algorithm=algorithm_name,
                solution_moves=result.solution,
                stats=stats,
                initial_state=self.initial_state,
            )
        except Exception as e:
            self.set_status(f"Report save failed: {e}", "warning")

    # ----------------------------
    # Responsive layout / sizing
    # ----------------------------

    def get_screen_size(self) -> tuple[int, int]:
        return self.screen.get_width(), self.screen.get_height()

    def refresh_layout(self) -> None:
        sw, sh = self.get_screen_size()

        self.top_margin = max(90, int(sh * 0.11))
        self.bottom_panel_h = max(180, int(sh * 0.24))

        self.font_title = pygame.font.SysFont("arial", max(28, int(sh * 0.038)), bold=True)
        self.font_main = pygame.font.SysFont("arial", max(19, int(sh * 0.024)))
        self.font_small = pygame.font.SysFont("arial", max(15, int(sh * 0.018)))

        self.tube_rects = self.compute_tube_rects()
        self.buttons = self.create_buttons()

    def compute_tube_rects(self) -> list[pygame.Rect]:
        sw, sh = self.get_screen_size()
        n = self.state.num_tubes

        cols = n if n <= 6 else math.ceil(n / 2)
        rows = math.ceil(n / cols)

        usable_w = sw - 80
        usable_h = sh - self.top_margin - self.bottom_panel_h - 40

        spacing_x = max(18, int(sw * 0.018))
        spacing_y = max(26, int(sh * 0.035))

        tube_w = int((usable_w - (cols - 1) * spacing_x) / cols)
        tube_h = int((usable_h - (rows - 1) * spacing_y) / rows)

        self.tube_width = max(62, min(110, tube_w))
        self.tube_height = max(180, min(330, tube_h))

        total_w = cols * self.tube_width + (cols - 1) * spacing_x
        total_h = rows * self.tube_height + (rows - 1) * spacing_y

        start_x = max(20, (sw - total_w) // 2)
        start_y = self.top_margin + max(10, (usable_h - total_h) // 2)

        self.tube_spacing_x = spacing_x
        self.tube_spacing_y = spacing_y

        rects = []
        for i in range(n):
            row = i // cols
            col = i % cols
            x = start_x + col * (self.tube_width + spacing_x)
            y = start_y + row * (self.tube_height + spacing_y)
            rects.append(pygame.Rect(x, y, self.tube_width, self.tube_height))
        return rects

    def create_buttons(self) -> list[Button]:
        sw, sh = self.get_screen_size()

        y1 = sh - self.bottom_panel_h + max(10, int(self.bottom_panel_h * 0.10))
        y2 = y1 + max(44, int(self.bottom_panel_h * 0.24)) + 8
        y3 = y2 + max(44, int(self.bottom_panel_h * 0.24)) + 8

        w = max(95, min(135, int(sw * 0.075)))
        h = max(36, min(46, int(self.bottom_panel_h * 0.22)))
        gap = max(8, int(sw * 0.006))

        row1 = [
            ("Undo", "undo"),
            ("Reset", "reset"),
            ("BFS", "solve_bfs"),
            ("DFS", "solve_dfs"),
            ("IDDFS", "solve_iddfs"),
            ("UCS", "solve_ucs"),
        ]
        row2 = [
            ("Greedy", "solve_greedy"),
            ("A*", "solve_astar"),
            ("WA*", "solve_wastar"),
            ("Hint", "hint"),
            ("Stop Auto", "stop_auto"),
        ]
        row3 = [
            ("New Puzzle", "new_puzzle"),
            ("Main Menu", "main_menu"),
        ]

        def build_row(row, y):
            total_w = len(row) * w + (len(row) - 1) * gap
            start_x = (sw - total_w) // 2
            return [
                Button(pygame.Rect(start_x + i * (w + gap), y, w, h), text, action)
                for i, (text, action) in enumerate(row)
            ]

        buttons = []
        buttons.extend(build_row(row1, y1))
        buttons.extend(build_row(row2, y2))
        buttons.extend(build_row(row3, y3))
        return buttons

    # ----------------------------
    # Status helpers
    # ----------------------------

    def set_status(self, text: str, style: str = "normal") -> None:
        self.status_text = text
        self.status_style = style

    # ----------------------------
    # Solver management
    # ----------------------------

    def is_solver_running(self) -> bool:
        return self.solver_future is not None

    def cancel_solver(self) -> None:
        if self.solver_future is not None:
            try:
                self.solver_future.cancel()
            except Exception:
                pass

        self.solver_future = None
        self.solver_started_at = None
        self.solver_job_kind = None

        # Reset worker process so runaway jobs do not keep consuming CPU.
        self._reset_executor()

    def start_solver_job(self, job_kind: str) -> None:
        if self.animation is not None:
            return
        if self.is_solver_running():
            self.set_status("A solver is already running.", "warning")
            return

        self.selected_tube = None
        self.solution_queue.clear()

        label_map = {
            "solve_bfs": "BFS",
            "solve_dfs": "DFS",
            "solve_iddfs": "IDDFS",
            "solve_ucs": "UCS",
            "solve_greedy": "Greedy",
            "solve_astar": "A*",
            "solve_wastar": f"WA* (W={WASTAR_WEIGHT})",
            "hint": "Hint",
        }
        self.set_status(f"Running {label_map.get(job_kind, 'solver')}...", "warning")

        self.solver_job_kind = job_kind
        self.solver_started_at = time.perf_counter()
        self.solver_future = self.executor.submit(_run_solver_job, job_kind, self.state)

    def poll_solver(self) -> None:
        if self.solver_future is None:
            return

        assert self.solver_started_at is not None
        elapsed = time.perf_counter() - self.solver_started_at

        if elapsed > SOLVER_TIMEOUT_SECONDS and not self.solver_future.done():
            timed_out_kind = self.solver_job_kind or "solver"
            self.cancel_solver()
            self.set_status(
                f"{timed_out_kind} timed out after {SOLVER_TIMEOUT_SECONDS:.0f}s. Puzzle may be unsolvable or too complex.",
                "error",
            )
            return

        if not self.solver_future.done():
            return

        future = self.solver_future
        self.solver_future = None
        self.solver_started_at = None
        job_kind = self.solver_job_kind
        self.solver_job_kind = None

        try:
            payload = future.result()
        except Exception as e:
            self.set_status(f"Solver failed: {e}", "error")
            return

        if job_kind == "hint":
            hint_move = payload.get("hint")
            if hint_move is None:
                self.set_status("No hint available. Puzzle may be unsolvable from this state.", "error")
                return

            algo_name = payload.get("hint_algorithm", "solver")
            src, dst = hint_move
            self.set_status(f"Hint ({algo_name}): pour tube {src} → tube {dst}", "hint")
            return

        label = payload.get("label", "Solver")
        result = payload.get("result")

        if result is None or result.solution is None:
            if result is not None:
                self.save_solver_report(label, result)
            self.set_status(f"{label} found no solution. Puzzle may be unsolvable.", "error")
            return

        if len(result.solution) == 0:
            self.save_solver_report(label, result)
            self.set_status("Puzzle already solved.", "success")
            return

        self.save_solver_report(label, result)
        self.solution_queue = list(result.solution)
        self.set_status(f"{label} found solution in {len(result.solution)} moves. Auto-playing...", "warning")

    # ----------------------------
    # State helpers
    # ----------------------------

    def reset(self) -> None:
        self.cancel_solver()
        self.state = self.initial_state
        self.history = [self.initial_state]
        self.selected_tube = None
        self.solution_queue.clear()
        self.animation = None
        self.set_status("Puzzle reset.")

    def request_main_menu(self) -> None:
        if self.animation is None:
            self.cancel_solver()
            self.pending_action = "main_menu"

    def request_new_puzzle(self) -> None:
        if self.animation is None:
            self.cancel_solver()
            self.pending_action = "new_puzzle"

    def undo(self) -> None:
        if self.animation is not None or self.is_solver_running():
            return
        if len(self.history) > 1:
            self.history.pop()
            self.state = self.history[-1]
            self.selected_tube = None
            self.solution_queue.clear()
            self.set_status("Undid last move.")
        else:
            self.set_status("Nothing to undo.", "warning")

    def can_interact(self) -> bool:
        return self.animation is None and not self.is_solver_running()

    def get_layer_height(self, tube_rect: pygame.Rect) -> float:
        return tube_rect.height / self.state.capacity

    def get_visual_tube_contents(self, idx: int) -> tuple[str, ...]:
        return tuple(self.state.tubes[idx])

    # ----------------------------
    # Tube drawing
    # ----------------------------

    def draw_glass_tube_on(self, surface: pygame.Surface, rect: pygame.Rect, selected: bool = False) -> None:
        shadow = rect.move(3, 5)
        pygame.draw.rect(surface, (15, 16, 22), shadow, border_radius=18)

        inner = rect.inflate(-8, -8)
        pygame.draw.rect(surface, (45, 50, 65), inner, border_radius=12)

        border_color = WHITE if selected else (210, 215, 225)
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=16)
        pygame.draw.rect(surface, (70, 75, 90), inner, width=1, border_radius=12)

        if selected:
            glow = rect.inflate(12, 12)
            pygame.draw.rect(surface, WHITE, glow, width=2, border_radius=20)

    def draw_glass_tube(self, rect: pygame.Rect, selected: bool = False) -> None:
        self.draw_glass_tube_on(self.screen, rect, selected)

    def draw_liquid_run_on(
        self,
        surface: pygame.Surface,
        tube_rect: pygame.Rect,
        color_name: str,
        start_layer: int,
        count: int,
        is_top_run: bool,
        extra_top_fill: float = 0.0,
        trim_top_px: float = 0.0,
    ) -> None:
        color = get_color(color_name)
        layer_h = tube_rect.height / self.state.capacity

        x = tube_rect.left + 8
        y = tube_rect.bottom - (start_layer + count) * layer_h + 3 - extra_top_fill + trim_top_px
        w = tube_rect.width - 16
        h = count * layer_h - 6 + extra_top_fill - trim_top_px

        if h < 1:
            return

        liquid_rect = pygame.Rect(int(x), int(y), int(w), int(h))

        pygame.draw.rect(surface, color, liquid_rect, border_radius=12)

        highlight = pygame.Rect(
            liquid_rect.left + 4,
            liquid_rect.top + 4,
            max(10, liquid_rect.width // 4),
            max(8, min(14, liquid_rect.height // 3)),
        )
        pygame.draw.rect(surface, lighten(color, 35), highlight, border_radius=10)

        shade = pygame.Rect(
            liquid_rect.left + 1,
            liquid_rect.bottom - max(8, liquid_rect.height // 5),
            liquid_rect.width - 2,
            max(7, liquid_rect.height // 5),
        )
        pygame.draw.rect(surface, darken(color, 22), shade, border_radius=10)

        sheen = pygame.Rect(
            liquid_rect.left + liquid_rect.width // 2 - 3,
            liquid_rect.top + 6,
            6,
            max(8, liquid_rect.height - 12),
        )
        pygame.draw.rect(surface, lighten(color, 18), sheen, border_radius=6)

        pygame.draw.rect(surface, WHITE, liquid_rect, width=1, border_radius=12)

        if is_top_run:
            cap_rect = pygame.Rect(
                liquid_rect.left + 2,
                liquid_rect.top - 4,
                liquid_rect.width - 4,
                12,
            )
            pygame.draw.ellipse(surface, lighten(color, 42), cap_rect)
            pygame.draw.ellipse(surface, WHITE, cap_rect, width=1)

    def draw_tube_liquid_on(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        tube_contents: tuple[str, ...] | list[str],
        preview_add: tuple[str, int, float] | None = None,
        top_trim_px: float = 0.0,
    ) -> None:
        runs = get_color_runs(tube_contents)
        for i, (color_name, start_layer, count) in enumerate(runs):
            is_top_run = (i == len(runs) - 1)
            trim = top_trim_px if is_top_run else 0.0
            self.draw_liquid_run_on(surface, rect, color_name, start_layer, count, is_top_run, trim_top_px=trim)

        if preview_add is not None:
            color_name, start_layer, amount_float = preview_add
            amount_float = max(0.0, amount_float)

            full_layers = int(amount_float)
            frac = amount_float - full_layers
            frac = max(0.0, min(1.0, frac))

            if full_layers > 0:
                self.draw_liquid_run_on(surface, rect, color_name, start_layer, full_layers, frac == 0.0)

            if frac > 0.0:
                layer_h = rect.height / self.state.capacity
                self.draw_liquid_run_on(
                    surface,
                    rect,
                    color_name,
                    start_layer + full_layers,
                    0,
                    True,
                    extra_top_fill=frac * layer_h,
                )

    def draw_tube_liquid(
        self,
        rect: pygame.Rect,
        tube_contents: tuple[str, ...] | list[str],
        preview_add: tuple[str, int, float] | None = None,
        top_trim_px: float = 0.0,
    ) -> None:
        self.draw_tube_liquid_on(self.screen, rect, tube_contents, preview_add, top_trim_px)

    def draw_tubes(self) -> None:
        hidden_src = self.animation["src"] if self.animation is not None else None

        for idx, rect in enumerate(self.tube_rects):
            if idx == hidden_src:
                continue

            selected = (idx == self.selected_tube)
            self.draw_glass_tube(rect, selected)

            tube_contents = self.get_visual_tube_contents(idx)
            preview_add = None

            if self.animation is not None and idx == self.animation["dst"]:
                fill_progress = self.get_stream_progress()
                dst_len = len(self.state.tubes[idx])
                preview_amount = min(fill_progress * self.animation["amount"], self.animation["amount"])
                preview_add = (self.animation["color_name"], dst_len, preview_amount)

            self.draw_tube_liquid(rect, tube_contents, preview_add=preview_add)

            label = self.font_small.render(str(idx), True, SUBTLE)
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.bottom + 18)))

    # ----------------------------
    # Pour animation
    # ----------------------------

    def start_pour_animation(self, src: int, dst: int) -> None:
        color_name = self.state.tubes[src][-1]
        amount = min(self.state.tube_top_count(src), self.state.tube_free_space(dst))

        src_rect = self.tube_rects[src]
        dst_rect = self.tube_rects[dst]

        pouring_right = dst_rect.centerx > src_rect.centerx
        direction = -1 if pouring_right else 1
        max_angle = 65 * direction

        start_center = (src_rect.centerx, src_rect.centery)
        target_center = (
            dst_rect.centerx + 40 * direction,
            min(src_rect.top, dst_rect.top) - 20 + src_rect.height // 2,
        )

        self.animation = {
            "src": src,
            "dst": dst,
            "color_name": color_name,
            "amount": amount,
            "t": 0.0,
            "duration": POUR_DURATION,
            "max_angle": max_angle,
            "start_center": start_center,
            "target_center": target_center,
        }

    def get_animation_phase(self) -> float:
        if self.animation is None:
            return 0.0
        duration = self.animation["duration"]
        if duration <= 0:
            return 1.0
        return max(0.0, min(1.0, self.animation["t"] / duration))

    def get_current_source_transform(self) -> tuple[tuple[float, float], float]:
        if self.animation is None:
            return (0.0, 0.0), 0.0

        t = self.get_animation_phase()
        start_cx, start_cy = self.animation["start_center"]
        target_cx, target_cy = self.animation["target_center"]
        max_angle = self.animation["max_angle"]

        if t < 0.30:
            local = ease_in_out(t / 0.30)
            cx = lerp(start_cx, target_cx, local)
            cy = lerp(start_cy, target_cy, local)
            angle = lerp(0, max_angle * 0.35, local)
        elif t < 0.50:
            local = ease_in_out((t - 0.30) / 0.20)
            cx = target_cx
            cy = target_cy
            angle = lerp(max_angle * 0.35, max_angle, local)
        elif t < 0.75:
            cx = target_cx
            cy = target_cy
            angle = max_angle
        else:
            local = ease_in_out((t - 0.75) / 0.25)
            cx = lerp(target_cx, start_cx, local)
            cy = lerp(target_cy, start_cy, local)
            angle = lerp(max_angle, 0, local)

        return (cx, cy), angle

    def get_stream_progress(self) -> float:
        if self.animation is None:
            return 0.0

        t = self.get_animation_phase()
        if t < 0.35:
            return 0.0
        if t < 0.45:
            return ease_in_out((t - 0.35) / 0.10)
        if t < 0.72:
            return 1.0
        if t < 0.85:
            return 1.0 - ease_in_out((t - 0.72) / 0.13)
        return 0.0

    def get_source_animation_view(self) -> tuple[tuple[str, ...], float]:
        assert self.animation is not None

        src = self.animation["src"]
        rect = self.tube_rects[src]
        layer_h = self.get_layer_height(rect)

        tube = list(self.state.tubes[src])
        amount = self.animation["amount"]

        drained = self.get_stream_progress() * amount
        drained = max(0.0, min(float(amount), drained))

        full_drained = int(drained)
        frac_drained = drained - full_drained

        if full_drained > 0:
            tube = tube[: len(tube) - full_drained]

        top_trim_px = 0.0
        if frac_drained > 0.0 and tube:
            top_trim_px = frac_drained * layer_h

        return tuple(tube), top_trim_px

    def build_tube_surface(
        self,
        idx: int,
        tube_contents: tuple[str, ...] | list[str],
        selected: bool = False,
        top_trim_px: float = 0.0,
    ) -> tuple[pygame.Surface, pygame.Rect]:
        rect = self.tube_rects[idx]
        surf_w = rect.width + 40
        surf_h = rect.height + 50

        surface = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
        local_rect = pygame.Rect(20, 20, rect.width, rect.height)

        self.draw_glass_tube_on(surface, local_rect, selected)
        self.draw_tube_liquid_on(surface, local_rect, tube_contents, top_trim_px=top_trim_px)

        return surface, local_rect

    def get_rotated_source_geometry(self) -> tuple[pygame.Surface, pygame.Rect, tuple[float, float], float]:
        assert self.animation is not None

        src = self.animation["src"]
        (cx, cy), angle = self.get_current_source_transform()
        tube_contents, top_trim_px = self.get_source_animation_view()

        surface, local_rect = self.build_tube_surface(src, tube_contents, selected=False, top_trim_px=top_trim_px)
        rotated = pygame.transform.rotate(surface, angle)
        rotated_rect = rotated.get_rect(center=(cx, cy))

        mouth_local = pygame.Vector2(local_rect.right - 8, local_rect.top + 16)
        mouth_centered = mouth_local - pygame.Vector2(surface.get_width() / 2, surface.get_height() / 2)
        rotated_offset = mouth_centered.rotate(-angle)
        mouth_world = pygame.Vector2(cx, cy) + rotated_offset

        return rotated, rotated_rect, (mouth_world.x, mouth_world.y), angle

    def get_destination_mouth(self) -> tuple[float, float]:
        assert self.animation is not None
        dst_rect = self.tube_rects[self.animation["dst"]]
        return (dst_rect.centerx, dst_rect.top + 28)

    def draw_pour_stream(self) -> None:
        if self.animation is None:
            return

        progress = self.get_stream_progress()
        if progress <= 0.0:
            return

        _, _, start_pos, _ = self.get_rotated_source_geometry()
        end_pos = self.get_destination_mouth()
        color = get_color(self.animation["color_name"])

        x1, y1 = start_pos
        x2, y2 = end_pos
        current_end = (lerp(x1, x2, progress), lerp(y1, y2, progress))

        pygame.draw.line(self.screen, darken(color, 25), start_pos, current_end, 14)
        pygame.draw.line(self.screen, color, start_pos, current_end, 10)
        pygame.draw.line(self.screen, lighten(color, 35), start_pos, current_end, 4)
        pygame.draw.circle(self.screen, lighten(color, 30), (int(current_end[0]), int(current_end[1])), 5)

    def draw_rotated_source_tube(self) -> None:
        if self.animation is None:
            return
        rotated, rotated_rect, _, _ = self.get_rotated_source_geometry()
        self.screen.blit(rotated, rotated_rect)

    def update(self, dt: float) -> None:
        current_size = (self.screen.get_width(), self.screen.get_height())
        if getattr(self, "_last_screen_size", None) != current_size:
            self._last_screen_size = current_size
            self.refresh_layout()

        self.poll_solver()

        if self.animation is None:
            if self.solution_queue:
                src, dst = self.solution_queue.pop(0)
                if self.state.is_valid_move(src, dst):
                    self.start_pour_animation(src, dst)
            return

        self.animation["t"] += dt
        if self.get_animation_phase() >= 1.0:
            src = self.animation["src"]
            dst = self.animation["dst"]
            self.state = self.state.apply_move(src, dst)
            self.history.append(self.state)
            self.animation = None

            if self.state.is_goal():
                self.solution_queue.clear()
                self.set_status("Solved!", "success")
            elif self.solution_queue:
                self.set_status("Auto-solving...", "warning")
            else:
                self.set_status("Move completed.")

    # ----------------------------
    # Input
    # ----------------------------

    def handle_button_click(self, pos: tuple[int, int]) -> bool:
        for button in self.buttons:
            if button.is_clicked(pos):
                if button.action == "undo":
                    self.undo()
                elif button.action == "reset":
                    self.reset()
                elif button.action in {
                    "solve_bfs",
                    "solve_dfs",
                    "solve_iddfs",
                    "solve_ucs",
                    "solve_greedy",
                    "solve_astar",
                    "solve_wastar",
                    "hint",
                }:
                    self.start_solver_job(button.action)
                elif button.action == "stop_auto":
                    self.cancel_solver()
                    self.solution_queue.clear()
                    self.set_status("Auto-play stopped.")
                elif button.action == "main_menu":
                    self.request_main_menu()
                elif button.action == "new_puzzle":
                    self.request_new_puzzle()
                return True
        return False

    def handle_tube_click(self, pos: tuple[int, int]) -> None:
        if not self.can_interact():
            return

        clicked_idx = None
        for i, rect in enumerate(self.tube_rects):
            if rect.inflate(12, 20).collidepoint(pos):
                clicked_idx = i
                break

        if clicked_idx is None:
            self.selected_tube = None
            return

        self.solution_queue.clear()

        if self.selected_tube is None:
            if self.state.is_tube_empty(clicked_idx):
                self.set_status("That tube is empty.", "warning")
            else:
                self.selected_tube = clicked_idx
                self.set_status(f"Selected tube {clicked_idx}. Now choose destination.")
            return

        src = self.selected_tube
        dst = clicked_idx

        if src == dst:
            self.selected_tube = None
            self.set_status("Selection cleared.")
            return

        if self.state.is_valid_move(src, dst):
            self.selected_tube = None
            self.start_pour_animation(src, dst)
            self.set_status(f"Pouring from tube {src} to tube {dst}...")
        else:
            self.selected_tube = None
            self.set_status("Invalid move.", "warning")

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_u:
                self.undo()
            elif event.key == pygame.K_r:
                self.reset()
            elif event.key == pygame.K_b:
                self.start_solver_job("solve_bfs")
            elif event.key == pygame.K_d:
                self.start_solver_job("solve_dfs")
            elif event.key == pygame.K_i:
                self.start_solver_job("solve_iddfs")
            elif event.key == pygame.K_c:
                self.start_solver_job("solve_ucs")
            elif event.key == pygame.K_g:
                self.start_solver_job("solve_greedy")
            elif event.key == pygame.K_s:
                self.start_solver_job("solve_astar")
            elif event.key == pygame.K_w:
                self.start_solver_job("solve_wastar")
            elif event.key == pygame.K_h:
                self.start_solver_job("hint")

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_button_click(event.pos):
                return True
            self.handle_tube_click(event.pos)

        return False

    # ----------------------------
    # Main drawing
    # ----------------------------

    def draw_top_bar(self) -> None:
        title = self.font_title.render("Water Sort Puzzle", True, WHITE)
        self.screen.blit(title, (28, 20))

        move_count = max(0, len(self.history) - 1)
        move_text = self.font_main.render(f"Moves: {move_count}", True, SUBTLE)
        self.screen.blit(move_text, (30, 68))

        if self.status_style == "success":
            color = SUCCESS
        elif self.status_style == "warning":
            color = WARNING
        elif self.status_style == "error":
            color = ERROR_COLOR
        elif self.status_style == "hint":
            color = WARNING
        else:
            color = SUBTLE

        message = "Solved!" if self.state.is_goal() else self.status_text
        status = self.font_main.render(message, True, color)
        self.screen.blit(status, (170, 68))

        if self.is_solver_running():
            solving = self.font_small.render("Solver running...", True, WARNING)
            self.screen.blit(solving, (30, 95))

    def draw_bottom_panel(self) -> None:
        sw, sh = self.get_screen_size()
        pygame.draw.rect(self.screen, PANEL, pygame.Rect(0, sh - self.bottom_panel_h, sw, self.bottom_panel_h))

        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            if button.action == "undo":
                button.enabled = self.animation is None and not self.is_solver_running() and len(self.history) > 1
            elif button.action == "reset":
                button.enabled = self.animation is None and not self.is_solver_running() and (
                    self.state != self.initial_state or len(self.history) > 1
                )
            elif button.action in {
                "solve_bfs",
                "solve_dfs",
                "solve_iddfs",
                "solve_ucs",
                "solve_greedy",
                "solve_astar",
                "solve_wastar",
                "hint",
            }:
                button.enabled = self.animation is None and not self.is_solver_running() and not self.state.is_goal()
            elif button.action == "stop_auto":
                button.enabled = (len(self.solution_queue) > 0 or self.is_solver_running()) and self.animation is None
            elif button.action in {"main_menu", "new_puzzle"}:
                button.enabled = self.animation is None

            button.draw(self.screen, self.font_main, mouse_pos)

    def draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.draw_top_bar()
        self.draw_tubes()

        if self.animation is not None:
            self.draw_pour_stream()
            self.draw_rotated_source_tube()

        self.draw_bottom_panel()