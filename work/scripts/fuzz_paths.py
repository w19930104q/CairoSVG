#!/usr/bin/env python3
"""Fuzz variants of two-rectangle subpaths under evenodd vs nonzero."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'

# (name, d, center pixel, expected evenodd center alpha, expected nonzero)
VARIANTS = {
    'basic_z': ('M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z', (50, 50), 0, 255),
    'relative_m': ('M10 10 H90 V90 H10 Z m20 20 h40 v40 h-40 z', (50, 50), 0, 255),
    'no_z_between': ('M10 10 H90 V90 H10 Z M30 30 H70 V70 H30', (50, 50), 0, 255),
    'commas': ('M10,10 H90 V90 H10 Z M30,30 H70 V70 H30 Z', (50, 50), 0, 255),
    'implicit_l': ('M10,10 L90,10 90,90 10,90 Z M30,30 70,30 70,70 30,70 Z',
                   (50, 50), 0, 255),
    'decimals': ('M10.0 10.0 H90.0 V90.0 H10.0 Z M30.0 30.0 H70 V70 H30 Z',
                 (50, 50), 0, 255),
    'newlines': ('M10 10\nH90 V90 H10 Z\nM30 30 H70 V70 H30 Z', (50, 50), 0, 255),
    'inner_first': ('M30 30 H70 V70 H30 Z M10 10 H90 V90 H10 Z', (50, 50), 0, 255),
    # opposite inner winding: nonzero cancels -> center hollow too
    'opposite_dir': ('M10 10 H90 V90 H10 Z M30 30 V70 H70 V30 Z', (50, 50), 0, 0),
    'sci_notation': ('M1e1 1e1 H9e1 V9e1 H1e1 Z M3e1 3e1 H7e1 V7e1 H3e1 Z',
                     (50, 50), 0, 255),
    'signed_numbers': ('M+10 +10 H+90 V+90 H+10 Z M+30 +30 H+70 V+70 H+30 Z',
                       (50, 50), 0, 255),
    'no_spaces': ('M10 10H90V90H10ZM30 30H70V70H30Z', (50, 50), 0, 255),
    # three nested squares: evenodd count=3 (odd) -> filled at (55,55)
    'repeat_m': ('M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z '
                 'M50 50 H60 V60 H50 Z', (55, 55), 255, 255),
    'rect_commands': ('M10 10 L90 10 L90 90 L10 90 Z '
                      'M30 30 L70 30 L70 70 L30 70 Z', (50, 50), 0, 255),
}

TEMPLATE = (
    '<?xml version="1.0"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
    'viewBox="0 0 100 100">'
    '<path d="{d}" fill="black" fill-rule="{rule}"/></svg>'
)

bad = []
for name, (d, (px, py), exp_eo, exp_nz) in VARIANTS.items():
    row = []
    for rule in ('evenodd', 'nonzero'):
        svg = TEMPLATE.format(d=d, rule=rule)
        png = f'{OUT_DIR}/fuzz_{name}_{rule}.png'
        cairosvg.svg2png(bytestring=svg.encode(), write_to=png)
        img = Image.open(png).convert('RGBA')
        center = img.getpixel((px, py))[3]
        ring = img.getpixel((20, 50))[3]
        row.append((center, ring))
    (eo_c, eo_r), (nz_c, nz_r) = row
    # ring band must always be filled; center matches spec per rule
    eo_ok = eo_c == exp_eo and eo_r == 255
    nz_ok = nz_c == exp_nz and nz_r == 255
    status = 'OK' if (eo_ok and nz_ok) else 'FAIL'
    if not (eo_ok and nz_ok):
        bad.append(name)
    print(f'{name:14s} evenodd(center={eo_c:3d},ring={eo_r:3d}) '
          f'nonzero(center={nz_c:3d},ring={nz_r:3d}) '
          f'expected eo={exp_eo:3d} nz={exp_nz:3d} {status}')

print()
print('FAILURES:', bad or 'none')
