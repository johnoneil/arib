"""
Module: drcs_decoder.py
Desc: Turn DRCS binary data into formats we can display.
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, September 28th 2025

Should be used via:

bmp = drcs_unpack_to_bitmap(font._width, font._height, font._pixels, depth=font._depth)
path = bitmap_to_ass_path(bmp, alpha_threshold=1)
text = ass_draw_dialogue(path, x=100, y=200)

"""

from arib.drcs_cache import DrcsGlyph


def drcs_unpack_to_bitmap(width, height, data, depth=2):
    """
    width, height: pixels
    data: bytes/bytearray (packed: left->right, top->bottom)
    depth: bits per pixel (1, 2, or 4)
    returns: 2D list [height][width] with values 0..(2**depth-1)
    """
    assert depth in (1, 2, 4), "Handle common DRCS depths; extend if needed."

    if depth == 1:
        masks_shifts = [(1 << (7 - i), 7 - i) for i in range(8)]  # 8 px/byte
    elif depth == 2:
        masks_shifts = [((3 << 6), 6), ((3 << 4), 4), ((3 << 2), 2), ((3 << 0), 0)]  # 4 px/byte
    else:  # depth == 4
        masks_shifts = [((0xF << 4), 4), ((0xF << 0), 0)]  # 2 px/byte

    px_per_byte = len(masks_shifts)
    total_px = width * height
    expected_bytes = (total_px + px_per_byte - 1) // px_per_byte

    # Be lenient: if the stream is short, pad; if it's long, ignore extras.
    if len(data) < expected_bytes:
        data = bytes(data) + bytes(expected_bytes - len(data))
    elif len(data) > expected_bytes:
        data = data[:expected_bytes]

    out = [[0] * width for _ in range(height)]
    x = y = 0

    for b in data:
        for mask, shift in masks_shifts:
            if y >= height:
                break
            val = (b & mask) >> shift
            out[y][x] = val
            x += 1
            if x >= width:
                x = 0
                y += 1
        if y >= height:
            break

    return out
