import os
import random
import sys
import pygame

from ui import WaterSortUI, SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from puzzle_io import load_puzzle, list_puzzles


BACKGROUND = (28, 30, 38)
PANEL = (40, 44, 54)
WHITE = (250, 250, 250)
SUBTLE = (170, 175, 185)
BUTTON = (70, 100, 170)
BUTTON_HOVER = (90, 125, 205)
TITLE_COLOR = (240, 240, 240)


class MenuButton:
    def __init__(self, rect: pygame.Rect, text: str, action: str):
        self.rect = rect
        self.text = text
        self.action = action

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, mouse_pos: tuple[int, int]) -> None:
        color = BUTTON_HOVER if self.rect.collidepoint(mouse_pos) else BUTTON
        pygame.draw.rect(screen, color, self.rect, border_radius=14)
        pygame.draw.rect(screen, WHITE, self.rect, width=2, border_radius=14)

        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def clicked(self, pos: tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


def get_random_puzzle_from_difficulty(difficulty: str):
    folder_map = {
        "easy": os.path.join("puzzles", "easy"),
        "medium": os.path.join("puzzles", "medium"),
        "hard": os.path.join("puzzles", "hard"),
    }

    if difficulty not in folder_map:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    folder = folder_map[difficulty]
    files = list_puzzles(folder)

    if not files:
        raise FileNotFoundError(f"No puzzle files found in '{folder}'")

    chosen = random.choice(files)
    state = load_puzzle(chosen)
    return state, chosen


def draw_centered_text(
    screen: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    y: int,
) -> None:
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen.get_width() // 2, y))
    screen.blit(surf, rect)


def create_main_menu_buttons(screen_w: int) -> list[MenuButton]:
    w, h = 240, 60
    gap = 22
    start_y = 300
    x = (screen_w - w) // 2

    return [
        MenuButton(pygame.Rect(x, start_y, w, h), "Play", "play"),
        MenuButton(pygame.Rect(x, start_y + h + gap, w, h), "Exit", "exit"),
    ]


def create_difficulty_menu_buttons(screen_w: int) -> list[MenuButton]:
    w, h = 260, 56
    gap = 18
    start_y = 250
    x = (screen_w - w) // 2

    return [
        MenuButton(pygame.Rect(x, start_y + 0 * (h + gap), w, h), "Easy", "easy"),
        MenuButton(pygame.Rect(x, start_y + 1 * (h + gap), w, h), "Medium", "medium"),
        MenuButton(pygame.Rect(x, start_y + 2 * (h + gap), w, h), "Hard", "hard"),
        MenuButton(pygame.Rect(x, start_y + 3 * (h + gap) + 10, w, h), "Back", "back"),
    ]


def draw_main_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    main_font: pygame.font.Font,
    small_font: pygame.font.Font,
    buttons: list[MenuButton],
) -> None:
    sw, sh = screen.get_width(), screen.get_height()
    screen.fill(BACKGROUND)

    panel = pygame.Rect(sw // 2 - 220, 120, 440, 420)
    pygame.draw.rect(screen, PANEL, panel, border_radius=22)
    pygame.draw.rect(screen, WHITE, panel, width=2, border_radius=22)

    draw_centered_text(screen, "Water Sort Puzzle", title_font, TITLE_COLOR, 180)
    draw_centered_text(screen, "Main Menu", main_font, SUBTLE, 225)

    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.draw(screen, main_font, mouse_pos)

    draw_centered_text(screen, "Choose an option", small_font, SUBTLE, 500)


def draw_difficulty_menu(
    screen: pygame.Surface,
    title_font: pygame.font.Font,
    main_font: pygame.font.Font,
    small_font: pygame.font.Font,
    buttons: list[MenuButton],
) -> None:
    sw, sh = screen.get_width(), screen.get_height()
    screen.fill(BACKGROUND)

    panel = pygame.Rect(sw // 2 - 250, 90, 500, 500)
    pygame.draw.rect(screen, PANEL, panel, border_radius=22)
    pygame.draw.rect(screen, WHITE, panel, width=2, border_radius=22)

    draw_centered_text(screen, "Select Difficulty", title_font, TITLE_COLOR, 165)
    draw_centered_text(screen, "Random puzzle will be loaded", small_font, SUBTLE, 205)

    mouse_pos = pygame.mouse.get_pos()
    for button in buttons:
        button.draw(screen, main_font, mouse_pos)


def draw_error_overlay(
    screen: pygame.Surface,
    main_font: pygame.font.Font,
    small_font: pygame.font.Font,
    message: str,
) -> None:
    box = pygame.Rect(140, screen.get_height() - 120, screen.get_width() - 280, 70)
    pygame.draw.rect(screen, (120, 50, 50), box, border_radius=14)
    pygame.draw.rect(screen, WHITE, box, width=2, border_radius=14)

    msg = main_font.render("Error", True, WHITE)
    screen.blit(msg, (box.x + 18, box.y + 8))

    text = small_font.render(message, True, WHITE)
    screen.blit(text, (box.x + 18, box.y + 40))


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Water Sort Puzzle")
    clock = pygame.time.Clock()

    title_font = pygame.font.SysFont("arial", 42, bold=True)
    main_font = pygame.font.SysFont("arial", 28)
    small_font = pygame.font.SysFont("arial", 20)

    main_menu_buttons = create_main_menu_buttons(screen.get_width())
    difficulty_buttons = create_difficulty_menu_buttons(screen.get_width())

    app_state = "main_menu"
    game_ui = None
    error_message = ""
    current_difficulty = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        if screen.get_width() != SCREEN_WIDTH:
            main_menu_buttons = create_main_menu_buttons(screen.get_width())
            difficulty_buttons = create_difficulty_menu_buttons(screen.get_width())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                if game_ui is not None:
                    game_ui.screen = screen
                    game_ui.refresh_layout()

                main_menu_buttons = create_main_menu_buttons(screen.get_width())
                difficulty_buttons = create_difficulty_menu_buttons(screen.get_width())

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if app_state == "game":
                    if game_ui is not None:
                        game_ui.close()
                    app_state = "main_menu"
                    game_ui = None
                    current_difficulty = None
                    pygame.display.set_caption("Water Sort Puzzle")
                elif app_state == "difficulty_menu":
                    app_state = "main_menu"
                else:
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                if app_state == "main_menu":
                    for button in main_menu_buttons:
                        if button.clicked(pos):
                            if button.action == "play":
                                app_state = "difficulty_menu"
                                error_message = ""
                            elif button.action == "exit":
                                running = False

                elif app_state == "difficulty_menu":
                    for button in difficulty_buttons:
                        if button.clicked(pos):
                            if button.action == "back":
                                app_state = "main_menu"
                                error_message = ""
                            else:
                                try:
                                    current_difficulty = button.action
                                    state, chosen_file = get_random_puzzle_from_difficulty(current_difficulty)

                                    if game_ui is not None:
                                        game_ui.close()

                                    game_ui = WaterSortUI(screen, state, puzzle_file=chosen_file)
                                    app_state = "game"
                                    error_message = ""
                                    pygame.display.set_caption(
                                        f"Water Sort Puzzle - {current_difficulty.capitalize()} - {os.path.basename(chosen_file)}"
                                    )
                                except Exception as e:
                                    error_message = str(e)

                elif app_state == "game" and game_ui is not None:
                    game_ui.handle_event(event)

            elif app_state == "game" and game_ui is not None:
                game_ui.handle_event(event)

        if app_state == "game" and game_ui is not None:
            game_ui.update(dt)

            if game_ui.pending_action == "main_menu":
                game_ui.pending_action = None
                game_ui.close()
                app_state = "main_menu"
                game_ui = None
                current_difficulty = None
                pygame.display.set_caption("Water Sort Puzzle")

            elif game_ui.pending_action == "new_puzzle":
                game_ui.pending_action = None
                try:
                    if current_difficulty is None:
                        raise ValueError("Current difficulty is unknown.")

                    game_ui.close()

                    state, chosen_file = get_random_puzzle_from_difficulty(current_difficulty)
                    game_ui = WaterSortUI(screen, state, puzzle_file=chosen_file)
                    pygame.display.set_caption(
                        f"Water Sort Puzzle - {current_difficulty.capitalize()} - {os.path.basename(chosen_file)}"
                    )
                except Exception as e:
                    error_message = str(e)
                    if game_ui is not None:
                        game_ui.close()
                    app_state = "difficulty_menu"
                    game_ui = None

            if app_state == "game" and game_ui is not None:
                game_ui.draw()

        elif app_state == "main_menu":
            draw_main_menu(screen, title_font, main_font, small_font, main_menu_buttons)

        elif app_state == "difficulty_menu":
            draw_difficulty_menu(screen, title_font, main_font, small_font, difficulty_buttons)
            if error_message:
                draw_error_overlay(screen, main_font, small_font, error_message)

        pygame.display.flip()

    if game_ui is not None:
        game_ui.close()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()