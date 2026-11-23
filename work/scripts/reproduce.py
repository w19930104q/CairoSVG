#!/usr/bin/env python3
"""Reproduce evenodd nested-squares fill in CairoSVG."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

INPUT_DIR = '/home/liiing/feedback/uid34741/work/inputs'
OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'

TEMPLATE = open(
    f'{INPUT_DIR}/nested_squares_TEMPLATE.svg', encoding='utf-8').read()

for rule in ('evenodd', 'nonzero'):
    svg = TEMPLATE.replace(
        'FILLRULE_ATTR', f'fill-rule="{rule}"')
    in_path = f'{INPUT_DIR}/nested_squares_{rule}.svg'
    png_path = f'{OUT_DIR}/nested_squares_{rule}.png'
    pdf_path = f'{OUT_DIR}/nested_squares_{rule}.pdf'
    with open(in_path, 'w', encoding='utf-8') as fd:
        fd.write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=png_path)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=pdf_path)

    img = Image.open(png_path).convert('RGBA')
    w, h = img.size
    center = img.getpixel((w // 2, h // 2))
    # ring pixel: between outer (10..90) and inner (30..70), e.g. (20, 50)
    ring = img.getpixel((20 * w // 100, 50 * h // 100))
    outside = img.getpixel((2 * w // 100, 2 * h // 100))
    print(f'{rule:8s} size={w}x{h} center={center} ring={ring} outside={outside}')
