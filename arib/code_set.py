# -*- coding: utf-8 -*-
# vim: set ts=2 expandtab:
"""
Module: code_set.py
Desc: stateful arib teletext decoder
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Sat, March 16th 2014

handling for code sets in japanese closed captions

"""

from arib import read
from arib.arib_exceptions import UnimplimentedError
from arib.drcs_cache import DRCS_CACHE, drcs0_pack, normalize_94

DEBUG = False


class Gaiji(object):
    # after ARIB std docs pg 54 onwards
    # note that columns and rows are swapped in this table to
    # facilitate reading
    ENCODING = {
        1: {
            90: "⛌",
            91: "⛣",
            92: "➡",
            93: "㈪",
            94: "Ⅰ",
        },
        2: {
            90: "⛍",
            91: "⭖",
            92: "⬅",
            93: "㈫",
            94: "Ⅱ",
        },
        3: {
            90: "❗",
            91: "⭗",
            92: "⬆",
            93: "㈬",
            94: "Ⅲ",
        },
        4: {
            90: "⛏",
            91: "⭘",
            92: "⬇",
            93: "㈭",
            94: "Ⅳ",
        },
        5: {
            90: "⛐",
            91: "⭙",
            92: "⬯",
            93: "㈮",
            94: "Ⅴ",
        },
        6: {
            90: "⛑",
            91: "☓",
            92: "⬮",
            93: "㈯",
            94: "Ⅵ",
        },
        7: {
            90: "◻",
            91: "㊋",
            92: "年",
            93: "㈰",
            94: "Ⅶ",
        },
        8: {
            90: "⛒",
            91: "〒",
            92: "月",
            93: "㈷",
            94: "Ⅷ",
        },
        9: {
            90: "⛕",
            91: "⛨",
            92: "日",
            93: "㍾",
            94: "Ⅸ",
        },
        10: {
            90: "⛓",
            91: "㉆",
            92: "円",
            93: "㍽",
            94: "Ⅹ",
        },
        11: {
            90: "⛔",
            91: "㉅",
            92: "㎡",
            93: "㍼",
            94: "Ⅺ",
        },
        12: {
            90: "◻",
            91: "⛩",
            92: "㎥",
            93: "㍻",
            94: "Ⅻ",
        },
        13: {
            90: "◻",
            91: "࿖",
            92: "㎝",
            93: "№",
            94: "⑰",
        },
        14: {
            90: "◻",
            91: "⛪",
            92: "㎠",
            93: "℡",
            94: "⑱",
        },
        15: {
            90: "◻",
            91: "⛫",
            92: "㎤",
            93: "〶",
            94: "⑲",
        },
        16: {
            90: "🅿",
            91: "⛬",
            92: "🄀",
            93: "⚾",
            94: "⑳",
        },
        17: {
            90: "🆊",
            91: "♨",
            92: "⒈",
            93: "🉀",
            94: "◻",
        },
        18: {
            90: "◻",
            91: "⛭",
            92: "⒉",
            93: "🉁",
            94: "◻",
        },
        19: {
            90: "◻",
            91: "⛮",
            92: "⒊",
            93: "🉂",
            94: "◻",
        },
        20: {
            90: "⛖",
            91: "⛯",
            92: "⒋",
            93: "🉃",
            94: "◻",
        },
        21: {
            90: "⛗",
            91: "⚓",
            92: "⒌",
            93: "🉄",
            94: "◻",
        },
        22: {
            90: "⛘",
            91: "✈",
            92: "⒍",
            93: "🉅",
            94: "◻",
        },
        23: {
            90: "⛙",
            91: "⛰",
            92: "⒎",
            93: "🉆",
            94: "◻",
        },
        24: {
            90: "⛚",
            91: "⛱",
            92: "⒏",
            93: "🉇",
            94: "◻",
        },
        25: {
            90: "⛛",
            91: "⛲",
            92: "⒐",
            93: "🉈",
            94: "◻",
        },
        26: {
            90: "⛜",
            91: "⛳",
            92: "氏",
            93: "🄪",
            94: "◻",
        },
        27: {
            90: "⛝",
            91: "⛴",
            92: "副",
            93: "🈧",
            94: "◻",
        },
        28: {
            90: "⛞",
            91: "⛵",
            92: "元",
            93: "🈨",
            94: "◻",
        },
        29: {
            90: "⛟",
            91: "🅗",
            92: "故",
            93: "🈩",
            94: "◻",
        },
        30: {
            90: "⛠",
            91: "Ⓓ",
            92: "前",
            93: "🈔",
            94: "◻",
        },
        31: {
            90: "⛡",
            91: "Ⓢ",
            92: "新",
            93: "🈪",
            94: "◻",
        },
        32: {
            90: "⭕",
            91: "⛶",
            92: "🄁",
            93: "🈫",
            94: "◻",
        },
        33: {
            90: "㉈",
            91: "🅟",
            92: "🄂",
            93: "🈬",
            94: "🄐",
        },
        34: {
            90: "㉉",
            91: "🆋",
            92: "🄃",
            93: "🈭",
            94: "🄑",
        },
        35: {
            90: "㉊",
            91: "🆍",
            92: "🄄",
            93: "🈮",
            94: "🄒",
        },
        36: {
            90: "㉋",
            91: "🆌",
            92: "🄅",
            93: "🈯",
            94: "🄓",
        },
        37: {
            90: "㉌",
            91: "🅹",
            92: "🄆",
            93: "🈰",
            94: "🄔",
        },
        38: {
            90: "㉍",
            91: "⛷",
            92: "🄇",
            93: "🈱",
            94: "🄕",
        },
        39: {
            90: "㉎",
            91: "⛸",
            92: "🄈",
            93: "ℓ",
            94: "🄖",
        },
        40: {
            90: "㉏",
            91: "⛹",
            92: "🄉",
            93: "㎏",
            94: "🄗",
        },
        41: {
            90: "◻",
            91: "⛺",
            92: "🄊",
            93: "㎐",
            94: "🄘",
        },
        42: {
            90: "◻",
            91: "🅻",
            92: "㈳",
            93: "㏊",
            94: "🄙",
        },
        43: {
            90: "◻",
            91: "☎",
            92: "㈶",
            93: "㎞",
            94: "🄚",
        },
        44: {
            90: "◻",
            91: "⛻",
            92: "㈲",
            93: "㎢",
            94: "🄛",
        },
        45: {
            90: "⒑",
            91: "⛼",
            92: "㈱",
            93: "㍱",
            94: "🄜",
        },
        46: {
            90: "⒒",
            91: "⛽",
            92: "㈹",
            93: "◻",
            94: "🄝",
        },
        47: {
            90: "⒓",
            91: "⛾",
            92: "㉄",
            93: "◻",
            94: "🄞",
        },
        48: {
            90: "🅊",
            91: "🅼",
            92: "▶",
            93: "½",
            94: "🄟",
        },
        49: {
            90: "🅌",
            91: "⛿",
            92: "◀",
            93: "↉",
            94: "🄠",
        },
        50: {
            90: "🄿",
            91: "◻",
            92: "〖",
            93: "⅓",
            94: "🄡",
        },
        51: {
            90: "🅆",
            91: "◻",
            92: "〗",
            93: "⅔",
            94: "🄢",
        },
        52: {
            90: "🅋",
            91: "◻",
            92: "⟐",
            93: "¼",
            94: "🄣",
        },
        53: {
            90: "🈐",
            91: "◻",
            92: "²",
            93: "¾",
            94: "🄤",
        },
        54: {
            90: "🈑",
            91: "◻",
            92: "³",
            93: "⅕",
            94: "🄥",
        },
        55: {
            90: "🈒",
            91: "◻",
            92: "🄭",
            93: "⅖",
            94: "🄦",
        },
        56: {
            90: "🈓",
            91: "◻",
            92: "◻",
            93: "⅗",
            94: "🄧",
        },
        57: {
            90: "🅂",
            91: "◻",
            92: "◻",
            93: "⅘",
            94: "🄨",
        },
        58: {
            90: "🈔",
            91: "◻",
            92: "◻",
            93: "⅙",
            94: "🄩",
        },
        59: {
            90: "🈕",
            91: "◻",
            92: "◻",
            93: "⅚",
            94: "㉕",
        },
        60: {
            90: "🈖",
            91: "◻",
            92: "◻",
            93: "⅐",
            94: "㉖",
        },
        61: {
            90: "🅍",
            91: "◻",
            92: "◻",
            93: "⅛",
            94: "㉗",
        },
        62: {
            90: "🄱",
            91: "◻",
            92: "◻",
            93: "⅑",
            94: "㉘",
        },
        63: {
            90: "🄽",
            91: "◻",
            92: "◻",
            93: "⅒",
            94: "㉙",
        },
        64: {
            90: "⬛",
            91: "◻",
            92: "◻",
            93: "☀",
            94: "㉚",
        },
        65: {
            90: "⬤",
            91: "◻",
            92: "◻",
            93: "☁",
            94: "①",
        },
        66: {
            90: "🈗",
            91: "◻",
            92: "◻",
            93: "☂",
            94: "②",
        },
        67: {
            90: "🈘",
            91: "◻",
            92: "◻",
            93: "⛄",
            94: "③",
        },
        68: {
            90: "🈙",
            91: "◻",
            92: "◻",
            93: "☖",
            94: "④",
        },
        69: {
            90: "🈚",
            91: "◻",
            92: "◻",
            93: "☗",
            94: "⑤",
        },
        70: {
            90: "🈛",
            91: "◻",
            92: "◻",
            93: "⛉",
            94: "⑥",
        },
        71: {
            90: "⚿",
            91: "◻",
            92: "◻",
            93: "⛊",
            94: "⑦",
        },
        72: {
            90: "🈜",
            91: "◻",
            92: "◻",
            93: "♦",
            94: "⑧",
        },
        73: {
            90: "🈝",
            91: "◻",
            92: "◻",
            93: "♥",
            94: "⑨",
        },
        74: {
            90: "🈞",
            91: "◻",
            92: "◻",
            93: "♣",
            94: "⑩",
        },
        75: {
            90: "🈟",
            91: "◻",
            92: "◻",
            93: "♠",
            94: "⑪",
        },
        76: {
            90: "🈠",
            91: "◻",
            92: "◻",
            93: "⛋",
            94: "⑫",
        },
        77: {
            90: "🈡",
            91: "◻",
            92: "◻",
            93: "⨀",
            94: "⑬",
        },
        78: {
            90: "🈢",
            91: "◻",
            92: "◻",
            93: "‼",
            94: "⑭",
        },
        79: {
            90: "🈣",
            91: "◻",
            92: "◻",
            93: "⁈",
            94: "⑮",
        },
        80: {
            90: "🈤",
            91: "◻",
            92: "◻",
            93: "⛅",
            94: "⑯",
        },
        81: {
            90: "🈥",
            91: "◻",
            92: "◻",
            93: "☔",
            94: "❶",
        },
        82: {
            90: "🅎",
            91: "◻",
            92: "◻",
            93: "⛆",
            94: "❷",
        },
        83: {
            90: "㊙",
            91: "◻",
            92: "◻",
            93: "☃",
            94: "❸",
        },
        84: {
            90: "🈀",
            91: "◻",
            92: "◻",
            93: "⛇",
            94: "❹",
        },
        85: {
            90: "◻",
            91: "◻",
            92: "◻",
            93: "⚡",
            94: "❺",
        },
        86: {
            90: "◻",
            91: "◻",
            92: "🄬",
            93: "⛈",
            94: "❻",
        },
        87: {
            90: "◻",
            91: "◻",
            92: "🄫",
            93: "◻",
            94: "❼",
        },
        88: {
            90: "◻",
            91: "◻",
            92: "㉇",
            93: "⚞",
            94: "❽",
        },
        89: {
            90: "◻",
            91: "◻",
            92: "🆐",
            93: "⚟",
            94: "❾",
        },
        90: {
            90: "◻",
            91: "◻",
            92: "🈦",
            93: "♫",
            94: "❿",
        },
        91: {
            90: "◻",
            91: "◻",
            92: "℻",
            93: "☎",
            94: "⓫",
        },
        92: {
            90: "◻",
            91: "◻",
            92: "◻",
            93: "◻",
            94: "⓬",
        },
        93: {
            90: "◻",
            91: "◻",
            92: "◻",
            93: "◻",
            94: "㉛",
        },
        94: {
            90: "◻",
            91: "◻",
            92: "◻",
            93: "◻",
            94: "◻",
        },
    }

    @staticmethod
    def is_gaiji(v):
        row = (v[0] & 0x007F) - 0x20
        col = (v[1] & 0x007F) - 0x20
        return (row >= 90 and row <= 94) and (col >= 1 and col <= 94)

    @staticmethod
    def decode(v):
        # [124][33]--> 0b01111100, 0b00100001
        # (0x7c-0x20)(0x21-0x20)--> 0x5c, 0x1 --> 92(col), 1(row)
        # upper byte can be used to calculate row
        row = (v[0] & 0x007F) - 0x20
        col = (v[1] & 0x007F) - 0x20
        if DEBUG:
            print("gaiji [{b1}],[{b2}]-->{r},{c},".format(b1=hex(v[0]), b2=hex(v[1]), r=row, c=col))
        return Gaiji.ENCODING[col][row]


