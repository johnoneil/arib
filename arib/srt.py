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
from pathlib import Path
from enum import Enum
import copy
from dataclasses import dataclass
from typing import List
import unicodedata
import arib.code_set as code_set
import arib.control_characters as control_characters
import re
from arib.arib_exceptions import FileOpenError


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
    if glyph.size == TextSize.NORMAL:
        return len(glyph.ch) * (36 + 4)
    else:
        # medium and small text are half width
        return len(glyph.ch) * (36 + 4) / 2.0


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

        run_is_small = self.is_small()
        x = self.pos.x
        y = self.pos.y
        # HACK: .ass files don't allow us to easily get lines of text to "fill up"
        # the correct vertical space, anchor the text using /an4 (midpoint) and positon
        # it as if it "fills up" the row.
        if run_is_small:
            y -= (36 + 24) / 4
        else:
            y -= (36 + 24) / 2
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
    formatter.add_char("�")


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
    start_time = asstime(start_time_s)
    end_time = asstime(end_time_s)
    runs = formatter.get_dialog_text_runs(start_time, end_time)
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
        video_filename="output.srt",
        verbose=False,
    ):
        """
        :param width: width of target screen in pixels
        :param height: height of target screen in pixels
        :param format_callback: callback method of form <None>callback(string) that
        can be used to dump strings to file upon each subsequent "clear screen" command.
        """
        self._color = default_color
        self._tmax = tmax
        self._CCArea = ClosedCaptionArea()
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

    def get_dialog_text_runs(self, start_time, end_time):
        runs = []
        prefix = f"Dialogue: 0,{start_time},{end_time},"
        for run in self._accumulated_text_runs:
            runs.append(prefix + str(run))
        self._accumulated_text_runs = []
        return runs

    def open_file(self):
        if not self._ass_file:
            if self._verbose:
                print("Found nonempty ARIB closed caption data in file.")
                print("Writing .ass file: " + self._filename)
            self._ass_file = ASSFile(self._filename)

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
