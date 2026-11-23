"""
CairoSVG API test suite.

These tests can be used as deployment tests.

"""

import io
import sys

import cairocffi as cairo
import pytest

from . import SURFACES, VERSION, parser, surface, svg2pdf, svg2png
from .__main__ import main
from .colors import color
from .defs import parse_opacity

MAGIC_NUMBERS = {
    'SVG': b'<?xml',
    'PNG': b'\211PNG\r\n\032\n',
    'PDF': b'%PDF',
    'PS': b'%!',
}

SVG_SAMPLE = b'''\
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="4in" height="5in">
  <rect x="5" y="10" width="13" height="15"
        fill="lime" stroke="black" stroke-width="1" />
</svg>
'''

GRADIENT_OPACITY_SVG = b'''\
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="20"
     viewBox="0 0 100 20">
  <rect width="100" height="20" fill="white"/>
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="red" stop-opacity="{left_opacity}"/>
      <stop offset="1" stop-color="red" stop-opacity="{right_opacity}"/>
    </linearGradient>
  </defs>
  <rect width="100" height="20" fill="url(#g)"/>
</svg>
'''

GRADIENT_RGBA_SVG = b'''\
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="20"
     viewBox="0 0 100 20">
  <rect width="100" height="20" fill="white"/>
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="rgba(255,0,0,{left_alpha})"/>
      <stop offset="1" stop-color="rgba(255,0,0,{right_alpha})"/>
    </linearGradient>
  </defs>
  <rect width="100" height="20" fill="url(#g)"/>
</svg>
'''


@pytest.mark.parametrize('format_name', MAGIC_NUMBERS)
def test_formats(format_name):
    """Convert to a given format and test that output looks right."""
    content = SURFACES[format_name].convert(SVG_SAMPLE)
    assert content.startswith(MAGIC_NUMBERS[format_name])


def read_file(filename):
    """Shortcut to return the whole content of a file as a byte string."""
    with open(filename, 'rb') as file_object:
        return file_object.read()


def test_api(tmp_path):
    """Test the Python API with various parameters."""
    expected_content = svg2png(SVG_SAMPLE)
    # Already tested above: just a sanity check:
    assert expected_content.startswith(MAGIC_NUMBERS['PNG'])

    # Read from a byte string
    assert svg2png(SVG_SAMPLE) == expected_content
    assert svg2png(bytestring=SVG_SAMPLE) == expected_content

    file_like = io.BytesIO(SVG_SAMPLE)
    # Read from a file-like object
    assert svg2png(file_obj=file_like) == expected_content

    file_like = io.BytesIO()
    # Write to a file-like object
    svg2png(SVG_SAMPLE, write_to=file_like)
    assert file_like.getvalue() == expected_content

    temp_0 = tmp_path / 'sample_0.svg'
    temp_0.write_bytes(SVG_SAMPLE)

    # Read from a filename
    assert svg2png(url=str(temp_0)) == expected_content
    assert svg2png(url=f'file://{temp_0}') == expected_content

    # Read from a pathlib.Path
    assert svg2png(url=temp_0) == expected_content

    with temp_0.open('rb') as file_object:
        # Read from a real file object
        assert svg2png(file_obj=file_object) == expected_content

    temp_1 = tmp_path / 'result_1.png'
    with temp_1.open('wb') as file_object:
        # Write to a real file object
        svg2png(SVG_SAMPLE, write_to=file_object)
    assert read_file(str(temp_1)) == expected_content

    temp_2 = tmp_path / 'result_2.png'
    # Write to a filename
    svg2png(SVG_SAMPLE, write_to=str(temp_2))
    assert read_file(str(temp_2)) == expected_content

    file_like = io.BytesIO()
    try:
        svg2png(write_to=file_like)
    except TypeError:
        pass
    else:  # pragma: no cover
        raise Exception('TypeError not raised')


def test_low_level_api():
    """Test the low-level Python API with various parameters."""
    expected_content = svg2png(SVG_SAMPLE)

    # Same as above, longer version
    tree = parser.Tree(bytestring=SVG_SAMPLE)
    file_like = io.BytesIO()
    png_surface = surface.PNGSurface(tree, file_like, 96)
    png_surface.finish()
    assert file_like.getvalue() == expected_content

    png_result = cairo.ImageSurface.create_from_png(
        io.BytesIO(expected_content))
    expected_width = png_result.get_width()
    expected_height = png_result.get_height()

    # Abstract surface
    png_surface = surface.PNGSurface(tree, None, 96)
    assert png_surface.width == expected_width
    assert png_surface.height == expected_height
    assert cairo.SurfacePattern(png_surface.cairo)


