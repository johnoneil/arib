# vim: set ts=2 expandtab:
"""
Module: control_characters.py
Desc: ARIB (Japanese Closed Caption) Control character support
Author: John O'Neil
Email: oneil.john@gmail.com
DATE: Sunday, March 9th 2014

"""

from arib import read
from arib.code_set import code_set_handler_from_final_byte
from arib.code_set import in_code_set_table
from arib.arib_exceptions import DecodingError

DEBUG = False


class NUL(object):
    """Null
    Control code, which can be added or deleted without effecting to
    information content.
    """

    CODE = 0x00

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "NUL"

    @staticmethod
    def handler(f):
        return NUL(f)


class SP(object):
    """Space"""

    CODE = 0x20

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return " "

    @staticmethod
    def handler(f):
        return SP(f)


class DEL(object):
    """Delete"""

    # See control character table 7-14 on page 89 arib std b-24
    CODE = 0x7F

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "DEL"

    @staticmethod
    def handler(f):
        return DEL(f)


class BEL(object):
    """Bell
    Control code used when calling attention (alarm or signal)
    """

    CODE = 0x07

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "BEL"

    @staticmethod
    def handler(f):
        return BEL(f)


class APB(object):
    """Active position backward
    Active position goes backward along character path in the length of
    character path of character field. When the reference point of the character
    field exceeds the edge of display area by this movement, move in the
    opposite side of the display area along the character path of the active
    position, for active position up.
    """

    CODE = 0x08

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "APB"

    @staticmethod
    def handler(f):
        return APB(f)


class APF(object):
    """Active position forward
    Active position goes forward along character path in the length of
    character path of character field. When the reference point of the character
    field exceeds the edge of display area by this movement, move in the
    opposite side of the display area along the character path of the active
    position, for active position down.
    """

    CODE = 0x09

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "APF"

    @staticmethod
    def handler(f):
        return APF(f)


class APD(object):
    """Active position down
    Moves to next line along line direction in the length of line direction of
    the character field. When the reference point of the character field exceeds
    the edge of display area by this movement, move to the first line of the
    display area along the line direction.
    """

    CODE = 0x0A

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "APD"

    @staticmethod
    def handler(f):
        return APD(f)


class APU(object):
    """Active position up
    Moves to the previous line along line direction in the length of line
    direction of the character field. When the reference point of the character
    field exceeds the edge of display area by this movement, move to the last
    line of the display area along the line direction.
    """

    CODE = 0x0B

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "AP"

    @staticmethod
    def handler(f):
        return APU(f)


class CS(object):
    """Clear screen
    Display area of the display screen is erased.
    """

    CODE = 0x0C

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<clear screen>"

    @staticmethod
    def handler(f):
        return CS(f)


class APR(object):
    """Active position return
    Active position down is made, moving to the first position of the same
    line.
    """

    CODE = 0x0D

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "APR"

    @staticmethod
    def handler(f):
        return APR(f)


class LS1(object):
    """Locking shift 1
    Code to invoke character code set.
    Sets GL code area to current G1 code set
    """

    CODE = 0x0E

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "LS1"

    @staticmethod
    def handler(f):
        return LS1(f)


class LS0(object):
    """Locking shift 0
    Code to invoke character code set.
    Sets GL code area to the current G0 code set
    """

    CODE = 0x0F

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "LS0"

    @staticmethod
    def handler(f):
        return LS0(f)


class PAPF(object):
    """Parameterized active position forward
    Active position forward is made in specified times by parameter P1 (1
    byte).
    Parameter P1 shall be within the range of 04/0 to 07/15 and time shall be
    specified within the range of 0 to 63 in binary value of 6-bit from b6 to b1.
    (b8 and b7 are not used.)
    """

    CODE = 0x16

    def __init__(self, f):
        # read the single byte paramter for now but ignore its effect on text placement
        # TODO: implement proper screen text placement
        read.ucb(f)

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 2

    def __str__(self):
        return "<PAPF>"

    @staticmethod
    def handler(f):
        return PAPF(f)


