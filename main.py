import sys
import pygame
from config import WIN_W, WIN_H, FPS, ROWS, COLS, NUM_MINES, COLOR_BG
from state import BoardState
from ui import screen_to_cell, draw_hud, draw_board, draw_result_modal
from anim import Animator

def main():
    pygame.init()
    pygame.display.set_caption("Minesweeper")
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    clock = pygame.time.Clock()

    pygame.font.init()
    font = pygame.font.Font(None, 28)

    state = BoardState(ROWS, COLS, NUM_MINES)
    anim = Animator(ROWS, COLS)
    state.attach_anim(anim)
    hover_cell = None
    elapsed_ms = 0
    timer_running = False
    modal_active = False
    best_time_sec = None

    running = True
    while running:
        dt = clock.tick(FPS)
        if timer_running and not state.game_over:
            elapsed_ms += dt

        if state.game_over and not modal_active:
            if state.victory:
                current_sec = elapsed_ms // 1000
                if(best_time_sec is None) or (current_sec < best_time_sec):
                    best_time_sec = current_sec
            modal_active = True
            timer_running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if modal_active:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_r, pygame.K_RETURN):
                        state = BoardState(ROWS, COLS, NUM_MINES)
                        hover_cell = None
                        elapsed_ms = 0
                        timer_running = False
                        modal_active = False
                    elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    pass
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    state = BoardState(ROWS, COLS, NUM_MINES)
                    hover_cell = None
                    elapsed_ms = 0
                    timer_running = False

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                hover_cell = screen_to_cell(mx, my)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                cell = screen_to_cell(mx, my)
                if cell is not None:
                    r, c = cell
                    if event.button == 1:
                        if state.revealed[r][c]:
                            state.chord(r, c)
                        else:
                            if state.first_move and not state.game_over:
                                timer_running = True
                            state.reveal(r, c)
                    elif event.button == 3:
                        was_flagged = state.flagged[r][c]
                        state.toggle_flag(r, c)
                        if not was_flagged and state.flagged[r][c] and state.anim is not None:
                            state.anim.schedule_flag_in(r, c, pygame.time.get_ticks())

                        if was_flagged and not state.flagged[r][c] and state.anim is not None:
                            state.anim.clear_flag_anim(r, c)

        screen.fill(COLOR_BG)
        elapsed_sec = elapsed_ms // 1000
        draw_hud(screen, font, elapsed_sec, state, best_time_sec)
        draw_board(screen, font, state, hover_cell)

        if modal_active:
            mx, my = pygame.mouse.get_pos()
            btn_restart, btn_quit = draw_result_modal(screen, font, state, elapsed_sec, (mx, my), best_time_sec)
            if pygame.mouse.get_pressed(num_buttons = 3)[0]:
                if btn_restart.collidepoint((mx, my)):
                    state = BoardState(ROWS, COLS, NUM_MINES)
                    hover_cell = None
                    elapsed_ms = 0
                    timer_running = False
                    modal_active = False
                elif btn_quit.collidepoint((mx, my)):
                    running = False

        pygame.display.flip()
    
    pygame.quit()
    sys.exit()
    
if __name__ == "__main__":
    main()