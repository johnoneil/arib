import io
import arib.read as read


def test_split_buffer_basic_mutation():
    buf = [1, 2, 3, 4]
    prefix, remaining = read.split_buffer(2, buf)
    assert prefix == [1, 2]
    # the function should mutate the original list
    assert remaining is buf
    assert buf == [3, 4]


def test_split_buffer_insufficient_no_mutation():
    buf = [1]
    prefix, remaining = read.split_buffer(2, buf)
    assert prefix == []
    assert remaining is buf
    assert buf == [1]  # unchanged


def test__join_to_bytes_accepts_mixed_types():
    # ints, 1-byte bytes/bytearray, 1-char str
    data = [0x41, b"\x42", bytearray(b"\x43"), "D"]
    out = read._join_to_bytes(data)
    assert out == b"ABCD"


def test__join_to_bytes_errors():
    # wrong-length bytes
    try:
        read._join_to_bytes([b"\x00\x01"])
    except ValueError as e:
        assert "1-byte items" in str(e)
    else:
        raise AssertionError("Expected ValueError for multi-byte bytes")

    # wrong-length str
    try:
        read._join_to_bytes(["AB"])
    except ValueError as e:
        assert "1-char strings" in str(e)
    else:
        raise AssertionError("Expected ValueError for multi-char str")

    # unsupported type
    try:
        read._join_to_bytes([3.14])
    except TypeError as e:
        assert "Unsupported element type" in str(e)
    else:
        raise AssertionError("Expected TypeError for unsupported element")


def test_dump_list_formats_hex(capsys):
    class IntLike:
        def __int__(self):  # number-like fallback
            return 7

    lst = [0, 1, b"\x0a", bytearray(b"\xff"), "A", IntLike(), None]
    read.dump_list(lst)
    out = capsys.readouterr().out.strip()
    # 0x0 0x1 0xa 0xff 0x41 0x7 0x0
    assert out.split() == ["0x0", "0x1", "0xa", "0xff", "0x41", "0x7", "0x0"]


def test__read_exact_file_and_eof():
    f = io.BytesIO(b"\x01\x02")
    assert read._read_exact_file(f, 2) == b"\x01\x02"
    f2 = io.BytesIO(b"\x01")
    try:
        read._read_exact_file(f2, 2)
    except read.EOFError:
        pass
    else:
        raise AssertionError("Expected EOFError for short read")


def test__read_exact_any_from_list_and_eof():
    buf = [0x10, 0x11, 0x12]
    assert read._read_exact_any(buf, 2) == b"\x10\x11"
    # buffer should be mutated
    assert buf == [0x12]
    # now ask for more than available
    try:
        read._read_exact_any(buf, 2)
    except read.EOFError:
        pass
    else:
        raise AssertionError("Expected EOFError when list too short")


def test_ucb_usb_ui3b_uib_ulb_from_file():
    # Bytes:  AB | 01 02 | 00 00 03 | 00 00 00 04 | 00..00 05 (8 bytes big-endian)
    payload = bytes(
        [
            0xAB,
            0x01,
            0x02,
            0x00,
            0x00,
            0x03,
            0x00,
            0x00,
            0x00,
            0x04,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
            0x05,
        ]
    )
    f = io.BytesIO(payload)

    assert read.ucb(f) == 0xAB
    assert read.usb(f) == 0x0102
    assert read.ui3b(f) == 0x000003
    assert read.uib(f) == 0x00000004
    assert read.ulb(f) == 0x0000000000000005


def test_ucb_usb_ui3b_uib_ulb_from_list():
    assert read.ucb([0xFF]) == 0xFF
    assert read.usb([0x12, 0x34]) == 0x1234
    assert read.ui3b([0x00, 0x01, 0x02]) == 0x000102
    assert read.uib([0x00, 0x00, 0x01, 0x02]) == 0x00000102
    assert read.ulb([0, 0, 0, 0, 0, 0, 0, 7]) == 7


def test_usb_debug_print_branch(capsys):
    # Only prints when DEBUG is True AND reading from a non-list (file-like)
    orig = read.DEBUG
    read.DEBUG = True
    try:
        f = io.BytesIO(b"\x01\x02")
        _ = read.usb(f)
        out = capsys.readouterr().out
        assert "usb:" in out and "0x1" in out and "0x2" in out
    finally:
        read.DEBUG = orig


def test_buffer_reads_n_bytes_and_eof():
    f = io.BytesIO(b"abcde")
    assert read.buffer(f, 3) == b"abc"
    # next read for 3 should fail (only 2 left)
    try:
        read.buffer(f, 3)
    except read.EOFError:
        pass
    else:
        raise AssertionError("Expected EOFError on short read")


def test_buffer_from_list_mixed_item_types():
    # Make sure _read_exact_any + _join_to_bytes cope with mixed item types
    buf = [0x41, b"\x42", bytearray(b"\x43"), "D", 0x45]
    got = read.buffer(buf, 5)
    assert got == b"ABCDE"
    assert buf == []  # consumed
