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


def _center_gray(svg_source):
    """Render an SVG and return the red channel of its center pixel."""
    png = svg2png(bytestring=svg_source, scale=8)
    surface = cairo.ImageSurface.create_from_png(io.BytesIO(png))
    data = surface.get_data()
    offset = (
        surface.get_height() // 2 * surface.get_stride()
        + surface.get_width() // 2 * 4)
    return data[offset + 2][0]


def test_opacity_element_and_group():
    """Element and group opacity are applied once and match the spec."""
    base = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="white"/>')
    element = (
        base +
        '<rect x="20" y="20" width="60" height="60" fill="black" '
        'opacity="0.5"/></svg>')
    group = (
        base +
        '<g opacity="0.5">'
        '<rect x="20" y="20" width="60" height="60" fill="black"/></g></svg>')
    # Black at 50% over white is a gray close to 128.
    assert abs(_center_gray(element) - 128) <= 2
    assert abs(_center_gray(group) - 128) <= 2
    # Percentage opacity is parsed like the fractional value.
    assert abs(_center_gray(element.replace('0.5', '50%')) - 128) <= 2


def test_opacity_stacked_groups_and_nesting():
    """Stacked and nested opacity combine by multiplication."""
    two_groups = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="white"/>'
        '<g opacity="0.5">'
        '<rect x="10" y="10" width="80" height="80" fill="black"/></g>'
        '<g opacity="0.5">'
        '<rect x="10" y="10" width="80" height="80" fill="black"/></g></svg>')
    # Combined alpha 0.75: the center is darker than a single 0.5 group.
    assert _center_gray(two_groups) < 120
    nested = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="white"/>'
        '<g opacity="0.5"><rect x="20" y="20" width="60" height="60" '
        'fill="black" opacity="0.5"/></g></svg>')
    # 0.5 * 0.5 = 0.25 black coverage -> gray close to 191.
    assert abs(_center_gray(nested) - 191) <= 2


def test_opacity_unchanged_without_opacity():
    """Rendering without opacity keeps solid colors."""
    opaque = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<rect width="100" height="100" fill="white"/>'
        '<rect x="20" y="20" width="60" height="60" fill="black"/></svg>')
    assert _center_gray(opaque) == 0


def test_opacity_luminance_mask():
    """SVG masks use luminance and the element opacity is applied once."""
    gray_mask = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<defs><mask id="m">'
        '<rect width="100" height="100" fill="#808080"/></mask></defs>'
        '<rect width="100" height="100" fill="white"/>'
        '<rect x="20" y="20" width="60" height="60" fill="black" '
        'mask="url(#m)"/></svg>')
    # A 50% luminance mask behaves like opacity 0.5.
    assert abs(_center_gray(gray_mask) - 128) <= 2

    masked_opacity = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        '<defs><mask id="m">'
        '<rect width="100" height="100" fill="white"/></mask></defs>'
        '<rect width="100" height="100" fill="white"/>'
        '<rect x="20" y="20" width="60" height="60" fill="black" '
        'opacity="0.5" mask="url(#m)"/></svg>')
    assert abs(_center_gray(masked_opacity) - 128) <= 2


def test_opacity_pdf_semantics():
    """PDF output exposes the alpha and a transparency group."""
    svg = (
        b'<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
        b'<rect width="100" height="100" fill="white"/>'
        b'<rect x="20" y="20" width="60" height="60" fill="black" '
        b'opacity="0.5"/></svg>')
    pdf = svg2pdf(bytestring=svg)
    assert b'/CA 0.5' in pdf and b'/ca 0.5' in pdf
    assert b'/S /Transparency' in pdf


def test_opacity_helper():
    """The helper parses numbers, percentages and clamps out-of-range values."""
    from .helpers import opacity
    assert opacity(None) == 1
    assert opacity('0.5') == 0.5
    assert opacity('50%') == 0.5
    assert opacity('0') == 0
    assert opacity('1') == 1
    assert opacity('-0.5') == 0
    assert opacity('2') == 1
    assert opacity(0.25) == 0.25
