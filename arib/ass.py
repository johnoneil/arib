# vim: set ts=2 expandtab:
# -*- coding: utf-8 -*-
"""
Module: ass.py
Desc: Advanced SubStation Alpha subtitle file formatter
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 6th 2014

This module provides a formatter class that can be used
to turn arib package subtitle objects into a .ass
file.

"""
import copy
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

import arib.code_set as code_set
import arib.control_characters as control_characters
from arib.arib_exceptions import FileOpenError
from arib.drcs_cache import DrcsGlyph
from arib.drcs_decoder import drcs_unpack_to_bitmap


# DRCS drawing support
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


def ass_draw_dialogue(path, p_scale=1, fscx=100, fscy=100, anchor=1):
    r"""
    x,y are the placement in script pixels (video coordinate space).
    We'll use \p<p_scale> and \pos(x,y). Path is in pixel units.
    """
    # Note: \an<1> bottom left anchor
    # colour is \1c, alpha is \1a; border is \bord for optional outline.
    return f"{{\\an{anchor}\\p{p_scale}}}" f"{path}{{\\p0}}"


def ass_draw_drcs_inline(glyph: DrcsGlyph, pad_spaces: int = 0) -> str:
    """
    Emit a DRCS vector drawing that inherits the CURRENT ASS state:
    - inherits \1c (primary color), \1a (alpha), \bord, \\shad, etc.
    - does NOT set \\pos or \an (use surrounding tags if you need them)
    - closes \\p mode so following text renders normally
    - optionally pads with N spaces after the drawing

    Example use (inline):
      "{\\c&H00FF00&}" + ass_draw_drcs_inline(glyph, pad_spaces=0) + "お前たちは"
    """
    bmp = drcs_unpack_to_bitmap(glyph.width, glyph.height, glyph.bitmap, depth=glyph.depth_bits)
    path = bitmap_to_ass_path(bmp, alpha_threshold=1)
    return f"{{\\p1}}{path}{{\\p0}}{' ' * pad_spaces}"


class Pos(object):
    """Screen position in pixels"""

    def __init__(self, x, y):
        self._x = x
        self._y = y

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y


class Size(object):
    """Screen width, height of an area in pixels"""

    def __init__(self, w, h):
        self._w = w
        self._h = h

    @property
    def width(self):
        return self._w

    @property
    def height(self):
        return self._h


class TextSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    NORMAL = "normal"

    def __str__(self):
        return self.value


class TextColor(Enum):
    BLACK = "black"
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    YELLOW = "yellow"
    CYAN = "cyan"
    MAGENTA = "magenta"
    WHITE = "white"

    def __str__(self):
        # Mapping to ASS format BBGGRR
        mapping = {
            "black": "&H000000&",
            "red": "&H0000FF&",
            "green": "&H00FF00&",
            "blue": "&HFF0000&",
            "yellow": "&H00FFFF&",
            "cyan": "&HFFFF00&",
            "magenta": "&HFF00FF&",
            "white": "&HFFFFFF&",
        }
        return mapping[self.value]


def default_text_glyph_width(glyph) -> float:
    return len(glyph.ch) * CLOSED_CAPTION_AREA.text_width(glyph.size)


def drcs_text_glyph_width(glyph) -> float:
    return CLOSED_CAPTION_AREA.text_width(glyph.size)


@dataclass
class TextGlyph:
    ch: str
    color: TextColor
    size: TextSize

    def __init__(self, ch, color, size, width_impl=default_text_glyph_width):
        self.ch = ch
        self.color = color
        self.size = size
        self.width_impl = width_impl


class TextRun:
    def __init__(self, pos: Pos):
        self.items: List[TextGlyph] = []
        self.items = []
        self.pos = copy.copy(pos)
        self.end_pos = copy.copy(pos)
        self.cc_area = CLOSED_CAPTION_AREA

    def add_glyph(self, glyph: TextGlyph):
        self.items.append(glyph)
        glyph_size = glyph.width_impl(glyph)
        self.end_pos._x += glyph_size

    def is_small(self) -> bool:
        return all(g.size == TextSize.SMALL for g in self.items)

    @property
    def UL(self):
        """Return the position in logical pixels of the end of this line.
        This is primarily to support line-wrap, that is lines which extend
        outside the teletext area should be wrapped to a new line.
        """
        return self.end_pos

    def __str__(self):
        """One TextRun represents one line of .ass file Dialog.
        We here only generate the text content. the initial tag and start time
        and end time are added at a higher level of abstraction.
        """
        if not self.items:
            print("WARNING: generating dialog line for empty teletext run.")
            return ""

        x = self.pos.x
        y = self.pos.y
        # .ass files don't allow us to easily get lines of text to "fill up"
        # the correct vertical space, anchor the text using /an4 (midpoint) and positon
        # it as if it "fills up" the row.
        y -= self.cc_area.text_nudge(self.is_small())
        current_text_size = None
        current_text_color = None
        output = ""
        for item in self.items:
            if current_text_color is None or current_text_size is None:
                current_text_size = item.size
                current_text_color = item.color
                # first item, so we emit color and size and pos
                output += (
                    f"{current_text_size},,0000,0000,0000,,{{\\c{current_text_color}}}"
                    f"{{\\pos({x},{y})}}{{\\an4}}"
                )

            if current_text_size != item.size:
                current_text_size = item.size
                output += f"{{\\r{current_text_size}}}{{\\c{current_text_color}}}"

            if current_text_color != item.color:
                current_text_color = item.color
                output += f"{{\\r{current_text_size}}}{{\\c{current_text_color}}}"

            output += item.ch
        output += "\\N\n"
        return output


def rectangles_dialog_union(
    runs: list,
    start_s: float,
    end_s: float,
    *,
    pad_x: int = 0,
    pad_y: int = 0,
    alpha: int = 0x80,  # 0x00 opaque .. 0xFF invisible
    color_bgr: str = "&H000000&",
    style: str = "Default",
    layer: int = 0,
    y_tol: int = 2,  # tolerance to group runs into same row band
) -> str:
    """
    Build a single Dialogue line that draws a set of axis-aligned rectangles
    representing merged background boxes for the given TextRuns. Merges
    horizontally within each row band to avoid overlap (and thus stacking).
    Coordinates are absolute screen pixels.
    """

    def _ass_time(seconds: float) -> str:
        secs = max(0.0, seconds)
        total_cs = int(round(secs * 100))
        cs = total_cs % 100
        total_s = total_cs // 100
        s = total_s % 60
        total_m = total_s // 60
        m = total_m % 60
        h = total_m // 60
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    # 1) Collect rectangles (before merging)
    rects_by_band = {}  # key: (band_y0, band_h) -> list of [x0, x1]
    for run in runs:
        row_h = 30 if run.is_small() else 60
        left = run.pos.x
        right = run.end_pos.x
        if right < left:
            left, right = right, left

        top = run.pos.y - (row_h / 2)
        top -= CLOSED_CAPTION_AREA.text_nudge(run.is_small())
        x0 = int(round(left - pad_x))
        x1 = int(round(right + pad_x))
        y0 = int(round(top - pad_y))
        h = int(round(row_h + 2 * pad_y))

        # Snap y0 to an existing band within tolerance, or create a new band
        chosen_key = None
        for by0, bh in rects_by_band.keys():
            if abs(by0 - y0) <= y_tol and bh == h:
                chosen_key = (by0, bh)
                break
        if chosen_key is None:
            chosen_key = (y0, h)
            rects_by_band[chosen_key] = []
        rects_by_band[chosen_key].append([x0, x1])

    # 2) Merge intervals within each band
    merged_rects = []  # list of (x0, y0, w, h)
    for (y0, h), intervals in rects_by_band.items():
        intervals.sort(key=lambda ab: (ab[0], ab[1]))
        merged = []
        for a, b in intervals:
            if not merged or a > merged[-1][1]:
                merged.append([a, b])
            else:
                merged[-1][1] = max(merged[-1][1], b)
        for a, b in merged:
            merged_rects.append((a, y0, b - a, h))

    if not merged_rects:
        return ""

    # 3) Build one drawing with absolute coords; \pos(0,0) + \an7
    t0 = _ass_time(start_s)
    t1 = _ass_time(end_s)

    tags = (
        f"{{\\an7}}{{\\pos(0,0)}}{{\\p1}}{{\\bord0}}{{\\shad0}}"
        f"{{\\1c{color_bgr}}}{{\\1a&H{alpha:02X}&}}"
    )

    # Multi-rect path; each rect is its own subpath
    path_parts = []
    for x, y, w, h in merged_rects:
        path_parts.append(f"m {x} {y} l {x+w} {y} l {x+w} {y+h} l {x} {y+h} l {x} {y}")

    path = " ".join(path_parts)
    return f"Dialogue: {layer},{t0},{t1},{style},,0,0,0,,{tags}{path}{{\\p0}}\n"


