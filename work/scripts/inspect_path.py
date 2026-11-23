#!/usr/bin/env python3
"""Inspect the cairo path CairoSVG builds for nested subpaths."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairocffi as cairo
import cairosvg
from cairosvg.parser import Tree
from cairosvg.surface import SVGSurface

D = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'

for rule in ('evenodd', 'nonzero'):
    svg = (
        '<?xml version="1.0"?>'
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        f'<path d="{D}" fill="black" fill-rule="{rule}"/></svg>'
    )
    tree = Tree(bytestring=svg.encode())
    surface = SVGSurface(tree, bytes, 96)
    ctx = surface.context
    print(rule, 'fill_rule =', ctx.fill_rule,
          '(EVEN_ODD=%d WINDING=%d)' % (
              cairo.FILL_RULE_EVEN_ODD, cairo.FILL_RULE_WINDING))

# Now inspect raw path elements built for the two-subpath d string
surface_ctx = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100))

class Dummy:
    pass

# Reuse CairoSVG's own path drawer directly
from cairosvg.path import path as draw_path
from cairosvg.helpers import normalize

dummy = Dummy()
dummy.context = surface_ctx
dummy.vertices = None
node = Dummy()
node.get = lambda key, default='': {
    'd': D, 'marker': '', 'marker-start': None,
    'marker-mid': None, 'marker-end': None}.get(key, default)
node.children = ()

# minimal size shim
import cairosvg.helpers as helpers
class FakeSurface(Dummy):
    dpi = 96
    font_size = 16
    context_width = 100
    context_height = 100

fs = FakeSurface()
fs.context = surface_ctx
draw_path(fs, node)
for item in surface_ctx.copy_path():
    print(item)
