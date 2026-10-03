#!/usr/bin/env python3

r"""
usage: litpyglass.py [--egg=EGG ...]

loop back to write Screen after reading from Touch/ Mouse/ Key

quirks:
  quits when given an unprintable byte three times in a row, inside of just three seconds

examples:
  python3 pylitglass/litpyglass.py  # show these examples
  chmod +x pylitglass/litpyglass.py
  pylitglass/litpyglass.py --  # pick a demo and run it
  pylitglass/litpyglass.py --egg=bytes  # print your input bytes, on screen
  pylitglass/litpyglass.py --egg=nanos  # print your input bytes and when they arrived
"""

# pylitglass/litpyglass.py --egg=frames  # print your inputs split into frames

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import dataclasses
import errno
import io
import os
import sys
import termios
import textwrap
import time
import tty

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


#
# Configure
#


_3_GIGA_NANOS_IS_FOREVER_ = 3 * 10**9

LAUNCH_NANO = time.perf_counter_ns()


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

    eggs = list(_ for _ in shargv if _ != "--")
    eggs = list(_.removeprefix("--egg=") for _ in eggs)
    if not eggs:
        eggs.append("bytes")

    if "bytes" in eggs:
        show_bytes()
    elif "nanos" in eggs:
        show_nanos()
    # elif "frames" in eggs:
    #     show_frames()
    else:
        assert False, (eggs,)

    # Succeed

    print()


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


def show_bytes() -> None:
    """Print your input bytes, on screen"""

    ilog = ByteLog()

    with TerminalBoss(ilog=ilog) as tb:

        print("Press Return three times quickly, to quit", end="\r\n")
        print(end="\r\n")

        while True:
            tb.read_bytes()

            pull = ilog.pull_bytes()
            for xx in pull:
                print(xx, repr(bytes([xx])), end="\r\n")

            if ilog.is_quitting():
                break


def show_nanos() -> None:
    """Print your input bytes and when they arrived"""

    ilog = ByteLog()

    nano = LAUNCH_NANO
    with TerminalBoss(ilog=ilog) as tb:

        print("Press Return three times quickly, to quit", end="\r\n")
        print(end="\r\n")

        while True:
            tb.read_bytes()

            pairs = ilog.pull_nano_byte_pairs()
            for pair in pairs:
                n, b = pair

                delta_n = n - nano
                xx = ord(b)

                print(f"{delta_n:_}", xx, repr(b), end="\r\n")

                nano = n

            if ilog.is_quitting():
                break


#
# Wrap one Terminal
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class TerminalBoss:
    """Wrap one Terminal"""

    stdio: io.TextIOWrapper
    fileno: int  # often 2 == sys.__stderr__.fileno()
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__
    ilog: ByteLog

    def __init__(self, ilog: ByteLog) -> None:

        assert sys.__stderr__, (sys.__stderr__,)
        stdio = sys.__stderr__  # todo: stdin, tty
        fileno = stdio.fileno()

        self.stdio = stdio
        self.fileno = fileno
        self.tcgetattr = list()
        self.ilog = ilog

    def __enter__(self) -> TerminalBoss:
        r"""Pause line-buffering Input, pause taking \n Output as \r\n, etc"""

        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Enter at most once, because entering makes .tcgetattr go truthy

        if tcgetattr:
            return self

        # Flush output()

        sys.stdout.flush()

        # Back up Input Mode before, drain Input, & choose Input Mode after

        tcgetattr = termios.tcgetattr(fileno)
        assert tcgetattr, (tcgetattr,)
        self.tcgetattr = tcgetattr  # replaces

        tty.setraw(fileno, when=termios.TCSADRAIN)

        # Succeed

        return self

        # also pauses Return Key meaning ⌃J b'\n', switches to ⌃M b'\r'

        # todo: swap tty.setcbreak in for tty.setraw to change what ⌃C means
        # todo: try termios.TCSAFLUSH to discard Input while entering

    def __exit__(self, *exc_info: object) -> None:
        r"""Resume line-buffering Input, resume taking \n Output as \r\n, etc"""

        fileno = self.fileno
        tcgetattr = self.tcgetattr

        # Exit at most once, because exiting makes .tcgetattr go falsey

        if not tcgetattr:
            return

        # Flush output()

        sys.stdout.flush()

        # Drain Input, restore Input Mode, & clear Input Mode backup

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

        # also resumes Return Key meaning ⌃J b'\n', switches from ⌃M b'\r'

        # todo: try termios.TCSAFLUSH to discard Input while exiting

    def read_bytes(self) -> None:
        """Do read the bytes, but don't frame them and don't return them"""

        fileno = self.fileno
        ilog = self.ilog

        fd = fileno
        length = 1
        read = os.read(fd, length)

        if not read:  # read == b'' only from input stream closed by macOS
            raise OSError(errno.EIO, os.strerror(errno.EIO))  # as Linux does for b''

        assert len(read) == 1, (read,)
        ilog.bytes_extend(read)


#
# Collect Bytes and track when they arrived
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class ByteLog:
    """Collect Bytes and track when they arrived"""

    data: bytearray  # the Bytes
    nanos: list[int]  # when they arrived
    index: int  # count of how many bytes we've pulled, with or without their nanos

    def __init__(self) -> None:

        self.data = bytearray()
        self.nanos = list()
        self.index = 0

    def bytes_extend(self, extend: bytes) -> None:
        """Say >= 0 more Bytes arrived now"""

        data = self.data
        nanos = self.nanos

        ns = time.perf_counter_ns()
        data.extend(extend)
        nanos.extend(len(extend) * [ns])

    def pull_bytes(self) -> bytes:
        """Read and clear the bytes queued since last sampled"""

        data = self.data
        index = self.index

        pull = bytes(data[index:])
        self.index = len(data)

        return pull

    def pull_nano_byte_pairs(self) -> tuple[tuple[int, bytes], ...]:
        """Read and clear the (nano, bytes) pairs queued since last sampled"""

        data = self.data
        nanos = self.nanos
        index = self.index

        pairs_list: list[tuple[int, bytes]] = list()
        for i in range(index, len(data)):
            n = nanos[i]
            b = bytes(data[i:][:1])
            pair = (n, b)
            pairs_list.append(pair)

        self.index = len(data)

        pairs = tuple(pairs_list)
        return pairs

    def is_quitting(self) -> bool:
        """Say if the Bytes have said please quit soon"""

        data = self.data
        nanos = self.nanos

        nano = time.perf_counter_ns()

        if data:
            if data[-3:] == (3 * data[-1:]):  # three strikes
                age = nano - nanos[-3]

                if age < _3_GIGA_NANOS_IS_FOREVER_:  # three seconds

                    if ord(" ") <= data[-1] <= ord("~"):
                        return False

                    return True

        return False


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()