class Kanji(object):
    """2 byte kanji code set.
    basically just euc-jisx0213 seven bit encoding.
    We read the initial byte from a binary filestream, its purpose is
    detected, and that byte (and the stream) passed to this class for
    further reading and decoding.
    so it goes BYTE-->(logic determining type)-->Instance of Kanji class
    Intances of this clas can then be stored, and printed, resulting in
    a UTF-8 version of the character.
    """

    FINAL_BYTE = 0x42

    def __init__(self, b, f):
        """Read from stream two bytes
        :param b: initial byte value read
        :b type: int
        :param f: filestream we're reading from
        :f type: file stream open for binary reading
        """
        # read the second byte of the 2 byte kanji
        b2 = read.ucb(f)
        self._args = []
        self._args.append(b)
        self._args.append(b2)

        if Gaiji.is_gaiji(self._args):
            # character is outside the shif-jis code set
            self._character = Gaiji.decode(self._args)
        else:
            # form utf-8 encoding of character
            s = "".join("{:02x}".format(a | 0x80) for a in self._args)
            h = bytes.fromhex(s)  # was: s.decode('hex')
            try:
                self._character = h.decode("euc-jisx0213")
            except UnicodeDecodeError:
                self._character = "◻"
        if DEBUG:
            print(
                "[{b}][{b2}]-->{char}".format(b=hex(b), b2=hex(b2), char=self._character).encode(
                    "utf-8"
                )
            )

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return self._character

    @staticmethod
    def decode(b, f):
        return Kanji(b, f)


