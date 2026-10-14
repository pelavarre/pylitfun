#!/usr/bin/env python3

r"""
usage: litpyglass.py [--egg=EGG ...]

loop back to write Screen after reading from Touch/ Mouse/ Key

options:
  --egg EGG  a hint of how to behave, such as 'bytes' or 'frames'

quirks:
  quits when given an unprintable, 3 times in a row, but 100ms or more apart, across less than 3s

examples:
  python3 pylitglass/litpyglass.py  # show these examples
  chmod +x pylitglass/litpyglass.py
  pylitglass/litpyglass.py --  # pick a demo and run it
  pylitglass/litpyglass.py --egg=bytes  # print your input bytes, on screen
  pylitglass/litpyglass.py --egg=nanos  # print your input bytes and when they arrived
  pylitglass/litpyglass.py --egg=frames  # print your inputs split into frames, named when known
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import collections
import dataclasses
import decimal
import errno
import functools
import io
import os
import re
import select
import string
import sys
import termios
import textwrap
import time
import tty
import typing
import unicodedata

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


#
# Configure
#


_3_GIGA_NANOS_IS_TOO_SLOW_ = 3 * 10**9  # to slow to take 3 same inputs in a row as a quit request
_100_MEGA_NANOS_IS_TOO_FAST_ = 100 * 10**6  # too fast to take 3 in a row as a quit request


assert unicodedata.name("¤").title() == "Currency Sign"


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    # Help or don't help

    closing = _main_doc_scrape_closing_()

    shargv = sys.argv[1:]
    if not shargv:
        print()
        print(closing)
        print()

        sys.exit(0)  # exits zero after printing help

    print()  # signal very very quietly that we have run this far since launching

    # Pick a demo, else freak  # todo: tighter parsing of .shargv

    eggs = list(_.removeprefix("--egg=") for _ in shargv if _.startswith("--egg="))
    if not eggs:
        eggs.append("bytes")

    GlassWorker.nano_launch = time.perf_counter_ns()

    if "bytes" in eggs:
        GlassWorker.show_bytes()
    elif "nanos" in eggs:
        GlassWorker.show_nanos()
    elif "frames" in eggs:
        GlassWorker.show_frames()
    else:
        assert False, (eggs,)

    # Self-test quickly, and succeed

    _try_terminal_byte_frame_()
    _try_keyboard_decoder_()

    print()

    # ends with 0 or 1 or 2 empty lines
    # 0 for Stdin Eof, 1 commonly, 2 for quit via Return Return Return in particular


def _main_doc_scrape_closing_() -> str:
    """Scrape out the last Graf of Main Doc, minus its header"""

    doc = __doc__ or ""  # pylance fears __doc__ is None
    header = "examples:\n"
    index = doc.index(header) + len(header)
    closing = textwrap.dedent(doc[index:]).strip()

    return closing


#
# Show off one Terminal feature and another
#


class GlassWorker:
    """Show off one Terminal feature and another"""

    nano_launch = -1

    @staticmethod
    def show_bytes() -> None:
        """Print your input bytes on screen"""

        # Launch (and prompt just once and early)

        print("Press Return three times quickly, to quit")
        print()

        with TerminalBoss() as tb:
            ibk = ByteKeeper()

            while True:

                # Read

                b = tb.read_one_byte_if()
                if not b:
                    break

                ibk.append_one_byte(b)

                # Print, and separate on request

                print(ord(b), repr(b), end="\r\n")
                if b == b"\r":
                    print()

                # Quit on request

                if ibk.is_quitting_bytes():
                    break

    _ = r"""

        % pylitglass/litpyglass.py --egg=bytes

        Press Return three times quickly, to quit

        27 b'\x1b'
        91 b'['
        65 b'A'
        13 b'\r'

        9 b'\t'
        9 b'\t'
        9 b'\t'

        %

    """

    @staticmethod
    def show_nanos() -> None:
        """Print your input bytes (and how quickly they arrived)"""

        # Launch (and prompt just once and early)

        print("Press Return three times quickly, to quit")
        print()

        before = GlassWorker.nano_launch

        with TerminalBoss() as tb:
            ibk = ByteKeeper()

            while True:

                # Read

                b = tb.read_one_byte_if()
                if not b:
                    break

                after = time.perf_counter_ns()
                ibk.append_one_byte(b, nano=after)

                # Print, and separate on request

                code = ord(b)
                between = after - before
                before = after

                print(f"{between:_}", code, repr(b), end="\r\n")
                if b == b"\r":
                    print()

                # Quit on request

                if ibk.is_quitting_bytes():
                    break

    _ = r"""

        % pylitglass/litpyglass.py --egg=nanos

        Press Return three times quickly, to quit

        600_288_333 27 b'\x1b'
        120_500 91 b'['
        25_250 65 b'A'
        553_496_542 13 b'\r'

        1_492_019_167 3 b'\x03'
        185_701_041 3 b'\x03'
        248_232_584 3 b'\x03'

        %

    """

    @staticmethod
    def show_frames() -> None:
        """Print your input byte frames, as Key Caps when known, and how quickly they arrived"""

        # Launch

        print("Press Return three times quickly, to quit")
        print()

        with TerminalBoss() as tb:
            ifk = TerminalFrameKeeper()

            before = time.perf_counter_ns()  # doesn't measure time to launch
            cells: list[object] = list()

            while True:

                # Prompt after each Byte

                frame = ifk.frame
                open_data = frame.to_frame_bytes()  # maybe empty
                _end_ = " + " if not frame.closed else " "  # ' +' while open, as str(Frame) has it
                GlassWorker.frame_print(open_data, cells=cells, end=_end_)

                # Flush writes to the Terminal

                sys.stdout.flush()
                sys.stderr.flush()

                # Wait for Byte, but then fetch the Byte, and start the next Wait for Byte

                after = before

                hit = tb.stdio_select_select(0)
                while not hit:
                    time.sleep(1e-9)  # slightly limits loop rate

                    hit = tb.stdio_select_select(0)
                    after = time.perf_counter_ns()

                waited = after - before
                before = after

                b = tb.read_one_byte_if()  # doesn't measure time to read
                if not b:
                    break

                ifk.keep_one_byte(b)
                cells.append(waited)
                cells.append(b)

                # Print each new Closed Frame, if any

                triples = ifk.pull_frame_triples()
                for triple in triples:  # maybe empty
                    start, end, data = triple

                    length = 2 * len(data)  # two cells per Byte
                    assert len(cells) >= length, (len(cells), length, data)

                    byte_cells = cells[:length]
                    GlassWorker.frame_print(data, cells=byte_cells, end="\r\n")
                    if data == b"\r":
                        print()

                    del cells[:length]

                if ifk.is_quitting_frames():
                    break

    @staticmethod
    def frame_print(data: bytes, cells: list[object], end: str) -> None:
        """Print 'caps data = cell cell ...' as a whole line, or as the start of one"""

        kd = keyboard_decoder()

        def ns(n: int) -> str:  # reps Int's as counting Nanoseconds
            m = tuple("nµm") + ("",) + tuple("kMGTPEZYRQ")  # reps 42*10**9 as '42s'
            rep = decimal_int_chop_to_eng_metric(n, multipliers=m, unit="s")
            return rep

        words: list[str] = list()

        # Choose the words

        caps = kd.bytes_to_key_caps_if(data)  # ⎋, ⎋[, ↑ when typed slowly
        if caps:
            words.append(caps)

        decode = TerminalByteFrame.bytes_decode_if(data)
        if decode:
            if decode.isprintable() and (decode.strip() == decode):
                words.append(decode)
            else:
                words.append(repr(decode))

        words.append(f"{data!r} =")

        piths = [c for (i, c) in enumerate(cells) if (i == 0) or (c != 0)]  # drops adds of '0ns'
        reps = [(ns(p) if isinstance(p, int) else str(p)) for p in piths]
        words.extend(reps)

        # Print the words

        start = "\r" "\033[K"  # tested by:  start = "\n¤"
        text = " ".join(words)
        print(f"{start}{text}{end}", end="")

        # known: "\r" snaps back the Terminal Column X only until the Terminal Row overflows
        # known: inject wide texts to overflow thin terminals

    _ = r"""

        % pylitglass/litpyglass.py --egg=frames

        Press Return three times quickly, to quit

        ⌥E J j́ b'j\xcc\x81' = 3.00s b'j' b'\xcc' b'\x81'
        ⇥ '\t' b'\t' = 1.11s b'\t'
        ⌥P π b'\xcf\x80' = 507ms b'\xcf' b'\x80'
        ⌥E E é b'\xc3\xa9' = 507ms b'\xc3' b'\xa9'
        Q q b'q' = 434ms b'q'
        ⇧Q Q b'Q' = 434ms b'Q'
        ␢ ' ' b' ' = 434ms b' '
        ↑ '\x1b[A' b'\x1b[A' = 706ms b'\x1b' b'[' b'A'
        ⏎ '\r' b'\r' = 434ms b'\r'

        ⏎ '\r' b'\r' = 162ms b'\r'

        ⏎ '\r' b'\r' = 163ms b'\r'

        %

    """


#
# Wrap one Terminal
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalBoss:
    """Wrap one Terminal"""

    stdio: io.TextIOWrapper
    isatty: bool
    fileno: int  # often 2 == sys.__stderr__.fileno()
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__

    def __init__(self) -> None:

        assert sys.__stdin__, (sys.__stdin__,)
        stdio = sys.__stdin__  # todo: stderr, tty
        isatty = stdio.isatty()
        fileno = stdio.fileno()

        self.stdio = stdio
        self.isatty = isatty
        self.fileno = fileno
        self.tcgetattr = list()

    def __enter__(self) -> TerminalBoss:
        r"""Pause line-buffering Input, pause taking \n Output as \r\n, etc"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        if tcgetattr:  # enters at most once, to make truthy
            return self

        # Flush writes to the Terminal

        sys.stdout.flush()
        sys.stderr.flush()

        # Back up Input Mode before, drain Input, & choose Input Mode after

        widened_list_int: list[int | list[bytes | int]] = [20261010]  # arbitrary 20261010

        truthy_attributes = termios.tcgetattr(fileno) if isatty else widened_list_int
        assert truthy_attributes, (truthy_attributes,)
        self.tcgetattr = truthy_attributes  # replaces falsey with truthy

        if isatty:
            tty.setraw(fileno, when=termios.TCSADRAIN)

        # Succeed

        return self

        # also pauses Return Key meaning ⌃J b'\n', switches to ⌃M b'\r'

        # todo: swap tty.setcbreak in for tty.setraw to change what ⌃C means
        # todo: try termios.TCSAFLUSH to discard Input while entering

    def __exit__(self, *exc_info: object) -> None:
        r"""Resume line-buffering Input, resume taking \n Output as \r\n, etc"""

        isatty = self.isatty
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        if not tcgetattr:  # exits at most once, to make falsey
            return

        # Flush writes to the Terminal

        sys.stdout.flush()
        sys.stderr.flush()

        # Drain Input, restore Input Mode, & clear Input Mode backup

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr  # truthy here too
        if isatty:
            termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces truthy with falsey

        # also resumes Return Key meaning ⌃J b'\n', switches from ⌃M b'\r'

        # todo: try termios.TCSAFLUSH to discard Input while exiting

    def stdio_select_select(self, timeout: float | None) -> bool:
        """Block till next Input Byte, else till Timeout, else till forever"""

        fileno = self.fileno

        assert self.tcgetattr, (self.tcgetattr,)

        r, w, x = select.select([fileno], [], [], timeout)

        hit = fileno in r

        return hit

        # a la msvcrt.kbhit

    def read_one_byte_if(self) -> bytes:
        """Read one byte and return it, else return b''"""

        try:
            b = self.read_one_byte()
        except AssertionError:
            raise
        except OSError:
            return b""

        assert len(b) == 1, (b,)
        return b

    def read_one_byte(self) -> bytes:
        """Read one byte and return it, else raise Exception"""

        fileno = self.fileno

        fd = fileno
        length = 1
        b = os.read(fd, length)

        if not b:  # b == b'' only from input stream closed by macOS
            raise OSError(errno.EIO, os.strerror(errno.EIO))  # as Linux does for b''

        assert len(b) == 1, (b,)
        return b


