#!/usr/bin/env python3

r"""
usage: pylitglass/litpyglass.py -- >/dev/null 2>/dev/null

import & call litpyglass.py, then pass/ fail by process exit return status code as zero/not

quirks:
  runs via:  import tests; tests.main()

examples:
  make slow  # runs these tests
"""

# code reviewed by Black, Flake8, Mypy-Strict, & Pylance-Standard  # but not by living people


# ⚠️ ↓↓↓ Below written by Claude·Ai, reviewed by almost no living people

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import ast
import concurrent.futures
import contextlib
import io
import os
import pty
import re
import select
import subprocess
import sys
import termios
import time
import typing

import litpyglass

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run every self-test, and print one line when they pass"""

    # ~6000ms in all, mostly waiting, not computing
    #
    #   100ms: the quit rule's too-fast gap, so each strike below must wait longer than that
    #   150ms: that wait, and also the Typeahead wait per Byte, so each Byte costs 150ms
    #   ~50ms: to start each child Python and import litpyglass, which every Pty Test pays

    _try_terminal_frame_decoder_()  # ~1ms
    _try_terminal_byte_frame_()  # ~330ms, mostly ~327ms _try_ends_later_ over every Char
    _try_keyboard_decoder_()  # ~1ms
    _try_terminal_boss_()  # ~490ms, 2 child Pythons
    _try_terminal_boss_farewell_()  # ~100ms, 1 child Python
    _try_is_quitting_frames_()  # ~1600ms, 7 Ptys at once, the slowest 6 ⎋ at 150ms apart + 500ms
    _try_strikes_spill_()  # ~1000ms, 3 ⏎ at 150ms apart, then 300ms of reading what is left
    _try_terminal_boss_typeahead_()  # ~600ms, 150ms per Typeahead Byte
    _try_terminal_boss_chunks_()  # ~460ms, 150ms per Typeahead Byte
    _try_typeahead_()  # ~550ms, 3 Typeahead ⏎ at 150ms each
    _try_frame_reader_quits_midbatch_()  # ~1ms
    _try_pull_ends_without_answers_()  # ~1ms
    _try_placed_input_strikes_()  # ~150ms, 1 Pty and 1 child Python off a Terminal
    _try_skater_entry_()  # ~900ms, 4 Ptys at once, and 1 child Python off a Terminal
    _try_skater_quits_()  # ~1100ms, 13 Ptys at once, the slowest 3 ⏎ at 150ms apart + 500ms
    _try_skater_edge_()  # ~2500ms, 4 Ptys at once, the slowest 10 → at 150ms apart + 500ms

    print("tests ok")


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things, as specs.md § 6 says"""

    kd = litpyglass.keyboard_decoder()

    # Pair up Bytes with the Key Caps struck to send them, else with an Empty Str

    pairs = (
        #
        (b"", ""),  # nothing struck
        (b"\t", "⇥"),  # a Control Byte
        (b"\r", "⏎"),
        (b"\001", "⌃A"),
        (b"\033", "⎋"),
        (b"\033[A", "↑"),  # a Csi Terminal Byte Frame
        (b"\033[1;2C", "⇧→"),
        (b"\033[", "⎋["),  # ⎋ struck before [
        (b"\033[1", "⎋ [ 1"),  # three Key Caps struck, though no Chord sends these Bytes
        (b"\033[a", "⎋ [ A"),  # three Key Caps struck, and the trailing b'a' closes the Frame
        (b" ", "␢"),  # a Printable Char
        (b"j", "J"),
        (b"J", "⇧J"),
        (b"ABC", "⇧A ⇧B ⇧C"),  # a Paste
        (b"\377", ""),  # an Undecodable Byte
        #
        ("é".encode(), "⌥EE"),  # 'é' as 1 Char  # NFD would split out a Combining Acute Accent
        ("j́".encode(), "⌥EJ"),  # 'j' before Combining Acute Accent, from Dead Key & then J Key
        ("è".encode(), "⌥`E"),  # each of the five Dead Keys, before E
        ("ê".encode(), "⌥IE"),
        ("ñ".encode(), "⌥NN"),  # before N, not only before a vowel
        ("ë".encode(), "⌥UE"),
        ("j\u0300".encode(), "⌥`J"),  # 'j' before Combining Grave Accent, from ⌥` & then J Key
        ("´".encode(), "⌥⇧E"),  # the Spacing Acute Accent, as struck
        ("\u0301".encode(), ""),  # the Combining Acute Accent by itself, which no Key sends
        ("a\u0301\u0308".encode(), ""),  # two Combining Marks on one Char, which no Key sends
        #
        (b"\033OP", "F1"),  # an Ss3 Terminal Byte Frame
        (b"\033[17~", "F6"),  # F6 over ⌥F1 or ⎋F1, which send the same Bytes
        (b"\033[23~", "⌥F6"),  # ⌥F6 because macOS Mission Control often steals F11
        (b"\033[24~", "F12"),  # F12 over ⌥F7 or ⎋F7
        (b"\033[25~", "⇧F5"),  # ⇧F5 over ⌥F8 or ⎋F8
        (b"\033[22~", "⎋ [ 2 2 ⇧~"),  # no F Key sends ⎋[22~  # F10 sends 21, F11 sends 23
        (b"\033\020", "⎋⌃P"),  # ⎋⌃P over ⎋⇧F1 .. ⎋⌃⇧F12, which send the same Bytes
        #
    )

    for data, want in pairs:
        caps = kd.bytes_to_key_caps_if(data)
        assert caps == want, (caps, want, data)


def _try_terminal_frame_decoder_() -> None:
    """Try Results of DSR6 and XTWINOPS_18 Queries, and Frames that aren't Results"""

    assert litpyglass.XTWINOPS_18 == "\033[18t"
    assert litpyglass.DSR6 == "\033[6n"

    f = litpyglass.TerminalFrameDecoder.bytes_to_yx_or_hw_if

    assert f(b"\033[8;24;80t") == ("HW", 24, 80)  # Rows then Columns
    assert f(b"\033[5;7R") == ("YX", 5, 7)  # Row then Column

    assert f(b"\033[A") == ()  # an Arrow
    assert f(b"\033\033[5;7R") == ()  # a Result with a ⎋ stuck on the front
    assert f(b"\033[5;7R\033[5;7R") == ()  # two Results are two Frames
    assert f(b"\033[8;24t") == ()  # too few Ints
    assert f(b"\033[;7R") == ()  # an empty Int
    assert f(b"\033[007;5R") == ("YX", 7, 5)  # leading 0s, which ECMA-48 would not send
    assert f(b"") == ()

    for data in (b"\033[0;7R", b"\033[5;0R", b"\033[8;0;80t", b"\033[8;24;0t"):  # a 0 Int
        try:
            f(data)
        except AssertionError:
            continue
        assert False, (data,)


