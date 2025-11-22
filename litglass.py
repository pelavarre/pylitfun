#!/usr/bin/env python3

r"""
usage: litglass.py [-h] [--egg EGG]

loop back Input to Output, to Screen from Touch/ Mouse/ Key

options:
  -h, --help  show this help message and exit
  --egg EGG   a hint of how to behave, such as 'repr' or 'sigint'

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
    parser.add_argument("--egg", dest="eggs", metavar="EGG", action="append", help=egg_help)

    return parser


def shell_args_take_in(args: list[str], parser: ArgDocParser) -> argparse.Namespace:
    """Take in the Shell Command-Line Args"""

    ns = parser.parse_args_if(args)  # often prints help & exits zero

    ns_keys = list(vars(ns).keys())
    assert ns_keys == ["eggs"], (ns_keys, ns, args)

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

    return ns


#
# Loop back Input to Output, to Screen from Touch/ Mouse/ Key
#


class Loopbacker:
    """Loop back Input to Output, to Screen from Touch/ Mouse/ Key"""

    def run_loopbacker_awhile(self) -> None:

        assert ord("C") ^ 0x40 == ord("\003")

        with TerminalBoss() as tb:
            kr = tb.keyboard_reader
            sw = tb.screen_writer

            sw.print_text("Press ⌃C")

            while True:

                tb.kbhit(timeout=None)
                reads = kr.read_kbhit_bytes()

                text = reads.decode()
                if flags._repr_:
                    sw.print_text(repr(text))
                else:
                    sw.write_text(text)

                if text == "\003":
                    break


class TerminalBoss:

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

    def __exit__(self, exc_type: type, exc_value: Exception, traceback: types.TracebackType) -> None:

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

        fileno = self.fileno
        fd = fileno
        os.write(fd, data)

    def read_one_byte(self) -> bytes:

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

    terminal_boss: TerminalBoss

    def __init__(self, terminal_boss: TerminalBoss) -> None:
        self.terminal_boss = terminal_boss

    def print_text(self, text: str, end="\r\n") -> None:

        self.write_text(text + end)

    def write_text(self, text: str) -> None:

        tb = self.terminal_boss
        data = text.encode()  # may raise UnicodeEncodeError
        tb.write_some_bytes(data)


class KeyboardReader:

    terminal_boss: TerminalBoss

    def __init__(self, terminal_boss: TerminalBoss) -> None:
        self.terminal_boss = terminal_boss

    def read_kbhit_bytes(self) -> bytes:
        """Read the zero or more available Bytes"""

        tb = self.terminal_boss

        ba = bytearray()
        while tb.kbhit(timeout=0e0):
            read = tb.read_one_byte()
            ba.extend(read)

        reads = bytes(ba)
        return reads  # maybe empty

        #  ⎋[200⇧~ .. ⎋[201⇧~ arrive together from ⎋[ ⇧?2004H Bracketed Paste

        #
        # at macOS Terminal
        #
        #   mashing the ← ↑ → ↓ Arrow Keys sends 1..3
        #   ⌥-Click sends >= 1 bursts of Arrow Keys
        #   ⌥` sends b"``" sometimes together, sometimes separately
        #

        #
        # at macOS iTerm2
        #
        #   mashing the ← ↑ → ↓ Arrow Keys sends 1..2
        #   ⌥-Click sends 1 burst of Arrow Keys
        #   ⌥` sends b"``" always together
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
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# todo1:


# 3456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litglass.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
