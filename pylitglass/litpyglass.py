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
  pylitglass/litpyglass.py --egg=frames  # print your inputs split into frames
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import dataclasses
import decimal
import errno
import io
import os
import re
import select
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
        """Print your input byte frames (and how quickly they arrived)"""

        # Launch

        print("Press Return three times quickly, to quit")
        print()

        with TerminalBoss() as tb:
            ifk = TerminalFrameKeeper()

            before = time.perf_counter_ns()  # doesn't measure time to launch
            cells: list[object] = list()

            while True:

                # Prompt after each Byte

                open_data = ifk.frame.to_frame_bytes()  # maybe empty
                GlassWorker.frame_print(open_data, cells=cells, end=" ")

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
        """Print 'data = cell cell ...' as a whole line, or as the start of one"""

        start = "\r" "\033[K"  # tested by:  start = "\n¤"

        def ns(n: int) -> str:  # reps Int's as counting Nanoseconds
            m = tuple("nµm") + ("",) + tuple("kMGTPEZYRQ")  # reps 42*10**9 as '42s'
            rep = decimal_int_chop_to_eng_metric(n, multipliers=m, unit="s")
            return rep

        piths = [c for (i, c) in enumerate(cells) if (i == 0) or (c != 0)]  # drops adds of '0ns'
        reps = [(ns(p) if isinstance(p, int) else str(p)) for p in piths]

        text = " ".join([f"{data!r} ="] + reps)
        print(f"{start}{text}{end}", end="")

        # known: "\r" snaps back the Terminal Column X only until the Terminal Row overflows
        # known: inject wide texts to overflow thin terminals

    _ = r"""

        % pylitglass/litpyglass.py --egg=frames

        Press Return three times quickly, to quit

        b'\x1b[A' = 1.46s b'\x1b' 369ms b'[' 346ms b'A'
        b'\x1b[A' = 3.20s b'\x1b' b'[' b'A'
        b'\r' = 3.32s b'\r'

        b'\x1c' = 3.78s b'\x1c'
        b'\x1c' = 175ms b'\x1c'
        b'\x1c' = 171ms b'\x1c'

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
    backtail: bytearray  # b''  # Csi Intermediates and Final  # Osc Terminator

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

    # def __str__(self) -> str:  # todo9: add for Class TerminalByteFrame

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

        # Take one of the ⎋ Esc Head's, without closing the Frame

        head_plus = head + data
        if head_plus in TerminalByteFrame.Headbook:
            lstrip = head_plus.lstrip(b"\033")
            assert len(lstrip) <= 1, (head_plus,)

            head.extend(data)
            return b""

            # doesn't take ⇧M after \⎋[ here

        # Take ⎋ Esc as an Emacs Meta Byte before 1..4 Bytes

        head.extend(data)
        self.close_frame()
        return b""

    def _take_after_ss3_if_(self, data: bytes) -> bytes:
        """Take 1..4 more Bytes in, after ⎋O SS3, else return what doesn't fit"""

        head = self.head

        head.extend(data)
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