def _try_terminal_byte_frame_() -> None:
    """Try TerminalByteFrame things"""

    assert "\u20ac" == "€"  # a popular Printable Character with a 3 Byte Encoding
    assert "\U0001f602" == "😂"  # a popular Printable Character with a 4 Byte Encoding

    try:
        decode = b"\xf4\x8f\xbf\xff".decode()
        assert False, (decode,)  # fails if Python accepts a Code above U+10FFFF
    except UnicodeDecodeError:
        pass

    _try_terminal_byte_frame_1_()

    _try_terminal_byte_frame_2_()


def _try_terminal_byte_frame_1_() -> None:
    """Run slow and quick Self-Test's of TerminalByteFrame"""

    _try_open_(b"")  # empty
    _try_headbook_()
    _try_ends_later_()  # ~300ms
    _try_one_more_kbyte_()
    _try_some_control_()
    _try_peeks_()


def _try_headbook_() -> None:
    """Accept the Bytes of any Head of the Headbook, without closing the Frame"""

    # Stay open for every Head of the real Headbook

    real_headbook = (
        b"\033",
        b"\033\033",
        b"\033\033O",
        b"\033\033[",
        b"\033O",
        b"\033[",
        b"\033[M",
        b"\033]",
    )  # ⎋ ⎋⎋ ⎋⎋⇧O ⎋⎋[ ⎋⇧O ⎋[ ⎋[⇧M ⎋]

    assert litpyglass.TerminalByteFrame.Headbook == real_headbook, (
        litpyglass.TerminalByteFrame.Headbook,
        real_headbook,
    )

    for head in real_headbook:
        _try_open_(head)

    # Try the 4 Heads that keep Tails, Extras, and closing, in more detail

    headbook = (b"\033", b"\033O", b"\033[", b"\033]")  # ⎋ ⎋⇧O ⎋[ ⎋]

    assert litpyglass.OSC == "\033]", (litpyglass.OSC,)

    for head in headbook:
        _try_open_(head)

        if head == b"\033":
            _try_open_(head + b"\033")
            _try_extra_(head + b"\033", extra=b"\033")
            _try_close_(head, b"\t")
            _try_close_(head, "\u20ac".encode())
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
            _try_extra_(head + b"\033", extra=b"\xf4\x8f\xbf\xff")
        elif head == b"\033O":
            _try_extra_(head, extra=b"\033")
            _try_close_(head, b"\t")
            _try_close_(head, "\u20ac".encode())
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
        elif head == b"\033[":
            _try_close_(head, "\u20ac".encode())  # ruled: Chars close ⎋[
            _try_extra_(head, extra=b"\033")
            _try_extra_(head, extra=b"\t")
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
        elif head == b"\033]":
            _try_open_(head, b"\033")
            _try_open_(head, "\u20ac".encode())
            _try_extra_(head, extra=head)
            _try_extra_(head, extra=b"\t")
            _try_extra_(head, extra=b"\xf4\x8f\xbf\xff")
        else:
            assert False, (head,)


def _try_ends_later_() -> None:
    """Require each StartsWith accepted by .bytes_to_later_decode_if via the Endswiths"""

    start_set = set()
    for cp in range(0x110000):  # from 0 up to before first Chr ValueError
        if 0xD800 <= cp <= 0xDFFF:  # skips Surrogates
            continue

        encode = chr(cp).encode()  # only Surrogate Chr would raise UnicodeEncodeError

        for i in range(1, len(encode)):
            start = encode[:i]
            start_set.add(start)

    start_byte_set = set()
    for start in start_set:
        assert litpyglass.TerminalByteFrame.bytes_to_later_decode_if(start), (start,)
        start_byte_set.add(start[:1])

    start_bytes = tuple(sorted(start_byte_set))
    assert start_bytes == litpyglass.StartBytes, (start_bytes, litpyglass.StartBytes)


def _try_one_more_kbyte_() -> None:
    """Try some Frames open to, or closed against, taking more Bytes"""

    # Decline Bytes after Closed

    _try_open_(b"")
    _try_extra_(b"\t", extra=b"\x41")

    # Take Bytes into Stash, while could be decodable

    _try_open_("Superb", b"\xc2")
    _try_open_(b"\xed\x80")  # Head of >= 3 Byte UTF-8 Encoding
    _try_open_(b"\xf4\x80\x80")  # Head of >= 4 Byte UTF-8 Encoding

    # Take 6 Bytes into a Mouse Report, never decoded, then bounce the rest  # ruled: close6

    _try_open_(b"\033[M", b"\xff\xff")  # 5 Undecodable Bytes
    _try_close_(b"\033[M", b".\xc2\xa3")  # 6 Bytes, 2 Chars
    _try_close_(b"\033[M", b"\xf4\x8f\xbf")  # 6 Bytes, unfinished Char

    _try_close_(b"\033[M", b"\xc2\x80\xff")  # 6 Undecodable Bytes
    _try_close_(b"\033[M", b"\xff\xff\xc2")  # 6 Bytes, \xc2 unfinished

    _try_extra_(b"\033[M" b"\xf4\x8f\xbf", extra=b"\xbf")  # bounces past 6
    _try_extra_(b"\033[M" b"\xff\xff\xc2", extra=b"\x80")  # bounces past 6

    # Take Bytes into Text

    _try_open_("\u20ac", "\ufffd".encode()[:-1])

    # Decline 1..4 Unprintable Bytes after Text

    _try_extra_(b"Text", extra=b"\x7f")
    _try_extra_(b"Plain", extra="\uffff".encode())
    _try_extra_(b"Text", extra="\u00ad".encode())  # 2 Bytes, a Soft-Hyphen Control
    _try_extra_(b"Text", extra="\U0010ffff".encode())  # 4 Bytes, the last Code


