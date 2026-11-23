#!/usr/bin/env python3
"""Edge-case spellings of fill-rule values."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'

D = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'

CASES = {
    'plain_evenodd': f'<path d="{D}" fill="black" fill-rule="evenodd"/>',
    'uppercase': f'<path d="{D}" fill="black" fill-rule="EVENODD"/>',
    'spaced': f'<path d="{D}" fill="black" fill-rule=" evenodd "/>',
    'hyphen_spelling': f'<path d="{D}" fill="black" fill-rule="even-odd"/>',
    'invalid_then_css': (
        '<style>.x{fill-rule:evenodd}</style>'
        f'<path class="x" d="{D}" fill="black" fill-rule="garbage"/>'),
    'css_class': (
        '<style>.eo{fill-rule:evenodd}</style>'
        f'<path class="eo" d="{D}" fill="black"/>'),
    'css_important': (
        '<style>p{fill-rule:evenodd !important}</style>'
        f'<p d="" /><path d="{D}" fill="black" fill-rule="nonzero"/>'),
    'presentation_vs_style': (
        f'<path d="{D}" fill="black" fill-rule="nonzero" '
        'style="fill-rule:evenodd"/>'),
    'newline_value': f'<path d="{D}" fill="black" fill-rule="evenodd\n"/>',
}

TEMPLATE = (
    '<?xml version="1.0"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
    'viewBox="0 0 100 100">{body}</svg>'
)

for name, body in CASES.items():
    svg = TEMPLATE.format(body=body)
    png = f'{OUT_DIR}/spell_{name}.png'
    cairosvg.svg2png(bytestring=svg.encode(), write_to=png)
    img = Image.open(png).convert('RGBA')
    center = img.getpixel((50, 50))[3]
    ring = img.getpixel((20, 50))[3]
    print(f'{name:22s} center={center:3d} ring={ring:3d}')