class CAN(object):
    """Cancel
    From the current active position to the end of the line is covered with
    background colour in the width of line direction in the current character
    field. Active position is not moved.
    """

    CODE = 0x18

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class SS2(object):
    """Single shift 2
    Code to invoke character code set.
    Sets the GL code area to the G2 code set for one character
    """

    CODE = 0x19

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "SS2"

    @staticmethod
    def handler(f):
        return SS2(f)


class LS2(object):
    """Class only generated by ESC sequence below.
    Represents Locking shift in GL area to current G2 codeset
    """

    CODE = 0x6E

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 2

    def __call__(self, decoder):
        """cause in  INVOCATION change on decoder"""
        # print 'setting GL to G2 with contents {g}'.format(g=str(type(decoder._G2.get())))
        decoder._GL = decoder._G2

    def __str__(self):
        return "LS2"

    @staticmethod
    def handler(f=None):
        return LS2(f)


class LS3(object):
    """Class only generated by ESC sequence below.
    Represents Locking shift in GL area to current G3 codeset
    """

    CODE = 0x6F

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 2

    def __call__(self, decoder):
        """cause in  INVOCATION change on decoder"""
        decoder._GL = decoder._G3

    def __str__(self):
        return "LS3"

    @staticmethod
    def handler(f=None):
        return LS3(f)


class LS1R(object):
    """Class only generated by ESC sequence below.
    Represents Locking shift in GR area to current G1 codeset
    """

    CODE = 0x7E

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 2

    def __call__(self, decoder):
        """cause in  INVOCATION change on decoder"""
        decoder._GR = decoder._G1

    def __str__(self):
        return "LS1R"

    @staticmethod
    def handler(f=None):
        return LS1R(f)


class LS2R(object):
    """Class only generated by ESC sequence below.
    Represents Locking shift in GR area to current G2 codeset
    """

    CODE = 0x7D

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 2

    def __call__(self, decoder):
        """cause in  INVOCATION change on decoder"""
        decoder._GR = decoder._G2

    def __str__(self):
        return "LS2R"

    @staticmethod
    def handler(f=None):
        return LS2R(f)


class LS3R(object):
    """Class only generated by ESC sequence below.
    Represents Locking shift in GR area to current G3 codeset
    """

    CODE = 0x7C

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 2

    def __call__(self, decoder):
        """cause in  INVOCATION change on decoder"""
        decoder._GR = decoder._G3

    def __str__(self):
        return "LS3R"

    @staticmethod
    def handler(f=None):
        return LS3R(f)


INVOCATION_TABLE = {
    LS2.CODE: LS2.handler,
    LS3.CODE: LS3.handler,
    LS1R.CODE: LS1R.handler,
    LS2R.CODE: LS2R.handler,
    LS3R.CODE: LS3R.handler,
}


class G0(object):
    CODE = 0x28

    def __init__(self):
        pass

    @staticmethod
    def factory():
        return G0()

    def load(self, esc, f):
        b = read.ucb(f)
        if b == DRCS.CODE:
            if DEBUG:
                print("G0 DRCS {:#x}".format(b))
            esc._args.append(b)
            DRCS.handler(esc, f)
        elif in_code_set_table(b):
            if DEBUG:
                print("G0 CODESET {:#x}".format(b))
            esc._args.append(b)
        else:
            raise DecodingError()

    def designate(self, decoder, final_byte):
        """cause in  Designation change on decoder"""
        decoder._G0.set(code_set_handler_from_final_byte(final_byte))


class G1(object):
    CODE = 0x29

    def __init__(self):
        pass

    @staticmethod
    def factory():
        return G1()

    def load(self, esc, f):
        b = read.ucb(f)
        if b == DRCS.CODE:
            if DEBUG:
                print("G1 DRCS {:#x}".format(b))
            esc._args.append(b)
            DRCS.handler(esc, f)
        elif in_code_set_table(b):
            if DEBUG:
                print("G1 CODESET {:#x}".format(b))
            esc._args.append(b)
        else:
            raise DecodingError()

    def designate(self, decoder, final_byte):
        """cause in  Designation change on decoder"""
        decoder._G1.set(code_set_handler_from_final_byte(final_byte))


