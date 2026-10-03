#!/usr/bin/env python3

r"""
usage: litpyglass.py

loop back to write Screen after reading from Touch/ Mouse/ Key

quirks:
  quits when given any byte three times in a row, inside of just three seconds

examples:
  pylitglass/litpyglass.py --  # run for real
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import dataclasses
import io
import os
import sys
import termios
import time
import tty

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


#
# Configure
#


_3_SECONDS_IS_FOREVER_ = 3


#
# Run from the Shell Command Line
#


def main() -> None:

    print()
    print("Press Return three times quickly, to quit")

    ilog = ByteLog()

    with TerminalBoss(ilog=ilog) as tb:
        while True:
            tb.read_bytes()
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
        stdio = sys.__stderr__
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
        assert len(read) <= 1, (read,)

        ilog.bytes_extend(read)

        for b in read:
            print(b, end="\r\n")


#
# Collect Bytes and track when they arrived
#


@dataclasses.dataclass(order=True)  # , frozen=True)
class ByteLog:
    """Collect Bytes and track when they arrived"""

    items: bytearray
    times: list[float]
    # index: int

    def __init__(self) -> None:

        self.items = bytearray()
        self.times = list()
        # self.index = 0

    def bytes_extend(self, data: bytes) -> None:
        """Say >= 0 more Bytes arrived now"""

        items = self.items
        times = self.times

        t = time.time()
        items.extend(data)
        times.extend(len(data) * [t])

    def is_quitting(self) -> bool:
        """Say if the Bytes have said please quit soon"""

        items = self.items
        times = self.times

        if items:
            if items[-3:] == (3 * items[-1:]):  # three strikes
                age = time.time() - times[-3]

                if age < _3_SECONDS_IS_FOREVER_:  # three seconds
                    return True

        return False


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()
