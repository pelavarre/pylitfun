#!/usr/bin/env python3

r"""
usage: litglass.py [-h] [-f] [--egg EGG]

loop Input back to Output, to Screen from Touch/ Mouse/ Key

options:
  -h, --help   show this help message and exit
  -f, --force  ask fewer questions (like do run slow self-test's)
  --egg EGG    a hint of how to behave, such as 'repr' or 'sigint'

quirks:
  talks with the Terminal at Stderr (with /dev/stderr, not with /dev/tty)
  quits when given ⌃C

examples:
  ./litglass.py --
  ./litglass.py --egg=repr
  ./litglass.py --egg=sigint
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections
import collections.abc  # .collections.abc is not .abc
import dataclasses
import difflib
import os
import pdb
import re
import select
import signal
import sys
import termios
import textwrap
import tty
import types
import typing


_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'

default_eq_None = None  # spells out 'default=None' where Python forbids that


#
# Choose a personality
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class Flags:
    """Choose a personality"""

    apple: bool = sys.platform == "darwin"  # flags.apple
    google: bool = bool(os.environ.get("CLOUD_SHELL", ""))  # flags.google
    terminal: bool = os.environ.get("TERM_PROGRAM", "") == "Apple_Terminal"  # flags.terminal

    _repr_: bool = False  # flags._repr_ to loop the Repr, not the Str
    sigint: bool = False  # flags.sigint for ⌃C to raise KeyboardInterrupt


flags = Flags()

# flags.sigint = True


#
# Run from the Shell, but tell uncaught Exceptions to launch the Py Repl
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    sys.excepthook = excepthook

    parser = arg_doc_to_parser(__main__.__doc__ or "")
    shell_args_take_in(args=sys.argv[1:], parser=parser)

    lbr = Loopbacker()
    lbr.run_loopbacker_awhile()


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Positional Arguments & Options"""

    parser = ArgDocParser(doc, add_help=True)

    egg_help = "a hint of how to behave, such as 'repr' or 'sigint'"
    force_help = "ask fewer questions (like do run slow self-test's)"

    parser.add_argument("-f", "--force", action="count", help=force_help)
    parser.add_argument("--egg", dest="eggs", metavar="EGG", action="append", help=egg_help)

    return parser


def shell_args_take_in(args: list[str], parser: ArgDocParser) -> argparse.Namespace:
    """Take in the Shell Command-Line Args"""

    ns = parser.parse_args_if(args)  # often prints help & exits zero

    ns_keys = list(vars(ns).keys())
    assert ns_keys == ["force", "eggs"], (ns_keys, ns, args)

    celebrated_eggs = ["repr", "sigint"]

    ns_eggs = ns.eggs or list()
    for egg_arg in ns_eggs:
        eggs = egg_arg.split(",")
        for egg in eggs:
            if egg and "repr".startswith(egg):
                flags._repr_ = True
            elif egg and "sigint".startswith(egg):
                flags.sigint = True
            else:
                parser.parser.print_usage()
                print(f"don't choose {egg!r}, do choose from {celebrated_eggs}", file=sys.stderr)
                sys.exit(2)  # exits 2 for bad Arg

    if ns.force:
        _try_lit_glass_()

    return ns


#
# Loop Input back to Output, to Screen from Touch/ Mouse/ Key
#


class Loopbacker:
    """Loop Input back to Output, to Screen from Touch/ Mouse/ Key"""

    terminal_boss: TerminalBoss
    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    keyboard_decoder: KeyboardDecoder

    def __init__(self) -> None:

        kd = KeyboardDecoder()
        self.keyboard_decoder = kd

    def run_loopbacker_awhile(self) -> None:
        """Loop Input back to Output, to Screen from Touch/ Mouse/ Key"""

        assert ord("C") ^ 0x40 == ord("\003")

        quitting = False
        with TerminalBoss() as tb:
            kr = tb.keyboard_reader
            sw = tb.screen_writer

            self.terminal_boss = tb
            self.screen_writer = sw
            self.keyboard_reader = kr

            sw.print_text()
            sw.print_text("Press ⌃C")

            if flags._repr_:
                sw.write_text("\t\t")

            while not quitting:
                tb.kbhit(timeout=None)
                frames = kr.read_byte_frames()

                if flags._repr_:
                    self.frames_print_repr(frames)
                else:
                    for frame in frames:
                        self.frame_write_reply(frame)

                if b"\003" in frames:
                    quitting = True
                    break

        sw.print_text("bye")
        sw.print_text()

    def frames_print_repr(self, frames: tuple[bytes, ...]) -> None:

        sw = self.screen_writer
        kd = self.keyboard_decoder

        for frame_index, frame in enumerate(frames):
            text = frame.decode()  # may raise UnicodeDecodeError

            kseqs = kd.to_kseqs_if(frame)
            if not kseqs:
                if not frames[1:]:
                    sw.print_text(repr(text))
                else:
                    sw.print_text(frame_index, repr(text))
            else:
                if not frames[1:]:
                    sw.print_text(kseqs, repr(text))
                else:
                    sw.print_text(kseqs, frame_index, repr(text))

            sw.write_text("\t\t")

    def frame_write_reply(self, frame: bytes) -> None:

        sw = self.screen_writer
        kd = self.keyboard_decoder

        # Leap the Cursor to the ⌥ -Click

        kbf = KeyByteFrame(frame)
        (marks, ints) = kbf.to_csi_marks_ints_if(frame)

        if (marks == b"<m") and (len(ints) == 3):
            (b, x, y) = ints  # todo: bounds check on Click Release
            text = "\033[" f"{y};{x}" "H"
            sw.write_text(text)
            return

        # If Frame has Keycaps

        text = frame.decode()  # may raise UnicodeDecodeError

        kseqs = kd.to_kseqs_if(frame)
        if kseqs and frame not in (b"\033", b"\033\033"):
            join = str(kseqs)

            # Loop back as Arrow, no matter the shifting Keys

            arrows = tuple(_ for _ in ("←", "↑", "→", "↓") if _ in join)
            if len(arrows) == 1:
                arrow = arrows[-1]
                alt_text = kd.decode_by_kseq[arrow]

                sw.write_text(alt_text)
                return

            # Trust loop back if Keycap found  # todo9: for now, not forever

            sw.write_text(text)
            return

        # Show a brief Repr of other Encodes

        alt_text = " "
        for decode in text:
            encode = decode.encode()
            kseqs = kd.to_kseqs_if(encode)
            kseq = kseqs[0] if kseqs else repr(decode)[1:-1]
            alt_text += kseq

        sw.write_text(alt_text)