class G2(object):
    CODE = 0x2A

    def __init__(self):
        pass

    @staticmethod
    def factory():
        return G2()

    def load(self, esc, f):
        b = read.ucb(f)
        if b == DRCS.CODE:
            if DEBUG:
                print("G2 DRCS {:#x}".format(b))
            esc._args.append(b)
            DRCS.handler(esc, f)
        elif in_code_set_table(b):
            if DEBUG:
                print("G2 CODESET {:#x}".format(b))
            esc._args.append(b)
        else:
            raise DecodingError()

    def designate(self, decoder, final_byte):
        """cause in  Designation change on decoder"""
        decoder._G2.set(code_set_handler_from_final_byte(final_byte))


class G3(object):
    CODE = 0x2B

    def __init__(self):
        pass

    @staticmethod
    def factory():
        return G3()

    def load(self, esc, f):
        b = read.ucb(f)
        if b == DRCS.CODE:
            if DEBUG:
                print("G3 DRCS {:#x}".format(b))
            esc._args.append(b)
            DRCS.handler(esc, f)
        elif in_code_set_table(b):
            if DEBUG:
                print("G3 CODESET {:#x}".format(b))
            esc._args.append(b)
        else:
            raise DecodingError()

    def designate(self, decoder, final_byte):
        """cause in  Designation change on decoder"""
        decoder._G3.set(code_set_handler_from_final_byte(final_byte))


DESIGNATION_TABLE = {
    G0.CODE: G0.factory,
    G1.CODE: G1.factory,
    G2.CODE: G2.factory,
    G3.CODE: G3.factory,
}


class TwoByte(object):
    CODE = 0x24

    @staticmethod
    def handler(esc, f):
        b = read.ucb(f)
        if in_code_set_table(b):
            esc._args.append(b)
            # return  code_set_from_final_byte(b, f)
        elif b in DESIGNATION_TABLE:
            esc._args.append(b)
            d = DESIGNATION_TABLE[b]()
            d.load(esc, f)
        else:
            raise DecodingError()


class DRCS(object):
    CODE = 0x20

    @staticmethod
    def handler(esc, f):
        b = read.ucb(f)
        if DEBUG:
            print("DRCS {:#x}".format(b))
        if in_code_set_table(b):
            esc._args.append(b)
        else:
            # return  code_set_from_final_byte(b, f)
            raise DecodingError()