class Alphanumeric(object):
    FINAL_BYTE = 0x4A

    def __init__(self, b, f):
        # accept either an int or a 1-byte bytes/bytearray
        if isinstance(b, (bytes, bytearray)):
            val = b[0]
        else:
            val = int(b) & 0xFF

        self._args = [val]
        ch = bytes([val]).decode("ascii")  # strict ASCII
        self._character = "¥" if ch == "\\" else ch

    def __len__(self):
        return len(self._args)

    def __str__(self):
        return self._character

    @staticmethod
    def decode(b, f):
        return Alphanumeric(b, f)


@staticmethod
def decode(b, f):
    return Alphanumeric(b, f)


class Hiragana(object):
    FINAL_BYTE = 0x30

    def __init__(self, b, f):
        """Read from stream one byte hiragana"""
        self._args = []
        self._args.append(b)

        upper_nibble = (b >> 4) & 0x07
        lower_nibble = b & 0x0F
        self._character = Hiragana.ENCODING[lower_nibble][upper_nibble]

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return self._character

    @staticmethod
    def decode(b, f):
        return Hiragana(b, f)

    # single byte hiragana coding table ARIB STD-B24 table 7-7 pg.50
    ENCODING = {
        0x0: {
            0x2: " ",
            0x3: "ぐ",
            0x4: "だ",
            0x5: "ば",
            0x6: "む",
            0x7: "る",
        },
        0x1: {
            0x2: "ぁ",
            0x3: "け",
            0x4: "ち",
            0x5: "ぱ",
            0x6: "め",
            0x7: "ゑ",
        },
        0x2: {
            0x2: "あ",
            0x3: "げ",
            0x4: "ぢ",
            0x5: "ひ",
            0x6: "も",
            0x7: "を",
        },
        0x3: {
            0x2: "ぃ",
            0x3: "こ",
            0x4: "っ",
            0x5: "び",
            0x6: "ゃ",
            0x7: "ん",
        },
        0x4: {
            0x2: "い",
            0x3: "ご",
            0x4: "つ",
            0x5: "ぴ",
            0x6: "や",
            0x7: "　",
        },
        0x5: {
            0x2: "ぅ",
            0x3: "さ",
            0x4: "づ",
            0x5: "ふ",
            0x6: "ゅ",
            0x7: "　",
        },
        0x6: {
            0x2: "う",
            0x3: "ざ",
            0x4: "て",
            0x5: "ぶ",
            0x6: "ゆ",
            0x7: "　",
        },
        0x7: {
            0x2: "ぇ",
            0x3: "し",
            0x4: "で",
            0x5: "ぷ",
            0x6: "ょ",
            0x7: "ゝ",
        },
        0x8: {
            0x2: "え",
            0x3: "じ",
            0x4: "と",
            0x5: "へ",
            0x6: "よ",
            0x7: "ゞ",
        },
        0x9: {
            0x2: "ぉ",
            0x3: "す",
            0x4: "ど",
            0x5: "べ",
            0x6: "ら",
            0x7: "ー",
        },
        0xA: {
            0x2: "お",
            0x3: "ず",
            0x4: "な",
            0x5: "ぺ",
            0x6: "り",
            0x7: "。",
        },
        0xB: {
            0x2: "か",
            0x3: "せ",
            0x4: "に",
            0x5: "ほ",
            0x6: "る",
            0x7: "「",
        },
        0xC: {
            0x2: "が",
            0x3: "ぜ",
            0x4: "ぬ",
            0x5: "ぼ",
            0x6: "れ",
            0x7: "」",
        },
        0xD: {
            0x2: "き",
            0x3: "そ",
            0x4: "ね",
            0x5: "ぽ",
            0x6: "ろ",
            0x7: "、",
        },
        0xE: {
            0x2: "ぎ",
            0x3: "ぞ",
            0x4: "の",
            0x5: "ま",
            0x6: "ゎ",
            0x7: "・",
        },
        0xF: {
            0x2: "く",
            0x3: "た",
            0x4: "は",
            0x5: "み",
            0x6: "わ",
            0x7: "　",
        },
    }


