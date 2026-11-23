#!/usr/bin/env python3
"""Render W3C fillrule sample SVGs and compare key pixels."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

SVG_DIR = '/home/liiing/feedback/uid34741/test_non_regression/svg'
OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'

for rule in ('evenodd', 'nonzero'):
    name = f'fillrule-{rule}'
    with open(f'{SVG_DIR}/{name}.svg', 'rb') as fd:
        svg = fd.read()
    out = f'{OUT_DIR}/{name}.png'
    cairosvg.svg2png(bytestring=svg, write_to=out)
    img = Image.open(out).convert('RGBA')
    w, h = img.size
    print(name, img.size)
    # middle shape: ring of two circles centered around x=600/1200
    cx = int(600 / 1200 * w)
    cy = h // 2
    print('  inner circle center:', img.getpixel((cx, cy)))
    # ring band between r=49 and r=107
    print('  ring band:', img.getpixel(
        (cx + int(75 / 1200 * w), cy)))
    # third shape x=950, inner center
    cx3 = int(950 / 1200 * w)
    print('  3rd inner center:', img.getpixel((cx3, cy)))