class ESC(object):
    """Escape
    Code for code extension.
    """

    CODE = 0x1B
    # Mapping by ESC led byte patterns to code "designations"
    # refer to ARIB STD B-24 table 7-12 (pg. 56)
    GRAPHIC_SETS_TABLE = [
        [
            G0.CODE,
        ],
        [
            G1.CODE,
        ],
        [
            G2.CODE,
        ],
        [
            G3.CODE,
        ],
        [
            TwoByte.CODE,
            G0.CODE,
        ],
        [
            TwoByte.CODE,
            G1.CODE,
        ],
        [
            TwoByte.CODE,
            G2.CODE,
        ],
        [
            TwoByte.CODE,
            G3.CODE,
        ],
        [
            G0.CODE,
            DRCS.CODE,
        ],
        [
            G1.CODE,
            DRCS.CODE,
        ],
        [
            G2.CODE,
            DRCS.CODE,
        ],
        [
            G3.CODE,
            DRCS.CODE,
        ],
        [
            TwoByte.CODE,
            G0.CODE,
            DRCS.CODE,
        ],
        [
            TwoByte.CODE,
            G1.CODE,
            DRCS.CODE,
        ],
        [
            TwoByte.CODE,
            G2.CODE,
            DRCS.CODE,
        ],
        [
            TwoByte.CODE,
            G3.CODE,
            DRCS.CODE,
        ],
    ]

    def __init__(self, f):
        """the interpretation and bytes read
        after reading 'ESC' can be complex. Here
        We'll just attempt to successfully read all
        required args, and leave interpretation for later
        """
        b = read.ucb(f)
        if DEBUG:
            print("esc first byte is " + "{:#x}".format(b))
        self._args = []
        self._args.append(b)

        if b in INVOCATION_TABLE:
            if DEBUG:
                print("ESC INVOCATION {:#x}".format(b))
            INVOCATION_TABLE[b](f)
            # self._args.append(next)
        elif b in DESIGNATION_TABLE:
            if DEBUG:
                print("ESC DESIGNATION {:#x}".format(b))
            d = DESIGNATION_TABLE[b]()
            d.load(self, f)
            # self._args.append(next)
        elif b == TwoByte.CODE:
            if DEBUG:
                print("ESC TWO BYTE {:#x}".format(b))
            TwoByte.handler(self, f)
            # self._args.append(next)
        else:
            raise DecodingError()

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return len(self._args) + 1

    def __str__(self):
        return "ESC {args}".format(args=" ".join("{:#x}".format(x) for x in self._args))

    def is_invocation(self):
        """Return whether this ESC control sequence
        describes an invocation or not
        """
        return self._args[0] in INVOCATION_TABLE

    def invoke(self, decoder):
        """Carry out an INVOCATION on a decoder object"""
        if not self.is_invocation():
            raise DecodingError("Attempting to get invocation from ESC sequence that has none.")
        invocation = INVOCATION_TABLE[self._args[0]]()
        if DEBUG:
            print("invoking {:#x}".format(self._args[0]))
        invocation(decoder)

    def is_designation(self):
        # print 'ESC ' + str(self)
        if len(self._args) < 2:
            raise DecodingError()

        designation = self._args[:-1]
        return designation in ESC.GRAPHIC_SETS_TABLE

    def designate(self, decoder):
        """Carry out an INVOCATION on a decoder object"""
        if not self.is_designation():
            raise DecodingError("Attempting to get designation from ESC sequence that has none.")
        final_byte = self._args[-1]
        byte_pattern = self._args[:-1]
        if DEBUG:
            print("designating via final_byte {:#x}".format(final_byte))
        d = ESC.find_designation(byte_pattern)
        designation = DESIGNATION_TABLE[d]()
        designation.designate(decoder, final_byte)

    def to_designation(self):
        """Look at current ESC arguments and return their meaning
        as a change in mapping in designation to code set
        """
        if DEBUG:
            print("ESC " + str(self))
        if len(self._args) < 2:
            raise DecodingError()

        # strip the last byte of _args to examine, since it varies by final byte
        # (i.e. the final byte indicates the code set we'll change to)
        final_byte = self._args[-1]
        # TODO: check final_byte to make sure it's code_set or throw
        designation = self._args[:-1]
        if DEBUG:
            print("final byte: {b}".format(b=final_byte))
            print("designation: {d}".format(d=str(designation)))
        code_set = code_set_handler_from_final_byte(final_byte)
        d = 0
        if designation in ESC.GRAPHIC_SETS_TABLE:
            if DEBUG:
                print("designation in table")
            # for now i'm assuming i only need the designation g0-g3
            # and the final byte (to get the new code set)
            d = ESC.find_designation(designation)
        else:
            if DEBUG:
                print("not in table")
            raise DecodingError()
        return (d, code_set)

    @staticmethod
    def find_designation(byte_pattern):
        for i, pattern in enumerate(ESC.GRAPHIC_SETS_TABLE):
            if DEBUG:
                print(f"{byte_pattern} : {i} {pattern}")
            if byte_pattern == pattern:
                idx = i % len(DESIGNATION_TABLE)  # was 4; safer to use length
                if DEBUG:
                    print(f"found designation match at {pattern} at index {i} and desig {idx}")
                # dict is insertion-ordered in Py3.7+, so this matches your literal order
                return list(DESIGNATION_TABLE)[idx]
        raise KeyError(f"No designation for pattern: {byte_pattern!r}")

    @staticmethod
    def handler(f):
        """Most of these command handler just return an instance of the
        associated class. But ESC is more complex.
        Depending upon the character sequence, it can return several different
        class instances, each representing the different sequence. e.g.:
        <ESC><0x6e> --> LS2
        <ESC><0x7c> --> LS2R
        <ESC><0x24><0x2b><final byte> --> set 2 byte G3 code set in G area
        (GL or GR?)according to final byte
        <ESC><0X24><0x2b><0x20><final byte> --> set 2 byte DRCS into G3 code
        area according to final byte
        """
        return ESC(f)