class Katakana(object):
    FINAL_BYTE = 0x31

    def __init__(self, b, f):
        """Read from stream one byte katakana"""
        self._args = []
        self._args.append(b)

        upper_nibble = (b >> 4) & 0x07
        lower_nibble = b & 0x0F
        self._character = Katakana.ENCODING[lower_nibble][upper_nibble]

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return self._character

    @staticmethod
    def decode(b, f):
        return Katakana(b, f)

    # single byte katakana coding table ARIB STD-B24 table 7-6 pg.49
    ENCODING = {
        0x0: {
            0x2: " ",
            0x3: "グ",
            0x4: "ダ",
            0x5: "バ",
            0x6: "ム",
            0x7: "ヰ",
        },
        0x1: {
            0x2: "ァ",
            0x3: "ケ",
            0x4: "チ",
            0x5: "パ",
            0x6: "メ",
            0x7: "ヱ",
        },
        0x2: {
            0x2: "ア",
            0x3: "ゲ",
            0x4: "ジ",
            0x5: "ヒ",
            0x6: "モ",
            0x7: "ヲ",
        },
        0x3: {
            0x2: "ィ",
            0x3: "コ",
            0x4: "ッ",
            0x5: "ビ",
            0x6: "ャ",
            0x7: "ン",
        },
        0x4: {
            0x2: "イ",
            0x3: "ゴ",
            0x4: "ツ",
            0x5: "ピ",
            0x6: "ヤ",
            0x7: "ヴ",
        },
        0x5: {
            0x2: "ゥ",
            0x3: "サ",
            0x4: "づ",
            0x5: "フ",
            0x6: "ュ",
            0x7: "ヵ",
        },
        0x6: {
            0x2: "ウ",
            0x3: "ザ",
            0x4: "テ",
            0x5: "ブ",
            0x6: "ユ",
            0x7: "ヶ",
        },
        0x7: {
            0x2: "ェ",
            0x3: "シ",
            0x4: "デ",
            0x5: "プ",
            0x6: "ョ",
            0x7: "ヽ",
        },
        0x8: {
            0x2: "エ",
            0x3: "ジ",
            0x4: "ト",
            0x5: "ヘ",
            0x6: "ヨ",
            0x7: "ヾ",
        },
        0x9: {
            0x2: "ォ",
            0x3: "ス",
            0x4: "ド",
            0x5: "ベ",
            0x6: "ラ",
            0x7: "ー",
        },
        0xA: {
            0x2: "オ",
            0x3: "ズ",
            0x4: "ナ",
            0x5: "ペ",
            0x6: "リ",
            0x7: "。",
        },
        0xB: {
            0x2: "カ",
            0x3: "セ",
            0x4: "ニ",
            0x5: "ホ",
            0x6: "ル",
            0x7: "「",
        },
        0xC: {
            0x2: "ガ",
            0x3: "ゼ",
            0x4: "ヌ",
            0x5: "ボ",
            0x6: "レ",
            0x7: "」",
        },
        0xD: {
            0x2: "キ",
            0x3: "ソ",
            0x4: "ネ",
            0x5: "ポ",
            0x6: "ロ",
            0x7: "、",
        },
        0xE: {
            0x2: "ギ",
            0x3: "ゾ",
            0x4: "ノ",
            0x5: "マ",
            0x6: "ヮ",
            0x7: "・",
        },
        0xF: {
            0x2: "ク",
            0x3: "タ",
            0x4: "ハ",
            0x5: "ミ",
            0x6: "ワ",
            0x7: "　",
        },
    }


