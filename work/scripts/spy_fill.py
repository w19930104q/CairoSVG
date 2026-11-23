#!/usr/bin/env python3
"""Record set_fill_rule calls and path structure during normal rendering."""
import io
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairocffi
from cairosvg.surface import PNGSurface
from cairosvg.parser import Tree

D = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'

orig_set = cairocffi.Context.set_fill_rule
calls = []

def spy_set(self, rule):
    calls.append(rule)
    return orig_set(self, rule)

cairocffi.Context.set_fill_rule = spy_set

orig_fill_preserve = cairocffi.Context.fill_preserve

def spy_fill(self):
    path = list(self.copy_path())
    moves = [p for p in path if p[0] == cairocffi.PATH_MOVE_TO]
    closes = [p for p in path if p[0] == cairocffi.PATH_CLOSE_PATH]
    print(f'  fill_preserve: rule={self.get_fill_rule()} subpaths={len(moves)} '
          f'closes={len(closes)} total_elts={len(path)}')
    return orig_fill_preserve(self)

cairocffi.Context.fill_preserve = spy_fill

for rule in ('evenodd', 'nonzero'):
    svg = (
        '<?xml version="1.0"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        f'<path d="{D}" fill="black" fill-rule="{rule}"/></svg>'
    )
    print(rule)
    tree = Tree(bytestring=svg.encode())
    PNGSurface(tree, None, 96)

print()
print('set_fill_rule call sequence:', calls)
print('EVEN_ODD =', cairocffi.FILL_RULE_EVEN_ODD,
      'WINDING =', cairocffi.FILL_RULE_WINDING)
