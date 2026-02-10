#!/usr/bin/env python3

r"""
usage: litpython.py [-h] [PYLINE ...]

exec some lines of python code, without making you type out the 'import's

positional arguments:
  PYLINE      a line of python code to execute

options:
  -h, --help  show this help message and exit

quirks:
  trusts Git to tell it when new Names becomes Importable

examples:
  p 'print("".join(chr(_) for _ in range(0x20, 0x7E + 1)))'
  p
    dt.datetime.now().astimezone()  # no import required
"""

# todo: ./litpython.py  # implies -i -c ''
# todo: ./litpython.py 'sys.otext = "".join(chr(_) for _ in range(0x20, 0x7E + 1))'  # pipes pb for you
# todo: pbpaste

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections.abc
import dataclasses
import datetime as dt
import decimal
import difflib
import importlib
import logging
import os
import pdb
import signal
import sys
import textwrap
import traceback
import types
import zoneinfo

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


logger = logging.getLogger(__name__)

Pacific = zoneinfo.ZoneInfo("America/Los_Angeles")
PacificLaunch = dt.datetime.now(Pacific)
UTC = zoneinfo.ZoneInfo("UTC")  # todo: extend welcome into the periphery beyond San Francisco


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    try:
        try_main()
    except BaseException:  # KeyboardInterrupt  # SystemExit
        excepthook(*sys.exc_info())


def try_main() -> None:
    """Run from the Shell Command Line"""

    doc = __main__.__doc__
    assert doc, (doc,)

    parser = arg_doc_to_parser(doc)
    ns = parser.parse_args_if(sys.argv[1:])

    pylines = ns.pylines
    pyjoin = "\n".join(pylines)
    pytext = textwrap.dedent(pyjoin).strip()

    globals_add_do_python_names()

    # Run the given Python Code
    # Else chat after Return from Def Main

    if pytext:
        exec(pytext)
    else:
        os.environ["PYTHONINSPECT"] = str(True)


def arg_doc_to_parser(doc: str) -> "ArgDocParser":
    """Declare the Options & Positional Arguments"""

    assert argparse.REMAINDER == "..."
    assert argparse.ZERO_OR_MORE == "*"

    parser = ArgDocParser(doc, add_help=True)

    pyline_help = "a line of python code to execute"
    parser.add_argument("pylines", metavar="PYLINE", nargs="*", help=pyline_help)

    return parser


#
# Launch a chat with Python
#


def globals_add_do_python_names() -> None:

    g = globals()
    for name in PYTHON_IMPORTS:
        if name not in g.keys():
            g[name] = LazyImport(name)

    if "D" not in g.keys():
        g["D"] = decimal.Decimal  # todo: lazily do:  from decimal import Decimal as D

    if "dt" not in g.keys():
        dt = LazyImport(import_="datetime", as_="dt")
        g["dt"] = dt

    if "et" not in g.keys():
        et = LazyImport(import_="xml.etree.ElementTree", as_="et")
        g["et"] = et

    if "np" not in g.keys():
        np = LazyImport(import_="numpy", as_="np")
        g["np"] = np

    if "logger" not in g.keys():
        g["logger"] = logger

    if "p" not in g.keys():
        p = print
        g["p"] = p

    if "parser" not in g.keys():
        parser = argparse.ArgumentParser()
        g["parser"] = parser

    if "pd" not in g.keys():
        pd = LazyImport(import_="pandas", as_="pd")
        g["pd"] = pd

    if "plt" not in g.keys():
        plt = LazyImport(import_="matplotlib.pyplot", as_="plt")
        g["plt"] = plt

    if "t" not in g.keys():
        g["t"] = PacificLaunch


class LazyImport:
    """Defer the work of "import X as Y" till first Y.Z fetched"""

    def __init__(self, import_: str, as_: str | None = None) -> None:
        self.import_ = import_
        self.as_ = import_ if (as_ is None) else as_

    def __getattribute__(self, name: str) -> object:
        if name in "as_ import_".split():
            return super().__getattribute__(name)
        module = importlib.import_module(self.import_)
        globals()[self.as_] = module
        return module.__getattribute__(name)

    def __repr__(self) -> str:
        module = importlib.import_module(self.import_)
        globals()[self.as_] = module
        return module.__repr__()