#
# Collect Bytes and track when they arrived
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class ByteKeeper:
    """Collect Bytes, and track when they arrived"""

    ba: bytearray  # the Bytes
    nano_list: list[int]  # when the Bytes arrived

    def __init__(self) -> None:

        self.ba = bytearray()
        self.nano_list = list()

    def append_one_byte(self, b: bytes, nano: int | None = None) -> None:
        """Say 1 more Byte arrived, and when"""

        assert len(b) == 1, (len(b), b)
        _nano_ = time.perf_counter_ns() if (nano is None) else nano

        ba = self.ba
        nano_list = self.nano_list

        ba.extend(b)
        nano_list.append(_nano_)

    def is_quitting_bytes(self) -> bool:
        """Say if the Bytes have said please quit soon"""

        ba = self.ba
        nano_list = self.nano_list

        firsts = range(max(0, len(ba) - 4), len(ba))
        pairs = [(nano_list[i], bytes(ba[i : i + 1])) for i in firsts]

        if is_quitting_shape(pairs):
            if ord(" ") <= ba[-1] <= ord("~"):  # US Ascii Printable, and not \t \n \r etc
                return False

            return True

        return False


def is_quitting_shape(pairs: list[tuple[int, bytes]]) -> bool:
    """Quits when given same Bytes, 3 times in a row, but >= 100ms apart, across < 3s"""

    nano = time.perf_counter_ns()

    nl = [n for (n, _) in pairs]  # when the last Byte of each arrived
    data_list = [data for (_, data) in pairs]

    last3 = data_list[-3:]
    if not last3:
        return False

    if last3 != (3 * last3[-1:]):  # three in a row
        return False

    age = nano - nl[-3]
    early_gaps = (nl[-3] - nl[-4],) if (len(nl) > 3) else ()
    late_gaps = (nl[-2] - nl[-3], nl[-1] - nl[-2])

    if age >= _3_GIGA_NANOS_IS_TOO_SLOW_:  # as a burst, not just now and then
        return False

    if min(early_gaps + late_gaps) < _100_MEGA_NANOS_IS_TOO_FAST_:  # held, or pasted
        return False

    return True


