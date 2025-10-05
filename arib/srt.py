"""
Module: srt.py
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
from typing import Optional, Union, Callable, Dict, Any
import re

import arib.code_set as code_set
import arib.control_characters as control_characters
from arib.arib_exceptions import FileOpenError

Number = Union[int, float]


class TextSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    NORMAL = "normal"

    def __str__(self):
        return self.value


class SRTFile:
    """Wrapper for a single open utf-8 encoded .srt subtitle file"""

    def __init__(
        self, filepath: str, width: int = 960, height: int = 540, show_debug_grid: bool = False
    ):
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

    def write(self, line: str) -> None:
        """Write indicated string to file. usually a line of dialog."""
        self._f.write(line)


def srt_timecode(seconds: Number, *, clamp_negative: bool = True) -> str:
    """
    Convert elapsed seconds to SRT timecode 'HH:MM:SS,mmm'.
    """
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
        raise ValueError("seconds must be a finite int or float")

    if clamp_negative and seconds < 0:
        seconds = 0.0

    total_ms = int(round(seconds * 1000))
    if total_ms < 0:
        sign = "-"
        total_ms = -total_ms
    else:
        sign = ""

    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)

    return f"{sign}{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


# Precompiled patterns used by control character handler
_a_regex = re.compile(rb'<CS:"(?P<x>\d{1,4});(?P<y>\d{1,4}) a">')
_pos_regex = r"({\\pos\(\d{1,4},\d{1,4}\)})"  # kept for compatibility (not used directly here)


class SRTFormatter:
    def __init__(
        self,
        default_color: str = "white",
        tmax: int = 5,
        width: int = 960,
        height: int = 540,
        video_filename: str = "output.srt",
        verbose: bool = False,
        enable_small_text: bool = False,
    ):
        """
        :param width: width of target screen in pixels
        :param height: height of target screen in pixels
        """
        self._color = default_color
        self._tmax = tmax
        self._elapsed_time_s = 0.0
        self._last_end_time_s = 0.0  # preserved (unused in snippet but kept for compatibility)
        self._srt_file: Optional[SRTFile] = None  # opened lazily on first *real* write
        self._current_textsize = TextSize.NORMAL
        self._filename = video_filename
        self._width = width
        self._height = height
        self._verbose = verbose
        self.line_count = 1
        self.current_lines = [""]  # start with an empty line ready to receive chars
        self.enable_small_text = enable_small_text

        # Build a bound-method dispatch table (modern idiom; no free functions)
        self._dispatch: Dict[Any, Callable[[Any, float], None]] = {
            code_set.Kanji: self._kanji,
            code_set.Alphanumeric: self._alphanumeric,
            code_set.Hiragana: self._hiragana,
            code_set.Katakana: self._katakana,
            control_characters.APS: self._position_set,  # {\pos(<X>,<Y>)}
            control_characters.MSZ: self._medium,  # {\rmedium}
            control_characters.NSZ: self._normal,  # {\rnormal}
            control_characters.SP: self._space,  # ' '
            control_characters.SSZ: self._small,  # {\rsmall}
            control_characters.CS: self._clear_screen,
            control_characters.CSI: self._control_character,  # {\pos(<X>,<Y>)}
            control_characters.PAPF: self._active_position_forward,
            # DRCS: replace with unknown char
            code_set.DRCS0: self._drcs,
            code_set.DRCS1: self._drcs,
            code_set.DRCS2: self._drcs,
            code_set.DRCS3: self._drcs,
            code_set.DRCS4: self._drcs,
            code_set.DRCS5: self._drcs,
            code_set.DRCS6: self._drcs,
            code_set.DRCS7: self._drcs,
            code_set.DRCS8: self._drcs,
            code_set.DRCS9: self._drcs,
            code_set.DRCS10: self._drcs,
            code_set.DRCS11: self._drcs,
            code_set.DRCS12: self._drcs,
            code_set.DRCS13: self._drcs,
            code_set.DRCS14: self._drcs,
            code_set.DRCS15: self._drcs,
        }

    # ---------- public API ----------

    def add_char(self, ch: str) -> None:
        """Add one or more characters to the current .srt subtitle."""
        if self._current_textsize != TextSize.SMALL or self.enable_small_text:
            if not self.current_lines:
                self.current_lines.append("")
            self.current_lines[-1] += ch

    def new_line(self, timestamp: float) -> None:
        """Start a new line within the current srt subtitle."""
        if self.current_lines and self.current_lines[-1]:  # only if current line nonempty
            self.current_lines.append("")

    def emit_lines(self, timestamp: float) -> None:
        """Emit current accumulated text to a new srt subtitle."""
        lines = "\n".join(s for s in self.current_lines if s)
        if lines:
            # lazily open file *only when writing first non-empty subtitle*
            if not self._srt_file:
                if self._verbose:
                    print("Found nonempty ARIB closed caption data in file.")
                    print("Writing .srt file: " + self._filename)
                self._srt_file = SRTFile(self._filename)

            # compute times exactly as before
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

        # reset for next accumulation regardless
        self.current_lines = [""]

    def position_forward(self, n: int, text_size: TextSize) -> None:
        spaces = " " * n
        self.add_char(spaces)

    def open_file(self) -> None:
        """Kept for compatibility; no longer opens until emit time (lazy)."""
        # no-op on purpose; file will be opened lazily in emit_lines()
        return

    def file_written(self) -> bool:
        return self._srt_file is not None

    def format(self, captions, timestamp: float) -> None:
        """Format ARIB closed caption info into text for an .srt file."""
        for c in captions:
            handler = self._dispatch.get(type(c))
            if handler is not None:
                handler(c, timestamp)
            else:
                # TODO: Warning of unhandled characters
                pass

    # ---------- bound handlers (formerly free functions) ----------

    def _kanji(self, k, timestamp: float) -> None:
        self.add_char(str(k))

    def _alphanumeric(self, a, timestamp: float) -> None:
        self.add_char(str(a))

    def _hiragana(self, h, timestamp: float) -> None:
        self.add_char(str(h))

    def _katakana(self, k, timestamp: float) -> None:
        self.add_char(str(k))

    def _medium(self, _k, _timestamp: float) -> None:
        self._current_textsize = TextSize.MEDIUM

    def _normal(self, _k, _timestamp: float) -> None:
        self._current_textsize = TextSize.NORMAL

    def _small(self, _k, _timestamp: float) -> None:
        self._current_textsize = TextSize.SMALL

    def _space(self, _k, _timestamp: float) -> None:
        self.add_char(" ")

    def _drcs(self, _c, _timestamp: float) -> None:
        # largely unhandled DRCS: replace with unicode unknown character square
        self.add_char("�")

    def _position_set(self, _p, timestamp: float) -> None:
        """
        For an .srt file we read "position set" as the start of a new line.
        """
        self.new_line(timestamp)

    def _active_position_forward(self, papf, timestamp: float) -> None:
        """Move the cursor forward n spaces (if papf carries count)."""
        # If papf contains a count attribute, respect it; otherwise ignore.
        try:
            n = int(getattr(papf, "count", 0))
        except Exception:
            n = 0
        if n > 0:
            self.position_forward(n, self._current_textsize)

    def _control_character(self, csi, timestamp: float) -> None:
        """
        CSI can represent many commands. For SRT we only detect a '{\\pos(x,y)}' style
        coordinate (as your original regex did) and treat it as a line break.
        """
        cmd = csi if isinstance(csi, (bytes, bytearray)) else str(csi).encode("utf-8")
        a_match = _a_regex.search(cmd)
        if a_match:
            self.new_line(timestamp)

    def _clear_screen(self, _cs, timestamp: float) -> None:
        """
        For .srt we emit accumulated subtitle lines on clear screen.
        Thus the subtitle will typically be displayed between the last
        clear screen event and the current one.
        """
        self.emit_lines(timestamp)
