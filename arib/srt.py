from pathlib import Path
from enum import Enum
import sys
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


class SRTWriter:
    """
    A simple sink that can write SRT content either to a file or to stdout.

    - Lazy open (file only opened on first write)
    - Context-manager friendly
    - If to_stdout=True or path == "-", writes to sys.stdout and does not close it
    """

    def __init__(self, path: Optional[str], *, to_stdout: bool = False):
        self._path = None if to_stdout else (None if path is None else str(path))
        if path == "-":  # conventional stdout marker
            to_stdout = True
            self._path = None
        self._to_stdout = to_stdout
        self._fh = None  # type: Optional[object]

    def __enter__(self):
        # Opening is lazy; we still return self so "with" works.
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    @property
    def is_open(self) -> bool:
        return self._fh is not None

    def _ensure_open(self):
        if self.is_open:
            return
        if self._to_stdout:
            self._fh = sys.stdout
            return
        if not self._path:
            raise FileOpenError("No output path provided and stdout not selected.")
        # Ensure parent dir exists
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fh = open(self._path, "w", encoding="utf-8", newline="")
        except Exception as e:
            raise FileOpenError(f"Could not open file {self._path!r} for writing: {e}") from e

    def write(self, text: str) -> None:
        self._ensure_open()
        self._fh.write(text)

    def flush(self) -> None:
        if self.is_open and self._fh is not sys.stdout:
            self._fh.flush()

    def close(self) -> None:
        if self.is_open and self._fh is not sys.stdout:
            try:
                self._fh.close()
            finally:
                self._fh = None


def srt_timecode(seconds: Number, *, clamp_negative: bool = True) -> str:
    if not isinstance(seconds, (int, float)) or not math.isfinite(seconds):
        raise ValueError("seconds must be a finite int or float")
    if clamp_negative and seconds < 0:
        seconds = 0.0
    total_ms = int(round(seconds * 1000))
    sign = ""
    if total_ms < 0:
        sign = "-"
        total_ms = -total_ms
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
        *,  # forced explicit naming for output_to_stdout
        output_to_stdout: bool = False,
    ):
        self._color = default_color
        self._tmax = tmax
        self._elapsed_time_s = 0.0
        self._last_end_time_s = 0.0  # preserved
        self._filename = video_filename
        self._width = width
        self._height = height
        self._verbose = verbose
        self.line_count = 1
        self.current_lines = [""]  # start ready to receive chars
        self.enable_small_text = enable_small_text
        self._current_textsize = TextSize.NORMAL

        # writer is created lazily on first emit (so we never open unless we have content)
        self._writer: Optional[SRTWriter] = None
        self._to_stdout = output_to_stdout or (video_filename == "-")

        # Bound-method dispatch
        self._dispatch: Dict[Any, Callable[[Any, float], None]] = {
            code_set.Kanji: self._kanji,
            code_set.Alphanumeric: self._alphanumeric,
            code_set.Hiragana: self._hiragana,
            code_set.Katakana: self._katakana,
            control_characters.APS: self._position_set,
            control_characters.MSZ: self._medium,
            control_characters.NSZ: self._normal,
            control_characters.SP: self._space,
            control_characters.SSZ: self._small,
            control_characters.CS: self._clear_screen,
            control_characters.CSI: self._control_character,
            control_characters.PAPF: self._active_position_forward,
            # DRCS -> unknown char replacement
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
        if self._current_textsize != TextSize.SMALL or self.enable_small_text:
            if not self.current_lines:
                self.current_lines.append("")
            self.current_lines[-1] += ch

    def new_line(self, timestamp: float) -> None:
        if self.current_lines and self.current_lines[-1]:
            self.current_lines.append("")

    def emit_lines(self, timestamp: float) -> None:
        lines = "\n".join(s for s in self.current_lines if s)
        if lines:
            # lazily create writer only when we truly write the first non-empty subtitle
            if not self._writer:
                if self._verbose and not self._to_stdout:
                    print("Found nonempty ARIB closed caption data in file.")
                    target = "(stdout)" if self._to_stdout else self._filename
                    print("Writing .srt output to: " + target)
                self._writer = SRTWriter(self._filename, to_stdout=self._to_stdout)

            # compute times as before
            start_time = self._elapsed_time_s
            end_time = timestamp
            if end_time - start_time <= 0.0:
                start_time = end_time - self._tmax
            elif end_time - start_time > self._tmax:
                start_time = end_time - self._tmax

            start = srt_timecode(start_time)
            end = srt_timecode(end_time)

            self._writer.write(f"{self.line_count}\n")
            self._writer.write(f"{start} --> {end}\n")
            self._writer.write(f"{lines}\n\n")

            self.line_count += 1
            self._elapsed_time_s = timestamp

        self.current_lines = [""]

    def position_forward(self, n: int) -> None:
        self.add_char(" " * n)

    def open_file(self) -> None:
        """Compatibility no-op: writer is opened lazily in emit_lines()."""
        return

    def file_written(self) -> bool:
        return self._writer is not None and self._writer.is_open

    def finalize(self) -> None:
        """Optional: flush/close output (useful for CLIs/tests)."""
        # No implicit emit here; we just close the writer if it exists.
        if self._writer:
            self._writer.flush()
            self._writer.close()

    def format(self, captions, timestamp: float) -> None:
        for c in captions:
            handler = self._dispatch.get(type(c))
            if handler is not None:
                handler(c, timestamp)
            else:
                # TODO: warning/log for unhandled characters
                pass

    # ---------- bound handlers ----------

    def _kanji(self, k, _ts: float) -> None:
        self.add_char(str(k))

    def _alphanumeric(self, a, _ts: float) -> None:
        self.add_char(str(a))

    def _hiragana(self, h, _ts: float) -> None:
        self.add_char(str(h))

    def _katakana(self, k, _ts: float) -> None:
        self.add_char(str(k))

    def _medium(self, _k, _ts: float) -> None:
        self._current_textsize = TextSize.MEDIUM

    def _normal(self, _k, _ts: float) -> None:
        self._current_textsize = TextSize.NORMAL

    def _small(self, _k, _ts: float) -> None:
        self._current_textsize = TextSize.SMALL

    def _space(self, _k, _ts: float) -> None:
        self.add_char(" ")

    def _drcs(self, _c, _ts: float) -> None:
        self.add_char("�")

    def _position_set(self, _p, ts: float) -> None:
        self.new_line(ts)

    def _active_position_forward(self, papf, _ts: float) -> None:
        try:
            n = int(getattr(papf, "count", 0))
        except Exception:
            n = 0
        if n > 0:
            self.position_forward(n)

    def _control_character(self, csi, ts: float) -> None:
        cmd = csi if isinstance(csi, (bytes, bytearray)) else str(csi).encode("utf-8")
        if _a_regex.search(cmd):
            self.new_line(ts)

    def _clear_screen(self, _cs, ts: float) -> None:
        self.emit_lines(ts)
