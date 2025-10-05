# vim: set ts=2 expandtab:
# -*- coding: utf-8 -*-
"""
Module: art.py
Desc: srt subtitle file formatter.
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Saturday, October 4th, 2025

This module provides a formatter class that can be used
to turn arib package subtitle objects into an .srt subtitles.

"""
from pathlib import Path
from enum import Enum
import math
from typing import Union
import arib.code_set as code_set
import arib.control_characters as control_characters
import re
from arib.arib_exceptions import FileOpenError

Number = Union[int, float]


class TextSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    NORMAL = "normal"

    def __str__(self):
        return self.value


class SRTFile(object):
    """Wrapper for a single open utf-8 encoded .srt subtitle file"""

    def __init__(self, filepath, width=960, height=540, show_debug_grid=False):
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        try:
            self._f = open(filepath, "w", encoding="utf-8", newline="")
        except Exception as e:
            raise FileOpenError(f"Could not open file {filepath!r} for writing: {e}") from e

    def __del__(self):
        try:
            if self._f:
                self._f.close()
        except AttributeError:
            pass

    def write(self, line):
        """Write indicated string to file. usually a line of dialog."""
        self._f.write(line)


def srt_timecode(seconds: Number, *, clamp_negative: bool = True) -> str:
    """
    Convert elapsed seconds to SRT timecode 'HH:MM:SS,mmm'.

    - Rounds to nearest millisecond.
    - Carries overflows correctly (e.g., 59.9999 -> 01:00:00,000).
    - Supports hours >= 100 (won't truncate).
    - If clamp_negative=True, negative inputs become 00:00:00,000 (SRT has no negatives).
    """
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
        raise ValueError("seconds must be a finite int or float")

    if clamp_negative and seconds < 0:
        seconds = 0.0

    total_ms = int(round(seconds * 1000))  # rounding is crucial for float inputs
    if total_ms < 0:  # only possible if clamp_negative=False
        sign = "-"
        total_ms = -total_ms
    else:
        sign = ""

    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)

    return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def kanji(formatter, k, timestamp):
    formatter.open_file()
    formatter.add_char(str(k))


def alphanumeric(formatter, a, timestamp):
    formatter.open_file()
    formatter.add_char(str(a))


def hiragana(formatter, h, timestamp):
    formatter.open_file()
    formatter.add_char(str(h))


def katakana(formatter, k, timestamp):
    formatter.open_file()
    formatter.add_char(str(k))


def medium(formatter, k, timestamp):
    # formatter.open_file()
    formatter._current_textsize = TextSize.MEDIUM


def normal(formatter, k, timestamp):
    # formatter.open_file()
    formatter._current_textsize = TextSize.NORMAL


def small(formatter, k, timestamp):
    # formatter.open_file()
    formatter._current_textsize = TextSize.SMALL


def space(formatter, k, timestamp):
    formatter.open_file()
    formatter.add_char(" ")


def drcs(formatter, c, timestamp):
    formatter.open_file()
    formatter.add_char("�")


def black(formatter, k, timestamp):
    pass


def red(formatter, k, timestamp):
    pass


def green(formatter, k, timestamp):
    pass


def yellow(formatter, k, timestamp):
    pass


def blue(formatter, k, timestamp):
    pass


def magenta(formatter, k, timestamp):
    pass


def cyan(formatter, k, timestamp):
    pass


def white(formatter, k, timestamp):
    pass


def position_set(formatter, p, timestamp):
    """
    For an .srt file we read "position set" as the start of a new line.
    """
    formatter.new_line(timestamp)


def active_position_forward(formatter, papf, timestamp):
    """Move the cursor forward n spaces"""
    pass


a_regex = re.compile(rb'<CS:"(?P<x>\d{1,4});(?P<y>\d{1,4}) a">')