class APS(object):
    """Active position set
    Specified times of active position down is made by P1 (1 byte) of the first
    parameter in line direction length of character field from the first position
    of the first line of the display area. Then specified times of active position
    forward is made by the second parameter P2 (1 byte) in the character path
    length of character field. Each parameter shall be within the range of 04/0
    to 07/15 and specify time within the range of 0 to 63 in binary value of 6-
    bit from b6 to b1. (b8 and b7 are not used.)
    """

    CODE = 0x1C

    def __init__(self, f):
        self._args = []
        self._args.append(read.ucb(f) & 0x3F)  # p1
        self._args.append(read.ucb(f) & 0x3F)  # p2
        if DEBUG:
            print("APS: --> {:#d},{:#d}>".format(self._args[0], self._args[1]).encode("utf-8"))

    @property
    def col(self):
        return self._args[1]

    @property
    def row(self):
        return self._args[0]

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return len(self._args) + 1

    def __str__(self):
        return "\n<Screen Posiiton to {:#d},{:#d}>".format(self._args[0], self._args[1])

    @staticmethod
    def handler(f):
        return APS(f)


class SS3(object):
    """Single shift 3
    Code to invoke character code set.
    Sets the GL code area to the G3 code set for one character
    """

    CODE = 0x1D

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "SS3"

    @staticmethod
    def handler(f):
        return SS3(f)


class RS(object):
    """Record separator
    It is information division code and declares identification and introduction
    of data header.
    """

    CODE = 0x1E

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "RS"

    @staticmethod
    def handler(f):
        pass


class US(object):
    """Unit separator
    It is information division code and declares identification and introduction
    of data unit.
    """

    CODE = 0x1F

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "US"

    @staticmethod
    def handler(f):
        pass


# Color support


class BKF(object):
    """Foreground colour: black, CMLA: 0BLACK FOREGROUND
    ( This indicates that foreground colour is set to black and colour map lower
    address (CMLA) specifying colouring value of the portrayal plane is set to 0.
    Same as follows.)
    """

    CODE = 0x80

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<black>"

    @staticmethod
    def handler(f):
        return BKF(f)


class COL(object):
    """Color Controls
    Colour control COL P1 (1 byte)
    Sets foreground colour, background colour, half foreground colour, half
    background colour and CMLA by the parameter.
    Colour between foreground and background in gradation font is defined that
    colour near to foreground colour is half foreground colour and colour near to
    background colour is half background colour.
    """

    CODE = 0x90

    def __init__(self, f):
        self._args = []
        p1 = read.ucb(f)
        self._args.append(p1)
        if p1 == 0x20:
            self._args.append(read.ucb(f))

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return len(self._args) + 1

    def __str__(self):
        return "COL {args}".format(args=" ".join("{:#x}".format(x) for x in self._args))

    @staticmethod
    def handler(f):
        return COL(f)


class RDF(object):
    """Foreground colour: red"""

    CODE = 0x81

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<red>"

    @staticmethod
    def handler(f):
        return RDF(f)


class FLC(object):
    """Flashing control
    Specifies the beginning and the end of flashing and the differences of the
    normal phase and the reverse phase by the parameter P1 (1 byte).
    """

    CODE = 0x91

    def __init__(self, f):
        self._args = []
        self._args.append(read.ucb(f))

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return len(self._args) + 1

    def __str__(self):
        return "FLC {args}".format(args=" ".join("{:#x}".format(x) for x in self._args))

    @staticmethod
    def handler(f):
        return FLC(f)