_PYTHON_IMPORTS_TEXT_ = """


    # hard-to-discover basics
    # sorted(_[0] for _  in sys.modules.items() if not hasattr(_[-1], "__file__"))

    __main__

    atexit builtins errno itertools marshal posix pwd sys time


    # from ".so" Shared Object Libraries
    # minus deprecated: audioop nis pyexpat

    array binascii cmath fcntl grp
    math mmap readline resource select syslog termios unicodedata zlib


    # from Py Files
    # minus deprecated: aifc cgi cgitb chunk crypt imghdr
    # minus deprecated: mailcap nntplib pipes sndhdr sunau telnetlib uu uuid xdrlib

    abc antigravity argparse ast asynchat asyncore  base64 bdb bisect bz2
    cProfile calendar cmd code codecs codeop colorsys
        compileall configparser contextlib contextvars copy copyreg csv
    dataclasses datetime decimal difflib dis doctest  enum
    filecmp fileinput fnmatch fractions ftplib functools
    genericpath getopt getpass gettext glob graphlib gzip
    hashlib heapq hmac  imaplib imp inspect io ipaddress  keyword
    linecache locale lzma

    mailbox mimetypes modulefinder
    netrc ntpath nturl2path numbers  opcode operator optparse os
    pathlib pdb pickle pickletools pkgutil platform plistlib poplib posixpath
        pprint profile pstats pty py_compile pyclbr pydoc
    queue quopri  random reprlib rlcompleter runpy
    sched secrets selectors shelve shlex shutil signal site smtpd smtplib socket
        socketserver sre_compile sre_constants sre_parse ssl stat statistics string
        stringprep struct subprocess symtable sysconfig
    tabnanny tarfile tempfile textwrap this threading timeit token tokenize
        trace traceback tracemalloc tty turtle types typing
    warnings  wave weakref webbrowser  zipapp zipfile zipimport


    # from Dirs containing an "_init__.py" File

    asyncio  collections concurrent ctypes curses  dbm distutils
    email encodings ensurepip  html http  idlelib importlib  json  lib2to3 logging

    multiprocessing  pydoc_data  re  sqlite3  test tkinter tomllib turtledemo
    unittest urllib urllib.parse  venv  wsgiref  xml xmlrpc  zoneinfo


    # from VEnv Pip Install

    jira matplotlib numpy pandas psutil psycopg2 redis requests


"""

PYTHON_IMPORTS = _PYTHON_IMPORTS_TEXT_.splitlines()
PYTHON_IMPORTS = list(_.partition("#")[0] for _ in PYTHON_IMPORTS)
PYTHON_IMPORTS = list(_.strip() for _ in PYTHON_IMPORTS)
PYTHON_IMPORTS = " ".join(PYTHON_IMPORTS).split()

assert len(PYTHON_IMPORTS) == 201, (len(PYTHON_IMPORTS), 201)

# todo: doc which Python Version we scraped these Importable Names from


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

                sys.exit(2)  # exits 2 for Help Doc and/or Parser gone wrong

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

        default_eq_none = None
        with_columns_else = os.environ.get("COLUMNS", default_eq_none)  # checkpoints
        with_no_color_else = os.environ.get("NO_COLOR", default_eq_none)  # checkpoints

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


assert sys.__stderr__ is not None  # refuses to run headless
with_stderr = sys.stderr


assert int(0x80 + signal.SIGINT) == 130  # discloses the Nonzero Exit Code for after ⌃C SigInt


def excepthook(  # ) -> ...:
    exc_type: type[BaseException] | None,  # aka .type
    exc_value: BaseException | None,  # aka .exc_obj aka .value
    exc_traceback: types.TracebackType | None,  # aka .exc_tb aka .traceback aka .tb
) -> None:
    """Run at Process Exit"""

    if exc_type is SystemExit:
        return

        # consciously no traceback.print_exception
        # happens without sys.flags.interactive when not called via sys.excepthook

    # Quit loudly for KeyboardInterrupt

    if exc_type is KeyboardInterrupt:
        pass

    # Quit quietly, early now, if BdbQuit

    if exc_type is bdb.BdbQuit:
        with_stderr.write("BdbQuit\n")
        sys.exit(130)  # 0x80 + signal.SIGINT  # same as for KeyboardInterrupt

    # Print the usual 'Traceback (most recent call last):', & Traceback, & Assert

    print(file=with_stderr)
    print(file=with_stderr)  # twice

    traceback.print_exception(exc_type, value=exc_value, tb=exc_traceback, file=with_stderr)

    print(file=with_stderr)
    print(file=with_stderr)  # twice

    # Launch the Post-Mortem Debugger

    if exc_value is not None:
        if not hasattr(sys, "last_exc"):
            setattr(sys, "last_exc", exc_value)  # ducks out of confusing pdb.pm()

            # todo: figure out when this does and doesn't happen

    if exc_traceback is not None:
        if not hasattr(sys, "last_traceback"):
            setattr(sys, "last_traceback", exc_traceback)  # ducks out of confusing pdb.pm()

            # todo: figure out when this does and doesn't happen

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litpython.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