def _try_some_control_() -> None:
    """Try closing on Unprintable or Undecodable Bytes alone, and on each kind of Head"""

    # Take & close 1 Unprintable Char or 1..4 Undecodable Bytes as an Alt Head

    _try_close_(b"\n")  # 7-bit Control Byte as Head alone
    _try_close_(b"\xc0")  # 8-bit Control Byte as Head alone
    _try_close_(b"\xc2\xad")  # 2 Byte UTF-8 of U+00AD Soft-Hyphen Control as Head alone
    _try_close_(b"\xf5")  # 1 Byte Undecodable as Head alone
    _try_close_(b"\xff")  # 1 Byte Undecodable as Head alone
    _try_close_(b"\xf4\x8f\xbf\xc0")  # 4 Bytes Undecodable as Head alone

    # Take & close 1 Printable Char escaped by a Head simpler than Csi, Esc Csi, and Osc

    _try_close_(b"\033", b"A")  # Head and then Text Tail of a Two-Byte Esc Frame
    _try_close_(b"\033O", b"P")  # Head and then Text Tail of a Three-Byte Ss3 Frame

    # Take & close 1 Unprintable Char escaped by a Simpler Head

    _try_close_(b"\033", b"\t")  # Head and then Control Tail of a Two-Byte Esc Frame

    # Take or don't take 1 Decodable Char escaped by Osc or Csi or Esc Csi

    _try_open_(b"\033[", b"6", b" ")  # Csi Head with Neck and Back but no Tail

    _try_close_(b"\033[", b"1", b"M")  # Csi Tail ⇧M that isn't ⎋[⇧M Head
    _try_close_(b"\033\033[", b"3;5", b"~")  # Esc Csi Head with Neck and Tail, no Back
    _try_close_(b"\033[", b"3;5", b"H")  # Csi Head with Neck and Tail, no Back
    _try_close_(b"\033[", b"6", b" q")  # Csi Head with Neck and Back & Tail

    _try_close_(b"\033]", b"\x07")  # Osc with 007 Bel as Tail
    _try_close_(b"\033]", b"\x1b" b"\\")  # Osc with ⎋\ String Terminator (ST) as Tail

    # Decline 1..4 Undecodable Bytes, when escaped by Csi or Esc Csi or Osc
    # Decline 1 Bytes of Unprintable or Multi-Byte Char

    _try_close_(b"\x1b[", "\u20ac".encode())  # Csi ends with Multi-Byte Char
    _try_open_(b"\x1b]", "\u20ac".encode())  # Osc ends with Multi-Byte Char

    _try_extra_(b"\x1b[", extra=b"\t")  # Csi bounces Unprintable
    _try_extra_(b"\x1b[", extra=b"\xf4\x8f\xff")  # Csi bounces Undecodable

    _try_extra_(b"\x1b]", extra=b"\t")  # Osc bounces Unprintable
    _try_extra_(b"\x1b]", extra="\033\u20ac".encode())  # Osc bounces 3 Byte Encoding
    _try_extra_(b"\x1b]", extra="\033\U0001f602".encode())  # Osc bounces 4 Byte Encoding

    # Try some commonly recurring choices

    assert litpyglass._END_PASTE_ == "\033[" "201~", (litpyglass._END_PASTE_,)

    _try_close_(b"\x1b[", b"201", b"~")


def _try_peeks_() -> None:
    """Stay open for the Combining Mark already fetched, where a Printable Char would close"""

    peek = "\u0301"  # Combining Acute Accent, as ⌥E J sends it after the J
    encode = peek.encode()

    # Stay open after the Printable Char that would have closed, and then close on the Mark

    for data in (b"\033j", b"\033\033j", b"\033Oj", b"\033[A", b"\033[1;5A", b"\033[ q"):
        f = litpyglass.TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and (not f.closed), (extras, f, data)

        extras = f.take_data_if(encode, peek="")
        assert (not extras) and f.closed, (extras, f, data)
        assert f.to_frame_bytes() == (data + encode), (f, data)

    # Close anyway, after an Unprintable Char, or after the 6 raw Bytes of ⎋[M

    for data in (b"\t", b"\033\t", b"\033[M !\xff"):
        f = litpyglass.TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and f.closed, (extras, f, data)

    # Stay open anyway, as Text, or as ⎋] Osc, and take the Mark

    for data in (b"j", b"\033]0;x"):
        f = litpyglass.TerminalByteFrame(b"")
        extras = f.take_data_if(data, peek=peek)
        assert (not extras) and (not f.closed), (extras, f, data)

        extras = f.take_data_if(encode, peek="")
        assert (not extras) and (not f.closed), (extras, f, data)
        assert f.to_frame_bytes() == (data + encode), (f, data)


def _try_extra_(data: bytes, extra: bytes) -> None:
    """Require the Frame to bounce these Bytes, and to stay as it was"""

    f = litpyglass.TerminalByteFrame(data)
    closed = f.closed

    returned_extra = f.take_data_if(extra, peek="")
    assert returned_extra == extra, (returned_extra, extra, str(f))

    assert f.closed == closed, (f.closed, closed, extra, f)
    assert f == litpyglass.TerminalByteFrame(data), (f, litpyglass.TerminalByteFrame(data))


def _try_open_(*args: str | bytes) -> None:
    """Frame these Bytes, and require the Frame still open"""

    f = _try_bytes_(*args)
    assert not f.closed, (f,)


def _try_close_(*args: bytes) -> None:
    """Frame these Bytes, and require the Frame closed"""

    f = _try_bytes_(*args)
    assert f.closed, (f,)


def _try_bytes_(*args: str | bytes) -> litpyglass.TerminalByteFrame:
    """Frame these Bytes, and require the Str of the Frame to speak each Arg as given"""

    data_list = list()
    for arg in args:
        if isinstance(arg, str):
            data_list.append(arg.encode())
        else:
            data_list.append(arg)

    join = " ".join(
        (litpyglass.str_repr(_) if isinstance(_, str) else litpyglass.bytes_repr(_)) for _ in args
    )

    fdata = b""
    for data in data_list:
        fdata += data

    f = litpyglass.TerminalByteFrame(fdata)
    fbytes = f.to_frame_bytes()
    fstr = str(f)

    join_plus = join if f.closed else (join + " +")  # ' +' marks an Open Frame

    assert fbytes == fdata, (fbytes, fdata)
    assert fstr == join_plus, (fstr, join_plus)

    return f