class GRF(object):
    """Foreground colour: green"""

    CODE = 0x82

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<green>"

    @staticmethod
    def handler(f):
        return GRF(f)


class CDC(object):
    """Conceal display controls
    Specifies the beginning and end of concealing and the type of concealing by
    the parameter.
    """

    CODE = 0x92

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class YLF(object):
    """Foreground colour: yellow"""

    CODE = 0x83

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<yellow>"

    @staticmethod
    def handler(f):
        return YLF(f)


class POL(object):
    """Pattern Polarity Controls"""

    CODE = 0x93

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class BLF(object):
    """Foreground colour: blue"""

    CODE = 0x84

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<blue>"

    @staticmethod
    def handler(f):
        return BLF(f)


class WMM(object):
    """Writing mode modification
    This Specifies the changing of the writing mode to the memory of display by
    parameter P1 (1 byte).
    For middle colour of gradation font, both set portions of half foreground colour
    Writing Mode and half background colours are to be treated as foreground colour.
    """

    CODE = 0x94

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class MGF(object):
    """Foreground colour: magenta"""

    CODE = 0x85

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<magenta>"

    @staticmethod
    def handler(f):
        return MGF(f)


class MACRO(object):
    """Macro command
    Macro definition start, macro definition mode and macro definition end is set
    by parameter P1 (1 byte).
    """

    CODE = 0x95

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class CNF(object):
    """Foreground colour: cyan"""

    CODE = 0x86

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<cyan>"

    @staticmethod
    def handler(f):
        return CNF(f)


class WHF(object):
    """White foreground color (text color)"""

    CODE = 0x87

    def __init__(self, f):
        pass

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<white>"

    @staticmethod
    def handler(f):
        return WHF(f)


class HLC(object):
    """Highlighting character block
    Starting and ending of enclosure are set by parameter P1 (1 byte).
    """

    CODE = 0x97

    def __init__(self, f):
        self._code = read.ucb(f)
        self._start = False
        if self._code & 0x1:
            self._start = True

    def __len__(self):
        return 2

    def __str__(self):
        if self._start:
            return "<Highlight start>"
        else:
            return "<Highlight end>"

    @staticmethod
    def handler(f):
        return HLC(f)


class SSZ(object):
    """Small size
    Specifies the character size is small.
    """

    CODE = 0x88

    def __init__(self, f):
        if DEBUG:
            print("SSZ: --> 0x88".encode("utf-8"))

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<Small Text>"

    @staticmethod
    def handler(f):
        return SSZ(f)


class RPC(object):
    """Repeat character
    The repeat code RPC with one parameter P1 (1 byte) causes a displayable
    character or mosaic that immediately follows the code, to be displayed a
    number of times specified by the parameter P1.
    """

    CODE = 0x98

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class MSZ(object):
    """Middle size
    Specifies the character size is middle.
    """

    CODE = 0x89

    def __init__(self, f):
        if DEBUG:
            print("MSZ: --> 0x89".encode("utf-8"))

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<Medium Text>"

    @staticmethod
    def handler(f):
        return MSZ(f)


class SPL(object):
    """Stop Lining
    Underlining and mosaic division process is terminated.
    """

    CODE = 0x1D

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class NSZ(object):
    """Normal size
    Specifies the character size is normal.
    """

    CODE = 0x8A

    def __init__(self, f):
        if DEBUG:
            print("NSZ: --> 0x8a".encode("utf-8"))

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return 1

    def __str__(self):
        return "<Normal Text>"

    @staticmethod
    def handler(f):
        return NSZ(f)


class STL(object):
    """Start lining
    The composition of mosaic A and B in the display after this code, is not made.
    When mosaic is included during composing non-spacing and composition
    command, dividing process (mosaic element is classified in small elements by
    Start Lining
    1/2 across direction and 1/3 length making space surrounding them) should be
    made after composition. In other cases, make underline
    """

    CODE = 0x9A

    def __init__(self, f):
        pass

    @staticmethod
    def handler(f):
        pass