def test_script(tmp_path):
    """Test the ``cairosvg`` script and the ``main`` function."""
    expected_png = svg2png(SVG_SAMPLE)[:100]
    expected_pdf = svg2pdf(SVG_SAMPLE)[:100]

    def test_main(args, exit_=False, input_=None, full=False):
        """Test main called with given ``args``.

        If ``exit_`` is ``True``, check that ``SystemExit`` is raised. We then
        assume that the program output is an unicode string.

        If ``input_`` is given, use this stream as input stream.

        """
        sys.argv = ['cairosvg'] + args
        old_stdin, old_stdout = sys.stdin, sys.stdout

        output_buffer = io.BytesIO()
        sys.stdout = io.TextIOWrapper(output_buffer)

        if input_:
            sys.stdin = open(input_, 'rb')
            sys.stdin.buffer = sys.stdin

        if exit_:
            try:
                main()
            except SystemExit:
                pass
            else:  # pragma: no cover
                raise Exception('CairoSVG did not exit')
        else:
            main()

        sys.stdout.flush()
        output = output_buffer.getvalue()
        sys.stdin, sys.stdout = old_stdin, old_stdout
        return output if full else output[:100]

    svg_path = tmp_path / "test.svg"
    svg_path.write_bytes(SVG_SAMPLE)
    svg_filename = str(svg_path)

    assert test_main(['--help'], exit_=True).startswith(b'usage: ')
    assert test_main(['--version'], exit_=True).strip() == (
        VERSION.encode('ascii'))

    assert test_main([svg_filename]) == expected_pdf
    assert test_main([svg_filename, '-d', '96', '-f', 'pdf']) == expected_pdf
    assert test_main([svg_filename, '-f', 'png']) == expected_png
    assert test_main(['-'], input_=svg_filename) == expected_pdf

    # Test DPI
    output = test_main([svg_filename, '-d', '10', '-f', 'png'], full=True)
    image = cairo.ImageSurface.create_from_png(io.BytesIO(output))
    assert image.get_width() == 40
    assert image.get_height() == 50

    temp_1 = tmp_path / 'result_1'
    # Default to PDF
    assert not test_main([svg_filename, '-o', str(temp_1)])
    assert read_file(temp_1)[:100] == expected_pdf

    temp_2 = tmp_path / 'result_2.png'
    # Guess from the file extension
    assert not test_main([svg_filename, '-o', str(temp_2)])
    assert read_file(temp_2)[:100] == expected_png

    temp_3 = tmp_path / 'result_3.png'
    # Explicit -f wins
    assert not test_main([svg_filename, '-o', str(temp_3), '-f', 'pdf'])
    assert read_file(str(temp_3))[:100] == expected_pdf


def png_pixels(svg_bytestring, width, height):
    """Render an SVG on white and return the RGB pixels of the middle row."""
    png_bytestring = svg2png(
        bytestring=svg_bytestring, output_width=width,
        output_height=height, background_color='white')
    image = cairo.ImageSurface.create_from_png(io.BytesIO(png_bytestring))
    data = image.get_data()
    stride = image.get_stride()
    row = stride * (height // 2)
    pixels = []
    for x in range(width):
        # Cairo ARGB32 stores B, G, R, A bytes in memory.
        b, g, r, _ = data[row + x * 4:row + x * 4 + 4]
        pixels.append((r, g, b))
    return pixels


def assert_pixel(pixel, expected, tolerance=2):
    """Check that a pixel matches an expected RGB value within a tolerance."""
    assert tuple(abs(value - target) for value, target in zip(
        pixel, expected)) <= (tolerance, tolerance, tolerance)


def test_gradient_stop_opacity():
    """Stop opacity enters the gradient interpolation."""
    pixels = png_pixels(
        GRADIENT_OPACITY_SVG.replace(b'{left_opacity}', b'0').replace(
            b'{right_opacity}', b'1'), 100, 20)
    # The left end is transparent over the white background
    assert_pixel(pixels[0], (255, 255, 255))
    # The right end is opaque red
    assert_pixel(pixels[-1], (255, 0, 0))
    # Intermediate pixels blend red with white, with an increasing opacity
    middle = pixels[len(pixels) // 2]
    assert_pixel(middle, (255, 128, 128))
    assert pixels[0] > middle > pixels[-1]


def test_gradient_stop_opacity_percentage():
    """Percentage values are accepted for ``stop-opacity``."""
    pixels = png_pixels(
        GRADIENT_OPACITY_SVG.replace(b'{left_opacity}', b'0%').replace(
            b'{right_opacity}', b'100%'), 100, 20)
    assert_pixel(pixels[0], (255, 255, 255))
    assert_pixel(pixels[-1], (255, 0, 0))
    middle = pixels[len(pixels) // 2]
    assert_pixel(middle, (255, 128, 128))
    assert pixels[0] > middle > pixels[-1]


def test_gradient_rgba_alpha():
    """Alpha of ``rgba()`` stop colors, numeric or percentage, is respected."""
    numeric = png_pixels(
        GRADIENT_RGBA_SVG.replace(b'{left_alpha}', b'0').replace(
            b'{right_alpha}', b'0.5'), 100, 20)
    percentage = png_pixels(
        GRADIENT_RGBA_SVG.replace(b'{left_alpha}', b'0%').replace(
            b'{right_alpha}', b'50%'), 100, 20)
    for pixels in (numeric, percentage):
        assert_pixel(pixels[0], (255, 255, 255))
        # Half-transparent red over white gives RGB(255, 128, 128)
        assert_pixel(pixels[-1], (255, 128, 128))


def test_parse_opacity():
    """The opacity parser accepts numbers and percentages."""
    assert parse_opacity(None) == 1
    assert parse_opacity('0') == 0
    assert parse_opacity('0.7') == 0.7
    assert parse_opacity('0%') == 0
    assert parse_opacity('45%') == 0.45
    assert parse_opacity('100%') == 1


def test_rgba_color_alpha():
    """``rgba()`` alpha values stay in the 0-1 range."""
    assert color('rgba(255, 0, 0, 0.5)') == (1, 0, 0, 0.5)
    assert color('rgba(255, 0, 0, 50%)') == (1, 0, 0, 0.5)
    assert color('rgba(100%, 0%, 0%, 50%)') == (1, 0, 0, 0.5)
    # The opacity argument still multiplies the alpha of the color
    assert color('rgba(255, 0, 0, 0.5)', 0.5) == (1, 0, 0, 0.25)
