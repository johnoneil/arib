
from dataclasses import dataclass
from typing import Dict, Tuple, Optional
from collections import OrderedDict
import threading
from arib import read
import math

from dataclasses import dataclass
import math

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