class SZX(object):
    """Character size controls
    The character size is set in parameter P1 (1 byte).
    """

    CODE = 0x8B

    def __init__(self, f):
        if DEBUG:
            print("SZX: --> 0x8b".encode("utf-8"))

    @staticmethod
    def handler(f):
        pass


class CSI(object):
    """Control Sequence Initiator
    Code for code system extension indicated in table 7-14.
    """

    CODE = 0x9B

    def __init__(self, f):
        """read from stream until we get "space" and then our CSI
        specific control character.
        """
        self._args = []
        c = read.ucb(f)
        while c != 0x20:
            self._args.append(c)
            c = read.ucb(f)
        self._args.append(c)
        # lastly read the command code
        c = read.ucb(f)
        self._args.append(c)

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return len(self._args) + 1

    def __str__(self):
        try:
            # Use ':c' (no '#'), and handle 1-byte bytes by taking x[0]
            return '<CS:"{seq}">'.format(
                seq="".join("{:c}".format(x if isinstance(x, int) else x[0]) for x in self._args)
            )
        except (ValueError, TypeError):
            # Fallback to hex; handle 1-byte bytes the same way
            return '<CS:"{seq}">'.format(
                seq="".join(
                    ":{h}".format(h=hex(x if isinstance(x, int) else x[0])) for x in self._args
                )
            )

    @staticmethod
    def handler(f):
        return CSI(f)


class TIME(object):
    """Time
    The time control designation is made by parameter P1 (1 byte) and P2 (1 byte)
    """

    CODE = 0x9D

    def __init__(self, f):
        self._args = []
        self._args.append(read.ucb(f))
        self._args.append(read.ucb(f))

    def __len__(self):
        """Defiing len() operator to help
        in calculating bytes read
        """
        return len(self._args) + 1

    def __str__(self):
        return "TIME {args}".format(args=" ".join("{:#x}".format(x) for x in self._args))

    @staticmethod
    def handler(f):
        return TIME(f)


COMMAND_TABLE = {
    NUL.CODE: NUL.handler,
    SP.CODE: SP.handler,
    DEL.CODE: DEL.handler,
    BEL.CODE: BEL.handler,
    APB.CODE: APB.handler,
    APF.CODE: APF.handler,
    APD.CODE: APD.handler,
    APU.CODE: APU.handler,
    CS.CODE: CS.handler,
    APR.CODE: APR.handler,
    LS1.CODE: LS1.handler,
    LS0.CODE: LS0.handler,
    PAPF.CODE: PAPF.handler,
    # CAN.CODE : CAN.handler,
    SS2.CODE: SS2.handler,
    ESC.CODE: ESC.handler,
    APS.CODE: APS.handler,
    SS3.CODE: SS3.handler,
    # RS.CODE : RS.handler,
    # US.CODE : US.handler,
    BKF.CODE: BKF.handler,
    COL.CODE: COL.handler,
    RDF.CODE: RDF.handler,
    FLC.CODE: FLC.handler,
    GRF.CODE: GRF.handler,
    # CDC.CODE : CDC.handler,
    YLF.CODE: YLF.handler,
    # POL.CODE : POL.handler,
    BLF.CODE: BLF.handler,
    # WMM.CODE : WMM.handler,
    MGF.CODE: MGF.handler,
    # MACRO.CODE : MACRO.handler,
    CNF.CODE: CNF.handler,
    WHF.CODE: WHF.handler,
    HLC.CODE: HLC.handler,
    SSZ.CODE: SSZ.handler,
    # RPC.CODE : RPC.handler,
    MSZ.CODE: MSZ.handler,
    # SPL.CODE : SPL.handler,
    NSZ.CODE: NSZ.handler,
    # STL.CODE : STL.handler,
    # SZX.CODE : SZX.handler,
    CSI.CODE: CSI.handler,
    TIME.CODE: TIME.handler,
}


def is_control_character(char):
    """return True if this is an ARIB control character"""
    return char in COMMAND_TABLE


def handle_control_character(b, f):
    """
    handle a given control character read from stream f
    """
    return COMMAND_TABLE[b](f)