def control_character(formatter, csi, timestamp):
    """This will be the most difficult to format, since the same class here
    can represent so many different commands.
    """
    cmd = csi if isinstance(csi, (bytes, bytearray)) else str(csi).encode("utf-8")
    a_match = a_regex.search(cmd)
    if a_match:
        formatter.new_line(timestamp)
        return


pos_regex = r"({\\pos\(\d{1,4},\d{1,4}\)})"


def clear_screen(formatter, cs, timestamp):
    """
    For .srt we emit accumulated subtitle lines on clear screen.
    Thus the subtitle will typically be displayed between the last
    clear screen event and the current one.
    """
    formatter.emit_lines(timestamp)


class SRTFormatter(object):
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
        # control_characters.BKF: black,  # {\c&H000000&} \c&H<bb><gg><rr>&
        # control_characters.RDF: red,  # {\c&H0000ff&}
        # control_characters.GRF: green,  # {\c&H00ff00&}
        # control_characters.YLF: yellow,  # {\c&H00ffff&}
        # control_characters.BLF: blue,  # {\c&Hff0000&}
        # control_characters.MGF: magenta,  # {\c&Hff00ff&}
        # control_characters.CNF: cyan,  # {\c&Hffff00&}
        # control_characters.WHF: white,  # {\c&Hffffff&}
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
        enable_small_text=False,
    ):
        """
        :param width: width of target screen in pixels
        :param height: height of target screen in pixels
        :param format_callback: callback method of form <None>callback(string) that
        can be used to dump strings to file upon each subsequent "clear screen" command.
        """
        self._color = default_color
        self._tmax = tmax
        self._elapsed_time_s = 0.0
        self._last_end_time_s = 0.0
        self._srt_file = None
        self._current_textsize = TextSize.NORMAL
        self._filename = video_filename
        self._width = width
        self._height = height
        self._height = height
        self._verbose = verbose
        self.line_count = 1
        self.current_lines = [str]
        self.enable_small_text = enable_small_text

    def add_char(self, ch: str):
        """Add one or more characters to the current .srt subtitle."""
        if self._current_textsize != TextSize.SMALL or self.enable_small_text:
            self.current_lines[-1] += ch

    def new_line(self, timestamp):
        """Start a new line within the current srt subtitle."""
        if self.current_lines and self.current_lines[-1]:  # is current line nonempty?
            self.current_lines.append("")

    def emit_lines(self, timestamp):
        """Emit current accumulated text to a new srt subtitle."""
        if self._srt_file:
            lines = "\n".join(s for s in self.current_lines if s)
            if lines:
                start_time = self._elapsed_time_s
                end_time = timestamp
                if end_time - start_time <= 0.0:
                    start_time = end_time - self._tmax
                elif end_time - start_time > self._tmax:
                    start_time = end_time - self._tmax
                start = srt_timecode(start_time)
                end = srt_timecode(end_time)
                self._srt_file.write(f"{self.line_count}\n")
                self._srt_file.write(f"{start} --> {end}\n")
                self._srt_file.write(f"{lines}\n\n")
                self.line_count += 1
                self._elapsed_time_s = timestamp
        self.current_lines = [""]

    def position_forward(self, n, text_size: TextSize):
        spaces = " " * n
        self.add_char(spaces)

    def open_file(self):
        if not self._srt_file:
            if self._verbose:
                print("Found nonempty ARIB closed caption data in file.")
                print("Writing .ass file: " + self._filename)
            self._srt_file = SRTFile(self._filename)

    def file_written(self):
        return self._srt_file is not None

    def format(self, captions, timestamp):
        """Format ARIB closed caption info tinto text for an .srt file"""

        for c in captions:
            if type(c) in SRTFormatter.DISPLAYED_CC_STATEMENTS:
                # invoke the handler for this object type
                SRTFormatter.DISPLAYED_CC_STATEMENTS[type(c)](self, c, timestamp)
            else:
                # TODO: Warning of unhandled characters
                pass