def _try_terminal_byte_frame_2_() -> None:
    """Try some Frames: ↑ ⎋↑ ⎋[M ⎋[↗ and the ⎋\\ String Terminator"""

    assert litpyglass.DL_Y == "\033[" "{}M", (litpyglass.DL_Y,)
    assert litpyglass._CLICK3_ == "\033[M", (litpyglass._CLICK3_,)
    assert litpyglass._NorthArrow_ == "\033[A", (litpyglass._NorthArrow_,)
    assert litpyglass.ST == "\033\134", (litpyglass.ST,)
    assert litpyglass._NortheastArrow_ == "\033[↗", (litpyglass._NortheastArrow_,)

    # Do nothing with grace & elegance

    litpyglass.TerminalByteFrame(b"")

    # Speak well of ↑ and ⎋↑

    f = litpyglass.TerminalByteFrame(b"\033[A")
    assert f.to_frame_bytes() == b"\033[A", (f,)
    assert f.closed, (f,)

    f = litpyglass.TerminalByteFrame(b"\033\033[A")
    assert f.to_frame_bytes() == b"\033\033[A", (f,)
    assert f.closed, (f,)

    # Dance well with the _CLICK3_ clash into DL_Y without Pn

    f = litpyglass.TerminalByteFrame(b"\033[M")
    assert f.to_frame_bytes() == b"\033[M", (f,)
    assert not f.closed, (f,)  # because could be ⎋[⇧M{b}{x}{y}

    f = litpyglass.TerminalByteFrame(b"\033[Mabc")
    assert f.to_frame_bytes() == b"\033[Mabc", (f,)
    assert f.closed, (f,)

    f = litpyglass.TerminalByteFrame(b"\033[Mab\xff")
    assert f.to_frame_bytes() == b"\033[Mab\xff", (f,)
    assert f.closed, (f,)

    # Accept ↖ ↗ ↘ ↙ Intercardinal Arrows, not just → ↑ ← ↓ Cardinal Arrows

    f = litpyglass.TerminalByteFrame("\033[↗".encode())  # not yet standard
    assert f.to_frame_bytes() == "\033[↗".encode(), (f,)
    assert f.closed, (f,)

    # Accept the ⎋\ String Terminator (ST) to close an ⎋] Osc Frame

    f = litpyglass.TerminalByteFrame(b"\033]11;?\033\\")
    assert f.to_frame_bytes() == b"\033]11;?\033\\", (f,)
    assert f.closed, (f,)


_TERMINAL_BOSS_TTY_CHILD_ = r"""
import os, select, sys, termios, tty
sys.path.insert(0, sys.argv[1])
import litpyglass


def slurp():
    data = b""
    while select.select([0], [], [], 0.1)[0]:
        data += os.read(0, 64)
    return data


sync_fileno = int(sys.argv[2])


class FlushSpy:  # stands in for sys.stdout and sys.stderr
    def __init__(self, stdio):
        self.stdio = stdio
        self.flush_count = 0

    def flush(self):  # mimics TextIO.flush
        self.flush_count += 1
        self.stdio.flush()

    def write(self, text):  # mimics TextIO.write
        return self.stdio.write(text)


real_stdout = sys.stdout
spy_stdout = FlushSpy(sys.stdout)
spy_stderr = FlushSpy(sys.stderr)
sys.stdout, sys.stderr = spy_stdout, spy_stderr

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
print("READY1", file=real_stdout, flush=True)
os.read(sync_fileno, 1)  # 'ab' has been typed, and the Terminal still takes Cooked Input
with boss:
    saved_attributes = boss.tcgetattr
    entered_twice = (boss.__enter__() is boss) and (boss.tcgetattr is saved_attributes)
    flushes_at_enter = (spy_stdout.flush_count, spy_stderr.flush_count)
    kept_at_enter = slurp()
    print("READY2", file=real_stdout, flush=True)
    os.read(sync_fileno, 1)  # 'xy' has been typed, and no one reads it
boss.__exit__()  # exits at most once
cleared_at_exit = boss.tcgetattr == []
flushes_at_exit = (spy_stdout.flush_count, spy_stderr.flush_count)
cooked_attributes = termios.tcgetattr(0)
tty.setraw(0, when=termios.TCSANOW)
left_at_exit = slurp()
termios.tcsetattr(0, termios.TCSANOW, cooked_attributes)
with boss:
    entered_afresh = bool(boss.tcgetattr)
result = (
    kept_at_enter,
    entered_twice,
    cleared_at_exit,
    left_at_exit,
    entered_afresh,
    flushes_at_enter,
    flushes_at_exit,
)
print("RESULT", repr(result), file=real_stdout, flush=True)
"""

_TERMINAL_BOSS_PIPE_CHILD_ = r"""
import sys
sys.path.insert(0, sys.argv[1])
import litpyglass

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
with boss:
    inside = (boss.isatty, boss.tcgetattr)
    boss.tty_setraw_before_farewell()  # does nothing off a Terminal, farewell or not
print("RESULT", repr((inside, boss.tcgetattr)), flush=True)
"""


def _try_terminal_boss_() -> None:
    """Try TerminalBoss things, as specs.md § 1 says"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    # Meet the Spec on a Terminal, with 'ab' typed before Enter and 'xy' typed inside

    sync_read_fileno, sync_write_fileno = os.pipe()
    os.set_inheritable(sync_read_fileno, True)  # lets the exec'd Child read it
    pid, master_fileno = pty.fork()
    if pid == 0:
        os.execv(
            sys.executable,
            [sys.executable, "-I", "-c", _TERMINAL_BOSS_TTY_CHILD_, here, str(sync_read_fileno)],
        )

    terminal_output = bytearray()

    def read_till_terminal_output(marker: bytes) -> None:
        deadline = time.monotonic() + 10
        while (marker not in terminal_output) and (time.monotonic() < deadline):
            if select.select([master_fileno], [], [], 0.05)[0]:
                try:
                    terminal_output.extend(os.read(master_fileno, 4096))
                except OSError:
                    break
        assert marker in terminal_output, (marker, bytes(terminal_output))

    read_till_terminal_output(b"READY1")
    os.write(master_fileno, b"ab")
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    read_till_terminal_output(b"READY2")
    os.write(master_fileno, b"xy")
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    read_till_terminal_output(b"RESULT (")
    read_till_terminal_output(b")\r\n")
    os.waitpid(pid, 0)
    os.close(master_fileno)
    os.close(sync_read_fileno)
    os.close(sync_write_fileno)

    tty_result_decoded = bytes(terminal_output).split(b"RESULT ")[1].split(b"\r\n")[0].decode()
    tty_result = ast.literal_eval(tty_result_decoded)
    tty_expected = (b"ab", True, True, b"xy", True, (1, 1), (2, 2))  # kept, twice, cleared, left,
    # afresh, then the Stdout and Stderr flush counts after Enter and after Exit
    assert tty_result == tty_expected, (tty_result, tty_expected)

    # Meet the Spec off a Terminal

    run = subprocess.run(
        [sys.executable, "-I", "-c", _TERMINAL_BOSS_PIPE_CHILD_, here],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )
    pipe_result = ast.literal_eval(run.stdout.split("RESULT ")[1])
    pipe_expected: tuple[tuple[bool, list[int]], list[int]] = ((False, [20261010]), [])
    assert pipe_result == pipe_expected, (pipe_result, pipe_expected, run.stderr)


_TERMINAL_BOSS_FAREWELL_CHILD_ = r"""
import os, sys, termios
sys.path.insert(0, sys.argv[1])
import litpyglass

real_tcsetattr = termios.tcsetattr


def tcsetattr_after_marker(fd, when, attributes):
    os.write(1, b"<RESTORED>")
    real_tcsetattr(fd, when, attributes)


def lflag_has(bit):
    return bool(termios.tcgetattr(0)[3] & bit)