class MosaicA(object):
    FINAL_BYTE = 0x32

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class MosaicB(object):
    FINAL_BYTE = 0x33

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class MosaicC(object):
    FINAL_BYTE = 0x34

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class MosaicD(object):
    FINAL_BYTE = 0x35

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class ProportionalAlphanumeric(object):
    FINAL_BYTE = 0x36

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class ProportionalHiragana(object):
    FINAL_BYTE = 0x37

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class ProportionalKatakana(object):
    FINAL_BYTE = 0x38

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class JISX0201Katakana(object):
    FINAL_BYTE = 0x49

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class JISCompatiblePlane1(object):
    FINAL_BYTE = 0x39

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class JISCompatiblePlane2(object):
    FINAL_BYTE = 0x3A

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class AdditionalSymbols(object):
    FINAL_BYTE = 0x3B

    def __init__(self):
        pass

    @staticmethod
    def decode(b, f):
        raise UnimplimentedError()


class Macro(object):
    FINAL_BYTE = 0x70

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return "{n} {s}".format(
            n=self.__class__.__name__, s=" ".join("{:#x}".format(x) for x in self._args)
        )

    @staticmethod
    def decode(b, f):
        return Macro(b, f)


class DRCS0(object):
    """0 is the 2 byte DRCS encoding"""

    FINAL_BYTE = 0x40

    def __init__(self, b, f):
        self._args = [b]
        hi = b
        lo = read.ucb(f)  # read second byte of the 2-byte DRCS-0 code
        self._args.append(lo)

        # Normalize GR (A1–FE) -> GL (21–7E) for both bytes
        row = normalize_94(hi)
        cell = normalize_94(lo)

        # Optional sanity checks (good for debugging bad streams)
        if not (0x21 <= row <= 0x7E and 0x21 <= cell <= 0x7E):
            print(
                "WARNNG: Invalid DRCS-0 code: row=%02X cell=%02X (raw %02X %02X)", row, cell, hi, lo
            )
            self.row = row
            self.col = cell
            self.glyph = None
            return

        self.row = row
        self.col = cell

        # DRCS-0 uses set_id=0, code = packed(row,cell)
        set_id = 0
        code = drcs0_pack(row, cell)  # (row<<8)|cell with bytes already normalized
        self.glyph = DRCS_CACHE.get(set_id, code)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return "DRCS group 0:"

    @staticmethod
    def decode(b, f):
        return DRCS0(b, f)


