# vim: set ts=2 expandtab:
"""
Module: gl.py
Desc: handle gl (left) are encodings
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Friday, March 15th 2014

"""
import read


def in_area(b):
    """Is this character in the GL area?
    :param b: single byte character to test
    :returns boolean indicating whether we're in the correct are
    """
    upper_byte = (b & 0xF0) >> 4
    # lower_byte = b & 0x0F
    if upper_byte > 0x01 and upper_byte < 0x08 and b != 0 and b != 0x7F:
        return True
    else:
        return False


class TwoByteKanji(object):
    """2 byte character, may be kanji or another symbol"""

    def __init__(self, b, f):
        """Read from stream two bytes"""
        b2 = read.ucb(f)
        self._args = []
        self._args.append(b)
        self._args.append(b2)

        self._value = ((0x0F & b) << 4) | (0x0F & b2)

    def __len__(self):
        return 2

    def __str__(self):
        """stringify to utf-8"""
        s = "".join("{:02x}".format(a | 0x80) for a in self._args)
        # print 's ' + s
        by = s.decode("hex")
        decoded = by.decode("euc-jisx0213")
        u = decoded.encode("utf-8")
        return u