def setraw_asserts(boss):
    try:
        boss.tty_setraw_before_farewell()
    except AssertionError:
        return True
    return False


before_enter = setraw_asserts(litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"<FAREWELL>"))
mute = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
with mute:
    without_farewell = setraw_asserts(mute)

termios.tcsetattr = tcsetattr_after_marker

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"<FAREWELL>")
with boss:
    cbreak = (lflag_has(termios.ISIG), lflag_has(termios.ICANON))
    boss.tty_setraw_before_farewell()
    raw = (lflag_has(termios.ISIG), lflag_has(termios.ICANON))
termios.tcsetattr = real_tcsetattr
print("RESULT", repr((cbreak, raw, before_enter, without_farewell)), flush=True)
"""


def _try_terminal_boss_farewell_() -> None:
    """Try the TerminalBoss farewell, as specs.md § 1 says"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    pid, master_fileno = pty.fork()
    if pid == 0:
        os.execv(
            sys.executable,
            [sys.executable, "-I", "-c", _TERMINAL_BOSS_FAREWELL_CHILD_, here],
        )

    terminal_output = bytearray()
    deadline = time.monotonic() + 10
    while (b")\r\n" not in terminal_output) and (time.monotonic() < deadline):
        if select.select([master_fileno], [], [], 0.05)[0]:
            try:
                terminal_output.extend(os.read(master_fileno, 4096))
            except OSError:
                break

    os.waitpid(pid, 0)
    os.close(master_fileno)

    heard = bytes(terminal_output)
    assert b"<FAREWELL><RESTORED>" in heard, (heard,)  # the farewell leaves before the restore

    tty_result = ast.literal_eval(heard.split(b"RESULT ")[1].split(b"\r\n")[0].decode())
    tty_expected = ((True, False), (False, False), True, True)  # (ISIG, ICANON) in cbreak, then
    # after setraw, then whether setraw asserted before Enter, and without a farewell
    assert tty_result == tty_expected, (tty_result, tty_expected)


_TERMINAL_BOSS_TYPEAHEAD_CHILD_ = r"""
import os, sys, time
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"ab", farewell_bytes=b"")
print("READY1", flush=True)
os.read(sync_fileno, 1)  # 'X' has been typed on the Terminal
with boss:
    first = boss.read_one_byte()
    second = boss.read_one_byte()
    selects_in_0ms = boss.stdio_select_select(timeout=0.0)
    start = time.monotonic()
    selects_in_1s = boss.stdio_select_select(timeout=1.0)
    waited_about_150ms = 0.1 <= (time.monotonic() - start) < 0.6
    third = boss.read_one_byte()
print(
    "RESULT",
    repr((first, second, selects_in_0ms, selects_in_1s, waited_about_150ms, third)),
    flush=True,
)
"""


def _try_terminal_boss_typeahead_() -> None:
    """Try TerminalBoss reading Typeahead, as specs.md § 9 says"""

    result = _pty_run_child_(_TERMINAL_BOSS_TYPEAHEAD_CHILD_, terminal_bytes=b"X")

    expected = (b"X", b"a", True, True, True, b"b")  # Terminal first, then Typeahead, and 2 selects
    assert result == expected, (result, expected)


_TERMINAL_BOSS_CHUNKS_CHILD_ = r"""
import os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"ab", farewell_bytes=b"")
print("READY1", flush=True)
os.read(sync_fileno, 1)  # 'XY' has been typed on the Terminal
with boss:
    chunks = tuple(boss.read_some_bytes_if() for _ in range(4))
print("RESULT", repr(chunks), flush=True)
"""


def _try_terminal_boss_chunks_() -> None:
    """Try TerminalBoss reading Typeahead in chunks, as specs.md § 9 says"""

    result = _pty_run_child_(_TERMINAL_BOSS_CHUNKS_CHILD_, terminal_bytes=b"XY")

    expected = (b"X", b"Y", b"a", b"b")  # each Byte alone, though 'XY' arrived all at once
    assert result == expected, (result, expected)