class TerminalBoss:
    """Talk with one KeyboardReader and one ScreenWriter"""

    stdio: typing.TextIO
    fileno: int
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    screen_writer: ScreenWriter
    keyboard_reader: KeyboardReader

    def __init__(self) -> None:

        stdio = sys.__stderr__
        assert stdio is not None  # refuses to run headless

        fileno = stdio.fileno()

        sw = ScreenWriter(self)
        kr = KeyboardReader(self)

        self.stdio = stdio
        self.fileno = fileno
        self.tcgetattr = list()  # replaced by .__enter__

        self.screen_writer = sw
        self.keyboard_reader = kr

    def __enter__(self) -> TerminalBoss:
        r"""Stop line-buffering Input, stop taking \n Output as \r\n, etc"""

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Enter once

        if tcgetattr:
            return self

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before 'tty.setraw' of TerminalStudio.__enter__

        with_tcgetattr = termios.tcgetattr(fileno)
        assert with_tcgetattr, (with_tcgetattr,)

        self.tcgetattr = with_tcgetattr  # replaces

        # Stop line-buffering Input, stop replacing \n Output with \r\n, etc

        if not flags.sigint:
            tty.setraw(fileno, when=termios.TCSADRAIN)
        else:
            tty.setcbreak(fileno, when=termios.TCSADRAIN)

        # Succeed

        return self

        # todo: try termios.TCSAFLUSH to discard Input while entering

    def __exit__(self, *args: object) -> None:
        r"""Restart line-buffering Input, restart taking \n Output as \r\n, etc"""

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Exit once

        if not tcgetattr:
            return

        # Flush Output, drain Input, and change Input Mode

        stdio.flush()  # before 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        # todo: try termios.TCSAFLUSH to discard Input while exiting

    def write_some_bytes(self, data: bytes) -> None:
        """Write zero or more Bytes"""

        fileno = self.fileno
        fd = fileno
        os.write(fd, data)  # maybe empty

    def read_one_byte(self) -> bytes:
        """Read one Byte"""

        fileno = self.fileno

        fd = fileno
        length = 1
        read = os.read(fd, length)

        assert len(read) == 1, (read,)  # todo: test os.read returns empty

        return read

    def kbhit(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        stdio = self.stdio
        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        stdio.flush()  # before select.select of .kbhit
        (r, w, x) = select.select([fileno], [], [], timeout)

        hit = fileno in r

        return hit

        # a la msvcrt.kbhit


class ScreenWriter:
    """Write Lines of Output to the Terminal Screen"""

    terminal_boss: TerminalBoss

    def __init__(self, terminal_boss: TerminalBoss) -> None:
        self.terminal_boss = terminal_boss

    def print_text(self, *args: object, end: str | None = "\r\n") -> None:
        """Answer the question of 'what is print?' here lately"""

        text = " ".join(str(_) for _ in args)
        end_plus = "" if (end is None) else end
        self.write_text(text + end_plus)

        # .end=None here puns with .end="", same as it does in Python's .print

    def write_text(self, text: str) -> None:
        """Write the Byte Encodings of Text without adding a Line-Break"""

        tb = self.terminal_boss
        data = text.encode()  # may raise UnicodeEncodeError
        tb.write_some_bytes(data)


class KeyboardReader:
    """Read Frames of Input from the Terminal Keyboard"""

    terminal_boss: TerminalBoss

    y_high: int  # H W Y X always positive after initial (-1, -1, -1, -1)
    x_wide: int

    row_y: int
    column_x: int

    def __init__(self, terminal_boss: TerminalBoss) -> None:

        self.terminal_boss = terminal_boss

        self.row_y = -1
        self.column_x = -1
        self.y_high = -1
        self.x_wide = -1

    #
    # Split the Input Bytes of a Cursor Position Report into >= 1 Frames,
    # and update the H W Y X of this KeyboardReader
    #

    def read_byte_frames(self) -> tuple[bytes, ...]:
        """Read one Frame at a time, and help the Client ignore H W Y X"""

        (click_release_frame, after) = self._read_click_release_frame_and_after_()

        frame_list = list()
        if click_release_frame:
            frame_list.append(click_release_frame)

        while after:
            (frame, next_after) = self._bytes_split_frame_(after)
            assert (frame + next_after) == after, (frame, next_after, after)

            frame_list.append(frame)
            after = next_after

        frames = tuple(frame_list)
        assert frames, (frames,)

        return frames

    def _read_click_release_frame_and_after_(self) -> tuple[bytes, bytes]:
        """Read Bytes, but split off a leading ⌥-Click if present"""

        reads = self.read_bytes()
        assert reads, (reads,)

        (arrowheads, after) = self.bytes_split_arrowheads(reads)
        assert arrowheads or after, (arrowheads, after, reads)

        click_release_frame = b""
        if arrowheads:
            click_release_frame = self._arrowheads_to_frame_(arrowheads)
            assert click_release_frame, (click_release_frame, arrowheads)

        return (click_release_frame, after)

    def bytes_split_arrowheads(self, data: bytes) -> tuple[str, bytes]:
        """Split a Burst of Arrows into a Head of Arrows and a Tail of Bytes"""

        marks: list[str] = list()
        after = b""

        if len(data) <= 3:
            return ("", data)

        for i in range(0, len(data), 3):
            few = data[i:][:3]  # spans of 3 bytes, but maybe short at end

            if few not in (b"\033[A", b"\033[B", b"\033[C", b"\033[D"):
                after = data[i:]
                break

            ord_mark = few[-1]
            mark = chr(ord_mark)  # the Csi Final Byte

            assert mark in ("A", "B", "C", "D"), (mark, few)
            marks.append(mark)

        arrowheads = "".join(marks)
        return (arrowheads, after)

    def _arrowheads_to_frame_(self, arrowheads: str) -> bytes:
        """Convert a Burst of Arrows into a ⌥-Click Release"""

        y = self.row_y
        x = self.column_x
        h = self.y_high
        w = self.x_wide

        o = (y, x, h, w, arrowheads)

        for a in arrowheads:

            if x > w:
                x -= w
                y += 1

            if a == "A":

                y -= 1

            elif a == "B":

                y += 1

            elif a == "C":

                x += 1

            else:
                assert a == "D", (a,)

                x -= 1
                if x < X1:
                    x += w
                    y -= 1

            if len(arrowheads) <= 3:  # takes Arrow Key Mash as ⌥-Click Release
                y = min(max(Y1, y), h)
                x = min(max(X1, x), w)
                continue

            assert Y1 <= y <= h, (y, x, h, w, o)
            assert X1 <= x <= (w + 1), (y, x, h, w, o)

        if x > w:
            x -= 1

        f = int("0b01000", base=0)  # f = 0b⌃⌥⇧00
        option_mouse_release = f"\033[<{f};{x};{y}m".encode()

        return option_mouse_release  # lower 'm' for Release

    def _bytes_split_frame_(self, data: bytes) -> tuple[bytes, bytes]:
        """Split one Frame off the Start of the Bytes"""

        if not data:
            return (data, b"")

        decode = KeyByteFrame.bytes_decode_if(data)

        # Accept the b"``" as the Frame of ⌥⇧`

        if len(decode) == 2:
            if decode == "``":
                frame = data
                after = b""
                return (frame, after)

            # Split the ⌥ Accents arriving together with an Unaccented Decode

            accents = "`" "´" "¨" "ˆ" "˜"  # ⌥⇧` ⌥⇧E ⌥⇧U ⌥⇧I ⌥⇧N
            if decode[0] in accents:
                frame = decode[0].encode()
                after = decode[1:].encode()
                return (frame, after)

        # Split one Text or Control Frame off the Start of the Bytes

        after = b""

        kbf = KeyByteFrame(b"")
        for i in range(len(data)):
            kbyte = data[i:][:1]
            kbytes = data[i:][1:]

            extras = kbf.take_one_kbyte_if(kbyte)
            if extras:
                assert kbf.closed, (kbf.closed, extras, kbyte, kbf)
                after = extras + kbytes
                break

            if kbf.closed:
                after = kbytes
                break

        frame = kbf.to_frame_bytes()
        assert (frame + after) == data, (frame, after, data)

        return (frame, after)

    #
    # Frame the Input Bytes that share a Cursor Position Report,
    # and update the H W Y X of this KeyboardReader
    #

    def read_bytes(self) -> bytes:
        """Frame the Bytes that share a Cursor Position Report"""

        tb = self.terminal_boss
        fileno = tb.fileno

        # Read one Byte, then call for Cursor Position, then block till it comes

        (yx, reads) = self.read_yx_bytes()
        (row_y, column_x) = yx

        fd = fileno
        (x_wide, y_high) = os.get_terminal_size(fd)

        # Publish this fresh H W Y X sample separately

        assert y_high >= 5, (y_high,)  # todo: test of Terminals smaller than macOS Terminals
        assert x_wide >= 20, (x_wide,)  # todo: test of 9 Columns x 2 Rows at macOS iTerm2

        self.row_y = row_y
        self.column_x = column_x

        self.y_high = y_high
        self.x_wide = x_wide

        # Succeed

        return reads

    def read_yx_bytes(self) -> tuple[tuple[int, int], bytes]:
        """Read one Byte, then call for Cursor Position, then block till it comes"""

        tb = self.terminal_boss

        assert DSR6 == "\033[" "6n"
        assert CPR_Y_X == "\033[" "{};{}R"

        tb.write_some_bytes(b"\033[6n")  # ⎋[6n
        tb.kbhit(timeout=0e0)  # flushes after .write_some_bytes

        y_row = -1
        x_column = -1
        ba = bytearray()

        while True:

            read = tb.read_one_byte()
            ba.extend(read)

            if y_row < 0:
                m = re.search(rb"\033\[([0-9]+);([0-9]+)R$", string=ba)
                if not m:
                    continue

                n = len(m.group(0))
                y_row = int(m.group(1))
                x_column = int(m.group(2))

                del ba[-n:]

                if not ba:  # someone else wrote ⎋[6n earlier
                    continue

            if not tb.kbhit(timeout=0e0):
                break

        yx = (y_row, x_column)
        reads = bytes(ba)

        return (yx, reads)

        # ⌥-Click sends D A B C in the sense of D's, then A's or B's, then C's;
        # except across a Wrapped Line it can even send like D B C B C, and A D A D A,
        # and A D A D C, and so on and on

    #  ⎋[200⇧~ .. ⎋[201⇧~ arrive together from ⎋[ ⇧?2004H Bracketed Paste

    #
    # at macOS Terminal
    #
    #   mashing the ← ↑ → ↓ Arrow Keys sends 1..3 Arrows
    #   ⌥-Click sends 1..X Burst of 1..Y Arrows each
    #   ⌥` sends b"``" sometimes together, sometimes separately
    #

    #
    # at macOS iTerm2
    #
    #   mashing the ← ↑ → ↓ Arrow Keys sends 1..2 Arrows
    #   ⌥-Click sends 1 Burst of 1..Y Arrows
    #   ⌥` sends b"``" always together
    #


@dataclasses.dataclass(order=True)  # , frozen=True)
class KeyByteFrame:
    """Frame the Bytes of an ⎋ Esc Sequence"""

    decodable: bytearray  # b''  # Decodable Printable Text

    head: bytearray  # b''  # N * ESC  # N * ESC + CSI  # N * ESC + SS3  # OSC
    neck: bytearray  # b''  # Csi Params  # Osc Payload
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator

    stash: bytearray  # b''  # 1..3 Bytes taken while not decodable

    closed: bool

    def __init__(self, data: bytes) -> None:

        self.decodable = bytearray()

        self.head = bytearray()
        self.neck = bytearray()
        self.backtail = bytearray()

        self.stash = bytearray()

        self.closed = False

        # Take the Bytes in, else raise ValueError

        for i in range(len(data)):
            kbyte = data[i:][:1]

            extras = self.take_one_kbyte_if(kbyte)
            if extras:
                raise ValueError(extras, kbyte, self)

    def to_frame_bytes(self) -> bytes:
        """List the Bytes taken"""

        decodable = self.decodable

        head = self.head
        neck = self.neck
        backtail = self.backtail

        stash = self.stash

        join = bytes(decodable + head + neck + backtail + stash)

        return join  # no matter if .closed or not

    def close(self) -> None:
        """Close if not closed already"""

        stash = self.stash
        assert not stash, (stash,)

        self.closed = True

    #
    # Pick apart a Esc Csi Sequence into its Marks and Ints
    #

    def to_csi_marks_ints_if(self, frame: bytes) -> tuple[bytes, tuple[int, ...]]:
        """Pick out the Nonnegative Int Literals of a Csi Escape Sequence"""

        decodable = self.decodable
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        assert CSI == "\033["

        if (head != b"\033[") or decodable or stash or (not backtail):
            return (b"", tuple())

        fm = re.fullmatch(rb"^([^0-9;]*)([0-9;]*)(.*)$", string=neck + backtail)
        assert fm, (fm, neck, backtail)

        marks = fm.group(1) + fm.group(3)
        ints = tuple((int(_) if _ else -1) for _ in fm.group(2).split(b";"))

        return (marks, ints)

        # (b"A", [])
        # (b"H", [123, -1])

    #
    # Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit
    #

    def take_one_kbyte_if(self, kbyte: bytes) -> bytes:
        """Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        assert len(kbyte) == 1, (kbyte,)

        decodable = self.decodable
        head = self.head
        stash = self.stash
        closed = self.closed

        assert ESC == "\033"

        assert SS3 == "\033O"
        assert CSI == "\033["
        assert CSI_SHIFT_M == "\033[M"
        assert OSC == "\033]"

        # Bounce while Closed

        if closed:
            return kbyte

        # Hold 1..3 Bytes to decode later

        encode = bytes(stash + kbyte)
        try:
            decode = encode.decode()
        except UnicodeDecodeError:
            decode = ""

        if not decode:
            if KeyByteFrame.bytes_to_later_decode_if(encode):
                stash.extend(kbyte)
                return b""

        assert len(decode) <= 1, (len(decode), decode, encode)

        stash.clear()

        # Take the Bytes in before the first Head, or without ever a Head

        if not head:
            extras = self._take_before_head_if_(encode, decode=decode)
            return extras

        # Take later Bytes in differently, after starts with each kind of Head

        assert not decodable, (decodable,)

        dent = len(head) - len(head.lstrip(b"\033"))
        dent = (dent - 1) if dent else 0
        undented_head = head[dent:]

        if undented_head == b"\033":
            extras = self._take_after_esc_if_(encode)
            return extras

        elif undented_head == b"\033O":
            extras = self._take_after_ss3_if_(encode)
            return extras

        elif undented_head == b"\033[M":
            extras = self._take_after_csi_m_if_(encode)
            return extras

        elif undented_head == b"\033[":
            extras = self._take_after_csi_if_(encode, decode=decode)
            return extras

        elif undented_head == b"\033]":
            extras = self._take_after_osc_if_(encode, decode=decode)
            return extras

        assert False, (head, head[dent:], dent, self)

    def _take_before_head_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 more Bytes in, before any Head, else return what doesn't fit"""

        decodable = self.decodable
        head = self.head

        # Take 1 Decoded Printable Char, without closing the Frame

        if decode:
            if decode.isprintable():
                self.decodable = decodable + encode
                return b""

        # End a Text Frame before Unprintable or Undecodable Bytes

        if decodable:
            self.close()
            return encode

        # Take 1..4 Unprintable or Undecodable Bytes as Head

        head.extend(encode)
        if head != b"\033":
            self.close()

        return b""

        # takes \b \t \n \r \x7f etc

        # doesn't take bytes([0x80 | 0x0B]) as meaning b"\033\x5b" Csi ⎋[
        # doesn't take bytes([0x80 | 0x0F]) as meaning b"\033\x4f" Ss3 ⎋O
        # doesn't take bytes([0x90 | 0x0D]) as meaning b"\033\x5d" Osc ⎋]

        # despite "Table 2b - Bit combinations" "control functions of the C1 set in an 8-bit code"

    Headbook = (
        b"\033",  # ⎋ ESC
        b"\033\033",  # ⎋⎋ after
        b"\033\033O",  # ⎋⎋O is ⎋ before ⎋O
        b"\033\033[",  # ⎋⎋[ is ⎋ before ⎋[
        b"\033O",  # ⎋O SS3
        b"\033[",  # ⎋[ CSI
        b"\033[M",  # ⎋[⇧M Click Press/ Release
        b"\033]",  # ⎋ OSC
    )

    def _take_after_esc_if_(self, encode: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋ Esc, else return what doesn't fit"""

        head = self.head

        # Take one of the ⎋ Esc Head's, without closing the Frame

        head_plus = head + encode
        if head_plus in KeyByteFrame.Headbook:
            lstrip = head_plus.lstrip(b"\033")
            assert len(lstrip) <= 1, (head_plus,)

            head.extend(encode)
            return b""

            # doesn't take ⇧M after \⎋ [ here

        # Take ⎋ Esc as an Emacs Meta Byte before 1..4 Bytes

        head.extend(encode)
        self.close()
        return b""

    def _take_after_ss3_if_(self, encode: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋O SS3, else return what doesn't fit"""

        head = self.head

        head.extend(encode)
        self.close()
        return b""

    def _take_after_csi_m_if_(self, encode: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[⇧M, else return what doesn't fit"""

        head = self.head
        backtail = self.backtail

        # Take up to three B X Y Chars after the Head, if all decodable

        head_backtail_plus = bytes(head + backtail + encode)
        plus_later = KeyByteFrame.bytes_to_later_decode_if(head_backtail_plus)
        assert not plus_later, (plus_later, head, backtail, encode)

        plus_decode = KeyByteFrame.bytes_decode_if(head_backtail_plus)
        if plus_decode:
            if len(plus_decode) <= 6:
                backtail.extend(encode)
                if len(plus_decode) == 6:
                    self.close()
                return b""

        # Take up to three B X Y Bytes after the Head without limitation

        fit = 6 - len(head + backtail)
        if fit > 0:
            backtail.extend(encode[:fit])
            extra = encode[fit:]
            if len(head_backtail_plus) >= 6:
                self.close()
            return extra  # maybe empty

        # Close the ⎋[⇧M Frame after 6 Bytes or before

        self.close()
        return encode

    def _take_after_csi_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[ CSI, else return what doesn't fit"""

        code = ord(decode)

        head = self.head
        neck = self.neck
        backtail = self.backtail

        assert CSI_SHIFT_M == "\033[M"

        # Take the 3-Byte ⎋[⇧M Esc Head, without closing the Frame

        if (not neck) and (not backtail):
            head_plus = head + encode
            if head_plus in KeyByteFrame.Headbook:
                assert head_plus == b"\033[M", (head_plus,)
                head.extend(encode)
                return b""

        # Grow the ⎋[ Csi Frame with 1 Decoded Printable Char

        if decode and decode.isprintable():
            assert code >= 0x20, (code, decode, encode)

            # Grow the Neck until the Backtail starts

            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?

                if not backtail:
                    neck.extend(encode)
                    return b""

                # Close before more Params, if Backtail has started

                self.close()
                return encode

            # Grow the Backtail

            if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # ␢!"#$%&\'()*+,-./
                backtail.extend(encode)
                return b""

            # Close after a Csi Final Code, or after Printable Unicode

            assert code >= 0x40, (code, decode, encode)  # 63 Final Codes  # @A Z[\\]^_`a z{|}~

            backtail.extend(encode)
            self.close()
            return b""

        # Close the ⎋[ Csi Frame before Unprintable or Undecodable Bytes

        self.close()
        return encode

    def _take_after_osc_if_(self, encode: bytes, decode: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋] OSC, else return what doesn't fit"""

        neck = self.neck
        backtail = self.backtail

        assert BEL == "\007"
        assert ST == "\033\134"

        # Grow the ⎋] Osc Frame with 1 Decoded Printable Char

        if decode and decode.isprintable():
            neck.extend(encode)
            return b""

        # Close the ⎋] Osc Frame with BEL or ST

        if decode == "\007":
            backtail.extend(encode)
            self.close()
            return b""

        if not backtail:
            if decode == "\033":
                backtail.extend(encode)
                self.close()
                return b""

        if backtail == b"\033":
            if decode == "\134":
                backtail.extend(encode)
                self.close()
                return b""

            # todo: how should other Bytes past "\033" close an ⎋] Osc Frame?

        # Close the ⎋] Osc Frame before Unprintable or Undecodable Bytes

        self.close()
        return encode

    #
    # Work with Decodable and Undecodable Bytes
    #

    @staticmethod
    def bytes_decode_if(data: bytes) -> str:
        """Say if decodable"""

        try:
            decode = data.decode()
            return decode  # returns first found
        except UnicodeDecodeError:
            pass

        return ""

    Endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    @staticmethod
    def bytes_to_later_decode_if(data: bytes) -> str:
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        endswiths = KeyByteFrame.Endswiths

        for endswith in endswiths:
            encode = data + endswith
            try:
                decode = encode.decode()
                assert len(decode) >= 1, (decode,)
                return decode  # returns first found
            except UnicodeDecodeError:
                continue

        return ""

    #
    # for b"\xc2", b"\xed", b"\xe0", b"\xf4", b"\xf0", & friends
    # because =>
    #
    # "\u0000"  # b"\x00"
    # "\u007f"  # b"\x7f"
    #
    # "\u0080"  # b"\xc2\x80" accepted with b"\xc2\xbf", could be accepted as b"\xc2\x80"
    # "\u07ff"  # b"\xdf\xbf" ditto
    #
    # "\u0800"  # b"\xe0\xa0\x80" accepted with b"\xe0\xbf\xbf"
    # "\ud7ff"  # b"\xed\x9f\xbf" accepted with b"\xed\x80\x80"
    # "\ud800".."\udfff"  # rejected as b"\xed\xa0\x80" .. b"\xed\xbf\xbf" surrogates
    # "\ue000"  # b"\xee\x80\x80" accepted
    # "\uffff"  # b"\xef\xbf\xbf" accepted
    #
    # "\U00010000"  # b"\xf0\x90\x80\x80" accepted with "\xf0\xbf\xbf\xbf"
    # "\U0010ffff"  # b"\xf4\x8f\xbf\xbf" accepted with "\xf4\x80\x80\x80"
    #

    # todo: invent UTF-8'ish Encoding beyond 1..4 Bytes for Unicode Codes > 0x10_FFFF ?


Y1 = 1  # min Y of Terminal Cursor
X1 = 1  # min X of Terminal Cursor


BEL = "\007"  # 00/07 Bell

ESC = "\033"  # 01/11 Escape ⎋

SS3 = "\033O"  # 01/11 04/15 Single Shift Three  # ⎋O
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer  # ⎋[
OSC = "\033]"  # 01/11 05/13 Operating System Command  # ⎋]

ST = "\033\134"  # 01/11 05/12 String Terminator  # ⎋\


CSI_SHIFT_M = "\033[M"  # ⎋[⇧M{b}{x}{y} Click Press/ Release


DSR6 = "\033[" "6n"  # Csi 06/14 [Request] Device Status Report  # Ps 6 Request CPR  # ⎋[6N
CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R


#
# Speak of a Byte Encoding as a Sequence of Chords of Keycaps
#


class KeyboardDecoder:
    """Speak of a Byte Encoding as a Sequence of Chords of Keycaps"""

    selves: list[KeyboardDecoder] = list()

    decode_by_kseq: dict[str, str]
    kseqs_by_decode: dict[str, tuple[str, ...]]

    def __init__(self) -> None:

        KeyboardDecoder.selves.append(self)

        self.decode_by_kseq = dict()
        self.kseqs_by_decode = dict()

        self._add_basic_kseqs_()
        self._invert_decode_by_kseq_()

    #
    # Speak of a Byte Encoding as a Sequence of Chords of Keycaps
    #

    def to_kseqs_if(self, data: bytes) -> tuple[str, ...]:
        """Speak of a Byte Encoding as a Sequence of Chords of Keycaps"""

        decode = data.decode()

        kseqs_by_decode = self.kseqs_by_decode

        if decode in kseqs_by_decode.keys():
            kseqs = kseqs_by_decode.get(decode, tuple())
            return kseqs

        return tuple()

    #
    # Add the Keycap Sequences for US-Ascii at MacBook
    #

    def _add_basic_kseqs_(self) -> None:
        """Add the Keycap Sequences for US-Ascii at MacBook"""

        decode_by_kseq = self.decode_by_kseq

        # Add the named Keycaps: Esc, Tab, ⇧Tab, Return, Delete

        d0 = {
            r"⇥": "\t",  # ⌃I
            r"⏎": "\r",  # ⌃M
            r"⎋": "\033",  # ⌃[
            r"⇧⇥": "\033[" "Z",  # ⎋ [ ⇧Z
            r"⌫": "\177",  # ⌃⇧?
        }

        for k, v in d0.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the forms of Spacebar

        d1 = {
            r"␢": "\040",  # ⌃`
            r"⌃␢": "\000",  # ⌃⇧@
            r"⌥␢": "\240",  # U+00A0 No-Break Space
        }

        for k, v in d1.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the unnamed Keycaps: ⇧A..⇧Z, A..Z, 0..9, and the marks

        kseq = r"""

            ⌃⇧@  ⌃A  ⌃B  ⌃C  ⌃D  ⌃E  ⌃F  ⌃G  ⌃H  ⌃I  ⌃J  ⌃K  ⌃L  ⌃M  ⌃N  ⌃O
            ⌃P  ⌃Q  ⌃R  ⌃S  ⌃T  ⌃U  ⌃V  ⌃W  ⌃X  ⌃Y  ⌃Z  ⌃[  ⌃\  ⌃]  ⌃⇧^  ⌃-

            ⌃`  ⇧!  ⇧"  ⇧#  ⇧$  ⇧%  ⇧&  '  ⇧(  ⇧)  ⇧*  ⇧+  ,  -  .  /
            0  1  2  3  4  5  6  7  8  9  ⇧:  ;  ⇧<  =  ⇧>  ⇧?

            ⇧@  ⇧A  ⇧B  ⇧C  ⇧D  ⇧E  ⇧F  ⇧G  ⇧H  ⇧I  ⇧J  ⇧K  ⇧L  ⇧M  ⇧N  ⇧O
            ⇧P  ⇧Q  ⇧R  ⇧S  ⇧T  ⇧U  ⇧V  ⇧W  ⇧X  ⇧Y  ⇧Z  [  \  ]  ⇧^  ⇧_

            `  A  B  C  D  E  F  G  H  I  J  K  L  M  N  O
            P  Q  R  S  T  U  V  W  X  Y  Z  ⇧{  ⇧|  ⇧}  ⇧~  ⌃⇧?

        """

        code = -1
        for kcap in kseq.split():
            code += 1
            decode = chr(code)

            if kcap not in ("⌃`", "⌃⇧?"):
                assert kcap not in decode_by_kseq.keys(), (kcap,)
                decode_by_kseq[kcap] = decode

        # Add the aliases

        d2 = {
            r"⌃⇧_": r"⌃-",  # quicker to type ⌃-, easier to encode ⌃⇧_
            r"⌃⇧{": r"⌃[",
            r"⌃⇧|": r"⌃\ ".rstrip(),
            r"⌃⇧}": r"⌃]",
        }

        for k, v in d2.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = decode_by_kseq[v]

        # Add the basic Arrows

        d3 = {
            r"↑": "\033[" "A",  # ⎋[⇧A
            r"↓": "\033[" "B",  # ⎋[⇧B
            r"→": "\033[" "C",  # ⎋[⇧C
            r"←": "\033[" "D",  # ⎋[⇧D
        }

        for k, v in d3.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

        # Add the ⌥ and ⇧ Arrows

        d4 = {
            r"⌥↑": d3[r"↑"],
            r"⌥↓": d3[r"↓"],
            r"⌥→": "\033" "f",  # ⎋F
            r"⌥←": "\033" "b",  # ⎋B
            #
            r"⇧↑": d3[r"↑"],
            r"⇧↓": d3[r"↓"],
            r"⇧→": "\033[" "1;2C",  # ⎋[1;2⇧C
            r"⇧←": "\033[" "1;2D",  # ⎋[1;2⇧D
            #
            r"⌥⇧↑": d3[r"↑"],
            r"⌥⇧↓": d3[r"↓"],
            r"⌥⇧→": d3[r"→"],
            r"⌥⇧←": d3[r"←"],
            #
            r"⇧Fn↑": "\033[" "5~",  # ⎋[5⇧~
            r"⇧Fn↓": "\033[" "6~",  # ⎋[6⇧~
            r"⇧Fn→": "\033[" "F",  # ⎋[⇧F
            r"⇧Fn←": "\033[" "H",  # ⎋[⇧H
        }

        for k, v in d4.items():
            assert k not in decode_by_kseq.keys(), (k,)
            decode_by_kseq[k] = v

    #
    # Index the Keycap Sequences by their Decodes
    #

    def _invert_decode_by_kseq_(self) -> None:
        """Index the Keycap Sequences by their Decodes"""

        decode_by_kseq = self.decode_by_kseq
        kseqs_by_decode = self.kseqs_by_decode

        # Index the Sequences collected by now

        d = collections.defaultdict(list)
        for kseq, decode in decode_by_kseq.items():
            d[decode].append(kseq)

        # Add the ⌥ variants of Non-Blank Printable US-Ascii

        assert "" == "\uf8ff"

        plain_printables = r"""
            -!"#$%&'()*+,-./
            0123456789:;<=>?
            @ABCDEFGHIJKLMNO
            PQRSTUVWXYZ[\]^_
            `abcdefghijklmno
            pqrstuvwxyz{|}~
        """

        option_printables = r"""
            ¥⁄Æ‹›ﬁ‡æ·‚°±≤–≥÷
            º¡™£¢∞§¶•ªÚ…¯≠˘¿
            €ÅıÇÎ´Ï˝ÓˆÔÒÂ˜Ø
            ∏Œ‰Íˇ¨◊„˛Á¸“«‘ﬂ—
            ¥å∫ç∂¥ƒ©˙¥∆˚¬µ¥ø
            πœ®ß†¥√∑≈¥Ω”»’¥
        """

        assert len(plain_printables) == len(option_printables)

        for plain, option in zip(plain_printables, option_printables):
            if option in ("\n", " ", "¥"):
                continue

            assert option not in plain_printables, (option,)

            kseq = "⌥" + d[plain][0]
            decode = option

            assert kseq not in decode_by_kseq.keys(), (kseq,)
            decode_by_kseq[kseq] = decode

            d[decode].append(kseq)

            # ⌥Y comes through as the U+005C Reverse-Solidus, not U+00A5 ¥ Yen-Sign

        assert option_printables.count("¥") == 8  # ⌥␢ ⌥E ⌥I ⌥N ⌥U ⌥Y ⌥` ⌥⌫

        option_kseq_by_decode = {  # upper "j́" is "J́" len 2 decode, led by plain U+004A 'J'
            # ⌥E
            "á": "⌥E A",  # ⌥⇧Y is Á is ⌥E ⇧A
            "é": "⌥E E",
            "í": "⌥E I",  # ⌥⇧S is Í is ⌥E ⇧I
            "j́": "⌥E J",  # len 2 decode, led by plain U+006A 'j'
            "ó": "⌥E O",  # ⌥⇧H is Ó is ⌥E ⇧O
            "ú": "⌥E U",
            "´": "⌥⇧E",
            # ⌥I
            "â": "⌥I A",  # ⌥⇧M is Â is ⌥I ⇧A
            "ê": "⌥I E",
            "î": "⌥I I",  # ⌥⇧D is Î is ⌥I ⇧I
            "ô": "⌥I O",  # ⌥⇧J is Ô is ⌥I ⇧O
            "û": "⌥I U",
            "ˆ": "⌥⇧I",
            # ⌥N
            "ã": "⌥N A",
            "ñ": "⌥N N",
            "õ": "⌥N O",
            "˜": "⌥⇧N",
            # ⌥U
            "ä": "⌥U A",
            "ë": "⌥U E",
            "ï": "⌥U I",  # ⌥⇧F is ï is ⌥U ⇧I
            "ö": "⌥U O",
            "ü": "⌥U U",
            "ÿ": "⌥U Y",
            "¨": "⌥⇧U",
            # ⌥`
            "à": "⌥` A",
            "è": "⌥` E",
            "ì": "⌥` I",
            "ò": "⌥` O",  # ⌥⇧L is Ò is ⌥` ⇧O
            "ù": "⌥` U",
            "``": "⌥`",  # len 2 decode, two copies of plain U+0060 ` Grave Accent
        }

        for decode, kseq in option_kseq_by_decode.items():

            if kseq in decode_by_kseq.keys():
                assert decode_by_kseq[kseq] == decode, (decode_by_kseq[kseq], decode, kseq)
            else:
                decode_by_kseq[kseq] = decode
                d[decode].append(kseq)

            if " " in kseq:
                ks = kseq[:-1] + "⇧" + kseq[-1:]
                dc = decode.upper()  # 'Á' from 'á'
                if dc != decode:

                    if ks in decode_by_kseq.keys():
                        assert decode_by_kseq[ks] == dc, (decode_by_kseq[ks], dc, ks)
                    else:
                        decode_by_kseq[ks] = dc
                        d[dc].append(ks)

        # Add the "Use Option as Meta key" of macOS Terminal

        for code in range(0, 0x80):
            if code not in (0, 0x1E):  # ⎋⌃␢ and ⎋⌃⇧@ and ⎋⌃⇧^ don't
                decode = chr(code)

                kseqs = tuple(d[decode])
                for kseq in kseqs:
                    assert " " not in kseq, (kseq,)

                    alt_kseq = "⎋" + kseq  # '⎋␢'
                    alt_decode = "\033" + decode

                    assert alt_kseq not in decode_by_kseq.keys(), (alt_kseq,)
                    decode_by_kseq[alt_kseq] = alt_decode

                    d[alt_decode].append(alt_kseq)

                    # ⎋B hides behind ⌥←, ⎋F hides behind ⌥→

        kseqs = ("⇧⇥", "↑", "↓", "→", "←")
        for kseq in kseqs:
            assert " " not in kseq, (kseq,)
            decode = decode_by_kseq[kseq]

            alt_kseq = "⎋" + kseq  # '⎋␢'
            alt_decode = "\033" + decode

            assert alt_kseq not in decode_by_kseq.keys(), (alt_kseq,)
            decode_by_kseq[alt_kseq] = alt_decode

            d[alt_decode].append(alt_kseq)

            # ⎋← hides behind ⎋B behind ⌥←, ⎋→ hides behind ⎋F behind ⌥→

        # Convert to immutable Tuples from mutable Lists

        for decode, kseq_list in d.items():
            assert decode not in kseqs_by_decode, (decode, kseqs_by_decode[decode], kseq_list)
            kseqs_by_decode[decode] = tuple(kseq_list)


#
# Try things
#


def _try_lit_glass_() -> None:
    """Run slow and quick Self-Test's of this Module"""

    _try_key_byte_frame_()


def _try_key_byte_frame_() -> None:

    KeyByteFrame(b"")

    kbf = KeyByteFrame(b"\x1b[A")
    assert kbf.to_frame_bytes() == b"\x1b[A", (kbf,)
    assert kbf.closed, (kbf,)

    kbf = KeyByteFrame(b"\x1b\x1b[A")
    assert kbf.to_frame_bytes() == b"\x1b\x1b[A", (kbf,)
    assert kbf.closed, (kbf,)

    kbf = KeyByteFrame(b"\x1b[Mabc")
    assert kbf.to_frame_bytes() == b"\x1b[Mabc", (kbf,)
    assert kbf.closed, (kbf,)

    kbf = KeyByteFrame(b"\x1b[Mab\xff")
    assert kbf.to_frame_bytes() == b"\x1b[Mab\xff", (kbf,)
    assert kbf.closed, (kbf,)

    #
    # todo: port in more KeyByteFrame tests from ._try_key_pack_ of
    #   https://github.com/pelavarre/less-beeps/blob/1009pl/bin/less-beeps.py
    #


#
# Amp up Import ArgParse
#


_ARGPARSE_3_10_ = (3, 10)  # Oct/2021 Python 3.10, like from Ubuntu 2022


@dataclasses.dataclass(order=True)  # , frozen=True)
class ArgDocParser:
    """Scrape Prog & Description & Epilog from Doc to form an ArgParse Argument Parser"""

    doc: str  # a copy of parser.format_help()
    add_help: bool  # truthy to define '-h, --help', else not

    parser: argparse.ArgumentParser  # the inner standard ArgumentParser
    text: str  # something like the __main__.__doc__, but dedented and stripped
    closing: str  # the last Graf of the Epilog, minus its Top Line

    add_argument: collections.abc.Callable[..., object]

    def __init__(self, doc: str, add_help: bool) -> None:

        self.doc = doc
        self.add_help = add_help

        text = textwrap.dedent(doc).strip()

        prog = self._scrape_prog_(text)
        description = self._scrape_description_(text)
        epilog = self._scrape_epilog_(text, description=description)
        closing = self._scrape_closing_(epilog)

        parser = argparse.ArgumentParser(  # doesn't distinguish Closing from Epilog
            prog=prog,
            description=description,
            add_help=add_help,
            formatter_class=argparse.RawTextHelpFormatter,  # lets Lines be wide
            epilog=epilog,
        )

        self.parser = parser
        self.text = text
        self.closing = closing

        self.add_argument = parser.add_argument

        # 'add_help=False' for needs like 'cal -h', 'df -h', 'du -h', 'ls -h', etc

        # callers who need Options & Positional Arguments have to add them

    #
    # Take in the Shell Args, else print Help and exit zero or nonzero
    #

    def parse_args_if(self, args: list[str]) -> argparse.Namespace:
        """Take in the Shell Args, else print Help and exit zero or nonzero"""

        parser = self.parser
        closing = self.closing

        # Print Diffs & exit nonzero, when Arg Doc wrong

        diffs = self._diff_doc_vs_format_help_()
        if diffs:
            if sys.version_info >= _ARGPARSE_3_10_:
                print("\n".join(diffs))

                sys.exit(2)  # exits 2 for wrong Args in Help Doc

            # takes 'usage: ... [HINT ...]', rejects 'usage: ... HINT [HINT ...]'
            # takes 'options:', rejects 'optional arguments:'
            # takes '-F, --isep ISEP', rejects '-F ISEP, --isep ISEP'

        # Print Closing & exit zero, if no Shell Args

        if not args:
            print()
            print(closing)
            print()

            sys.exit(0)  # exits 0 after printing Closing

        # Drop the "--" Shell Args Separator, if present,
        # because 'ArgumentParser.parse_args()' without Pos Args wrongly rejects it

        shargs = list(args)
        if len(args) == 1:  # because ArgParse chokes if '--' Sep present without Pos Args
            if args[0] == "--":
                shargs.clear()

        # Print help lines & exit zero, else return Parsed Args

        ns = parser.parse_args(shargs)

        return ns

        # often prints help & exits zero

    #
    # Scrape out Parser, Prog, Description, Epilog, & Closing from Doc Text
    #

    def _scrape_prog_(self, text: str) -> str:
        """Pick the Prog out of the Usage Graf that starts the Doc"""

        lines = text.splitlines()
        prog = lines[0].split()[1]  # second Word of first Line  # 'prog' from 'usage: prog'

        return prog

    def _scrape_description_(self, text: str) -> str:
        """Take the first Line of the Graf after the Usage Graf as the Description"""

        lines = text.splitlines()

        firstlines = list(_ for _ in lines if _ and (_ == _.lstrip()))
        docline = firstlines[1]  # first Line of second Graf

        description = docline
        if self._docline_is_skippable_(docline):
            description = "just do it"

        return description

    def _scrape_epilog_(self, text: str, description: str) -> str:
        """Take up the Lines past Usage, Positional Arguments, & Options, as the Epilog"""

        lines = text.splitlines()

        epilog = ""
        for index, line in enumerate(lines):
            if self._docline_is_skippable_(line) or (line == description):
                continue

            epilog = "\n".join(lines[index:])
            break

        return epilog  # maybe empty

    def _docline_is_skippable_(self, docline: str) -> bool:
        """Guess when a Doc Line can't be the first Line of the Epilog"""

        strip = docline.rstrip()

        skippable = not strip
        skippable = skippable or strip.startswith(" ")  # includes .startswith("  ")
        skippable = skippable or strip.startswith("usage")
        skippable = skippable or strip.startswith("positional arguments")
        skippable = skippable or strip.startswith("options")  # ignores "optional arguments"

        return skippable

    def _scrape_closing_(self, epilog: str) -> str:
        """Pick out the last Graf of the Epilog, minus its Top Line"""

        lines = epilog.splitlines()

        indices = list(_ for _ in range(len(lines)) if lines[_])  # drops empty Lines
        indices = list(_ for _ in indices if not lines[_].startswith(" "))  # finds top Lines

        closing = ""
        if indices:
            index = indices[-1] + 1

            join = "\n".join(lines[index:])  # last Graf, minus its Top Line
            dedent = textwrap.dedent(join)
            closing = dedent.strip()

        return closing  # maybe empty

    #
    # Form Diffs from Help Doc to Parser Format_Help
    #

    def _diff_doc_vs_format_help_(self) -> list[str]:
        """Form Diffs from Help Doc to Parser Format_Help"""

        text = self.text
        parser = self.parser

        # Say where the Help Doc came from

        a = text.splitlines()

        basename = os.path.split(__file__)[-1]
        fromfile = "{} --help".format(basename)

        # Fetch the Parser Doc from a fitting virtual Terminal
        # Fetch from a Black Terminal of 89 columns, not from the current Terminal Width
        # Fetch from later Python of "options:", not earlier Python of "optional arguments:"

        with_columns_else = os.environ.get("COLUMNS", default_eq_None)  # checkpoints
        with_no_color_else = os.environ.get("NO_COLOR", default_eq_None)  # checkpoints

        os.environ["COLUMNS"] = str(89)  # adds or replaces
        os.environ["NO_COLOR"] = "True"  # adds or replaces

        try:

            b_text = parser.format_help()

        finally:

            if with_no_color_else is None:
                del os.environ["NO_COLOR"]  # removes
            else:
                os.environ["NO_COLOR"] = with_no_color_else  # reverts

            if with_columns_else is None:
                del os.environ["COLUMNS"]  # removes
            else:
                os.environ["COLUMNS"] = with_columns_else  # reverts

        b = b_text.splitlines()

        tofile = "ArgumentParser(...)"

        # Form >= 0 Diffs from Help Doc to Parser Format_Help,
        # but ask for lineterm="", for else the '---' '+++' '@@' Diff Control Lines end with '\n'

        diffs = list(difflib.unified_diff(a=a, b=b, fromfile=fromfile, tofile=tofile, lineterm=""))

        # Succeed

        return diffs

        # .parser.format_help defaults to color its texts, since Oct/2025 Python 3.14


#
# Amp up Import Traceback
#
# Especially when installed via:  sys.excepthook = excepthook
#


with_excepthook = sys.excepthook  # aliases old hook, and fails fast to chain hooks
assert with_excepthook.__module__ == "sys", (with_excepthook.__module__,)
assert with_excepthook.__name__ == "excepthook", (with_excepthook.__name__,)

assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr


assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def excepthook(  # ) -> ...:
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: types.TracebackType | None,
) -> None:
    """Run at Process Exit"""

    sys.excepthook = with_excepthook

    if exc_type is SystemExit:
        assert sys.flags.interactive, (sys.flags.interactive, exc_type, exc_value)  # aka python3 -i
        return

        # consciously doesn't call: with_excepthook(exc_type, exc_value, exc_traceback)

    # Quit loudly for KeyboardInterrupt

    if exc_type is KeyboardInterrupt:
        pass

    # Quit quickly quietly, if BdbQuit

    if exc_type is bdb.BdbQuit:
        with_stderr.write("BdbQuit\n")
        sys.exit(130)  # 0x80 + signal.SIGINT  # same as for KeyboardInterrupt

    # Print the Traceback, etc

    print(file=with_stderr)
    print(file=with_stderr)  # twice
    print("ExceptHook", file=with_stderr)

    with_excepthook(exc_type, exc_value, exc_traceback)

    # Launch the Post-Mortem Debugger

    print(">>> pdb.pm()", file=with_stderr)
    pdb.pm()


#
# Cite some Terminal Escape & Control Sequence Docs
#


_ = """  # our top choices

    https://unicode.org/charts/PDF/U0000.pdf
    https://unicode.org/charts/PDF/U0080.pdf

    https://en.wikipedia.org/wiki/ANSI_escape_code
    https://jvns.ca/blog/2025/03/07/escape-code-standards

    https://invisible-island.net/xterm/ctlseqs/ctlseqs.html

    https://www.ecma-international.org/publications-and-standards/standards/ecma-48
        /wp-content/uploads/ECMA-48_5th_edition_june_1991.pdf

"""

_ = """  # more breadth found via https://jvns.ca/blog/2025/03/07/escape-code-standards

    https://github.com/tmux/tmux/blob/master/tools/ansicode.txt  <= close to h/t jvns.ca
    https://man7.org/linux/man-pages/man4/console_codes.4.html
    https://sw.kovidgoyal.net/kitty/keyboard-protocol
    https://vt100.net/docs/vt100-ug/chapter3.html

    https://iterm2.com/feature-reporting
    https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
    https://github.com/Alhadis/OSC8-Adoption?tab=readme-ov-file

"""

_ = """  # more famous Python Imports to run in place of our Code here

    curses — Terminal handling for character-cell displays
    https://docs.python.org/3/library/curses.html for 'import curses'

    tkinter — Python interface to Tcl/Tk
    https://docs.python.org/3/library/tkinter.html

    turtle — Turtle graphics
    https://docs.python.org/3/library/turtle.html for 'import turtle'

"""


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# todo9: reply to KeyCaps
# todo9: scavenge repeat count input as Python Literal Int, maybe marked with ⌃U

# todo9: drop Keycaps specific to macOS Terminal, when elsewhere
# todo9: add iTerm2 Keycaps
# todo9: add Google Cloud Shell Keycaps

# todo9: add Fn Keycaps

# todo9: --egg=scroll to scroll then swap in Alt Screen
# todo9: --egg=paste to do bracketed paste
# todo9: echo input
# todo9: show settings
# todo9: place input echoes on the side


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
