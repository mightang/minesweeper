import math
import pygame
def clamp01(x):
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def ease_out_cubic(t):
    return 1 - (1 - t) ** 3

def ease_out_back(t, s = 1.70158):
    t = clamp01(t)
    t -= 1
    return (t * t * ((s + 1) * t + s) + 1)

class Animator:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

        self.reveal_phase = [[0] * cols for _ in range(rows)]
        self.reveal_start = [[0] * cols for _ in range(rows)]
        self.reveal_dur = [[140] * cols for _ in range(rows)]
        self.reveal_stagger_ms = 30

        self.num_start = [[-1] * cols for _ in range(rows)]
        self.num_dur = [[120] * cols for _ in range(rows)]

        self.flag_start = [[-1] * cols for _ in range(rows)]
        self.flag_dur = [[100] * cols for _ in range(rows)]

    def schedule_reveal(self, r, c, depth, now_ms, with_number: bool):
        if self.reveal_phase[r][c] != 0:
            return
        start = now_ms + depth * self.reveal_stagger_ms
        self.reveal_phase[r][c] = 1
        self.reveal_start[r][c] = start

        if with_number:
            self.num_start[r][c] = start
    
    def mark_reveal_done_if_over(self, r, c, now_ms):
        if self.reveal_phase[r][c] == 1:
            start = self.reveal_start[r][c]
            dur = self.reveal_dur[r][c]
            if now_ms >= start + dur:
                self.reveal_phase[r][c] = 2

    def schedule_flag_in(self, r, c, now_ms):
        self.flag_start[r][c] = now_ms
    
    def clear_flag_anim(self, r, c):
        self.flag_start[r][c] = -1

    def reveal_t(self, r, c, now_ms):
        if self.reveal_phase[r][c] == 0:
            return None
        start = self.reveal_start[r][c]
        dur = self.reveal_dur[r][c]
        t = (now_ms - start) / dur
        return clamp01(t)
    
    def num_pop_t(self, r, c, now_ms):
        start = self.num_start[r][c]
        if(start < 0):
            return None
        dur = self.num_dur[r][c]
        t = (now_ms - start) / dur
        return 0.0 if t < 0 else 1.0 if t > 1 else t
    
    def flag_t(self, r, c, now_ms):
        start = self.flag_start[r][c]
        if start < 0:
            return None
        dur = self.flag_dur[r][c]
        t = (now_ms - start) / dur
        return 0.0 if t < 0 else 1.0 if t > 1 else t