#
# Collect TerminalByteFrame's and track when they arrived
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalFrameKeeper:
    """Collect TerminalByteFrame's and track when they arrived"""

    bk: ByteKeeper  # the Bytes, and when each arrived

    frame: TerminalByteFrame  # the Open Frame
    frames: list[TerminalByteFrame]  # the Closed Frames
    index: int  # how many Closed Frames pulled

    def __init__(self) -> None:

        self.bk = ByteKeeper()

        self.frame = TerminalByteFrame(b"")  # the first open Frame
        self.frames = list()
        self.index = 0

    def keep_one_byte(self, b: bytes) -> None:
        """Say 1 more Byte arrived now, and keep each Frame as it closes"""

        bk = self.bk

        # Stamp the Byte with Now, and grow-close-replace, or just grow the Frame

        assert len(b) == 1, (len(b), b)
        nano = time.perf_counter_ns()

        bk.append_one_byte(b, nano=nano)

        extras = self._frame_take_data_if_(b)
        if not extras:
            return

        _frame_ = self.frame
        assert not _frame_, (_frame_,)  # bounced from Closed Frame means replaced Frame

        # Split the Bytes that bounced, if Bytes bounced

        prefix = extras[:-1]
        last = extras[-1:]
        assert last == b, (last, extras, b)

        if prefix:
            assert TerminalByteFrame.bytes_to_later_decode_if(prefix), (prefix, b, extras)

            # not yet a Char alone, though prefix + last may be one, bounced from a non-empty Frame

        # Place the Bytes that bounced into their own Frame, and replace it only if it closes

        _extras_ = self._frame_take_data_if_(extras)
        assert not _extras_, (_extras_, extras)  # an Empty Frame never bounces

    def _frame_take_data_if_(self, data: bytes) -> bytes:
        """Grow the Frame, replace the Frame if it closes, and do return the bounced Bytes, if any"""

        frame = self.frame
        frames = self.frames

        assert not frame.closed, (frame,)

        # Grow the Open Frame, or grow it & close it, or close it

        extras = frame.take_data_if(data)
        assert (not extras) or frame.closed, (extras, frame)  # bounces extras only when closed

        # Keep & replace the Frame if it closed

        _frame_ = frame
        if frame.closed:
            frames.append(frame)

            _frame_ = TerminalByteFrame(b"")  # empty and open
            self.frame = _frame_

        assert (not extras) or (not _frame_), (extras, _frame_)

        # Always leave an Open Frame, and sometimes an Empty Open Frame

        assert not _frame_.closed, (_frame_,)

        return extras

    def pull_frame_triples(self) -> tuple[tuple[int, int, bytes], ...]:
        """Read and clear the (before, after, bytes) triples of Frames closed since last sampled"""

        bk = self.bk
        frame = self.frame
        frames = self.frames
        index = self.index

        ba = bk.ba
        nano_list = bk.nano_list

        # Pull the Closed Frames not yet pulled

        pulls = frames[index:]
        self.index = len(frames)

        # Measure back from the end of the Bytes, to find where the oldest of them starts

        open_length = len(frame.to_frame_bytes())
        pulls_length = sum(len(_.to_frame_bytes()) for _ in pulls)
        first_index = len(ba) - open_length - pulls_length

        # Say when each started and ended, while walking forward over them

        triples_list: list[tuple[int, int, bytes]] = list()

        start_index = first_index
        for pull in pulls:
            data = pull.to_frame_bytes()
            stop_index = start_index + len(data)

            kept = bytes(ba[start_index:stop_index])
            assert kept == data, (kept, data, start_index, stop_index)

            start = nano_list[start_index]
            end = nano_list[stop_index - 1]

            triple = (start, end, data)
            triples_list.append(triple)

            start_index = stop_index

        assert start_index == (len(ba) - open_length), (start_index, len(ba), open_length)

        triples = tuple(triples_list)
        return triples

    def is_quitting_frames(self) -> bool:
        """Say if the Frames have said please quit soon"""

        bk = self.bk
        frame = self.frame
        frames = self.frames

        ba = bk.ba
        nano_list = bk.nano_list

        # Hand down the last 4 Closed Frames, each with when its last Byte arrived

        stop = len(ba) - len(frame.to_frame_bytes())  # back past the Open Frame

        pairs_list = list()
        for closed in reversed(frames[-4:]):
            data = closed.to_frame_bytes()
            pairs_list.append((nano_list[stop - 1], data))
            stop -= len(data)

        pairs = list(reversed(pairs_list))  # oldest first, as for Bytes

        if is_quitting_shape(pairs):
            if frames[-1].encodes:  # is text frame
                return False

            return True

        return False


#
# Frame Bytes of Input, as an ⎋ Esc Sequence, else simply
#