def _pty_run_child_(child_code: str, terminal_bytes: bytes) -> object:
    """Run this Python on a Pty, type these Bytes when it says READY1, and return its RESULT"""

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))

    sync_read_fileno, sync_write_fileno = os.pipe()
    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", "-c", child_code, here, str(sync_read_fileno)]
    process = subprocess.Popen(
        argv,
        stdin=slave_fileno,
        stdout=slave_fileno,
        stderr=slave_fileno,
        pass_fds=(sync_read_fileno,),
    )
    os.close(slave_fileno)

    terminal_output = bytearray()

    _pty_read_till_marker_(master_fileno, terminal_output, b"READY1")
    os.write(master_fileno, terminal_bytes)  # typed before the Child reads Input
    time.sleep(0.05)
    os.write(sync_write_fileno, b"g")

    _pty_read_till_marker_(master_fileno, terminal_output, b"RESULT (")
    _pty_read_till_marker_(master_fileno, terminal_output, b")\r\n")
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()  # a Child that never printed its RESULT is still blocked reading Input
        process.wait()
    os.close(master_fileno)
    os.close(sync_read_fileno)
    os.close(sync_write_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    assert "RESULT " in screen_decode, (screen_decode,)
    result_decode = screen_decode.split("RESULT ")[1].split("\r\n")[0]
    result: object = ast.literal_eval(result_decode)

    return result


def _try_typeahead_() -> None:
    """Try the --typeahead flag, as specs.md § 9 says"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=strikes", "--typeahead=\r\r\r"]
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
    os.close(slave_fileno)

    terminal_output = bytearray()

    deadline = time.monotonic() + 5
    while (process.poll() is None) and (time.monotonic() < deadline):
        _pty_read_once_(master_fileno, terminal_output)

    returncode = process.poll()
    if returncode is None:
        process.kill()
        process.wait()

    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    assert returncode == 0, (returncode, screen_decode)


def _try_is_quitting_frames_() -> None:
    """Try which strikes quit --egg=strikes, as specs.md § 4 says"""

    cases = (
        (b"\r", 3, True, ""),  # ⏎ ⏎ ⏎
        (b"\r", 2, False, ""),
        (b"\033[", 3, True, ""),  # ⎋[ ⎋[ ⎋[ with the 3rd still an Open Frame
        (b"\033", 3, False, "⎋⎋ '' b'\\033\\033' +"),  # ⎋ ⎋ ⎋ with the 2nd joined to the 1st
        (b"\033\033", 3, True, ""),  # ⎋⎋ ⎋⎋ ⎋⎋
        (b"\033", 6, True, ""),  # ⎋ ⎋ ⎋ ⎋ ⎋ ⎋ joined in pairs
        (b"x", 3, False, ""),  # Text
        (b"\r\r\r", 1, False, "⏎ '' b'\\r'\r\n\r\x1b[K" * 2 + "⏎ '' b'\\r'\r\n"),  # ⏎ ⏎ ⏎ pasted
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(
            executor.map(lambda case: _try_egg_quit_("strikes", case[0], case[1], b""), cases)
        )

    for case, (quit, screen_decode) in zip(cases, results):
        data, count, want, shows = case
        assert quit == want, (quit, want, data, count)
        assert shows in screen_decode, (shows, data, count, screen_decode)


def _skater_move_(warp: str) -> str:
    """Spell what --egg=skater writes to move one pixel, away from every edge of the Screen"""

    return "\033[7m  \033[m\b\b" + warp + "  \b\b"  # inverse behind, plain ahead


def _try_skater_quits_() -> None:
    """Try which strikes quit --egg=skater, as specs.md § 8 says"""

    cases = (
        (b"\r", 3, True, "X\bO\b"),  # ⏎ ⏎ ⏎
        (b"\r", 2, False, "X\bO\b"),
        (b"\r\r\r", 1, False, "X\bO\bX\b"),  # ⏎ ⏎ ⏎ pasted
        (b"x\033[C", 1, False, "X\b" + _skater_move_("\033[C\033[C")),  # x the Taken Frame, then →
        (b"\033[C", 3, False, _skater_move_("\033[C\033[C")),  # → → →
        (b"\033[A", 3, False, _skater_move_("\033[A")),  # ↑ ↑ ↑
        (b"\033[D", 3, False, _skater_move_("\033[D\033[D")),  # ← ← ←
        (b"\033[B", 3, False, _skater_move_("\033[B")),  # ↓ ↓ ↓
        (b"\033", 1, False, "1\b"),  # ⎋ the Open Frame of 1 Byte
        (b"\033[", 1, False, "2\b"),  # ⎋[ the Open Frame of 2 Bytes
        (b"\033[12345678", 1, False, "0\b"),  # ⎋[ and 8 more, 10 Bytes
        (b"x\033[", 1, False, "3\b"),  # x the Taken Frame of 1 Byte, then ⎋[
        (b"x\033[C\033[", 1, False, "2\b"),  # ⎋[C the Taken Arrow resets the count
        ("\033[↗".encode(), 3, True, "X\bO\b"),  # ↗ ↗ ↗, an Intercardinal Arrow, not yet a Stalwart
    )

    results24x80 = b"\033[1;1R\033[8;24;80t"  # the Terminal answers Row 1 Column 1, and 24 x 80

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(
            executor.map(
                lambda case: _try_egg_quit_("skater", case[0], case[1], results24x80), cases
            )
        )

    for case, (quit, screen_decode) in zip(cases, results):
        data, count, want, shows = case
        assert quit == want, (quit, want, data, count, screen_decode)
        assert shows in screen_decode, (shows, data, count, screen_decode)

        launch = "\033[?25l\033[6n\033[18t\r  \b\b"
        # hides the Cursor, asks the Queries, draws the first pixel plain
        assert launch in screen_decode, (launch, data, count, screen_decode)

        farewell = "\r\033[?25h\033[32100B\033[A"  # shows Cursor, parks it
        assert (farewell in screen_decode) == quit, (farewell, quit, data, count, screen_decode)


def _try_skater_edge_() -> None:
    """Try --egg=skater at the far East Column, as specs.md § 8 says"""

    results20 = b"\033[1;1R\033[8;5;20t"  # Row 1 Column 1, and a Screen 5 high, 20 wide
    results21 = b"\033[1;1R\033[8;5;21t"  # the same, 21 wide

    cases = (
        (20, results20, 9),  # → x 9 reaches the pixel at Columns 19 and 20
        (20, results20, 10),  # → x 10 bounces off the East edge to the pixel at 17 and 18
        (21, results21, 9),  # an odd Width acts as the even Width below it
        (21, results21, 10),
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        results = tuple(
            executor.map(lambda case: _try_egg_quit_("skater", b"\033[C", case[2], case[1]), cases)
        )

    for case, (quit, screen_decode) in zip(cases, results):
        screen_width, _, count = case
        assert not quit, (quit, screen_width, count, screen_decode)

        screen_cells, row_y, column_x, wrap_pending = _screen_of_(
            screen_decode, screen_width=screen_width, screen_height=5
        )
        here = (row_y, column_x, wrap_pending)

        want_x = 19 if (count == 9) else 17  # the left Cell of the plain pixel
        assert here == (1, want_x, False), (here, want_x, screen_width, count, screen_decode)

        row1 = screen_cells[0]  # (Character, Inverse) per Column
        plains = list(x for (x, cell) in enumerate(row1, start=1) if not cell[1])
        want_plains = [want_x, want_x + 1] + list(
            range(21, screen_width + 1)
        )  # Column 21 never written
        assert plains == want_plains, (plains, want_plains, screen_width, count, screen_decode)

        below = list(c for row in screen_cells[1:] for c in row if c != (" ", False))
        assert not below, (below, screen_width, count, screen_decode)  # no spill into Row 2


def _screen_of_(
    screen_decode: str, screen_width: int, screen_height: int
) -> tuple[list[list[tuple[str, bool]]], int, int, bool]:
    """Replay the Bytes onto a Screen that waits to wrap, as macOS Terminal does, from Row 1"""

    screen_cells = list(
        list((" ", False) for _ in range(screen_width)) for _ in range(screen_height)
    )
    row_y = 1
    column_x = 1
    wrap_pending = False  # true after a write into the last Column, till the next write or move
    inverse = False

    pattern = re.compile(r"\033\[([?0-9;]*)([ -/]*[@-~])|.", re.DOTALL)
    for match in pattern.finditer(screen_decode):
        text = match.group(0)
        if text.startswith("\033["):
            ps = match.group(1)
            final = text[-1]
            n = int(ps) if ps.isdigit() else 1
            if final == "m":
                inverse = ps == "7"
            elif final == "A":
                row_y = max(1, row_y - n)
            elif final == "B":
                row_y = min(screen_height, row_y + n)
            elif final == "C":
                column_x = min(screen_width, column_x + n)
                wrap_pending = False
            elif final == "D":
                column_x = max(1, column_x - n)
                wrap_pending = False
            continue

        if text == "\r":
            column_x = 1
            wrap_pending = False
        elif text == "\b":
            column_x = max(1, column_x - 1)
            wrap_pending = False
        elif text.isprintable() and (len(text) == 1):
            if wrap_pending:
                column_x = 1
                row_y = min(screen_height, row_y + 1)
                wrap_pending = False

            screen_cells[row_y - 1][column_x - 1] = (text, inverse)
            if column_x == screen_width:
                wrap_pending = True
            else:
                column_x += 1

    return (screen_cells, row_y, column_x, wrap_pending)


_PLACED_CHILD_ = r"""
import dataclasses, os, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

sync_fileno = int(sys.argv[2])
boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"<FAREWELL>")
ts = litpyglass.TerminalShadow(boss)
ist = litpyglass.InputStrikeTaker(ts)
print("READY1", flush=True)
os.read(sync_fileno, 1)  # ↑, a Result, a lookalike Result, a Result, and ↓ are typed
places = list()
with boss:
    ist.pull_yx_hw_from_ts_if(stalwarts=())
    for isap in ist.take_input_strikes_and_yield_each_placed(stalwarts=()):
        if not isap.strike.taken:
            continue  # the Open Frame comes before each Read, and says nothing yet
        place = isap.place and dataclasses.astuple(isap.place)
        places.append((isap.strike.caps, place))
        if len(places) == 2:
            break
