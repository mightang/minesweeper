import random
import pygame
from collections import deque

class BoardState:
    def __init__(self, rows:int, cols: int, num_mines: int):
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines

        self.anim = None
        self.first_move = True
        self.game_over = False
        self.victory = False

        self.mines = [[False]*cols for _ in range(rows)]
        self.revealed = [[False]*cols for _ in range(rows)]
        self.flagged = [[False]*cols for _ in range(rows)]
        self.adj = [[0]*cols for _ in range(rows)]

        self.revealed_safe = 0

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols
    
    def neighbors(self, r, c):
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if(self.in_bounds(nr, nc)):
                    yield nr, nc
    
    def place_mines_safe(self, safe_r, safe_c):
        forbidden = {(safe_r, safe_c)}
        for nr, nc in self.neighbors(safe_r, safe_c):
            forbidden.add((nr, nc))

        pool = [(r, c) for r in range(self.rows) for c in range(self.cols) if(r, c) not in forbidden]
        mines_coords = random.sample(pool, self.num_mines)
        for r, c in mines_coords:
            self.mines[r][c] = True

        for r in range(self.rows):
            for c in range(self.cols):
                if self.mines[r][c]:
                    self.adj[r][c] = -1
                else:
                    cnt = 0
                    for nr, nc in self.neighbors(r, c):
                        if self.mines[nr][nc]:
                            cnt += 1
                    self.adj[r][c] = cnt

    def toggle_flag(self, r, c):
        if self.game_over:
            return
        if not self.in_bounds(r, c):
            return
        if self.revealed[r][c]:
            return
        self.flagged[r][c] = not self.flagged[r][c]

    def reveal(self, r, c):
        if self.game_over:
            return
        if not self.in_bounds(r, c):
            return
        if self.revealed[r][c] or self.flagged[r][c]:
            return
        
        if self.first_move:
            self.place_mines_safe(r, c)
            self.first_move = False

        if self.mines[r][c]:
            self.revealed[r][c] = True
            self.game_over = True
            self.victory = False
            return
        
        q = deque()
        q.append((r, c, 0))
        while q:
            cr, cc, d = q.popleft()
            if self.revealed[cr][cc]:
                continue
            self.revealed[cr][cc] = True
            self.revealed_safe += 1

            if self.anim is not None:
                n = self.adj[cr][cc]
                with_number = (n > 0)
                self.anim.schedule_reveal(cr, cc, d, pygame.time.get_ticks(), with_number)

            if self.adj[cr][cc] == 0:
                for nr, nc in self.neighbors(cr, cc):
                    if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                        if not self.mines[nr][nc]:
                            q.append((nr, nc, d + 1))

        total_safe = self.rows * self.cols - self.num_mines
        if self.revealed_safe == total_safe:
            self.game_over = True
            self.victory = True

    def chord(self, r, c):
        if self.game_over or not self.in_bounds(r, c):
            return
        if not self.revealed[r][c]:
            return
        
        n = self.adj[r][c]
        if n <= 0:
            return
        flags = sum(1 for nr, nc in self.neighbors(r, c) if self.flagged[nr][nc])
        if flags != n:
            return
        for nr, nc in self.neighbors(r, c):
            if not self.revealed[nr][nc] and not self.flagged[nr][nc]:
                self.reveal(nr, nc)

    def attach_anim(self, anim):
        self.anim = anim
    
def count_found_mines(state: "BoardState") -> int:
    count = 0
    for r in range(state.rows):
        for c in range(state.cols):
            if state.mines[r][c] and state.flagged[r][c]:
                count += 1
    return count