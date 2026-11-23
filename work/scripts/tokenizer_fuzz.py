#!/usr/bin/env python3
"""Randomized differential test of the regex tokenizer on path strings."""
import random
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairocffi as cairo

random.seed(34741)

CMD_NUMARGS = {
    'M': 2, 'L': 2, 'H': 1, 'V': 1, 'C': 6, 'S': 4, 'Q': 4, 'T': 2,
    'A': 7, 'Z': 0,
}

def rand_num():
    style = random.choice(('int', 'dec', 'sci', 'sign'))
    v = random.uniform(-50, 100)
    if style == 'int':
        return str(int(v))
    if style == 'dec':
        return f'{v:.3f}'
    if style == 'sci':
        return f'{v:.2e}'
    return f'{v:+.2f}'

def rand_path(n_subpaths=2):
    parts = []
    for sp in range(n_subpaths):
        parts.append('M')
        parts.append(rand_num())
        parts.append(rand_num())
        for _ in range(random.randint(1, 5)):
            cmd = random.choice('LHVCSQT')
            parts.append(cmd)
            for _ in range(CMD_NUMARGS[cmd]):
                parts.append(rand_num())
        if random.random() < 0.8:
            parts.append(random.choice('Zz'))
    d = ''.join(
        p if p in 'MLHVCSQTAZmlhvcsqtaz' else
        (p if random.random() < 0.5 else ' ' + p) for p in parts)
    # inject commas sometimes
    if random.random() < 0.5:
        d = d.replace(' ', ',', random.randint(1, 3))
    return d

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

mismatch = 0
checked = 0
for i in range(300):
    d = rand_path()
    fs = FakeSurface()
    node = Node({'d': d})
    node.vertices = None
    try:
        draw_path(fs, node)
        elts = list(fs.context.copy_path())
    except Exception as exc:
        print('RAISES on', repr(d), '->', type(exc).__name__, exc)
        mismatch += 1
        continue
    checked += 1
    # structural sanity: every subpath started with MOVE_TO
    moves = [e for e in elts if e[0] == cairo.PATH_MOVE_TO]
    if len(moves) != 2:
        print('SUBPATH COUNT', len(moves), 'for', repr(d))
        mismatch += 1

print(f'checked={checked} structural failures={mismatch}')
