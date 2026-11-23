#!/usr/bin/env python3
"""Compound-scenario evenodd tests: use, pattern, mask, marker, groups."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'

D = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'

CASES = {
    # reference via <use>
    'use': f'''<defs><path id="p" d="{D}" fill="black"
        fill-rule="evenodd"/></defs><use href="#p"/>''',
    # fill-rule inherited through use into referenced path
    'use_inherit': f'''<defs><path id="p2" d="{D}" fill="black"/></defs>
        <use href="#p2" fill-rule="evenodd"/>''',
    # pattern tile containing an evenodd path
    'pattern': f'''<defs><pattern id="pat" width="20" height="20"
        patternUnits="userSpaceOnUse">
        <path d="{D}" fill-rule="evenodd" fill="black"/></pattern></defs>
        <rect width="100" height="100" fill="url(#pat)"/>''',
    # mask built from an evenodd path
    'mask': f'''<defs><mask id="m">
        <path d="{D}" fill-rule="evenodd" fill="white"/></mask></defs>
        <rect width="100" height="100" fill="black" mask="url(#m)"/>''',
    # group with opacity < 1 renders to an intermediate group surface
    'opacity_group': f'''<g opacity="0.5">
        <path d="{D}" fill="black" fill-rule="evenodd"/></g>''',
    # nested groups with inherited fill-rule
    'nested_g': f'''<g fill-rule="evenodd"><g><path d="{D}"
        fill="black"/></g></g>''',
    # marker present on the evenodd path
    'marker': f'''<defs><marker id="mk" markerWidth="4" markerHeight="4"
        refX="2" refY="2"><path d="M0 0 L4 2 L0 4 Z" fill="red"/>
        </marker></defs>
        <path d="{D}" fill="black" fill-rule="evenodd"
        marker-start="url(#mk)" marker-mid="url(#mk)" marker-end="url(#mk)"/>''',
    # evenodd path inside a transformed group
    'transformed': f'''<g transform="translate(0,0) scale(1)">
        <path d="{D}" fill="black" fill-rule="evenodd"/></g>''',
    # two evenodd paths sharing a context, then a nonzero one
    'mixed_order': f'''<path d="{D}" fill="black" fill-rule="nonzero"
        transform="translate(200,0)"/>
        <path d="{D}" fill="black" fill-rule="evenodd"/>''',
}

TEMPLATE = (
    '<?xml version="1.0"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
    'viewBox="0 0 100 100" xmlns:xlink="http://www.w3.org/1999/xlink">'
    '{body}</svg>'
)

for name, body in CASES.items():
    svg = TEMPLATE.format(body=body)
    png = f'{OUT_DIR}/compound_{name}.png'
    try:
        cairosvg.svg2png(bytestring=svg.encode(), write_to=png)
    except Exception as exc:
        print(f'{name:14s} ERROR {exc!r}')
        continue
    img = Image.open(png).convert('RGBA')
    center = img.getpixel((50, 50))
    ring = img.getpixel((20, 50))
    print(f'{name:14s} center={center} ring={ring}')
