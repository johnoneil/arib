# vim: set ts=2 expandtab:
"""
Module: read.py
Desc: unpack data from binary files
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Thursday, March 13th 2014
"""

import struct

DEBUG = False


class EOFError(Exception):
    """Custom exception raised when we read to EOF"""

    pass


def split_buffer(length, buf):
    """Split provided array at index `length`, returning (prefix, remaining).

    NOTE: Mutates `buf` by popping from the front.
    """
    a = []
    if len(buf) < length:
        return (a, buf)
    for _ in range(length):
        a.append(buf.pop(0))
    return (a, buf)


def _join_to_bytes(seq):
    """Join a sequence of elements into bytes.

    Accepts:
      - ints (0..255)
      - 1-byte `bytes`/`bytearray`
      - 1-char `str` (interpreted as raw byte via ord)
    """
    out = bytearray()
    for el in seq:
        if isinstance(el, int):
            out.append(el & 0xFF)
        elif isinstance(el, (bytes, bytearray)):
            if len(el) != 1:
                raise ValueError("Expected 1-byte items in buffer list")
            out.extend(el)
        elif isinstance(el, str):
            if len(el) != 1:
                raise ValueError("Expected 1-char strings in buffer list")
            out.append(ord(el) & 0xFF)
        else:
            raise TypeError(f"Unsupported element type in buffer list: {type(el)!r}")
    return bytes(out)


def dump_list(lst):
    # Make this tolerant of bytes/str elements too
    vals = []
    for x in lst:
        if isinstance(x, int):
            vals.append(x)
        elif isinstance(x, (bytes, bytearray)):
            vals.append(x[0] if x else 0)
        elif isinstance(x, str):
            vals.append(ord(x) if x else 0)
        else:
            # Fallback: try int() if it's number-like
            try:
                vals.append(int(x))
            except Exception:
                vals.append(0)
    print(" ".join("{:#x}".format(x) for x in vals))


def _read_exact_file(f, n):
    """Read exactly n bytes from a (binary) file-like."""
    data = f.read(n)
    if len(data) < n:
        raise EOFError()
    return data


def _read_exact_any(f, n):
    """Read exactly n bytes from either a list buffer or a file-like."""
    if isinstance(f, list):
        chunk, _ = split_buffer(n, f)
        if len(chunk) < n:
            raise EOFError()
        return _join_to_bytes(chunk)
    else:
        return _read_exact_file(f, n)


def ucb(f):
    """Read unsigned char (1 byte) from binary file or buffer."""
    b = _read_exact_any(f, 1)
    return struct.unpack("B", b)[0]


def usb(f):
    """Read unsigned short (2 bytes, big-endian) from binary file or buffer."""
    b = _read_exact_any(f, 2)
    if DEBUG and not isinstance(f, list):
        # In Py3, indexing bytes gives ints already.
        print("usb: " + hex(b[0]) + ":" + hex(b[1]))
    return struct.unpack(">H", b)[0]


def ui3b(f):
    """Read a 3-byte unsigned integer (big-endian) from binary file or buffer."""
    three = _read_exact_any(f, 3)
    # Prepend zero byte to make 4 bytes for struct.unpack of >I
    return struct.unpack(">I", b"\x00" + three)[0]
    # Alternatively: return int.from_bytes(three, 'big')


def uib(f):
    """Read unsigned 4-byte integer (big-endian) from binary file or buffer."""
    b4 = _read_exact_any(f, 4)
    return struct.unpack(">L", b4)[0]
    # Alternatively prefer '>I' in modern code.


def ulb(f):
    """Read unsigned long long (8 bytes, big-endian) from binary file or buffer."""
    b8 = _read_exact_any(f, 8)
    return struct.unpack(">Q", b8)[0]


def buffer(f, size):
    """Read N raw bytes from either a file or list."""
    return _read_exact_any(f, size)
