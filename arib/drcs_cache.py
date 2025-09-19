
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from collections import OrderedDict
import threading
from arib import read
import math

from dataclasses import dataclass
import math

def normalize_94(b: int) -> int:
    # map GR (A1–FE) to GL (21–7E); leave others as-is
    return b - 0x80 if 0xA1 <= b <= 0xFE else b

def is_94_byte(b: int) -> bool:
    return (0x21 <= b <= 0x7E) or (0xA1 <= b <= 0xFE)

def drcs_set_from_font_id_byte(b: int) -> int | None:
    # 0x41..0x4E => DRCS-1..14
    if 0x41 <= b <= 0x4E:
        return b - 0x40
    return None  # not a DRCS-1..14 font id byte

def drcs0_pack(row_byte: int, cell_byte: int) -> int:
    row = normalize_94(row_byte)
    cell = normalize_94(cell_byte)
    # optional sanity checks:
    # if not (0x21 <= row <= 0x7E and 0x21 <= cell <= 0x7E):
    #     raise ValueError(f"Invalid DRCS-0 code: row={row:#x}, cell={cell:#x}")
    return (row << 8) | cell

def drcs0_unpack(code: int) -> tuple[int,int]:
    row = (code >> 8) & 0xFF
    cell = code & 0xFF
    return row, cell

def drcs_set_id_from_font_id(font_id_byte):
    # 0x41..0x4E => 1..14
    if 0x41 <= font_id_byte <= 0x4E:
        return font_id_byte - 0x40
    raise ValueError(f"Unexpected DRCS font id byte: {font_id_byte:#x}")

@dataclass
class DrcsGlyph:
    font_id: int
    mode: int
    width: int
    height: int
    depth_bits: int # 1, 2, or 4
    bitmap: bytes # packed rows, left->right, top->bottom
    baseline: int = 0
    advance: int = 0

    def __init__(self, f):
        b = read.ucb(f) # 1 byte: [font_id(4 bits)][mode(4 bits)]
        self.font_id = (b & 0xF0) >> 4
        self.mode    = (b & 0x0F)

        # Many DRCS variants then carry depth/width/height as single bytes:
        self.depth_bits = read.ucb(f) # expect 1, 2, or 4
        self.width      = read.ucb(f)
        self.height     = read.ucb(f)

        pixels = self.width * self.height
        bytes_needed = (pixels * self.depth_bits + 7) // 8
        self.bitmap = bytearray(read.ucb(f) for _ in range(bytes_needed))
    
    def __str__(self):
        px = ''
        i = 0
        for h in range(self._height//2):
            for w in range(self._width//4):
                p = self._pixels[h * self._width//2 + w]
                if p == 0:
                    px += " "
                elif p == 0xff:
                    px += "█"
                elif p == 0x0f:
                    px += "▐"
                elif p == 0xf0:
                    px += "▌"
                else:
                    px += "╳"
                i = i + 1
            px += '\n'
        return px
    
    def __str__(self):
        # expand to 2D pixels
        pixels = drcs_unpack_to_bitmap(self.width, self.height, self.bitmap, depth=self.depth_bits)

        # choose a palette depending on depth
        if self.depth_bits == 1:
            chars = [" ", "█"]
        elif self.depth_bits == 2:
            chars = [" ", "░", "▒", "█"]
        elif self.depth_bits == 4:
            # 16 levels: pick a coarse gradient
            chars = [" "] + ["░","▒","▓","█"]*3 + ["█"]
        else:
            chars = ["?"]  # fallback

        lines = []
        for row in pixels:
            line = "".join(chars[val] if val < len(chars) else "?" for val in row)
            lines.append(line)

        return "\n".join(lines)

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



def drcs_unpack_glyph(glyph: DrcsGlyph):
    return drcs_unpack_to_bitmap(
        glyph.width,
        glyph.height,
        glyph.bitmap, # accepts bytes/bytearray
        depth=glyph.depth_bits
    )

class _DrcsCache:
    def __init__(self, max_glyphs: int = 4096):
        self._lock = threading.RLock()
        self._store: "OrderedDict[Tuple[int,int], DrcsGlyph]" = OrderedDict()
        self._max = max_glyphs

    def _key(self, set_id: int, code: int) -> Tuple[int, int]:
        return (set_id, code)

    def put(self, set_id: int, code: int, glyph: DrcsGlyph) -> None:
        with self._lock:
            k = self._key(set_id, code)
            if k in self._store:
                # re-definition: overwrite and move to end (LRU refresh)
                del self._store[k]
            self._store[k] = glyph
            # enforce LRU limit
            while len(self._store) > self._max:
                self._store.popitem(last=False)

    def get(self, set_id: int, code: int) -> Optional[DrcsGlyph]:
        with self._lock:
            k = self._key(set_id, code)
            g = self._store.get(k)
            if g is not None:
                # LRU touch
                self._store.move_to_end(k)
            return g

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

# a module level static cache. Access this cache in other modules to set/get characters.
DRCS_CACHE = _DrcsCache()

# Helper for 2-byte DRCS-0 code:
def drcs0_code(row: int, cell: int) -> int:
    """Row/cell are 0x21..0x7E; pack to one int for dict key."""
    return ((row & 0xFF) << 8) | (cell & 0xFF)
