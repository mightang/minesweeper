import pygame
from config import (
    ROWS, COLS, CELL, HUD_H, WIN_W, WIN_H, BOARD_H, BOARD_W,
    COLOR_BG, COLOR_HUD_BG, COLOR_GRID, COLOR_TEXT,
    COLOR_CELL_COVERED, COLOR_CELL_REVEALED, COLOR_HOVER,
    COLOR_NUM, COLOR_MINE, COLOR_FLAG,
    COLOR_BACKDROP, COLOR_MODAL_BG, COLOR_BTN_BG, COLOR_BTN_HOVER,
    COLOR_WIN, COLOR_LOSE
)
from state import count_found_mines, BoardState
from anim import ease_out_cubic, ease_out_back

# 좌표 변환
def screen_to_cell(x : int, y : int):
    grid_y = y - HUD_H
    if grid_y < 0:
        return None
    
    r = grid_y // CELL
    c = x // CELL
    if 0 <= r < ROWS and 0 <= c < COLS:
        return (r, c)
    return None

def cell_to_rect(r: int, c : int) -> pygame.Rect:
    x = c * CELL
    y = HUD_H + r * CELL
    return pygame.Rect(x, y, CELL, CELL)

# HUD 그리기(상단 게임 진행 바)
def draw_hud(surf: pygame.Surface, font: pygame.font.Font, elapsed_sec: int, state: BoardState, hover_cell=None, best_time_sec = None):
    pygame.draw.rect(surf, COLOR_HUD_BG, (0, 0, WIN_W, HUD_H))

    title = font.render(
        f"MINESWEEPER {'WIN!' if state.victory else 'LOSE!' if state.game_over else ''}",
        True, COLOR_TEXT
    )
    info = font.render("press R to restart", True, COLOR_TEXT)
    surf.blit(title, (16, 16))
    surf.blit(info, (16, 40))

    flags_used = sum(state.flagged[r][c] for r in range(state.rows) for c in range(state.cols))
    info_text = f"TIME {elapsed_sec:03d} MINES {state.num_mines:02d} FLAGS {flags_used:02d}"
    info = font.render(info_text, True, COLOR_TEXT)
    surf.blit(info, (WIN_W - info.get_width() - 16, 16))

    best_str = "--" if best_time_sec is None else f"{best_time_sec:03d} s"
    stat3 = font.render(f"Best:{best_str}", True, COLOR_TEXT)
    surf.blit(stat3, (WIN_W - info.get_width() - 16, 40))

    pygame.draw.line(surf, COLOR_GRID, (0, HUD_H - 1), (WIN_W, HUD_H - 1), 1)