def _try_terminal_byte_frame_() -> None:
    """Try TerminalByteFrame things"""

    assert DL_Y == "\033[" "{}M"
    assert _CLICK3_ == "\033[M"
    assert _NorthArrow_ == "\033[A"
    assert ST == "\033\134"
    assert _NortheastArrow_ == "\033[↗"

    # Do nothing with grace & elegance

    TerminalByteFrame(b"")

    # Speak well of ↑ and ⎋↑

    f = TerminalByteFrame(b"\033[A")
    assert f.to_frame_bytes() == b"\033[A", (f,)
    assert f.closed, (f,)

    f = TerminalByteFrame(b"\033\033[A")
    assert f.to_frame_bytes() == b"\033\033[A", (f,)
    assert f.closed, (f,)

    # Dance well with the _CLICK3_ clash into DL_Y without Pn

    f = TerminalByteFrame(b"\033[M")
    assert f.to_frame_bytes() == b"\033[M", (f,)
    assert not f.closed, (f,)  # because could be ⎋[⇧M{b}{x}{y}

    f = TerminalByteFrame(b"\033[Mabc")
    assert f.to_frame_bytes() == b"\033[Mabc", (f,)
    assert f.closed, (f,)

    f = TerminalByteFrame(b"\033[Mab\xff")
    assert f.to_frame_bytes() == b"\033[Mab\xff", (f,)
    assert f.closed, (f,)

    # Accept ↖↗↘↙ Intercardinal Arrows, not just ←↑→↓ Cardinal Arrows

    f = TerminalByteFrame("\033[↗".encode())  # not yet standard
    assert f.to_frame_bytes() == "\033[↗".encode(), (f,)
    assert f.closed, (f,)

    # Accept the ⎋\ String Terminator (ST) to close an ⎋] Osc Frame

    f = TerminalByteFrame(b"\033]11;?\033\\")
    assert f.to_frame_bytes() == b"\033]11;?\033\\", (f,)
    assert f.closed, (f,)

    #
    # todo: port in more TerminalByteFrame tests from ._try_key_pack_ of
    #   https://github.com/pelavarre/less-beeps/blob/1009pl/bin/less-beeps.py
    #


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalByteFrame:
    """Frame Bytes of Input, as an ⎋ Esc Sequence, else simply"""

    encodes: bytearray  # b''  # Decodable Printable Text

    head: bytearray  # b''  # N * ESC  # N * ESC + CSI  # N * ESC + SS3  # OSC
    neck: bytearray  # b''  # Csi Params  # Osc Payload
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator  # Esc or Ss3 Char

    stash: bytearray  # b''  # 1..3 Bytes taken while not printable

    closed: bool

    def __init__(self, data: bytes) -> None:

        self.encodes = bytearray()

        self.head = bytearray()
        self.neck = bytearray()
        self.backtail = bytearray()

        self.stash = bytearray()

        self.closed = False

        # Take the Bytes in, else raise ValueError

        for d in data:
            b = bytes([d])

            extras = self.take_one_byte_if(b)
            if extras:
                raise ValueError(extras, b, self)

    def __bool__(self) -> bool:

        truthy = self != TerminalByteFrame(b"")
        return truthy

    def __str__(self) -> str:
        """Speak of the Frame as its Parts, each a Repr of Bytes, plus ' +' while open"""

        encodes = self.encodes

        head = self.head
        neck = self.neck
        backtail = self.backtail

        stash = self.stash

        closed = self.closed

        # Speak of Text as a Repr of Str, with the Repr of Bytes of an unfinished Char after it

        if encodes:
            text = encodes.decode()
            join = repr(text)  # "'abc'"
            if stash:
                join += " " + repr(bytes(stash))  # "'abc' b'\xc0'"

        # Speak of no Head as the Repr of Bytes stashed, else as b''

        elif not head:
            join = repr(bytes(stash))  # "b'\xc0'"  # "b''"

        # Speak of the Head, then the Neck, then the Back & Tail, if any

        else:
            parts = [bytes(head)]

            if neck:
                parts.append(bytes(neck))  # Csi Params  # Osc Payload
            if backtail or stash:
                parts.append(bytes(backtail + stash))  # Csi Back & Tail  # Osc Terminator

            join = " ".join(repr(_) for _ in parts)

        # Mark an Open Frame with ' +', since more Bytes may yet arrive

        if not closed:
            join += " +"

        assert join.isprintable(), (join,)
        return join

        # "b'\x1b[' b'6' b' q'"  # "b'\x1b' b'A'"  # "b'\x1b[M' b'\xc2\x80\xff'"  # "b'\x1b[' +"

    def clear_frame(self) -> None:
        """Start again"""

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        encodes.clear()
        head.clear()
        neck.clear()
        backtail.clear()
        stash.clear()

        self.closed = False

    def tilt_to_close_frame(self) -> None:
        """Transform into a Closed DL_Y without explicit Pn, if it was _CLICK3_ and no Stash"""

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash
        closed = self.closed

        assert _CLICK3_ == "\033[M"
        assert DL_Y == "\033[" "{}M"

        data = self.to_frame_bytes()

        if data == b"\033[M":  # takes the ⎋[⇧M DL_Y that isn't the ⎋[⇧M{b}{x}{y} _CLICK3_
            assert (not encodes) and (not neck) and (not backtail), (head, self, data)
            assert head == b"\033[M", (head, self, data)

            if not stash:
                assert head == b"\033[M", (head,)
                assert not closed, (closed, self)

                del head[len(b"\033[") :]
                backtail.extend(b"M")

                self.close_frame()

                # stops staying open to accepting b x y into ⎋[⇧M{b}{x}{y}

        # todo: can the .tilt_to_close_frame idea be spoken lots more simply?

    def to_frame_bytes(self) -> bytes:
        """List the Bytes taken"""

        encodes = self.encodes

        head = self.head
        neck = self.neck
        backtail = self.backtail

        stash = self.stash

        join = bytes(encodes + head + neck + backtail + stash)

        return join  # no matter if .closed or not

    def close_frame(self) -> None:
        """Close if not closed already"""

        stash = self.stash
        assert not stash, (stash,)

        self.closed = True

    #
    # Pick apart a Esc Csi Sequence into its Marks and Ints
    #

    def to_csi_marks_ints_if(self) -> tuple[bytes, tuple[int, ...]]:
        """Pick out the Nonnegative Int Literals of a Csi Escape Sequence"""

        encodes = self.encodes
        head = self.head
        neck = self.neck
        backtail = self.backtail
        stash = self.stash

        assert CSI == "\033["

        if (head != b"\033[") or encodes or stash or (not backtail):
            return (b"", tuple())

        fm = re.fullmatch(rb"^([^0-9;]*)([0-9;]*)(.*)$", string=neck + backtail)
        assert fm, (fm, neck, backtail)

        marks = fm.group(1) + fm.group(3)
        ints_bytes = fm.group(2)

        ints: tuple[int, ...] = tuple()
        if ints_bytes:
            ints = tuple((int(_) if _ else -1) for _ in ints_bytes.split(b";"))

        return (marks, ints)

        # (b"A", []) for "\033[A"
        # (b"H", [123, -1]) for "\033[123;H"

        # todo9: give examples of corners of .to_csi_marks_ints_if

    #
    # Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit
    #

    def take_data_if(self, data: bytes) -> bytes:
        """Try to take X Bytes in and return 0 <= Y <= X Bytes that don't fit"""

        for index in range(len(data)):
            b = data[index:][:1]
            beyond = data[index:][1:]

            extras = self.take_one_byte_if(b)
            if extras:
                extras_plus = extras + beyond
                return extras_plus

        return b""

    def take_one_byte_if(self, b: bytes) -> bytes:
        """Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit"""

        assert len(b) == 1, (b,)

        extras = self._take_one_byte_if_(b)

        # Promise to bounce this Byte last, if at all, after the 0..3 Bytes of 1 unfinished Char

        assert extras[-1:] in (b"", b), (extras, b)

        prefix = extras[:-1]
        o = (prefix, extras, b)
        assert (not prefix) or TerminalByteFrame.bytes_to_later_decode_if(prefix), o

        return extras

    def _take_one_byte_if_(self, b: bytes) -> bytes:
        """Take 1 Byte in and return 0 Bytes, else return 1..4 Bytes that don't fit, unchecked"""

        encodes = self.encodes
        head = self.head
        stash = self.stash
        closed = self.closed

        assert ESC == "\033"

        assert SS3 == "\033O"
        assert CSI == "\033["
        assert _CLICK3_ == "\033[M"
        assert OSC == "\033]"

        # Bounce while Closed

        if closed:
            return b

        # Hold 1..3 Bytes to decode later, except after ⎋[⇧M where 0x80..0xFF are raw Coords

        data = bytes(stash + b)
        text = TerminalByteFrame.bytes_decode_if(data)

        if not text:
            if head != b"\033[M":
                if TerminalByteFrame.bytes_to_later_decode_if(data):
                    stash.extend(b)
                    return b""

        assert len(text) <= 1, (len(text), text, data)

        stash.clear()

        # Take the Bytes in before the first Head, or without ever a Head

        if not head:
            extras = self._take_before_head_if_(data, text=text)
            return extras

        # Take later Bytes in differently, after starts with each kind of Head

        assert not encodes, (encodes,)

        escapes = len(head) - len(head.lstrip(b"\033"))
        escapes = (escapes - 1) if escapes else 0
        undented_head = head[escapes:]

        if undented_head == b"\033":
            extras = self._take_after_esc_if_(data)
            return extras

        elif undented_head == b"\033O":
            extras = self._take_after_ss3_if_(data)
            return extras

        elif undented_head == b"\033[M":
            extras = self._take_after_csi_m_if_(data)
            return extras

        elif undented_head == b"\033[":
            extras = self._take_after_csi_if_(data, text=text)
            return extras

        elif undented_head == b"\033]":
            extras = self._take_after_osc_if_(data, text=text)
            return extras

        assert False, (head, head[escapes:], escapes, self)

    def _take_before_head_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, before any Head, else return what doesn't fit"""

        encodes = self.encodes
        head = self.head

        # Take 1 Decoded Printable Char, without closing the Frame

        if text:
            if text.isprintable():
                encodes.extend(data)
                return b""

        # End a Text Frame before Unprintable or Undecodable Bytes

        if encodes:
            self.close_frame()
            return data

        # Take 1..4 Unprintable or Undecodable Bytes as Head

        head.extend(data)
        if head != b"\033":
            self.close_frame()

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

    def _take_after_esc_if_(self, data: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋ Esc, else return what doesn't fit"""

        head = self.head
        backtail = self.backtail

        # Take one of the ⎋ Esc Head's, without closing the Frame

        head_plus = head + data
        if head_plus in TerminalByteFrame.Headbook:
            lstrip = head_plus.lstrip(b"\033")
            assert len(lstrip) <= 1, (head_plus,)

            head.extend(data)
            return b""

            # doesn't take ⇧M after \⎋[ here

        # Take ⎋ Esc as an Emacs Meta Byte before 1..4 Bytes

        backtail.extend(data)
        self.close_frame()
        return b""

    def _take_after_ss3_if_(self, data: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋O SS3, else return what doesn't fit"""

        backtail = self.backtail

        backtail.extend(data)
        self.close_frame()
        return b""

    def _take_after_csi_m_if_(self, data: bytes) -> bytes:
        """Take 1 more Byte in, after ⎋[⇧M, and never bounce it"""

        head = self.head
        backtail = self.backtail

        # Take three raw B X Y Bytes after the Head, each 32 + Coord, so 0x20..0xFF, never decoded

        assert len(data) == 1, (data, head, backtail)  # stashes nothing after ⎋[⇧M
        assert len(head + backtail) < 6, (head, backtail, data)  # closes at 6, before now

        backtail.extend(data)
        if len(head + backtail) == 6:
            self.close_frame()

        return b""

        # ⎋[?1005h Utf-8 Mouse Coords never enabled here, so never decoded here

    def _take_after_csi_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋[ CSI, else return what doesn't fit"""

        head = self.head
        neck = self.neck
        backtail = self.backtail

        assert _CLICK3_ == "\033[M"

        # Take the 3-Byte ⎋[⇧M Esc Head, without closing the Frame

        if (not neck) and (not backtail):
            head_plus = head + data
            if head_plus in TerminalByteFrame.Headbook:
                assert head_plus == b"\033[M", (head_plus,)
                head.extend(data)
                return b""

        # Grow the ⎋[ Csi Frame with 1 Decoded Printable Char

        if text and text.isprintable():
            code = ord(text)
            assert code >= 0x20, (code, text, data)

            # Grow the Neck until the Backtail starts

            if 0x30 <= code < 0x40:  # 16 Parameter Codes  # 0123456789:;<=>?

                if not backtail:
                    neck.extend(data)
                    return b""

                # Close before more Params, if Backtail has started

                self.close_frame()
                return data

            # Grow the Backtail

            if 0x20 <= code < 0x30:  # 16 Intermediate Codes  # ␢!"#$%&\'()*+,-./
                backtail.extend(data)
                return b""

            # Close after a Csi Final Code, or after Printable Unicode

            assert code >= 0x40, (code, text, data)  # 63 Final Codes  # @A Z[\\]^_`a z{|}~

            backtail.extend(data)
            self.close_frame()
            return b""

        # Close the ⎋[ Csi Frame before Unprintable or Undecodable Bytes

        self.close_frame()
        return data

    def _take_after_osc_if_(self, data: bytes, text: str) -> bytes:
        """Take 1..4 more Bytes in, after ⎋] OSC, else return what doesn't fit"""

        neck = self.neck
        backtail = self.backtail

        assert BEL == "\007"
        assert ST == "\033\134"

        # Grow the ⎋] Osc Frame with 1 Decoded Printable Char

        if not backtail:
            if text and text.isprintable():
                neck.extend(data)
                return b""

        # Close the ⎋] Osc Frame with BEL or ST

        if text == "\007":
            backtail.extend(data)
            self.close_frame()
            return b""

        if not backtail:
            if text == "\033":
                backtail.extend(data)
                return b""

        if backtail == b"\033":
            if text == "\134":
                backtail.extend(data)
                self.close_frame()
                return b""

            # todo: how should other Bytes past "\033" close an ⎋] Osc Frame?

        # Close the ⎋] Osc Frame before Unprintable or Undecodable Bytes

        self.close_frame()
        return data

    #
    # Work with Decodable and Undecodable Bytes
    #

    @staticmethod
    def bytes_decode_if(data: bytes) -> str:
        """Say if printable"""

        try:
            text = data.decode()
            return text  # returns first found
        except UnicodeDecodeError:
            pass

        return ""

    Endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")

    @staticmethod
    def bytes_to_later_decode_if(data: bytes) -> str:
        """Say if some Bytes start 1 or more UTF-8 Encodings of Chars"""

        endswiths = (b"\xbf", b"\x80\x80", b"\xbf\xbf", b"\x80\x80\x80", b"\xbf\xbf\xbf")
        assert endswiths == TerminalByteFrame.Endswiths

        for endswith in endswiths:
            data_plus = data + endswith

            try:
                text = data_plus.decode()
            except UnicodeDecodeError:
                continue

            assert len(text) >= 1, (text,)
            return text  # returns first found

        return ""

        # todo: compare Endswiths vs Python 3 encodings.utf_8.IncrementalDecoder

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


#
# Speak of a Byte Sequence as a Strike of Key Caps at a macBook
#


def _try_keyboard_decoder_() -> None:
    """Try KeyboardDecoder things"""

    kd = keyboard_decoder()

    # Pair up Bytes with the Key Caps struck to send them, else with an Empty Str

    pairs = (
        #
        (b"", ""),  # nothing struck
        (b"\t", "⇥"),  # a Control Byte
        (b"\r", "⏎"),
        (b"\001", "⌃A"),
        (b"\033", "⎋"),
        (b"\033[A", "↑"),  # a Csi Sequence
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
        ("é".encode(), "⌥E E"),  # 'é' as 1 Char  # NFD would split out a Combining Acute Accent
        ("j́".encode(), "⌥E J"),  # 'j' before Combining Acute Accent, from Dead Key & then J Key
        ("´".encode(), "⌥⇧E"),  # the Spacing Acute Accent, as struck
        ("\u0301".encode(), ""),  # the Combining Acute Accent by itself, which no Key sends
        ("a\u0301\u0308".encode(), ""),  # two Combining Marks on one Char, which no Key sends
        #
        (b"\033OP", "F1"),  # an Ss3 Sequence
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

    # Show Unicode tells Apple that the Dead Key should accent the Char struck after it

    dead_key_echo_by_combining = KeyboardDecoder.DeadKeyEchoByCombining
    for t in dead_key_echo_by_combining.keys():
        assert unicodedata.combining(t), (t,)


@functools.cache
def keyboard_decoder() -> KeyboardDecoder:
    """Build the one KeyboardDecoder, once, and hand it back on each later call"""

    kd = KeyboardDecoder()
    return kd


class KeyboardDecoder:
    """Speak of a Byte Sequence as a Strike of Key Caps at a macBook"""

    decode_by_echo: dict[str, str]
    echoes_by_decode: dict[str, tuple[str, ...]]

    PlainCapsWithoutFn = r"""
        ⎋
        ` 1 2 3 4 5 6 7 8 9 0 - = ⌫
        ⇥ Q W E R T Y U I O P [ ] \
        A S D F G H J K L ; ' ⏎
        Z X C V B N M , . /
        ␢ ← ↑ → ↓
    """  # Plain Caps apart from F1 .. F12 etc

    ShiftCapsWithoutFn = """
        ⎋
        ~ ! @ # $ % ^ & * ( ) _ + ⌫
        ⇥ Q W E R T Y U I O P { } |
        A S D F G H J K L : " ⏎
        Z X C V B N M < > ?
        ␢ ← ↑ → ↓
    """  # Shift Caps apart from ⇧ F1 .. ⇧ F12 etc

    ShortcutShifts: tuple[str, ...]  # ⌃ ⌥ ⇧ ⌃⌥ ⌃⇧ ⌥⇧ ⌃⌥⇧ ⎋ ⎋⌃ ⎋⇧ ⎋⌃⇧
    ShortcutShifts = ("", "⌃", "⌥", "⌃⌥", "⇧", "⌃⇧", "⌥⇧", "⌃⌥⇧", "⎋", "⎋⌃", "⎋⇧", "⎋⌃⇧")

    FamiliarShifts: tuple[str, ...]  # ⇧ ⌃ ⌥ ⌃⇧ ⌥⇧ ⌃⌥ ⌃⌥⇧ ⎋ ⎋⇧ ⎋⌃ ⎋⌃⇧
    FamiliarShifts = ("", "⇧", "⌃", "⌥", "⌃⇧", "⌥⇧", "⌃⌥", "⌃⌥⇧", "⎋", "⎋⇧", "⎋⌃", "⎋⌃⇧")

    assert sorted(ShortcutShifts) == sorted(FamiliarShifts)

    DeadKeyEchoByCombining = {  # Typists say Dead Keys do not step the Cursor forward
        "\u0300": "⌥`",  # Combining Grave Accent
        "\u0301": "⌥E",  # Combining Acute Accent
        "\u0302": "⌥I",  # Combining Circumflex Accent
        "\u0303": "⌥N",  # Combining Tilde
        "\u0308": "⌥U",  # Combining Diaeresis
    }

    def __init__(self) -> None:

        self.decode_by_echo = dict()
        self._form_macos_keyboards_()
        self._form_apple_terminal_keyboards_()

        self.echoes_by_decode = self._form_echoes_by_decode_()

    def _form_macos_keyboards_(self) -> None:
        """Form the ordinary Apple macBook Keyboards of Codes sent by Caps"""

        # 1 ''

        shifts = ""
        strikes = r"""
            033
            140 1 2 3 4 5 6 7 8 9 0 - = 177
            011 q w e r t y u i o p [ ] \
            a s d f g h j k l ; ' 015
            z x c v b n m , . /
            040 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 2 ⇧

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2D and ⎋[1;2C

        strikes = """
            033
            176 ! @ # $ % ^ & * ( ) _ + 177
            ⎋[⇧Z Q W E R T Y U I O P { } |
            A S D F G H J K L : " 015
            Z X C V B N M < > ?
            040 ⎋[1;2⇧D ⎋[⇧A ⎋[1;2⇧C ⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 3 ⌃

        shifts = "⌃"
        strikes = """
            033
            ... ... ... ... ... ... ... ... ... ... ... 037 ... 177
            011 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 006 007 010 012 013 014 ... ... ...
            032 030 003 026 002 016 015 ... ... ...
            000 ... ... ... ...
        """  # the '...' in here mark Key Strikes that send no Bytes: a Bell, the ⌃⏎ Menu, or macOS

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 4 ⌥

        shifts = "⌥"  # ⌥Y sends \, coded here as r""" \ """
        strikes = r"""
            033
            ¤ ¡ ™ £ ¢ ∞ § ¶ • ª º – ≠ 177
            011 œ ∑ ¤ ® † \ ¤ ¤ ø π “ ‘ «
            å ß ∂ ƒ © ˙ ∆ ˚ ¬ … æ 015
            Ω ≈ ç √ ∫ ¤ µ ≤ ≥ ÷
            302.240 ⎋B ⎋⎋[⇧A ⎋F ⎋⎋[⇧B
        """  # the five ¤ splats in here mark Dead Keys that do not step the Cursor forward

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 5 ⌃⇧

        shifts = "⌃⇧"
        strikes = """
            033
            ... ... 000 ... ... ... 036 ... ... ... ... 037 ... 177
            ⎋[⇧Z ... ... ... ... ... ... ... ... ... ... 033 035 034
            ... ... ... ... ... ... ... ... ... ... ... ...
            ... ... ... ... ... ... ... ... ... ...
            000 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """  # the '...' in here mark Key Strikes that send no Bytes: a Bell, or the ⌃⇧⏎ Menu

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 6 ⌥⇧

        shifts = "⌥⇧"  # ⌥⇧K sends the Apple Logo, coded here as \uf8ff
        strikes = """
            033
            140 ⁄ € ‹ › ﬁ ﬂ ‡ ° · ‚ — ± 177
            ⎋[⇧Z Œ „ ´ ‰ ˇ Á ¨ ˆ Ø ∏ ” ’ »
            Å Í Î Ï ˝ Ó Ô \uf8ff Ò Ú Æ 015
            ¸ ˛ Ç ◊ ı ˜ Â ¯ ˘ ¿
            302.240 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """  # can't be = r""", because \u inside.

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 7 ⌃⌥

        shifts = "⌃⌥"
        strikes = """
            033
            140 1 2 3 4 5 6 7 8 9 0 037 = 177
            011 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 006 007 010 012 013 014 ; ' 015
            032 030 003 026 002 016 015 , . /
            000 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """
        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 8 ⌃⌥⇧

        shifts = "⌃⌥⇧"
        strikes = """
            033
            140 1 000 3 4 5 036 7 8 9 0 037 = 177
            ⎋[⇧Z 021 027 005 022 024 031 025 011 017 020 033 035 034
            001 023 004 ... 007 010 012 013 014 ; ' 015
            032 030 003 026 ... 016 015 , . /
            000 ⎋[⇧D ⎋[⇧A ⎋[⇧C ⎋[⇧B
        """  # the '...' in here mark Key Strikes that send no Bytes: a Bell instead
        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 9 ⎋

        shifts = "⎋"

        strikes = r"""
            ⎋⎋
            033.140 ⎋1 ⎋2 ⎋3 ⎋4 ⎋5 ⎋6 ⎋7 ⎋8 ⎋9 ⎋0 ⎋- ⎋= 033.177
            033.011 ⎋Q ⎋W ⎋E ⎋R ⎋T ⎋Y ⎋U ⎋I ⎋O ⎋P ⎋[ ⎋] ⎋\
            ⎋A ⎋S ⎋D ⎋F ⎋G ⎋H ⎋J ⎋K ⎋L ⎋; ⎋' 033.015
            ⎋Z ⎋X ⎋C ⎋V ⎋B ⎋N ⎋M ⎋, ⎋. ⎋/
            033.040 ⎋B ⎋⎋[⇧A ⎋F ⎋⎋[⇧B
        """  # ⎋B ⎋F, not ⎋⎋[⇧D ⎋⎋[⇧C

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 10 ⎋⇧

        shifts = "⎋⇧"
        strikes = """
            033.033
            033.176 ⎋⇧! ⎋⇧@ ⎋⇧# ⎋⇧$ ⎋⇧% ⎋⇧^ ⎋⇧& ⎋⇧* ⎋⇧( ⎋⇧) ⎋⇧_ ⎋⇧+ 033.010
            ⎋⎋[⇧Z ⎋⇧Q ⎋⇧W ⎋⇧E ⎋⇧R ⎋⇧T ⎋⇧Y ⎋⇧U ⎋⇧I ⎋⇧O ⎋⇧P ⎋⇧{ ⎋⇧} ⎋⇧|
            ⎋⇧A ⎋⇧S ⎋⇧D ⎋⇧F ⎋⇧G ⎋⇧H ⎋⇧J ⎋⇧K ⎋⇧L ⎋⇧: ⎋⇧" 033.015
            ⎋⇧Z ⎋⇧X ⎋⇧C ⎋⇧V ⎋⇧B ⎋⇧N ⎋⇧M ⎋⇧< ⎋⇧> ⎋⇧?
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """  # 033.117 ⎋O stops without closing its Frame (like could be ⎋OP)

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 11 ⎋⌃

        shifts = "⎋⌃"

        strikes = """
            033.033
            033.140 ⎋1 ⎋2 ⎋3 ⎋4 ⎋5 ⎋6 ⎋7 ⎋8 ⎋9 ⎋0 033.037 ⎋= 033.010
            033.011 033.021 033.027 033.005 033.022 033.024 033.031 033.025 033.011 033.017 033.020 033.033 033.035 033.034
            033.001 033.023 033.004 033.006 033.007 033.010 033.012 033.013 033.014 ⎋; ⎋' 033.015
            033.032 033.030 033.003 033.026 033.002 033.016 033.015 ⎋, ⎋. ⎋/
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

        # 12 ⎋⌃⇧

        shifts = "⎋⌃⇧"
        strikes = """
            033.033
            033.140 ⎋1 ⎋2 ⎋3 ⎋4 ⎋5 ⎋6 ⎋7 ⎋8 ⎋9 ⎋0 033.037 ⎋= 033.010
            ⎋⎋[⇧Z 033.021 033.027 033.005 033.022 033.024 033.031 033.025 033.011 033.017 033.020 033.033 033.035 033.034
            033.001 033.023 033.004 033.006 033.007 033.010 033.012 033.013 033.014 ⎋; ⎋' 033.015
            033.032 033.030 033.003 033.026 033.002 033.016 033.015 ⎋, ⎋. ⎋/
            033.040 ⎋⎋[⇧D ⎋⎋[⇧A ⎋⎋[⇧C ⎋⎋[⇧B
        """

        self._add_keyboard_(shifts=shifts, strikes=strikes)

    def _add_keyboard_(self, shifts: str, strikes: str) -> None:
        """Add in 1 Keyboard of Key Caps and their Strikes"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)

        strikes_split = strikes.split()
        if not strikes_split:
            return

        plain_caps = tuple(KeyboardDecoder.PlainCapsWithoutFn.split())
        shift_caps = tuple(KeyboardDecoder.ShiftCapsWithoutFn.split())

        o = (len(plain_caps), len(shift_caps), len(strikes_split))
        assert len(plain_caps) == len(shift_caps) == len(strikes_split), o

        caps = shift_caps if ("⇧" in shifts) else plain_caps
        for cap, cap_strikes in zip(caps, strikes_split):
            echo = shifts + cap
            decode = self._cap_strikes_to_decode_(cap_strikes, echo=echo)
            if decode:

                self._keyboard_add_decode_(decode, echo=echo)

    def _cap_strikes_to_decode_(self, cap_strikes: str, echo: str) -> str:
        """Convert to Decode of Byte Encoding of Key Strike"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        if cap_strikes in ("...", "¤"):  # splats of width 3 and width 1
            return ""

        ba = bytearray()

        octets = [cap_strikes]
        if cap_strikes not in (".", "⎋."):
            octets = cap_strikes.split(".")

        for octet in octets:

            # Accept single Characters

            if len(octet) == 1:  # '€'
                t = octet
                assert t not in ("⎋⌃⌥⇧" "`~"), (octet, octets, cap_strikes, echo)
                octet_data = octet.encode()
                ba.extend(octet_data)
                continue

            # Accept single Characters escaped, no matter if shifted or not

            if octet == "⎋⎋":  # ⎋⎋
                octet_data = b"\033\033"
                ba.extend(octet_data)
                continue

            if octet.startswith("⎋") and (len(octet) == 2):  # ⎋Z  # ⎋/
                t = octet[1:]
                if t not in (string.digits + string.ascii_uppercase):
                    assert t in ("-=" "[]\\" ";'" ",./"), (t, octet, cap_strikes, echo)
                octet_data = b"\033" + t.lower().encode()
                ba.extend(octet_data)
                continue

                # rejects ⎋`

            if octet.startswith("⎋⇧") and (len(octet) == 3):  # ⎋⇧Z  # ⎋⇧?
                t = octet[2:]
                if t not in string.ascii_uppercase:
                    assert t in ("!@#$%^&*()_+" "{}|" ':"' "<>?"), (t, octet, cap_strikes, echo)
                octet_data = b"\033" + t.encode()
                ba.extend(octet_data)
                continue

                # rejects ⎋⇧~

            # Accept three Octal Digits as an Octet

            m = re.fullmatch(r"[0-7][0-7][0-7]", string=octet)
            if m:  # 177
                ba.append(int(octet, base=0o010))  # raises ValueError when > 0o377
                continue

            # Accept simple Ss3 Sequences spoken as ⎋O... ⇧...

            m = re.fullmatch(r"(⎋)⇧(O)⇧([PQRS])", string=octet)
            if m:  # ⎋⇧O⇧S
                octet_data = b"\033"
                octet_data += m.group(2).encode() + m.group(3).encode()
                ba.extend(octet_data)
                continue

            # Accept simple Csi Sequences spoken as ⎋[... ⇧..., even when preceded by one extra ⎋

            m = re.fullmatch(r"(⎋|⎋⎋)(\[)([0-9;]*)⇧([ABCDPQRSZ~])", string=octet)
            if m:  # ⎋[⇧Z  # ⎋[1;2⇧C  # ⎋⎋[⇧D  # ⎋[17⇧~
                octet_data = len(m.group(1)) * b"\033"
                octet_data += m.group(2).encode() + m.group(3).encode() + m.group(4).encode()
                ba.extend(octet_data)
                continue

            assert False, (octet, octets, cap_strikes, echo)

        decode = ba.decode()
        assert ba and decode, (ba, decode)

        return decode

    def _keyboard_add_decode_(self, decode: str, echo: str) -> None:
        """Add a Key Cap and its Byte Encoding to a Keyboard"""

        assert decode, (decode, echo)
        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode_by_echo = self.decode_by_echo

        assert echo not in decode_by_echo.keys(), (echo, decode_by_echo[echo])
        decode_by_echo[echo] = decode

    def _form_apple_terminal_keyboards_(self) -> None:
        """Form an Apple macOS Terminal Keyboard, out of Octets"""

        # 1 ''

        self._add_ten_fn_()
        self._keyboard_add_("F12", cap_strikes="⎋[24⇧~")

        # 2 ⇧  # Sideband Bells on ⌃ F1 F2 F3 F4

        shifts = "⇧"  # ⇧← and ⇧→ send ⎋[1;2D and ⎋[1;2C

        caps = "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"  # without "F1 F2 F3 F4" + " " +
        strikes = """
            ⎋[25⇧~ ⎋[26⇧~ ⎋[28⇧~ ⎋[29⇧~
            ⎋[31⇧~ ⎋[32⇧~ ⎋[33⇧~ ⎋[34⇧~
        """  # omitting ⎋[27⇧~

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # 3 ⌃  # Sideband Bells on ⌃ F2 F3 F4 F5 F6, ⌃ F9 F10 F11 F12  # No Codes on ⌃ F7 F8

        pass

        # 4 ⌥

        shifts = "⌥"

        meta_caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        meta_strikes = """
            ⎋[17⇧~ ⎋[18⇧~ ⎋[19⇧~ ⎋[20⇧~
            ⎋[21⇧~ ⎋[23⇧~ ⎋[24⇧~ ⎋[25⇧~
            ⎋[26⇧~ ⎋[28⇧~ ⎋[29⇧~ ⎋[31⇧~
        """  # omitting ⎋[22⇧~ ⎋[27⇧~

        self._keyboard_add_some_(meta_caps, strikes=meta_strikes, shifts=shifts)

        # 5 ⌃⇧  # Sideband Bells on ⌥⇧ F1..F6, ⌥⇧ F8..F12  # No Codes on ⌥⇧ F7
        # 6 ⌥⇧  # Sideband Bells on ⌥⇧ F1..F12
        # 7 ⌃⌥  # Sideband Bells on ⌃⌥ F1..F12
        # 8 ⌃⌥⇧  # Sideband Bells on ⌥⇧ F1..F12

        pass

        # 9 ⎋

        shifts = "⎋"
        self._keyboard_add_some_(meta_caps, strikes=meta_strikes, shifts=shifts)

        # 10 ⎋⇧

        shifts = "⎋⇧"
        self._add_twelve_fn_meta_control_p_(shifts=shifts)  # only via 'Use Option As Meta Key'

        # 11 ⎋⌃

        shifts = "⎋⌃"
        self._add_twelve_fn_meta_control_p_(shifts=shifts)  # only via 'Use Option As Meta Key'

        # 12 ⎋⌃⇧

        shifts = "⎋⌃⇧"
        self._add_twelve_fn_meta_control_p_(shifts=shifts)  # only via 'Use Option As Meta Key'

        # Terminal ⇧Fn = ⎋[ 25 26 28 29 ⇧~, ⎋[ 31 32 33 34 ⇧~,
        # no encodes of ⇧F1 ⇧F2 ⇧F3 ⇧F4 in Apple Terminal without distributing configuration

    def _add_ten_fn_(self) -> None:
        """Add the first Ten F Keys, held in common across all our Unshifted Keyboards"""

        shifts = ""

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10"  # without " F11 F12"
        strikes = """
            ⎋⇧O⇧P ⎋⇧O⇧Q ⎋⇧O⇧R ⎋⇧O⇧S
            ⎋[15⇧~ ⎋[17⇧~ ⎋[18⇧~ ⎋[19⇧~
            ⎋[20⇧~ ⎋[21⇧~
        """  # omitting ⎋[16~  # not-colliding with ⎋[ ⇧R

        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

        # ⎋OP ⎋OQ ⎋OR ⎋OS  # ⎋[15~ ⎋[17~ ⎋[18~ ⎋[19~  # ⎋[20~ ⎋[21

    def _keyboard_add_some_(self, caps: str, strikes: str, shifts: str) -> None:
        """Add some Key Caps at Strikes to a Keyboard"""

        caps_split = caps.split()
        strikes_split = strikes.split()
        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)

        assert len(caps_split) == len(strikes_split), (len(caps_split), len(strikes_split))
        for cap, cap_strikes in zip(caps_split, strikes_split):
            echo = shifts + cap
            self._keyboard_add_(echo, cap_strikes=cap_strikes)

    def _keyboard_add_(self, echo: str, cap_strikes: str) -> None:
        """Add a Key Cap and its Octets to a Keyboard"""

        assert len(echo.split()) == 1, (len(echo.split()), echo)

        decode = self._cap_strikes_to_decode_(cap_strikes, echo=echo)
        self._keyboard_add_decode_(decode, echo=echo)

    def _add_twelve_fn_meta_control_p_(self, shifts: str) -> None:
        """Add the Twelve F Keys at the one Decode"""

        assert shifts in KeyboardDecoder.ShortcutShifts, (shifts,)

        caps = "F1 F2 F3 F4" + " " + "F5 F6 F7 F8" + " " + "F9 F10 F11 F12"
        strikes = 12 * " 033.020"  # ⎋⌃P
        self._keyboard_add_some_(caps, strikes=strikes, shifts=shifts)

    def _form_echoes_by_decode_(self) -> dict[str, tuple[str, ...]]:
        """Sort and invert our Decode_by_Echo Dict"""

        decode_by_echo = self.decode_by_echo

        familiar_shifts = KeyboardDecoder.FamiliarShifts

        def echo_to_echo_key(echo: str) -> tuple[str, ...]:
            """Sort Key Caps from least to most celebrated"""

            assert len(echo.split()) == 1, (len(echo.split()), echo)

            lstrip = echo.lstrip("⎋⌃⌥⇧")
            cap = lstrip if lstrip else echo[-1:]

            shifts = echo[: -len(cap)]
            chr_index = chr(familiar_shifts.index(shifts))

            chr_wide_cap = chr(len(cap) > 1)
            chr_len_cap = chr(len(cap))

            echo_key = (chr_wide_cap, chr_index, chr_len_cap, cap)
            return echo_key

            # ⎋⌃P ⎋⌃⇧P before ⎋⇧F2 before ⎋⇧F12, for example

        vxk = decode_by_echo

        kkxv = collections.defaultdict(list)
        for k, v in vxk.items():
            assert k and v, (k, v)
            kkxv[v].append(k)

        assert "" not in vxk.keys()

        d = dict()
        for v, kk in kkxv.items():
            assert kk, (v, kk)
            d[v] = tuple(sorted(kk, key=echo_to_echo_key))

        assert "" not in d.keys()

        return d

    #
    # Speak of a Byte Encoding as a Sequence of Chords of Key Caps
    #

    def bytes_to_key_caps_if(self, data: bytes) -> str:
        """Name the Key Caps struck to send these Bytes, else an Empty Str when unsure"""

        dead_key_echo_by_combining = KeyboardDecoder.DeadKeyEchoByCombining

        # Give up on Undecodable Bytes

        text = TerminalByteFrame.bytes_decode_if(data)
        if not text:
            return ""

        # Name the one Chord of Key Caps that sends the whole Text, when there is one

        echoes = self.bytes_to_echoes_if(data)
        if echoes:
            echo = echoes[0]
            return echo  # ⇥  # ⏎  # ↑  # ⌃A  # ⌥⇧E

        # Else name one Chord per Char, with each ⌥ Dead Key struck before the Char it accents

        nfd = unicodedata.normalize("NFD", text)  # splits é into e plus Combining Acute Accent

        words: list[str] = list()
        dead_key_echo = ""
        for t in nfd:

            if t in dead_key_echo_by_combining.keys():
                if (not words) or dead_key_echo:
                    return ""  # a Combining Mark pasted alone or doubled, which no Key sends

                dead_key_echo = dead_key_echo_by_combining[t]
                words.insert(len(words) - 1, dead_key_echo)  # before the Char, as struck
                continue

            dead_key_echo = ""

            t_echoes = self.bytes_to_echoes_if(t.encode())
            if not t_echoes:
                return ""  # such as a Char that no macBook Keyboard sends

            t_echo = t_echoes[0]
            words.append(t_echo)

        caps = " ".join(words)
        return caps  # ⌥E J  # ⌥E E  # ⇧A ⇧B ⇧C

    def bytes_to_echoes_if(self, data: bytes) -> tuple[str, ...]:
        """Speak of a Byte Encoding as Sequences of Chords of Key Caps"""

        text = data.decode()

        echoes_by_decode = self.echoes_by_decode

        if text in echoes_by_decode.keys():
            echoes = echoes_by_decode[text]
            return echoes

            # tuple of '⎋', of '␢', of '⌥⇧⇥', of '⌃⌥⇧Fn'

        return tuple()


#
# Name the more basic Terminal Encodings
#


BEL = "\007"  # 00/07 Bell

ESC = "\033"  # 01/11 Escape ⎋

SS3 = "\033O"  # 01/11 04/15 Single Shift Three  # ⎋O
CSI = "\033["  # 01/11 05/11 Control Sequence Introducer  # ⎋[
OSC = "\033]"  # 01/11 05/13 Operating System Command  # ⎋]

ST = "\033\134"  # 01/11 05/12 String Terminator  # ⎋\


X1 = 1  # min X of Terminal Cursor
Y1 = 1  # min Y of Terminal Cursor


PS0 = 0  # default Csi Ps = 0 for some

PN1 = 1  # default Csi Pn = 1 for others
_MAX_PN_32100_ = 32100  # max Csi Pn = 32100 exceeds the .x_wide .y_high of most Terminal Screens


ICH_X = "\033[" "{}" "@"  # Csi 04/00 [Insert] Cursor Horizontal [Pn] [Columns]
CUU_Y = "\033[" "{}" "A"  # Csi 04/01 Cursor Up [Pn] [Rows]
CUF_X = "\033[" "{}" "C"  # Csi 04/03 Cursor Forward [Pn] [Columns]
CUB_X = "\033[" "{}" "D"  # Csi 04/04 Cursor Backward [Pn] [Columns]
CUP_Y_X = "\033[" "{};{}H"  # Csi 04/08 [Choose] Cursor Position [Y and X]
ED_PS = "\033[" "{}" "J"  # CSI 04/10 Erase in Display  # 0 Tail # 1 Head # 2 Rows # 3 Scrollback
EL_PS = "\033[" "{}" "K"  # CSI 04/11 Erase in Line [Row]  # 0 Tail # 1 Head # 2 Row
IL_Y = "\033[" "{}" "L"  # Csi 04/12 Insert Line [Row]
_CLICK3_ = "\033[M"  # ⎋[⇧M{b}{x}{y} Click Press/ Release
DL_Y = "\033[" "{}M"  # Csi 04/13 Delete Line [Row]

DCH_X = "\033[" "{}" "P"  # Csi 05/00 [Delete] Cursor Horizontal [Pn] [Columns]
SU_Y = "\033[" "{}S"  # CSI 05/03 Scroll Up [Into Scrollback]

VPA_Y = "\033[" "{}" "d"  # Csi 06/04 Vertical Position Absolute [Row]

DECIC_X = "\033[" "{}" "'}}"  # Csi 07/13 [DEC] Insert Column [Pn]
DECDC_X = "\033[" "{}" "'~"  # Csi 07/14 [DEC] Delete Column [Pn]


SM_PS = "\033[" "{}" "h"  # CSI 06/08 4 Set Mode
RM_PS = "\033[" "{}" "l"  # CSI 06/12 4 Reset Mode
SGR_PS = "\033[" "{}" "m"  # CSI 06/13 Select Graphic Rendition [Text Style]
DSR_PS = "\033[" "{}n"  # Csi 06/14 [Request] Device Status Report [Ps]
DECSCUSR_PS = "\033[" "{}" " q"  # CSI 06/15 [DEC] Set Cursor Style [Ps]  # Two Byte Backtail

DSR0 = "\033[" "0n"  # DSR_PS Ps 0
DSR5 = "\033[" "5n"  # DSR_PS Ps 5 for DSR0
DSR6 = "\033[" "6n"  # DSR_PS Ps 6 for CPR_Y_X

CPR_Y_X = "\033[" "{};{}R"  # ⎋[y;x⇧R


ClassicArrows = ("\033[A", "\033[B", "\033[C", "\033[D")

_NorthArrow_ = "\033[A"  # ←↑→↓ reordered as ↑↓→←
_SouthArrow_ = "\033[B"
_EastArrow_ = "\033[C"
_WestArrow_ = "\033[D"

_NorthwestArrow_ = "\033[↖"  # ⎋[ ↖↗↘↙  # not yet standard
_NortheastArrow_ = "\033[↗"
_SoutheastArrow_ = "\033[↘"
_SouthwestArrow_ = "\033[↙"

_ = _MAX_PN_32100_
_ = _SouthArrow_, _EastArrow_, _WestArrow_
_ = _NorthwestArrow_, _SoutheastArrow_, _SouthwestArrow_


AppleLogo = "\uf8ff"  # Apple Logo occupies U+F8FF = end of U+E000 .. U+F8FF Private Use Area (PUA)
_ = AppleLogo
# todo: every mention of  in Source makes Code Patches difficult to send across platforms


#
# Amp up Import Decimal
#


_ = "qryzafpnµm"  # also 'u' for 'µ'
_ = "kMGTPEZYRQ"


def decimal_int_chop_to_eng_metric(n: int, multipliers: typing.Sequence[str], unit: str) -> str:
    """Convert 9876 to '9.87ns' and so on"""

    clip = decimal_int_chop_to_eng(n)
    digits, e, ms = clip.partition("e")

    if not e:
        assert not ms, (ms, digits, e, clip)

        m = multipliers[0]
        rep = digits + m + unit
        return rep

    exp = int(ms)
    assert (exp % 3) == 0, (exp, digits, e, ms, clip, n)

    i = exp // 3
    assert i >= 1, (i, exp, digits, e, ms, clip, n)

    m = multipliers[i]  # (m) may be Empty Str
    rep = digits + m + unit  # (m + unit) may be Empty Str
    return rep


def decimal_int_chop_to_eng(n: int) -> str:
    """Rep the exact Int, else chop down to 3 Digits at an explicit Multiple-of-Three Exponent"""

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)  # the towards-zero kind of "Down"
    D = ctx.create_decimal  # truncating is not ceiling, floor, half down/up, half even, nor 0 5 up

    clip = D(i).to_eng_string().lower().replace("e+", "e")

    if -(2**53) < i < 2**53:
        aif = abs(int(float(clip)))
        assert aif <= abs(i), (aif, abs(i), i, n)

    return clip  # int(float(clip)) == n, or near to n but a little closer to zero

    # raises ValueError above n = 10**4300 - 1

    # '-9.99e3'  # '-2'  # '0'  # '1'  # '987'  # '1.00e3'  # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of float, int, int, int, int, float, float, float, float
    # with the unsigned 'e' standing in place of the int digits we did chop off

    # Python's hex int("987e3", 0x10) == 0x9_87E3 does nearly collide with our '987e3' lacking '.'
    # Python Floats overflow out beyond '179e306', but we correctly clip '180 * 10**306' and above

    # 'def decimal_int_chop_to_eng' last modified for py2def.py on 2026-08-25 or later


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/pylitglass/litpyglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
