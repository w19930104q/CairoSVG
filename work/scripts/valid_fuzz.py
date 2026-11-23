#!/usr/bin/env python3
"""Fuzz only valid path strings; check subpath count and evenodd parity."""
import io
import random
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairocffi as cairo
import cairosvg
from PIL import Image

random.seed(34741)

CMD_NUMARGS = {
    'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2,
    'Z': 0,
}

def num():
    v = random.uniform(-50, 100)
    return random.choice((str(int(v)), f'{v:.2f}', f'{v:+.1f}'))

def sep():
    return random.choice((' ', ' ', ' ', '\n', '\t'))

def rand_path(n_subpaths):
    parts = []
    for sp in range(n_subpaths):
        parts.append('M' + sep() + num() + sep() + num())
        for _ in range(random.randint(1, 4)):
            cmd = random.choice('LHVSQT')
            parts.append(cmd + ' ' + ' '.join(
                num() for _ in range(CMD_NUMARGS[cmd])))
        if random.random() < 0.9:
            parts.append(random.choice('Zz'))
    return ' '.join(parts)

from cairosvg.path import path as draw_path

class FakeSurface:
    def __init__(self):
        self.context = cairo.Context(
            cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 400))
        self.dpi = 96
        self.font_size = 16
        self.context_width = 400
        self.context_height = 400
        self.cursor_position = [0.0, 0.0]
        self.cursor_d_position = [0.0, 0.0]
        self.text_path_width = 0

class Node(dict):
    pass

fails = 0
for i in range(200):
    n_sub = random.choice((2, 3, 4))
    d = rand_path(n_sub)
    fs = FakeSurface()
    node = Node({'d': d})
    draw_path(fs, node)
    elts = list(fs.context.copy_path())
    # path() emits a (0,0) move-to bootstrap before the first real M,
    # so expect n_sub explicit subpaths plus at most that one extra move
    moves = sum(1 for e in elts if e[0] == cairo.PATH_MOVE_TO)
    if moves not in (n_sub, n_sub + 1):
        fails += 1
        print('SUBPATH MISMATCH', moves, n_sub, repr(d))

# Render-level: random nested rectangles, check evenodd parity against spec
for trial in range(100):
    n_rect = random.randint(2, 5)
    # concentric nested rectangles: bounds shrink toward center (50, 50)
    rects = []
    for k in range(n_rect):
        m = 5 + k * (40 // n_rect)
        rects.append((m, m, 100 - m, 100 - m))
    d = ' '.join(
        f'M{x1} {y1} H{x2} V{y2} H{x1} Z' for x1, y1, x2, y2 in rects)
    # probe point at center (50,50): inside every rect -> count == n_rect
    px = py = 50
    for rule in ('evenodd', 'nonzero'):
        svg = (
            '<?xml version="1.0"?>'
            '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
            f'<path d="{d}" fill="black" fill-rule="{rule}"/></svg>')
        buf = io.BytesIO()
        cairosvg.svg2png(bytestring=svg.encode(), write_to=buf)
        img = Image.open(io.BytesIO(buf.getvalue())).convert('RGBA')
        alpha = img.getpixel((px, py))[3]
        if rule == 'evenodd':
            expected = 255 if n_rect % 2 == 1 else 0
        else:
            expected = 255  # all same winding direction
        if alpha != expected:
            fails += 1
            print('PARITY FAIL', n_rect, rule, alpha, expected, d)

print('fuzz done, failures =', fails)