class ClosedCaptionArea(object):
    def __init__(self):
        # these values represent horizontal mode ('7')
        # TODO: make these configurable via CSI
        self._UL = Pos(170, 30)
        self._Dimensions = Size(620, 480)
        self._CharacterDim = Size(36, 36)
        self._char_spacing = 4
        self._line_spacing = 24

    @property
    def UL(self):
        return self._UL

    @property
    def Dimensions(self):
        return self._Dimensions

    def text_nudge(self, is_small: bool):
        if is_small:
            return (self._CharacterDim.height + self._line_spacing) // 4
        else:
            return (self._CharacterDim.height + self._line_spacing) // 2

    def text_width(self, size: TextSize):
        if size == TextSize.NORMAL:
            return self._CharacterDim.width + self._char_spacing
        else:
            return (self._CharacterDim.width + self._char_spacing) // 2

    # A tricky function.
    # Text ROWs are actually "number of line feeds", or zero based.
    # The vertical position is determined by current text size when the
    # position even arrives.
    def RowCol2ScreenPos(self, row, col, size=TextSize.NORMAL):

        cell_w = self._CharacterDim.width
        cell_h = self._CharacterDim.height
        line_space = self._line_spacing
        char_space = self._char_spacing

        # baisc normal text size location.
        # ARIB geometry gives us the lower left text corner, so
        # we add 1 to row.
        x = self.UL.x + col * (cell_w + char_space)
        y = self.UL.y + (row + 1) * (cell_h + line_space)

        if size == TextSize.SMALL:
            x = self.UL.x + col * (cell_w + char_space) * 0.5
            y = self.UL.y + (row + 1) * 0.5 * (cell_h + line_space)
        elif size == TextSize.MEDIUM:
            x = self.UL.x + col * (cell_w + char_space) * 0.5

        return Pos(int(round(x)), int(round(y)))


CLOSED_CAPTION_AREA = ClosedCaptionArea()


class ASSFile(object):
    """Wrapper for a single open utf-8 encoded .ass subtitle file"""

    def __init__(self, filepath, width=960, height=540, show_debug_grid=False):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        try:
            self._f = open(filepath, "w", encoding="utf-8", newline="")
        except Exception as e:
            raise FileOpenError(f"Could not open file {filepath!r} for writing: {e}") from e

        self.write_header(width, height, filepath)
        self.write_styles()
        if show_debug_grid:
            self.write_debug_grid()

    def __del__(self):
        try:
            if self._f:
                self._f.close()
        except AttributeError:
            pass

    def write(self, line):
        """Write indicated string to file. usually a line of dialog."""
        self._f.write(line)

    def write_header(self, width, height, title):
        header = """[Script Info]
; *****************************************************************************
; File generated via arib-ts2ass
; https://github.com/johnoneil/arib
; *****************************************************************************
Title: Japanese Closed Caption Subtitlies
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes
Video Aspect Ratio: 0
Video Zoom: 1
Video Position: 0
Last Style Storage: Default
Video File: {title}

""".format(
            width=width, height=height, title=title
        )
        self._f.write(header)

    def write_styles(self):
        styles = """[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: normal,Noto Sans Mono CJK JP,39,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,0,0,0,0,100,100,4,0,1,1,2,2,10,10,10,0
Style: medium,Noto Sans Mono CJK JP,39,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,0,0,0,0,100,100,2,0,1,1,2,2,10,10,10,0
Style: small,Noto Sans Mono CJK JP,19,&H00FFFFFF,&H000000FF,&H00000000,&H88000000,0,0,0,0,100,100,2,0,1,1,2,2,10,10,10,0


[Events]
"""  # noqa: E501
        self._f.write(styles)

    def write_debug_grid(self):
        debug_grid = generate_debug_screen_grid()
        self._f.write(debug_grid)


def asstime(seconds):
    """format floating point seconds elapsed time to 0:02:14.53"""
    hrs = int(seconds / 3600)
    seconds -= 3600 * hrs
    mins = int(seconds / 60)
    seconds -= 60 * mins
    return f"{hrs:d}:{mins:02d}:{seconds:05.2f}"


def kanji(formatter, k, timestamp):
    formatter.open_file()
    if formatter._current_textsize == TextSize.MEDIUM:
        c = to_halfwidth_katakana_or_punct_char(str(k))
        formatter.add_char(c)
    else:
        formatter.add_char(str(k))


def alphanumeric(formatter, a, timestamp):
    formatter.open_file()
    if formatter._current_textsize == TextSize.MEDIUM:
        c = to_halfwidth_katakana_or_punct_char(str(a))
        formatter.add_char(c)
    else:
        formatter.add_char(str(a))


def hiragana(formatter, h, timestamp):
    formatter.open_file()
    if formatter._current_textsize == TextSize.MEDIUM:
        c = to_halfwidth_katakana_or_punct_char(str(h))
        formatter.add_char(c)
    else:
        formatter.add_char(str(h))


def katakana(formatter, k, timestamp):
    formatter.open_file()
    # In order to use a full width CJK font for medium characters ("half width")
    # we replace katakana with their half-width equivalent if the current font is medium.
    # That may sound a bit confusing, but CJK fonts typically mix half width and full width
    # characters, even in "uniform" width fonts. So this replacement enables us to
    # use a typical CJK font without scaling it to half width for medium.
    if formatter._current_textsize == TextSize.MEDIUM:
        c = to_halfwidth_katakana_or_punct_char(str(k))
        formatter.add_char(c)
    else:
        formatter.add_char(str(k))