class DRCS1(object):
    FINAL_BYTE = 0x41

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(1, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 1 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS1(b, f)


class DRCS2(object):
    FINAL_BYTE = 0x42

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(2, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify to"""
        return f"<DRCS group 2 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS2(b, f)


class DRCS3(object):
    FINAL_BYTE = 0x43

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(3, n_64)

    def glyph(self):
        return self.glyph

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"DRCS group 3: id: {self._normalized_character_id}."

    @staticmethod
    def decode(b, f):
        return DRCS3(b, f)


class DRCS4(object):
    FINAL_BYTE = 0x44

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(4, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 4 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS4(b, f)


class DRCS5(object):
    FINAL_BYTE = 0x45

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(5, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 5 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS5(b, f)


class DRCS6(object):
    FINAL_BYTE = 0x46

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(6, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 6 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS6(b, f)


class DRCS7(object):
    FINAL_BYTE = 0x47

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(7, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 7 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS7(b, f)


class DRCS8(object):
    FINAL_BYTE = 0x48

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(8, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 8 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS8(b, f)


class DRCS9(object):
    FINAL_BYTE = 0x49

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(9, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 9 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS9(b, f)


class DRCS10(object):
    FINAL_BYTE = 0x4A

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(10, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 10 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS10(b, f)


class DRCS11(object):
    FINAL_BYTE = 0x4B

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(11, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 11 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS11(b, f)


class DRCS12(object):
    FINAL_BYTE = 0x4C

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(12, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 12 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS12(b, f)


class DRCS13(object):
    FINAL_BYTE = 0x4D

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(13, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"DRCS group 13: id: {self._normalized_character_id}."

    @staticmethod
    def decode(b, f):
        return DRCS13(b, f)


class DRCS14(object):
    FINAL_BYTE = 0x4E

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(14, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 14 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS14(b, f)


class DRCS15(object):
    FINAL_BYTE = 0x4F

    def __init__(self, b, f):
        self._args = []
        self._args.append(b)
        n_64 = normalize_94(b)
        self._normalized_character_id = n_64
        self.glyph = DRCS_CACHE.get(15, n_64)

    def __len__(self):
        return len(self._args)

    def __str__(self):
        """stringify"""
        return f"<DRCS group 15 id: {self._normalized_character_id}>"

    @staticmethod
    def decode(b, f):
        return DRCS15(b, f)


# ARIB STD-B24 Table 7-3 Classification of code set and Final Byte (pg.57)
CODE_SET_TABLE = {
    Kanji.FINAL_BYTE: Kanji.decode,
    Alphanumeric.FINAL_BYTE: Alphanumeric.decode,
    Hiragana.FINAL_BYTE: Hiragana.decode,
    Katakana.FINAL_BYTE: Katakana.decode,
    MosaicA.FINAL_BYTE: MosaicA.decode,
    MosaicB.FINAL_BYTE: MosaicB.decode,
    MosaicC.FINAL_BYTE: MosaicC.decode,
    MosaicD.FINAL_BYTE: MosaicD.decode,
    ProportionalAlphanumeric.FINAL_BYTE: ProportionalAlphanumeric.decode,
    ProportionalHiragana.FINAL_BYTE: ProportionalHiragana.decode,
    ProportionalKatakana.FINAL_BYTE: ProportionalKatakana.decode,
    JISX0201Katakana.FINAL_BYTE: JISX0201Katakana.decode,
    JISCompatiblePlane1.FINAL_BYTE: JISCompatiblePlane1.decode,
    JISCompatiblePlane2.FINAL_BYTE: JISCompatiblePlane2.decode,
    AdditionalSymbols.FINAL_BYTE: AdditionalSymbols.decode,
    Macro.FINAL_BYTE: Macro.decode,
    DRCS0.FINAL_BYTE: DRCS0.decode,
    DRCS1.FINAL_BYTE: DRCS1.decode,
    # DRCS2.FINAL_BYTE : DRCS2.decode,#TODO: fix final byte key overlap with non-DRCS
    DRCS3.FINAL_BYTE: DRCS3.decode,
    DRCS4.FINAL_BYTE: DRCS4.decode,
    DRCS5.FINAL_BYTE: DRCS5.decode,
    DRCS6.FINAL_BYTE: DRCS6.decode,
    DRCS7.FINAL_BYTE: DRCS7.decode,
    DRCS8.FINAL_BYTE: DRCS8.decode,
    DRCS9.FINAL_BYTE: DRCS9.decode,
    # DRCS10.FINAL_BYTE : DRCS10.decode,#TODO: fix final byte key overlap with non-DRCS
    DRCS11.FINAL_BYTE: DRCS11.decode,
    DRCS12.FINAL_BYTE: DRCS12.decode,
    DRCS13.FINAL_BYTE: DRCS13.decode,
    DRCS14.FINAL_BYTE: DRCS14.decode,
    DRCS15.FINAL_BYTE: DRCS15.decode,
}


def in_code_set_table(b):
    """Is this in the code table"""
    return b in CODE_SET_TABLE


def code_set_from_final_byte(b, f):
    """Given the final byte of a code set control sequence
    return an object representing that code set and its decoding
    """
    return CODE_SET_TABLE[b](b, f)


def code_set_handler_from_final_byte(b):
    """Given the final byte of a code set control sequence
    return an object representing that code set and its decoding
    """
    return CODE_SET_TABLE[b]