print("RESULT", repr(tuple(places)), flush=True)
"""

_PLACED_OFF_TERMINAL_CHILD_ = r"""
import dataclasses, sys
sys.path.insert(0, sys.argv[1])
import litpyglass

boss = litpyglass.TerminalBoss(typeahead=b"", farewell_bytes=b"")
ts = litpyglass.TerminalShadow(boss)
ist = litpyglass.InputStrikeTaker(ts)
places = list()
with boss:
    ist.pull_yx_hw_from_ts_if(stalwarts=())
    for isap in ist.take_input_strikes_and_yield_each_placed(stalwarts=()):
        if not isap.strike.taken:
            continue  # the Open Frame comes before each Read, and says nothing yet
        place = isap.place and dataclasses.astuple(isap.place)
        places.append((isap.strike.caps, place))
print("RESULT", repr(tuple(places)), flush=True)
"""


def _try_frame_reader_quits_midbatch_() -> None:
    """Try that a Caller who quits mid-batch leaves the later Taken Frames, as specs.md § 5 says"""

    class FakeBoss:
        def __init__(self) -> None:
            self.reads = 0

        def read_some_bytes_if(self) -> bytes:
            self.reads += 1
            return b"\033[1;1R\033[8;24;80t\033[B" if (self.reads == 1) else b""

    boss = FakeBoss()
    tfr = litpyglass.TerminalFrameReader()

    taken_count = 0
    for taken, frame, _ in tfr.take_frames_and_yield_each(
        typing.cast(litpyglass.TerminalBoss, boss), stalwarts=()
    ):
        taken_count += int(taken)
        if taken_count == 2:
            break  # quits at the second Frame of three

    assert boss.reads == 1, (boss.reads,)

    shows = list()
    for taken, frame, _ in tfr.take_frames_and_yield_each(
        typing.cast(litpyglass.TerminalBoss, boss), stalwarts=()
    ):
        shows.append((taken, frame.to_frame_bytes(), boss.reads))

    # the third Frame comes first, before the Open Frame, and before any second read

    expected = [(True, b"\033[B", 1), (False, b"", 1)]
    assert shows == expected, (shows, expected)


def _try_pull_ends_without_answers_() -> None:
    """Try that Input ending before both Results fails loudly, as specs.md § 7 says"""

    class FakeBoss:
        isatty = True

        def bytes_write_flush(self, data: bytes) -> None:
            pass

        def read_some_bytes_if(self) -> bytes:
            return b""  # Input ends at once, with no Result

    boss = typing.cast(litpyglass.TerminalBoss, FakeBoss())
    ist = litpyglass.InputStrikeTaker(litpyglass.TerminalShadow(boss))

    heard = io.StringIO()
    with contextlib.redirect_stdout(heard):
        try:
            ist.pull_yx_hw_from_ts_if(stalwarts=())
            code = None
        except SystemExit as exc:
            code = exc.code

    complaint = "Input ended before Y X H W replies to ⎋[6n and ⎋[18t"
    assert code == 1, (code, heard.getvalue())
    assert complaint in heard.getvalue(), (complaint, heard.getvalue())


def _try_placed_input_strikes_() -> None:
    """Try the Place each Strike takes, as specs.md § 7 says"""

    typed = b"\033[A" + b"\033[5;7R" + b"\033[9;9R" + b"\033[8;24;80t" + b"\033[B"
    result = _pty_run_child_(_PLACED_CHILD_, terminal_bytes=typed)

    place = (9, 80, 9, 24)  # column_x, x_width, row_y, y_height: the last Cursor Result, ⎋[9;9⇧R
    expected = (("↑", place), ("↓", place))  # the answers are no Strikes
    assert result == expected, (result, expected)

    here = os.path.dirname(os.path.abspath(litpyglass.__file__))
    argv = [sys.executable, "-I", "-c", _PLACED_OFF_TERMINAL_CHILD_, here]
    run = subprocess.run(argv, input=b"\033[A\033[B", capture_output=True, timeout=10)
    assert run.returncode == 0, (run.returncode, run.stdout, run.stderr)

    off_expected = "RESULT (('↑', (1, 1, 1, 1)), ('↓', (1, 1, 1, 1)))"  # no Terminal to ask
    assert off_expected in run.stdout.decode(), (run.stdout, off_expected)


def _try_skater_entry_() -> None:
    """Try how --egg=skater waits for the Results of its Queries, as specs.md § 8 says"""

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        mute = executor.submit(_try_egg_entry_, b"", b"")  # no Results
        half = executor.submit(_try_egg_entry_, b"", b"\033[1;1R")  # only the Cursor Result
        other = executor.submit(_try_egg_entry_, b"", b"\033[8;24;80t")  # only the Size Result
        ahead = executor.submit(_try_egg_entry_, b"\033[C", b"\033[1;1R\033[8;24;80t")  # → typed
        swapped = executor.submit(_try_egg_entry_, b"", b"\033[8;24;80t\033[1;1R")  # Size first

    complaint = "Input ended before Y X H W replies to ⎋[6n and ⎋[18t"

    for future in (mute, half, other):
        screen_decode, isig, returncode = future.result()
        assert "\r  \b\b" not in screen_decode, (screen_decode,)  # no writes while the hang lasts
        assert isig, (isig, screen_decode)  # ⌃C ⌃Z ⌃\ still signal while the hang lasts
        assert returncode == 1, (returncode, screen_decode)  # ⌃D ends the hang
        assert complaint in screen_decode, (complaint, screen_decode)

    screen_decode, isig, returncode = ahead.result()
    assert "\r  \b\b" in screen_decode, (screen_decode,)
    assert screen_decode.index("\033[6n") < screen_decode.index("\r  \b\b"), (screen_decode,)
    assert not isig, (isig, screen_decode)
    assert returncode is None, (returncode, screen_decode)

    moved = _skater_move_("\033[C\033[C")  # the → typed before the Results came, kept
    assert screen_decode.index("\r  \b\b") < screen_decode.index(moved), (moved, screen_decode)

    screen_decode, isig, returncode = swapped.result()
    assert screen_decode.index("\033[6n") < screen_decode.index("\r  \b\b"), (screen_decode,)
    assert not isig, (isig, screen_decode)  # the Results take either order
    assert returncode is None, (returncode, screen_decode)

    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=skater"]
    run = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10)
    assert run.returncode == 0, (run.returncode, run.stdout, run.stderr)
    assert "\033[6n" not in run.stdout, (run.stdout,)  # asks no Terminal, off a Terminal


def _try_egg_entry_(typed_data: bytes, answers: bytes) -> tuple[str, bool, int | None]:
    """Run --egg=skater on a Pty, answer its Queries as told, and say how it waits"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, "--egg=skater"]
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
    os.close(slave_fileno)

    terminal_output = bytearray()
    _pty_read_till_marker_(master_fileno, terminal_output, b"\033[6n\033[18t")
    os.write(master_fileno, typed_data + answers)
    _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)

    isig = bool(termios.tcgetattr(master_fileno)[3] & termios.ISIG)  # ⌃C ⌃Z ⌃\ signal, or not

    returncode = None
    if isig:  # still waiting, since the Terminal takes ⌃C ⌃Z ⌃\ as Signals till both Results come
        os.write(master_fileno, b"\004")  # ⌃D
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)
        returncode = process.poll()

    if process.poll() is None:
        process.kill()
    process.wait()
    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    return (screen_decode, isig, returncode)