def medium(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_textsize = TextSize.MEDIUM


def normal(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_textsize = TextSize.NORMAL


def small(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_textsize = TextSize.SMALL


def space(formatter, k, timestamp):
    formatter.open_file()
    if formatter._current_textsize == TextSize.MEDIUM:
        c = to_halfwidth_katakana_or_punct_char(str(" "))
        formatter.add_char(c)
    else:
        formatter.add_char(" ")


def drcs(formatter, c, timestamp):
    if formatter._disable_drcs:
        formatter.add_char("�")
    else:
        drawing_code = ass_draw_drcs_inline(c.glyph)
        formatter.add_char(drawing_code, size_strategy=drcs_text_glyph_width)


def black(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.BLACK


def red(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.RED


def green(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.GREEN


def yellow(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.YELLOW


def blue(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.BLUE


def magenta(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.MAGENTA


def cyan(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.CYAN


def white(formatter, k, timestamp):
    formatter.open_file()
    formatter._current_text_color = TextColor.WHITE


def position_set(formatter, p, timestamp):
    """Active Position set coordinates are given in character row, column
    So we have to calculate pixel coordinates (and then sale them)
    """
    pos = formatter._CCArea.RowCol2ScreenPos(p.row, p.col, formatter._current_textsize)
    formatter.new_run(pos, formatter._current_textsize)


def active_position_forward(formatter, papf, timestamp):
    """Move the cursor forward n spaces"""
    formatter.position_forward(papf.count, formatter._current_textsize)


a_regex = re.compile(rb'<CS:"(?P<x>\d{1,4});(?P<y>\d{1,4}) a">')


def control_character(formatter, csi, timestamp):
    """This will be the most difficult to format, since the same class here
    can represent so many different commands.
    """
    cmd = csi if isinstance(csi, (bytes, bytearray)) else str(csi).encode("utf-8")
    a_match = a_regex.search(cmd)
    if a_match:
        # APS Control Sequences (absolute positioning of text as <CS: 170;389 a> above
        # indicate the LOWER LEFT HAND CORNER of text position.
        # TODO: this code is very fragile and needs better error handling.
        x = float(a_match.group("x").decode("ascii"))
        y = float(a_match.group("y").decode("ascii"))
        pos = Pos(x, y)
        formatter.new_run(pos, formatter._current_textsize)
        return


pos_regex = r"({\\pos\(\d{1,4},\d{1,4}\)})"


def clear_screen(formatter, cs, timestamp):
    # edge case where no timestamp turned up from the .ts file while parsing it,
    # so we can use the cached end_time of the last subtitle as the start of this one.
    start_time_s = formatter._elapsed_time_s
    end_time_s = timestamp
    if formatter._elapsed_time_s == timestamp:
        start_time_s = formatter._last_end_time_s
        end_time_s = start_time_s + formatter._tmax
    elif timestamp - formatter._elapsed_time_s > formatter._tmax:
        end_time_s = formatter._elapsed_time_s + formatter._tmax

    formatter._elapsed_time_s = timestamp
    formatter._last_end_time_s = end_time_s
    formatter._current_textsize = TextSize.NORMAL
    formatter._current_text_color = TextColor.WHITE

    runs = formatter.get_dialog_text_runs(start_time_s, end_time_s)
    for run in runs:
        if formatter._ass_file:
            formatter._ass_file.write(run)


class ASSFormatter(object):
    DISPLAYED_CC_STATEMENTS = {
        code_set.Kanji: kanji,
        code_set.Alphanumeric: alphanumeric,
        code_set.Hiragana: hiragana,
        code_set.Katakana: katakana,
        control_characters.APS: position_set,  # {\pos(<X>,<Y>)}
        control_characters.MSZ: medium,  # {\rmedium}
        control_characters.NSZ: normal,  # {\rnormal}
        control_characters.SP: space,  #' '
        control_characters.SSZ: small,  # {\rsmall}
        control_characters.CS: clear_screen,
        control_characters.CSI: control_character,  # {\pos(<X>,<Y>)}
        # control_characters.COL,
        control_characters.PAPF: active_position_forward,
        control_characters.BKF: black,  # {\c&H000000&} \c&H<bb><gg><rr>&
        control_characters.RDF: red,  # {\c&H0000ff&}
        control_characters.GRF: green,  # {\c&H00ff00&}
        control_characters.YLF: yellow,  # {\c&H00ffff&}
        control_characters.BLF: blue,  # {\c&Hff0000&}
        control_characters.MGF: magenta,  # {\c&Hff00ff&}
        control_characters.CNF: cyan,  # {\c&Hffff00&}
        control_characters.WHF: white,  # {\c&Hffffff&}
        # largely unhandled DRCS just replaces them with unicode unknown character square
        code_set.DRCS0: drcs,
        code_set.DRCS1: drcs,
        code_set.DRCS2: drcs,
        code_set.DRCS3: drcs,
        code_set.DRCS4: drcs,
        code_set.DRCS5: drcs,
        code_set.DRCS6: drcs,
        code_set.DRCS7: drcs,
        code_set.DRCS8: drcs,
        code_set.DRCS9: drcs,
        code_set.DRCS10: drcs,
        code_set.DRCS11: drcs,
        code_set.DRCS12: drcs,
        code_set.DRCS13: drcs,
        code_set.DRCS14: drcs,
        code_set.DRCS15: drcs,
    }

    def __init__(
        self,
        default_color="white",
        tmax=5,
        width=960,
        height=540,
        video_filename="output.ass",
        verbose=False,
        disable_drcs=False,
        disable_backgrounds=False,
        show_debug_grid=False,
    ):
        """
        :param width: width of target screen in pixels
        :param height: height of target screen in pixels
        :param format_callback: callback method of form <None>callback(string) that
        can be used to dump strings to file upon each subsequent "clear screen" command.
        """
        self._color = default_color
        self._tmax = tmax
        self._CCArea = CLOSED_CAPTION_AREA
        self._pos = Pos(0, 0)
        self._elapsed_time_s = 0.0
        self._last_end_time_s = 0.0
        self._ass_file = None
        self._current_text_color = TextColor.WHITE
        self._current_textsize = TextSize.NORMAL
        self._filename = video_filename
        self._width = width
        self._height = height
        self._height = height
        self._verbose = verbose
        self._disable_drcs = disable_drcs
        self._disable_backgrounds = disable_backgrounds
        self._show_debug_grid = show_debug_grid
        self._accumulated_text_runs: List[TextRun] = []

    def new_run(self, pos, text_size: TextSize):
        # basic normal text size mid-line
        self._accumulated_text_runs.append(TextRun(pos))

    def position_forward(self, n, text_size: TextSize):
        # TODO: for now we'll pad spaces, but we really
        # should start a new run at the location.
        # Note we move n*2 spaces because for CJK fonts ascii spaces are typically
        # half width.
        spaces = " " * (n * 2)
        self.add_char(spaces)

    def add_char(self, ch: str, size_strategy=default_text_glyph_width):
        glyph = TextGlyph(
            ch, self._current_text_color, self._current_textsize, width_impl=size_strategy
        )
        if self._accumulated_text_runs:
            end_pos = self._accumulated_text_runs[-1].end_pos
            # wrap text into a new text run if we're extending outside the CC area.
            # we wrap on 5 pixels to the edge or greater
            if end_pos.x >= self._CCArea._UL.x + self._CCArea._Dimensions.width - 5:
                new_run_pos = Pos(
                    self._CCArea._UL.x,
                    end_pos.y + self._CCArea._CharacterDim.height + self._CCArea._line_spacing,
                )
                self.new_run(new_run_pos, self._current_textsize)

            self._accumulated_text_runs[-1].add_glyph(glyph)

    def get_dialog_text_runs(self, start_time_s, end_time_s):
        start_time = asstime(start_time_s)
        end_time = asstime(end_time_s)
        runs = []
        prefix = f"Dialogue: 1,{start_time},{end_time},"
        for run in self._accumulated_text_runs:
            runs.append(prefix + str(run))
        if not self._disable_backgrounds:
            rectangles = rectangles_dialog_union(
                self._accumulated_text_runs, start_s=start_time_s, end_s=end_time_s
            )
            runs.append(rectangles)
        self._accumulated_text_runs = []
        return runs

    def open_file(self):
        if not self._ass_file:
            if self._verbose:
                print("Found nonempty ARIB closed caption data in file.")
                print("Writing .ass file: " + self._filename)
            self._ass_file = ASSFile(self._filename, show_debug_grid=self._show_debug_grid)

    def file_written(self):
        return self._ass_file is not None

    def format(self, captions, timestamp):
        """Format ARIB closed caption info tinto text for an .ASS file"""

        for c in captions:
            if type(c) in ASSFormatter.DISPLAYED_CC_STATEMENTS:
                # invoke the handler for this object type
                ASSFormatter.DISPLAYED_CC_STATEMENTS[type(c)](self, c, timestamp)
            else:
                # TODO: Warning of unhandled characters
                pass
                # print str(type(c))


# Katakana base -> Halfwidth
KATA_BASE_TO_HALF = {
    "ア": "ｱ",
    "イ": "ｲ",
    "ウ": "ｳ",
    "エ": "ｴ",
    "オ": "ｵ",
    "カ": "ｶ",
    "キ": "ｷ",
    "ク": "ｸ",
    "ケ": "ｹ",
    "コ": "ｺ",
    "サ": "ｻ",
    "シ": "ｼ",
    "ス": "ｽ",
    "セ": "ｾ",
    "ソ": "ｿ",
    "タ": "ﾀ",
    "チ": "ﾁ",
    "ツ": "ﾂ",
    "テ": "ﾃ",
    "ト": "ﾄ",
    "ナ": "ﾅ",
    "ニ": "ﾆ",
    "ヌ": "ﾇ",
    "ネ": "ﾈ",
    "ノ": "ﾉ",
    "ハ": "ﾊ",
    "ヒ": "ﾋ",
    "フ": "ﾌ",
    "ヘ": "ﾍ",
    "ホ": "ﾎ",
    "マ": "ﾏ",
    "ミ": "ﾐ",
    "ム": "ﾑ",
    "メ": "ﾒ",
    "モ": "ﾓ",
    "ヤ": "ﾔ",
    "ユ": "ﾕ",
    "ヨ": "ﾖ",
    "ラ": "ﾗ",
    "リ": "ﾘ",
    "ル": "ﾙ",
    "レ": "ﾚ",
    "ロ": "ﾛ",
    "ワ": "ﾜ",
    "ヲ": "ｦ",
    "ン": "ﾝ",
    # small kana
    "ァ": "ｧ",
    "ィ": "ｨ",
    "ゥ": "ｩ",
    "ェ": "ｪ",
    "ォ": "ｫ",
    "ャ": "ｬ",
    "ュ": "ｭ",
    "ョ": "ｮ",
    "ッ": "ｯ",
    # prolonged sound
    "ー": "ｰ",
    # middle dot (full → half handled below too)
    "・": "･",
    # Vu base (dakuten added separately)
    "ヴ": "ｳ",
    # small ka/ke
    "ヵ": "ｶ",
    "ヶ": "ｹ",
}

# Full-width CJK punctuation -> Half-width
FULL_PUNCT_TO_HALF = {
    "。": "｡",  # U+3002 -> U+FF61
    "、": "､",  # U+3001 -> U+FF64
    "・": "･",  # U+30FB -> U+FF65
    "「": "｢",  # U+300C -> U+FF62
    "」": "｣",  # U+300D -> U+FF63
    "ー": "ｰ",  # already in KATA map; here for completeness
    "　": " ",  # ideographic space -> ASCII space
    "（": "(",
    "）": ")",
}

COMBINING_DAKUTEN = "\u3099"  # ゙
COMBINING_HANDAKUTEN = "\u309A"  # ゚


def to_halfwidth_katakana_or_punct_char(ch: str) -> str:
    """Return half-width version for full-width Katakana/punct/space; else original.
    Voiced/semi-voiced kana become halfwidth base + combining dakuten/handakuten."""
    if not ch:
        return ch

    code = ord(ch)
    # Already halfwidth block? leave as-is
    if 0xFF61 <= code <= 0xFF9F:
        return ch

    # Direct punctuation/space mapping first
    if ch in FULL_PUNCT_TO_HALF:
        return FULL_PUNCT_TO_HALF[ch]

    # Decompose to split dakuten/handakuten (e.g., ガ -> カ + ゙)
    decomp = unicodedata.normalize("NFD", ch)
    base = decomp[0]
    accents = "".join(c for c in decomp[1:] if c in (COMBINING_DAKUTEN, COMBINING_HANDAKUTEN))

    mapped = KATA_BASE_TO_HALF.get(base)
    return (mapped + accents) if mapped is not None else ch


def generate_debug_screen_grid():
    """
    Emit .ass code for a standard arib character grid.
    This is meant to help debugging character positioning onscreen.
    """
    return """Dialogue: 0,0:00:00.00,2:00:00.00,normal,,0,0,0,,{\\an7\\pos(170,30)\\p1\\shad0\\1a&HFF&\\3a&H00&\\bord1.2\\3c&H00FFFF&}m 0 0 l 620 0 m 620 0 l 620 480 m 620 480 l 0 480 m 0 480 l 0 0 m 0 60 l 620 60 m 0 120 l 620 120 m 0 180 l 620 180 m 0 240 l 620 240 m 0 300 l 620 300 m 0 360 l 620 360 m 0 420 l 620 420 m 40 0 l 40 480 m 80 0 l 80 480 m 120 0 l 120 480 m 160 0 l 160 480 m 200 0 l 200 480 m 240 0 l 240 480 m 280 0 l 280 480 m 320 0 l 320 480 m 360 0 l 360 480 m 400 0 l 400 480 m 440 0 l 440 480 m 480 0 l 480 480 m 520 0 l 520 480 m 560 0 l 560 480 m 600 0 l 600 480 {\\p0}
Dialogue: 0,0:00:00.00,2:00:00.00,normal,,0,0,0,,{\\an7\\pos(170,30)\\p1\\shad0\\1a&HFF&\\3a&H00&\\bord0.6\\3c&H808080&}m 0 30 l 6 30 m 12 30 l 18 30 m 24 30 l 30 30 m 36 30 l 42 30 m 48 30 l 54 30 m 60 30 l 66 30 m 72 30 l 78 30 m 84 30 l 90 30 m 96 30 l 102 30 m 108 30 l 114 30 m 120 30 l 126 30 m 132 30 l 138 30 m 144 30 l 150 30 m 156 30 l 162 30 m 168 30 l 174 30 m 180 30 l 186 30 m 192 30 l 198 30 m 204 30 l 210 30 m 216 30 l 222 30 m 228 30 l 234 30 m 240 30 l 246 30 m 252 30 l 258 30 m 264 30 l 270 30 m 276 30 l 282 30 m 288 30 l 294 30 m 300 30 l 306 30 m 312 30 l 318 30 m 324 30 l 330 30 m 336 30 l 342 30 m 348 30 l 354 30 m 360 30 l 366 30 m 372 30 l 378 30 m 384 30 l 390 30 m 396 30 l 402 30 m 408 30 l 414 30 m 420 30 l 426 30 m 432 30 l 438 30 m 444 30 l 450 30 m 456 30 l 462 30 m 468 30 l 474 30 m 480 30 l 486 30 m 492 30 l 498 30 m 504 30 l 510 30 m 516 30 l 522 30 m 528 30 l 534 30 m 540 30 l 546 30 m 552 30 l 558 30 m 564 30 l 570 30 m 576 30 l 582 30 m 588 30 l 594 30 m 600 30 l 606 30 m 612 30 l 618 30 m 0 90 l 6 90 m 12 90 l 18 90 m 24 90 l 30 90 m 36 90 l 42 90 m 48 90 l 54 90 m 60 90 l 66 90 m 72 90 l 78 90 m 84 90 l 90 90 m 96 90 l 102 90 m 108 90 l 114 90 m 120 90 l 126 90 m 132 90 l 138 90 m 144 90 l 150 90 m 156 90 l 162 90 m 168 90 l 174 90 m 180 90 l 186 90 m 192 90 l 198 90 m 204 90 l 210 90 m 216 90 l 222 90 m 228 90 l 234 90 m 240 90 l 246 90 m 252 90 l 258 90 m 264 90 l 270 90 m 276 90 l 282 90 m 288 90 l 294 90 m 300 90 l 306 90 m 312 90 l 318 90 m 324 90 l 330 90 m 336 90 l 342 90 m 348 90 l 354 90 m 360 90 l 366 90 m 372 90 l 378 90 m 384 90 l 390 90 m 396 90 l 402 90 m 408 90 l 414 90 m 420 90 l 426 90 m 432 90 l 438 90 m 444 90 l 450 90 m 456 90 l 462 90 m 468 90 l 474 90 m 480 90 l 486 90 m 492 90 l 498 90 m 504 90 l 510 90 m 516 90 l 522 90 m 528 90 l 534 90 m 540 90 l 546 90 m 552 90 l 558 90 m 564 90 l 570 90 m 576 90 l 582 90 m 588 90 l 594 90 m 600 90 l 606 90 m 612 90 l 618 90 m 0 150 l 6 150 m 12 150 l 18 150 m 24 150 l 30 150 m 36 150 l 42 150 m 48 150 l 54 150 m 60 150 l 66 150 m 72 150 l 78 150 m 84 150 l 90 150 m 96 150 l 102 150 m 108 150 l 114 150 m 120 150 l 126 150 m 132 150 l 138 150 m 144 150 l 150 150 m 156 150 l 162 150 m 168 150 l 174 150 m 180 150 l 186 150 m 192 150 l 198 150 m 204 150 l 210 150 m 216 150 l 222 150 m 228 150 l 234 150 m 240 150 l 246 150 m 252 150 l 258 150 m 264 150 l 270 150 m 276 150 l 282 150 m 288 150 l 294 150 m 300 150 l 306 150 m 312 150 l 318 150 m 324 150 l 330 150 m 336 150 l 342 150 m 348 150 l 354 150 m 360 150 l 366 150 m 372 150 l 378 150 m 384 150 l 390 150 m 396 150 l 402 150 m 408 150 l 414 150 m 420 150 l 426 150 m 432 150 l 438 150 m 444 150 l 450 150 m 456 150 l 462 150 m 468 150 l 474 150 m 480 150 l 486 150 m 492 150 l 498 150 m 504 150 l 510 150 m 516 150 l 522 150 m 528 150 l 534 150 m 540 150 l 546 150 m 552 150 l 558 150 m 564 150 l 570 150 m 576 150 l 582 150 m 588 150 l 594 150 m 600 150 l 606 150 m 612 150 l 618 150 m 0 210 l 6 210 m 12 210 l 18 210 m 24 210 l 30 210 m 36 210 l 42 210 m 48 210 l 54 210 m 60 210 l 66 210 m 72 210 l 78 210 m 84 210 l 90 210 m 96 210 l 102 210 m 108 210 l 114 210 m 120 210 l 126 210 m 132 210 l 138 210 m 144 210 l 150 210 m 156 210 l 162 210 m 168 210 l 174 210 m 180 210 l 186 210 m 192 210 l 198 210 m 204 210 l 210 210 m 216 210 l 222 210 m 228 210 l 234 210 m 240 210 l 246 210 m 252 210 l 258 210 m 264 210 l 270 210 m 276 210 l 282 210 m 288 210 l 294 210 m 300 210 l 306 210 m 312 210 l 318 210 m 324 210 l 330 210 m 336 210 l 342 210 m 348 210 l 354 210 m 360 210 l 366 210 m 372 210 l 378 210 m 384 210 l 390 210 m 396 210 l 402 210 m 408 210 l 414 210 m 420 210 l 426 210 m 432 210 l 438 210 m 444 210 l 450 210 m 456 210 l 462 210 m 468 210 l 474 210 m 480 210 l 486 210 m 492 210 l 498 210 m 504 210 l 510 210 m 516 210 l 522 210 m 528 210 l 534 210 m 540 210 l 546 210 m 552 210 l 558 210 m 564 210 l 570 210 m 576 210 l 582 210 m 588 210 l 594 210 m 600 210 l 606 210 m 612 210 l 618 210 m 0 270 l 6 270 m 12 270 l 18 270 m 24 270 l 30 270 m 36 270 l 42 270 m 48 270 l 54 270 m 60 270 l 66 270 m 72 270 l 78 270 m 84 270 l 90 270 m 96 270 l 102 270 m 108 270 l 114 270 m 120 270 l 126 270 m 132 270 l 138 270 m 144 270 l 150 270 m 156 270 l 162 270 m 168 270 l 174 270 m 180 270 l 186 270 m 192 270 l 198 270 m 204 270 l 210 270 m 216 270 l 222 270 m 228 270 l 234 270 m 240 270 l 246 270 m 252 270 l 258 270 m 264 270 l 270 270 m 276 270 l 282 270 m 288 270 l 294 270 m 300 270 l 306 270 m 312 270 l 318 270 m 324 270 l 330 270 m 336 270 l 342 270 m 348 270 l 354 270 m 360 270 l 366 270 m 372 270 l 378 270 m 384 270 l 390 270 m 396 270 l 402 270 m 408 270 l 414 270 m 420 270 l 426 270 m 432 270 l 438 270 m 444 270 l 450 270 m 456 270 l 462 270 m 468 270 l 474 270 m 480 270 l 486 270 m 492 270 l 498 270 m 504 270 l 510 270 m 516 270 l 522 270 m 528 270 l 534 270 m 540 270 l 546 270 m 552 270 l 558 270 m 564 270 l 570 270 m 576 270 l 582 270 m 588 270 l 594 270 m 600 270 l 606 270 m 612 270 l 618 270 m 0 330 l 6 330 m 12 330 l 18 330 m 24 330 l 30 330 m 36 330 l 42 330 m 48 330 l 54 330 m 60 330 l 66 330 m 72 330 l 78 330 m 84 330 l 90 330 m 96 330 l 102 330 m 108 330 l 114 330 m 120 330 l 126 330 m 132 330 l 138 330 m 144 330 l 150 330 m 156 330 l 162 330 m 168 330 l 174 330 m 180 330 l 186 330 m 192 330 l 198 330 m 204 330 l 210 330 m 216 330 l 222 330 m 228 330 l 234 330 m 240 330 l 246 330 m 252 330 l 258 330 m 264 330 l 270 330 m 276 330 l 282 330 m 288 330 l 294 330 m 300 330 l 306 330 m 312 330 l 318 330 m 324 330 l 330 330 m 336 330 l 342 330 m 348 330 l 354 330 m 360 330 l 366 330 m 372 330 l 378 330 m 384 330 l 390 330 m 396 330 l 402 330 m 408 330 l 414 330 m 420 330 l 426 330 m 432 330 l 438 330 m 444 330 l 450 330 m 456 330 l 462 330 m 468 330 l 474 330 m 480 330 l 486 330 m 492 330 l 498 330 m 504 330 l 510 330 m 516 330 l 522 330 m 528 330 l 534 330 m 540 330 l 546 330 m 552 330 l 558 330 m 564 330 l 570 330 m 576 330 l 582 330 m 588 330 l 594 330 m 600 330 l 606 330 m 612 330 l 618 330 m 0 390 l 6 390 m 12 390 l 18 390 m 24 390 l 30 390 m 36 390 l 42 390 m 48 390 l 54 390 m 60 390 l 66 390 m 72 390 l 78 390 m 84 390 l 90 390 m 96 390 l 102 390 m 108 390 l 114 390 m 120 390 l 126 390 m 132 390 l 138 390 m 144 390 l 150 390 m 156 390 l 162 390 m 168 390 l 174 390 m 180 390 l 186 390 m 192 390 l 198 390 m 204 390 l 210 390 m 216 390 l 222 390 m 228 390 l 234 390 m 240 390 l 246 390 m 252 390 l 258 390 m 264 390 l 270 390 m 276 390 l 282 390 m 288 390 l 294 390 m 300 390 l 306 390 m 312 390 l 318 390 m 324 390 l 330 390 m 336 390 l 342 390 m 348 390 l 354 390 m 360 390 l 366 390 m 372 390 l 378 390 m 384 390 l 390 390 m 396 390 l 402 390 m 408 390 l 414 390 m 420 390 l 426 390 m 432 390 l 438 390 m 444 390 l 450 390 m 456 390 l 462 390 m 468 390 l 474 390 m 480 390 l 486 390 m 492 390 l 498 390 m 504 390 l 510 390 m 516 390 l 522 390 m 528 390 l 534 390 m 540 390 l 546 390 m 552 390 l 558 390 m 564 390 l 570 390 m 576 390 l 582 390 m 588 390 l 594 390 m 600 390 l 606 390 m 612 390 l 618 390 m 0 450 l 6 450 m 12 450 l 18 450 m 24 450 l 30 450 m 36 450 l 42 450 m 48 450 l 54 450 m 60 450 l 66 450 m 72 450 l 78 450 m 84 450 l 90 450 m 96 450 l 102 450 m 108 450 l 114 450 m 120 450 l 126 450 m 132 450 l 138 450 m 144 450 l 150 450 m 156 450 l 162 450 m 168 450 l 174 450 m 180 450 l 186 450 m 192 450 l 198 450 m 204 450 l 210 450 m 216 450 l 222 450 m 228 450 l 234 450 m 240 450 l 246 450 m 252 450 l 258 450 m 264 450 l 270 450 m 276 450 l 282 450 m 288 450 l 294 450 m 300 450 l 306 450 m 312 450 l 318 450 m 324 450 l 330 450 m 336 450 l 342 450 m 348 450 l 354 450 m 360 450 l 366 450 m 372 450 l 378 450 m 384 450 l 390 450 m 396 450 l 402 450 m 408 450 l 414 450 m 420 450 l 426 450 m 432 450 l 438 450 m 444 450 l 450 450 m 456 450 l 462 450 m 468 450 l 474 450 m 480 450 l 486 450 m 492 450 l 498 450 m 504 450 l 510 450 m 516 450 l 522 450 m 528 450 l 534 450 m 540 450 l 546 450 m 552 450 l 558 450 m 564 450 l 570 450 m 576 450 l 582 450 m 588 450 l 594 450 m 600 450 l 606 450 m 612 450 l 618 450 m 20 0 l 20 6 m 20 12 l 20 18 m 20 24 l 20 30 m 20 36 l 20 42 m 20 48 l 20 54 m 20 60 l 20 66 m 20 72 l 20 78 m 20 84 l 20 90 m 20 96 l 20 102 m 20 108 l 20 114 m 20 120 l 20 126 m 20 132 l 20 138 m 20 144 l 20 150 m 20 156 l 20 162 m 20 168 l 20 174 m 20 180 l 20 186 m 20 192 l 20 198 m 20 204 l 20 210 m 20 216 l 20 222 m 20 228 l 20 234 m 20 240 l 20 246 m 20 252 l 20 258 m 20 264 l 20 270 m 20 276 l 20 282 m 20 288 l 20 294 m 20 300 l 20 306 m 20 312 l 20 318 m 20 324 l 20 330 m 20 336 l 20 342 m 20 348 l 20 354 m 20 360 l 20 366 m 20 372 l 20 378 m 20 384 l 20 390 m 20 396 l 20 402 m 20 408 l 20 414 m 20 420 l 20 426 m 20 432 l 20 438 m 20 444 l 20 450 m 20 456 l 20 462 m 20 468 l 20 474 m 60 0 l 60 6 m 60 12 l 60 18 m 60 24 l 60 30 m 60 36 l 60 42 m 60 48 l 60 54 m 60 60 l 60 66 m 60 72 l 60 78 m 60 84 l 60 90 m 60 96 l 60 102 m 60 108 l 60 114 m 60 120 l 60 126 m 60 132 l 60 138 m 60 144 l 60 150 m 60 156 l 60 162 m 60 168 l 60 174 m 60 180 l 60 186 m 60 192 l 60 198 m 60 204 l 60 210 m 60 216 l 60 222 m 60 228 l 60 234 m 60 240 l 60 246 m 60 252 l 60 258 m 60 264 l 60 270 m 60 276 l 60 282 m 60 288 l 60 294 m 60 300 l 60 306 m 60 312 l 60 318 m 60 324 l 60 330 m 60 336 l 60 342 m 60 348 l 60 354 m 60 360 l 60 366 m 60 372 l 60 378 m 60 384 l 60 390 m 60 396 l 60 402 m 60 408 l 60 414 m 60 420 l 60 426 m 60 432 l 60 438 m 60 444 l 60 450 m 60 456 l 60 462 m 60 468 l 60 474 m 100 0 l 100 6 m 100 12 l 100 18 m 100 24 l 100 30 m 100 36 l 100 42 m 100 48 l 100 54 m 100 60 l 100 66 m 100 72 l 100 78 m 100 84 l 100 90 m 100 96 l 100 102 m 100 108 l 100 114 m 100 120 l 100 126 m 100 132 l 100 138 m 100 144 l 100 150 m 100 156 l 100 162 m 100 168 l 100 174 m 100 180 l 100 186 m 100 192 l 100 198 m 100 204 l 100 210 m 100 216 l 100 222 m 100 228 l 100 234 m 100 240 l 100 246 m 100 252 l 100 258 m 100 264 l 100 270 m 100 276 l 100 282 m 100 288 l 100 294 m 100 300 l 100 306 m 100 312 l 100 318 m 100 324 l 100 330 m 100 336 l 100 342 m 100 348 l 100 354 m 100 360 l 100 366 m 100 372 l 100 378 m 100 384 l 100 390 m 100 396 l 100 402 m 100 408 l 100 414 m 100 420 l 100 426 m 100 432 l 100 438 m 100 444 l 100 450 m 100 456 l 100 462 m 100 468 l 100 474 m 140 0 l 140 6 m 140 12 l 140 18 m 140 24 l 140 30 m 140 36 l 140 42 m 140 48 l 140 54 m 140 60 l 140 66 m 140 72 l 140 78 m 140 84 l 140 90 m 140 96 l 140 102 m 140 108 l 140 114 m 140 120 l 140 126 m 140 132 l 140 138 m 140 144 l 140 150 m 140 156 l 140 162 m 140 168 l 140 174 m 140 180 l 140 186 m 140 192 l 140 198 m 140 204 l 140 210 m 140 216 l 140 222 m 140 228 l 140 234 m 140 240 l 140 246 m 140 252 l 140 258 m 140 264 l 140 270 m 140 276 l 140 282 m 140 288 l 140 294 m 140 300 l 140 306 m 140 312 l 140 318 m 140 324 l 140 330 m 140 336 l 140 342 m 140 348 l 140 354 m 140 360 l 140 366 m 140 372 l 140 378 m 140 384 l 140 390 m 140 396 l 140 402 m 140 408 l 140 414 m 140 420 l 140 426 m 140 432 l 140 438 m 140 444 l 140 450 m 140 456 l 140 462 m 140 468 l 140 474 m 180 0 l 180 6 m 180 12 l 180 18 m 180 24 l 180 30 m 180 36 l 180 42 m 180 48 l 180 54 m 180 60 l 180 66 m 180 72 l 180 78 m 180 84 l 180 90 m 180 96 l 180 102 m 180 108 l 180 114 m 180 120 l 180 126 m 180 132 l 180 138 m 180 144 l 180 150 m 180 156 l 180 162 m 180 168 l 180 174 m 180 180 l 180 186 m 180 192 l 180 198 m 180 204 l 180 210 m 180 216 l 180 222 m 180 228 l 180 234 m 180 240 l 180 246 m 180 252 l 180 258 m 180 264 l 180 270 m 180 276 l 180 282 m 180 288 l 180 294 m 180 300 l 180 306 m 180 312 l 180 318 m 180 324 l 180 330 m 180 336 l 180 342 m 180 348 l 180 354 m 180 360 l 180 366 m 180 372 l 180 378 m 180 384 l 180 390 m 180 396 l 180 402 m 180 408 l 180 414 m 180 420 l 180 426 m 180 432 l 180 438 m 180 444 l 180 450 m 180 456 l 180 462 m 180 468 l 180 474 m 220 0 l 220 6 m 220 12 l 220 18 m 220 24 l 220 30 m 220 36 l 220 42 m 220 48 l 220 54 m 220 60 l 220 66 m 220 72 l 220 78 m 220 84 l 220 90 m 220 96 l 220 102 m 220 108 l 220 114 m 220 120 l 220 126 m 220 132 l 220 138 m 220 144 l 220 150 m 220 156 l 220 162 m 220 168 l 220 174 m 220 180 l 220 186 m 220 192 l 220 198 m 220 204 l 220 210 m 220 216 l 220 222 m 220 228 l 220 234 m 220 240 l 220 246 m 220 252 l 220 258 m 220 264 l 220 270 m 220 276 l 220 282 m 220 288 l 220 294 m 220 300 l 220 306 m 220 312 l 220 318 m 220 324 l 220 330 m 220 336 l 220 342 m 220 348 l 220 354 m 220 360 l 220 366 m 220 372 l 220 378 m 220 384 l 220 390 m 220 396 l 220 402 m 220 408 l 220 414 m 220 420 l 220 426 m 220 432 l 220 438 m 220 444 l 220 450 m 220 456 l 220 462 m 220 468 l 220 474 m 260 0 l 260 6 m 260 12 l 260 18 m 260 24 l 260 30 m 260 36 l 260 42 m 260 48 l 260 54 m 260 60 l 260 66 m 260 72 l 260 78 m 260 84 l 260 90 m 260 96 l 260 102 m 260 108 l 260 114 m 260 120 l 260 126 m 260 132 l 260 138 m 260 144 l 260 150 m 260 156 l 260 162 m 260 168 l 260 174 m 260 180 l 260 186 m 260 192 l 260 198 m 260 204 l 260 210 m 260 216 l 260 222 m 260 228 l 260 234 m 260 240 l 260 246 m 260 252 l 260 258 m 260 264 l 260 270 m 260 276 l 260 282 m 260 288 l 260 294 m 260 300 l 260 306 m 260 312 l 260 318 m 260 324 l 260 330 m 260 336 l 260 342 m 260 348 l 260 354 m 260 360 l 260 366 m 260 372 l 260 378 m 260 384 l 260 390 m 260 396 l 260 402 m 260 408 l 260 414 m 260 420 l 260 426 m 260 432 l 260 438 m 260 444 l 260 450 m 260 456 l 260 462 m 260 468 l 260 474 m 300 0 l 300 6 m 300 12 l 300 18 m 300 24 l 300 30 m 300 36 l 300 42 m 300 48 l 300 54 m 300 60 l 300 66 m 300 72 l 300 78 m 300 84 l 300 90 m 300 96 l 300 102 m 300 108 l 300 114 m 300 120 l 300 126 m 300 132 l 300 138 m 300 144 l 300 150 m 300 156 l 300 162 m 300 168 l 300 174 m 300 180 l 300 186 m 300 192 l 300 198 m 300 204 l 300 210 m 300 216 l 300 222 m 300 228 l 300 234 m 300 240 l 300 246 m 300 252 l 300 258 m 300 264 l 300 270 m 300 276 l 300 282 m 300 288 l 300 294 m 300 300 l 300 306 m 300 312 l 300 318 m 300 324 l 300 330 m 300 336 l 300 342 m 300 348 l 300 354 m 300 360 l 300 366 m 300 372 l 300 378 m 300 384 l 300 390 m 300 396 l 300 402 m 300 408 l 300 414 m 300 420 l 300 426 m 300 432 l 300 438 m 300 444 l 300 450 m 300 456 l 300 462 m 300 468 l 300 474 m 340 0 l 340 6 m 340 12 l 340 18 m 340 24 l 340 30 m 340 36 l 340 42 m 340 48 l 340 54 m 340 60 l 340 66 m 340 72 l 340 78 m 340 84 l 340 90 m 340 96 l 340 102 m 340 108 l 340 114 m 340 120 l 340 126 m 340 132 l 340 138 m 340 144 l 340 150 m 340 156 l 340 162 m 340 168 l 340 174 m 340 180 l 340 186 m 340 192 l 340 198 m 340 204 l 340 210 m 340 216 l 340 222 m 340 228 l 340 234 m 340 240 l 340 246 m 340 252 l 340 258 m 340 264 l 340 270 m 340 276 l 340 282 m 340 288 l 340 294 m 340 300 l 340 306 m 340 312 l 340 318 m 340 324 l 340 330 m 340 336 l 340 342 m 340 348 l 340 354 m 340 360 l 340 366 m 340 372 l 340 378 m 340 384 l 340 390 m 340 396 l 340 402 m 340 408 l 340 414 m 340 420 l 340 426 m 340 432 l 340 438 m 340 444 l 340 450 m 340 456 l 340 462 m 340 468 l 340 474 m 380 0 l 380 6 m 380 12 l 380 18 m 380 24 l 380 30 m 380 36 l 380 42 m 380 48 l 380 54 m 380 60 l 380 66 m 380 72 l 380 78 m 380 84 l 380 90 m 380 96 l 380 102 m 380 108 l 380 114 m 380 120 l 380 126 m 380 132 l 380 138 m 380 144 l 380 150 m 380 156 l 380 162 m 380 168 l 380 174 m 380 180 l 380 186 m 380 192 l 380 198 m 380 204 l 380 210 m 380 216 l 380 222 m 380 228 l 380 234 m 380 240 l 380 246 m 380 252 l 380 258 m 380 264 l 380 270 m 380 276 l 380 282 m 380 288 l 380 294 m 380 300 l 380 306 m 380 312 l 380 318 m 380 324 l 380 330 m 380 336 l 380 342 m 380 348 l 380 354 m 380 360 l 380 366 m 380 372 l 380 378 m 380 384 l 380 390 m 380 396 l 380 402 m 380 408 l 380 414 m 380 420 l 380 426 m 380 432 l 380 438 m 380 444 l 380 450 m 380 456 l 380 462 m 380 468 l 380 474 m 420 0 l 420 6 m 420 12 l 420 18 m 420 24 l 420 30 m 420 36 l 420 42 m 420 48 l 420 54 m 420 60 l 420 66 m 420 72 l 420 78 m 420 84 l 420 90 m 420 96 l 420 102 m 420 108 l 420 114 m 420 120 l 420 126 m 420 132 l 420 138 m 420 144 l 420 150 m 420 156 l 420 162 m 420 168 l 420 174 m 420 180 l 420 186 m 420 192 l 420 198 m 420 204 l 420 210 m 420 216 l 420 222 m 420 228 l 420 234 m 420 240 l 420 246 m 420 252 l 420 258 m 420 264 l 420 270 m 420 276 l 420 282 m 420 288 l 420 294 m 420 300 l 420 306 m 420 312 l 420 318 m 420 324 l 420 330 m 420 336 l 420 342 m 420 348 l 420 354 m 420 360 l 420 366 m 420 372 l 420 378 m 420 384 l 420 390 m 420 396 l 420 402 m 420 408 l 420 414 m 420 420 l 420 426 m 420 432 l 420 438 m 420 444 l 420 450 m 420 456 l 420 462 m 420 468 l 420 474 m 460 0 l 460 6 m 460 12 l 460 18 m 460 24 l 460 30 m 460 36 l 460 42 m 460 48 l 460 54 m 460 60 l 460 66 m 460 72 l 460 78 m 460 84 l 460 90 m 460 96 l 460 102 m 460 108 l 460 114 m 460 120 l 460 126 m 460 132 l 460 138 m 460 144 l 460 150 m 460 156 l 460 162 m 460 168 l 460 174 m 460 180 l 460 186 m 460 192 l 460 198 m 460 204 l 460 210 m 460 216 l 460 222 m 460 228 l 460 234 m 460 240 l 460 246 m 460 252 l 460 258 m 460 264 l 460 270 m 460 276 l 460 282 m 460 288 l 460 294 m 460 300 l 460 306 m 460 312 l 460 318 m 460 324 l 460 330 m 460 336 l 460 342 m 460 348 l 460 354 m 460 360 l 460 366 m 460 372 l 460 378 m 460 384 l 460 390 m 460 396 l 460 402 m 460 408 l 460 414 m 460 420 l 460 426 m 460 432 l 460 438 m 460 444 l 460 450 m 460 456 l 460 462 m 460 468 l 460 474 m 500 0 l 500 6 m 500 12 l 500 18 m 500 24 l 500 30 m 500 36 l 500 42 m 500 48 l 500 54 m 500 60 l 500 66 m 500 72 l 500 78 m 500 84 l 500 90 m 500 96 l 500 102 m 500 108 l 500 114 m 500 120 l 500 126 m 500 132 l 500 138 m 500 144 l 500 150 m 500 156 l 500 162 m 500 168 l 500 174 m 500 180 l 500 186 m 500 192 l 500 198 m 500 204 l 500 210 m 500 216 l 500 222 m 500 228 l 500 234 m 500 240 l 500 246 m 500 252 l 500 258 m 500 264 l 500 270 m 500 276 l 500 282 m 500 288 l 500 294 m 500 300 l 500 306 m 500 312 l 500 318 m 500 324 l 500 330 m 500 336 l 500 342 m 500 348 l 500 354 m 500 360 l 500 366 m 500 372 l 500 378 m 500 384 l 500 390 m 500 396 l 500 402 m 500 408 l 500 414 m 500 420 l 500 426 m 500 432 l 500 438 m 500 444 l 500 450 m 500 456 l 500 462 m 500 468 l 500 474 m 540 0 l 540 6 m 540 12 l 540 18 m 540 24 l 540 30 m 540 36 l 540 42 m 540 48 l 540 54 m 540 60 l 540 66 m 540 72 l 540 78 m 540 84 l 540 90 m 540 96 l 540 102 m 540 108 l 540 114 m 540 120 l 540 126 m 540 132 l 540 138 m 540 144 l 540 150 m 540 156 l 540 162 m 540 168 l 540 174 m 540 180 l 540 186 m 540 192 l 540 198 m 540 204 l 540 210 m 540 216 l 540 222 m 540 228 l 540 234 m 540 240 l 540 246 m 540 252 l 540 258 m 540 264 l 540 270 m 540 276 l 540 282 m 540 288 l 540 294 m 540 300 l 540 306 m 540 312 l 540 318 m 540 324 l 540 330 m 540 336 l 540 342 m 540 348 l 540 354 m 540 360 l 540 366 m 540 372 l 540 378 m 540 384 l 540 390 m 540 396 l 540 402 m 540 408 l 540 414 m 540 420 l 540 426 m 540 432 l 540 438 m 540 444 l 540 450 m 540 456 l 540 462 m 540 468 l 540 474 m 580 0 l 580 6 m 580 12 l 580 18 m 580 24 l 580 30 m 580 36 l 580 42 m 580 48 l 580 54 m 580 60 l 580 66 m 580 72 l 580 78 m 580 84 l 580 90 m 580 96 l 580 102 m 580 108 l 580 114 m 580 120 l 580 126 m 580 132 l 580 138 m 580 144 l 580 150 m 580 156 l 580 162 m 580 168 l 580 174 m 580 180 l 580 186 m 580 192 l 580 198 m 580 204 l 580 210 m 580 216 l 580 222 m 580 228 l 580 234 m 580 240 l 580 246 m 580 252 l 580 258 m 580 264 l 580 270 m 580 276 l 580 282 m 580 288 l 580 294 m 580 300 l 580 306 m 580 312 l 580 318 m 580 324 l 580 330 m 580 336 l 580 342 m 580 348 l 580 354 m 580 360 l 580 366 m 580 372 l 580 378 m 580 384 l 580 390 m 580 396 l 580 402 m 580 408 l 580 414 m 580 420 l 580 426 m 580 432 l 580 438 m 580 444 l 580 450 m 580 456 l 580 462 m 580 468 l 580 474 {\\p0}
"""  # noqa: E501
