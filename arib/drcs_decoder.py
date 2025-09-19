'''
Module: drcs_decoder.py
Desc: Turn DRCS binary data into formats we can display.
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, September 28th 2025

Should be used via:

bmp = drcs_unpack_to_bitmap(font._width, font._height, font._pixels, depth=font._depth)
path = bitmap_to_ass_path(bmp, alpha_threshold=1)
text = ass_draw_dialogue(path, x=100, y=200)

'''

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
        masks_shifts = [(1 << (7 - i), 7 - i) for i in range(8)]   # 8 px/byte
    elif depth == 2:
        masks_shifts = [((3 << 6), 6), ((3 << 4), 4), ((3 << 2), 2), ((3 << 0), 0)]  # 4 px/byte
    else:  # depth == 4
        masks_shifts = [((0xF << 4), 4), ((0xF << 0), 0)]          # 2 px/byte

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


def bitmap_to_ass_path(bitmap, alpha_threshold=1):
    """
    bitmap: 2D list [h][w] with values 0..N (N = 2**depth-1)
    alpha_threshold: draw pixels with value >= threshold (simple mono)
    returns: ASS path string like 'm x y l x2 y l x2 y2 l x y2'
    """
    h = len(bitmap)
    if h == 0:
        return ""
    w = len(bitmap[0])

    path_parts = []
    for y in range(h):
        row = bitmap[y]
        x = 0
        while x < w:
            # find start of a run
            while x < w and row[x] < alpha_threshold:
                x += 1
            if x >= w:
                break
            run_start = x
            while x < w and row[x] >= alpha_threshold:
                x += 1
            run_end = x  # exclusive

            # rectangle from (run_start, y) to (run_end, y+1)
            # ASS path is integer-friendly; y grows downward in libass
            x1, y1 = run_start, y
            x2, y2 = run_end, y + 1
            path_parts.append(f"m {x1} {y1} l {x2} {y1} l {x2} {y2} l {x1} {y2}")

    return " ".join(path_parts)

def ass_draw_dialogue(path, x, y, colour="&H00FFFFFF&", outline_colour="&H00000000&",
                      alpha="&H00&", border=0, p_scale=1, fscx=100, fscy=100,
                      anchor=7, extra_tags=""):
    """
    x,y are the placement in script pixels (video coordinate space).
    We'll use \p<p_scale> and \pos(x,y). Path is in pixel units.
    """
    # Note: \an<7> top-left anchor is nice for pixel-aligned sprites.
    # colour is \1c, alpha is \1a; border is \bord for optional outline.
    return (
        f"{{\\an{anchor}\\pos({x},{y})\\p{p_scale}\\bord{border}"
        f"\\1c{colour}\\3c{outline_colour}\\1a{alpha}{extra_tags}}}"
        f"{path}{{\\p0}}"
    )

def ass_draw_drcs(drcs):
  if not isinstance(drcs, DrcsGlyph):
        raise TypeError(f"Expected DrcsGlyph, got {type(drcs).__name__}")
  bmp = drcs_unpack_to_bitmap(drcs.width, drcs.height, drcs.bitmap, depth=drcs.depth_bits)
  path = bitmap_to_ass_path(bmp, alpha_threshold=1)
  text = ass_draw_dialogue(path, x=100, y=200)
  return text

def ass_draw_drcs_debug(drcs):
    """
    produce a DRCS like drawing command for .ass files.
    This is how DRCS characters are "rendered" for .ass.
    Dialogue: 0,0:00:10.00,0:00:13.00,Default,,0,0,0,,{\p1\an7\pos(100,100)\fscx100\fscy100\1c&HFFFFFF&}m 0 0 l 0 24 24 24 24 0 c{\p0}  Call me!
    """
    return "{\p1\an7\pos(100,100)\fscx100\fscy100\1c&HFFFFFF&}m 0 0 l 0 24 24 24 24 0 c{\p0}"
