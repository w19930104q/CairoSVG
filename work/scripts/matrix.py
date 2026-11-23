#!/usr/bin/env python3
"""Broader matrix for evenodd fill-rule behavior."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'

D = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'

CASES = {
    'attr_evenodd':
        f'<path d="{D}" fill="black" fill-rule="evenodd"/>',
    'style_evenodd':
        f'<path d="{D}" fill="black" style="fill-rule:evenodd"/>',
    'inherit_evenodd':
        f'<g fill-rule="evenodd"><path d="{D}" fill="black"/></g>',
    'attr_nonzero':
        f'<path d="{D}" fill="black" fill-rule="nonzero"/>',
    'two_paths_eo':
        f'<path d="{D}" fill="black" fill-rule="evenodd"/>'
        f'<path d="M0 0 L1 1" fill="none"/>',
    'eo_then_nonzero':
        f'<path d="{D}" fill="black" fill-rule="evenodd"/>'
        f'<path d="{D}" fill="black" fill-rule="nonzero" '
        f'transform="translate(0,0)"/>',
}

TEMPLATE = (
    '<?xml version="1.0"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
    'viewBox="0 0 100 100">{body}</svg>'
)

for name, body in CASES.items():
    svg = TEMPLATE.format(body=body)
    png_path = f'{OUT_DIR}/matrix_{name}.png'
    pdf_path = f'{OUT_DIR}/matrix_{name}.pdf'
    cairosvg.svg2png(bytestring=svg.encode(), write_to=png_path)
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=pdf_path)
    img = Image.open(png_path).convert('RGBA')
    center = img.getpixel((50, 50))
    ring = img.getpixel((20, 50))
    outside = img.getpixel((2, 2))
    with open(pdf_path, 'rb') as fd:
        pdf = fd.read()
    has_evenodd = b' f*' in pdf or b'f*\n' in pdf or b'B*' in pdf
    print(f'{name:16s} center={center[3]:3d} ring={ring[3]:3d} '
          f'outside={outside[3]:3d} pdf_evenodd_op={has_evenodd}')
