#!/usr/bin/env python3
"""PS output check + repeated-render state-leak check."""
import sys

sys.path.insert(0, '/home/liiing/feedback/uid34741')

import cairosvg
from PIL import Image

OUT_DIR = '/home/liiing/feedback/uid34741/work/outputs'
D = 'M10 10 H90 V90 H10 Z M30 30 H70 V70 H30 Z'
TMPL = (
    '<?xml version="1.0"?>'
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    f'<path d="{D}" fill="black" fill-rule="{{rule}}"/></svg>'
)

# 1. PostScript output: cairo emits its even-odd operator ("eo*"/"eofill")
ps = cairosvg.svg2ps(bytestring=TMPL.format(rule='evenodd').encode())
with open(f'{OUT_DIR}/evenodd.ps', 'wb') as fd:
    fd.write(ps)
print('PS contains eo*:', b'eo*' in ps, ' eofill:', b'eofill' in ps)
ps_nz = cairosvg.svg2ps(bytestring=TMPL.format(rule='nonzero').encode())
print('PS nonzero has plain fill:', b' f\n' in ps_nz or ps_nz.rstrip().endswith(b'f'))

# 2. State leak: render nonzero first, then evenodd in the same process,
#    alternate many times, every evenodd frame must have a hollow center
import io
fail = 0
for i in range(20):
    rule = 'nonzero' if i % 2 == 0 else 'evenodd'
    buf = io.BytesIO()
    cairosvg.svg2png(bytestring=TMPL.format(rule=rule).encode(), write_to=buf)
    img = Image.open(io.BytesIO(buf.getvalue())).convert('RGBA')
    center = img.getpixel((50, 50))[3]
    expected = 255 if rule == 'nonzero' else 0
    if center != expected:
        fail += 1
        print('LEAK at', i, rule, center)
print('alternating renders failures:', fail)

# 3. Same with pdf: check f* operator on the evenodd frame each time
for i in range(5):
    rule = 'nonzero' if i % 2 == 0 else 'evenodd'
    import zlib, re
    pdf = cairosvg.svg2pdf(bytestring=TMPL.format(rule=rule).encode())
    streams = re.findall(rb'stream\r?\n(.*?)endstream', pdf, re.S)
    has_fstar = False
    for s in streams:
        try:
            s = zlib.decompress(s)
        except Exception:
            pass
        if b'f*' in s:
            has_fstar = True
    print(f'pdf frame {i} ({rule}): f* present = {has_fstar}')