def _try_egg_quit_(egg: str, data: bytes, count: int, results: bytes) -> tuple[bool, str]:
    """Run --egg= on a Pty, strike these Bytes this often 150ms apart, and say if it quit"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", litpyglass.__file__, f"--egg={egg}"]
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
    os.close(slave_fileno)

    terminal_output = bytearray()

    if egg == "skater":  # answers the Queries, as a Terminal does
        _pty_read_till_marker_(master_fileno, terminal_output, b"\033[6n\033[18t")
        os.write(master_fileno, results)

    prompt = b"\r  \b\b" if (egg == "skater") else b"+ "
    _pty_read_till_marker_(
        master_fileno, terminal_output, prompt
    )  # waits for the Prompt, since Bytes read too soon count as too fast
    assert prompt in terminal_output, (prompt, bytes(terminal_output))

    if egg == "skater":  # the Results count as Frames in the quit rule, so strike after the gap
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)

    isig = termios.tcgetattr(master_fileno)[3] & termios.ISIG  # ⌃C ⌃Z ⌃\ signal, or else not
    assert not isig, (isig, egg, bytes(terminal_output))

    for _ in range(count):
        try:
            os.write(master_fileno, data)
        except OSError:
            break  # the Child has already exited, so the Pty is closed
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)  # over the 100ms too-fast gap

    _pty_read_for_seconds_(master_fileno, terminal_output, 0.5)  # long enough for a quit to show
    quit = process.poll() is not None
    if not quit:
        process.kill()
    process.wait()
    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    return (quit, screen_decode)


def _try_strikes_spill_() -> None:
    """Try what --egg=strikes leaves in Stdin after it quits, as specs.md § 8 says"""

    cases = (
        (b"", b""),  # nothing struck after the 3rd ⏎, so nothing left
        (b"zz", b"zz"),  # 'zz' struck after the exit, so left for the next program
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(cases)) as executor:
        lefts = tuple(executor.map(lambda case: _try_strikes_left_(case[0]), cases))

    wants = tuple(case[1] for case in cases)
    assert lefts == wants, (lefts, wants, cases)


_STRIKES_LEFT_CHILD_ = r"""
import os, select, subprocess, sys, termios, tty
subprocess.run([sys.executable, "-I", sys.argv[1], "--egg=strikes"])
print("DEMO_EXITED", flush=True)
tty.setraw(0, when=termios.TCSANOW)
left = b""
while select.select([0], [], [], 0.3)[0]:
    left += os.read(0, 64)
print("LEFT", repr(left), flush=True)
"""


def _try_strikes_left_(extra: bytes) -> bytes:
    """Run --egg=strikes on a Pty, quit it, strike these Bytes after, and say what Stdin holds"""

    master_fileno, slave_fileno = pty.openpty()
    argv = [sys.executable, "-I", "-c", _STRIKES_LEFT_CHILD_, litpyglass.__file__]
    process = subprocess.Popen(argv, stdin=slave_fileno, stdout=slave_fileno, stderr=slave_fileno)
    os.close(slave_fileno)

    terminal_output = bytearray()

    _pty_read_till_marker_(master_fileno, terminal_output, b"+ ")  # waits for the Prompt
    assert b"+ " in terminal_output, (bytes(terminal_output),)

    for _ in range(3):
        os.write(master_fileno, b"\r")
        _pty_read_for_seconds_(master_fileno, terminal_output, 0.15)  # over the 100ms too-fast gap

    if extra:
        os.write(master_fileno, extra)

    _pty_read_till_marker_(master_fileno, terminal_output, b"LEFT ")
    _pty_read_for_seconds_(master_fileno, terminal_output, 0.1)
    process.wait()
    os.close(master_fileno)

    screen_decode = bytes(terminal_output).decode(errors="replace")
    lines = list(_ for _ in screen_decode.split("\r\n") if _.startswith("LEFT "))
    assert len(lines) == 1, (lines, screen_decode)

    left = ast.literal_eval(lines[0].removeprefix("LEFT "))
    assert isinstance(left, bytes), (left,)

    return left


def _pty_read_till_marker_(master_fileno: int, terminal_output: bytearray, marker: bytes) -> None:
    """Take the Bytes arriving from the Pty till the Marker, else till 10s"""

    deadline = time.monotonic() + 10
    while (time.monotonic() < deadline) and (marker not in terminal_output):
        if not _pty_read_once_(master_fileno, terminal_output):
            return


def _pty_read_for_seconds_(master_fileno: int, terminal_output: bytearray, seconds: float) -> None:
    """Take the Bytes arriving from the Pty for this long"""

    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _pty_read_once_(master_fileno, terminal_output):
            return


def _pty_read_once_(master_fileno: int, terminal_output: bytearray) -> bool:
    """Take the Bytes waiting, and say if the Pty is still open"""

    if select.select([master_fileno], [], [], 0.02)[0]:
        try:
            terminal_output.extend(os.read(master_fileno, 4096))
        except OSError:
            return False

    return True


# ⚠️ ↑↑↑ Above written by Claude·Ai, reviewed by almost no living people


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitglass/tests.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