# 보드 그리기
def draw_board(surf: pygame.Surface, font: pygame.font.Font, state: BoardState, hover_cell = None):
    now = pygame.time.get_ticks()
    rows, cols = state.rows, state.cols

    for r in range(ROWS):
        for c in range(COLS):
            rect = cell_to_rect(r, c)
            base = COLOR_CELL_REVEALED if state.revealed[r][c] else COLOR_CELL_COVERED
            pygame.draw.rect(surf, base, rect)

            if state.revealed[r][c] and state.anim is not None:
                t = state.anim.reveal_t(r, c, now)
                if t is not None:
                    et = ease_out_cubic(t)
                    cover_alpha = int((1.0 - et) * 255)
                    if cover_alpha > 0:
                        cover = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                        cover.fill((*COLOR_CELL_COVERED, cover_alpha))
                        surf.blit(cover, rect.topleft)
                    
                    state.anim.mark_reveal_done_if_over(r, c, now)

            if state.revealed[r][c] or (state.game_over and state.mines[r][c]):
                if state.mines[r][c]:
                    pygame.draw.circle(surf, COLOR_MINE, rect.center, CELL // 4)
                else:
                    n = state.adj[r][c]
                    if n > 0:
                        scale = 1.0
                        if state.anim is not None:
                            tpop = state.anim.num_pop_t(r, c, now)
                            if tpop is not None:
                                scale = 1.0 + 0.1 * ease_out_back(tpop)

                        text = font.render(str(n), True, COLOR_NUM.get(n, COLOR_TEXT))
                        if abs(scale - 1.0) > 1e-3:
                            tw, th = text.get_width(), text.get_height()
                            sw, sh = int(tw * scale), int(th * scale)
                            text = pygame.transform.smoothscale(text, (sw, sh))
                        text_rect = text.get_rect(center = rect.center)
                        surf.blit(text, text_rect)
                    else:
                        pass
            else:
                if state.flagged[r][c]:
                    y_offset = 0
                    alpha = 255
                    if state.anim is not None:
                        tf = state.anim.flag_t(r, c, now)
                        if tf is not None:
                            y_offset = int((1.0 - tf) * (CELL * 0.3))
                            alpha = int(tf * 255)

                    flag_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                    px = CELL // 3
                    py = CELL // 3 + y_offset
                    pts = [(px, py + CELL // 2), (px, py), (px + CELL // 2, py + CELL // 4)]
                    pygame.draw.polygon(flag_surf, (*COLOR_FLAG, alpha), pts)
                    surf.blit(flag_surf, rect.topleft)

                if hover_cell is not None and (r, c) == hover_cell and not state.revealed[r][c] and not state.game_over:
                    pygame.draw.rect(surf, COLOR_HOVER, rect)

    for c in range(COLS + 1):
        x = c * CELL
        pygame.draw.line(surf, COLOR_GRID, (x, HUD_H), (x, HUD_H + BOARD_H), 1)

    for r in range(ROWS + 1):
        y = HUD_H + r * CELL
        pygame.draw.line(surf, COLOR_GRID, (0, y), (BOARD_W, y), 1)

def draw_result_modal(surf:pygame.Surface, font:pygame.font.Font, state: BoardState, elapsed_sec: int, mouse_pos, best_time_sec = None):

    backdrop = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
    backdrop.fill(COLOR_BACKDROP)
    surf.blit(backdrop, (0, 0))

    modal_w = 520
    modal_h = 290
    modal_rect = pygame.Rect((WIN_W - modal_w) // 2, (WIN_H - modal_h) // 2, modal_w, modal_h)
    pygame.draw.rect(surf, COLOR_MODAL_BG, modal_rect, border_radius = 12)

    title_str = "VICTORY!" if state.victory else "DEFEAT"
    title_color = COLOR_WIN if state.victory else COLOR_LOSE
    title_img = font.render(title_str, True, title_color)
    surf.blit(title_img, (modal_rect.centerx - title_img.get_width() // 2, modal_rect.y + 26))

    found = count_found_mines(state)
    stat1 = font.render(f"Time: {elapsed_sec:03d} s", True, COLOR_TEXT)
    stat2 = font.render(f"Mines Found: {found} / {state.num_mines}", True, COLOR_TEXT)
    best_str = "--" if best_time_sec is None else f"{best_time_sec:03d} s"
    stat3 = font.render(f"Best:{best_str}", True, COLOR_TEXT)

    surf.blit(stat1, (modal_rect.centerx - stat1.get_width() // 2, modal_rect.y + 90))
    surf.blit(stat2, (modal_rect.centerx - stat2.get_width() // 2, modal_rect.y + 122))
    surf.blit(stat3, (modal_rect.centerx - stat3.get_width() // 2, modal_rect.y + 154))

    btn_w, btn_h, gap = 180, 44, 24
    btn_y = modal_rect.y + modal_rect.height - btn_h - 28
    btn_restart = pygame.Rect(modal_rect.centerx - btn_w - gap // 2, btn_y, btn_w, btn_h)
    btn_quit = pygame.Rect(modal_rect.centerx + gap // 2, btn_y, btn_w, btn_h)

    def draw_button(rect, label):
        hover = rect.collidepoint(mouse_pos)
        color = COLOR_BTN_HOVER if hover else COLOR_BTN_BG
        pygame.draw.rect(surf, color, rect, border_radius = 10)
        txt = font.render(label, True, COLOR_TEXT)
        surf.blit(txt, (rect.centerx - txt.get_width() // 2, rect.y + (btn_h - txt.get_height()) // 2))

    draw_button(btn_restart, "Restart (R / Enter)")
    draw_button(btn_quit, "Quit(Q / Esc)")

    return btn_restart, btn_quit