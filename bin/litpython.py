#!/usr/bin/env python3

r"""
usage: litpython.py [-h] [PY ...]

exec some lines of python code, without making you type out the 'import's

positional arguments:
  PY          one more line of python code to exec

options:
  -h, --help  show this help message and exit

quirks:
  trusts Git to say when new Names becomes Importable

examples:
  p  # and then no imports required, like you can just say:  dt.datetime.now().astimezone()
  p 'p(t)' 'p(repr(t))'  # speaking of (p, t, logger, parser, ...) already eagerly defined for you
  p 'print("".join(chr(_) for _ in range(0x20, 0x7E + 1)))'  # no interaction required
  p '!pwd'  # shell or python, you choose
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections.abc  # .collections.abc is not .abc import collections.abc collections.abc.Callable is not typing.Callable
import dataclasses
import datetime as dt
import difflib
import importlib
import logging
import os
import pdb
import signal
import subprocess
import sys
import textwrap
import traceback
import types
import urllib  # eager 'import urllib', at first without our lazy 'import urllib.parse'
import zoneinfo

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


UTC = zoneinfo.ZoneInfo("UTC")  # extends welcome into the Periphery (outside San Francisco)


Pacific = zoneinfo.ZoneInfo("America/Los_Angeles")
PacificLaunch = dt.datetime.now(Pacific)


def main() -> None:
    """Run Python Code else a Python Chat, but tell uncaught Exceptions to launch the Py Repl"""

    # sys.excepthook = sys_excepthook_shell_else_pdb_pm  # catches SystemExit, KeyboardInterrupt, etc
    # try_main()

    try:

        try_main()

    except SyntaxError:

        sys_excepthook_shell_else_pdb_pm(*sys.exc_info())  # launches shell or pdb.pm()

    except (Exception, KeyboardInterrupt):  # BrokenPipeError # never SystemExit

        PacificQuit = dt.datetime.now(Pacific)
        launch, _quit_ = PacificLaunch, PacificQuit
        print(str(_quit_ - launch), "Quit='" + str(_quit_) + "'", "launch='" + str(launch) + "'")

        sys_excepthook_shell_else_pdb_pm(*sys.exc_info())  # launches pdb.pm()

    except SystemExit:

        pass  # because 'return' shouts less than 'sys.exit' does, when run by 'python3 -i'


def try_main() -> None:
    """Run Python Code else a Python Chat"""

    doc = __main__.__doc__
    assert doc, (doc,)

    parser = arg_doc_to_parser(doc)
    ns = parser.parse_args_if(sys.argv[1:])

    pylines = ns.pylines
    pyjoin = "\n".join(pylines)
    pytext = textwrap.dedent(pyjoin).strip()

    sys.path[0] = ""  # matches 'python3 -c', not 'python3 F.py'

    _globals_add_lazy_imports_()
    _globals_add_eager_objects_()

    # Run Python Code else a Python Chat

    g = globals()
    if pytext:
        exec(pytext, g)  # syntax 'exec(pytext, globals=g)' works only in later Python
    else:
        os.environ["PYTHONINSPECT"] = str(True)
        sys.excepthook = sys_excepthook_shell_else_pdb_pm

        # t = dt.datetime.now(Pacific)
        # print(t - PacificLaunch)  # < 2ms lately at my desk


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Options & Positional Arguments"""

    assert argparse.REMAINDER == "..."
    assert argparse.ZERO_OR_MORE == "*"

    parser = ArgDocParser(doc, add_help=True)

    py_help = "one more line of python code to exec"
    parser.add_argument("pylines", metavar="PY", nargs="*", help=py_help)

    return parser


#
# Delay chat for long enough to form some commonly helpful Python Objects
#


def _globals_add_eager_objects_() -> None:
    "Delay chat for long enough to form some commonly helpful Python Objects"

    g = globals()

    if "logger" not in g.keys():
        logger = logging.getLogger(__name__)
        g["logger"] = logger

    if "p" not in g.keys():
        p = print
        g["p"] = p

    if "parser" not in g.keys():
        parser = argparse.ArgumentParser()
        g["parser"] = parser

    if "t" not in g.keys():
        g["t"] = PacificLaunch


#
# Define 'print(repr(globals()))' to mean Import Everything
#


def _globals_add_lazy_imports_() -> None:
    "Define 'print(repr(globals()))' to mean Import Everything"

    g = globals()

    for name in PYTHON_IMPORTS:
        if name not in g.keys():
            g[name] = LazyImport(name)

    if "D" not in g.keys():
        D = LazyImport(_import_="decimal", _as_="D", _what_="Decimal")
        g["D"] = D

    if "dt" not in g.keys():
        dt = LazyImport(_import_="datetime", _as_="dt")
        g["dt"] = dt

    if "et" not in g.keys():
        et = LazyImport(_import_="xml.etree.ElementTree", _as_="et")
        g["et"] = et

    if "np" not in g.keys():
        np = LazyImport(_import_="numpy", _as_="np")
        g["np"] = np

    if "pd" not in g.keys():
        pd = LazyImport(_import_="pandas", _as_="pd")
        g["pd"] = pd

    if "plt" not in g.keys():
        plt = LazyImport(_import_="matplotlib.pyplot", _as_="plt")
        g["plt"] = plt

    setattr(urllib, "parse", LazyImport(_import_="urllib.parse"))

    # todo: lazy 'email.mime.multipart', 'email.mime.text', 'logging.handlers', 'unittest.mock'
    # todo: lazy 'urllib' without 'urllib.parse'

    # todo: lazy PyPi 'import mysql.connector'


class LazyImport:
    """Defer the work of "import X as Y" or "from X import Z as Y" till first Y.Q fetched"""

    def __init__(self, _import_: str, _as_: str | None = None, _what_: str | None = None) -> None:
        self._import_ = _import_
        self._as_ = _import_ if (_as_ is None) else _as_
        self._what_ = _what_

    def _fetch_(self) -> object:
        module = importlib.import_module(self._import_)
        value = module if (self._what_ is None) else getattr(module, self._what_)
        globals()[self._as_] = value
        return value

    def __getattribute__(self, name: str) -> object:
        if name in "_import_ _as_ _what_ _fetch_".split():
            return super().__getattribute__(name)
        value = self._fetch_()
        return getattr(value, name)

    def __repr__(self) -> str:
        value = self._fetch_()
        return repr(value)


_PYTHON_IMPORTS_TEXT_ = """

    # the most eager Imports
    #
    #   import sys
    #   items = list(sys.modules.items())
    #   sorted(_[0] for _  in items if not _[0].startswith("_") and not hasattr(_[-1], "__file__"))
    #

    __main__

    atexit builtins errno itertools marshal posix pwd sys time


    # the ".so" Shared Object Libraries of
    #
    #   cd $(python3 -c 'import os, readline; print(os.path.dirname(readline.__file__))')
    #   ls *.so |grep -v ^_
    #
    # minus obscure:  xxlimited_35 xxlimited xxsubtype

    array  binascii  cmath  fcntl  grp
    math mmap  readline resource  select syslog  termios  unicodedata  zlib


    # the Py Files of
    #
    #   cd $(python3 -c 'import abc, os; print(os.path.dirname(abc.__file__))')
    #   ls *.py |grep -v ^_ |cut -d. -f1 |cut -d/ -f1 |LC_ALL=C sort
    #

    abc annotationlib antigravity argparse ast  base64 bdb bisect bz2
    cProfile calendar cmd code codecs codeop colorsys
        compileall configparser contextlib contextvars copy copyreg csv
    dataclasses datetime decimal difflib dis doctest  enum
    filecmp fileinput fnmatch fractions ftplib functools
    genericpath getopt getpass gettext glob graphlib gzip
    hashlib heapq hmac  imaplib inspect io ipaddress  keyword  linecache locale lzma

    mailbox mimetypes modulefinder
    netrc ntpath nturl2path numbers  opcode operator optparse os
    pdb pickle pickletools pkgutil platform plistlib poplib posixpath
        pprint profile pstats pty py_compile pyclbr pydoc
    queue quopri  random reprlib rlcompleter runpy
    sched secrets selectors shelve shlex shutil signal site sitecustomize smtplib socket
        socketserver sre_compile sre_constants sre_parse ssl stat statistics
        stringprep struct subprocess symtable
    tabnanny tarfile tempfile textwrap this threading timeit token tokenize
        trace traceback tracemalloc tty turtle types typing
    uuid  warnings wave weakref webbrowser  zipapp zipimport

    # the Py Folders of
    #
    #   cd $(python3 -c 'import abc, os; print(os.path.dirname(abc.__file__))')
    #   ls */__init__.py |grep -v ^_ |cut -d. -f1 |cut -d/ -f1 |LC_ALL=C sort

    asyncio  collections compression concurrent ctypes curses  dbm
    email encodings ensurepip  html http  idlelib importlib  json  logging

    multiprocessing  pathlib pydoc_data  re  sqlite3 string sysconfig
    test tkinter tomllib turtledemo  unittest urllib  venv  wsgiref  xml xmlrpc  zipfile zoneinfo


    # from VEnv Pip Install

    jira matplotlib mysql numpy pandas psutil psycopg2 redis requests

"""


PYTHON_IMPORTS = _PYTHON_IMPORTS_TEXT_.splitlines()
PYTHON_IMPORTS = list(_.partition("#")[0] for _ in PYTHON_IMPORTS)
PYTHON_IMPORTS = list(_.strip() for _ in PYTHON_IMPORTS)
PYTHON_IMPORTS = " ".join(PYTHON_IMPORTS).split()

assert len(PYTHON_IMPORTS) == 199, (len(PYTHON_IMPORTS), 199)  # Feb/2026 Python 3.14.3


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


def sys_excepthook_shell_else_pdb_pm(
    exc_type: type[BaseException] | None,  # aka .type
    exc_value: BaseException | None,  # aka .exc_obj aka .value
    exc_traceback: types.TracebackType | None,  # aka .exc_tb aka .traceback aka .tb
) -> None:
    """Take a typed '!' Line as a Shell Input Line, else print the Exception as usual"""

    if isinstance(exc_value, SyntaxError):
        filename = exc_value.filename or ""
        if filename.startswith("<python-input") or (filename in ("<stdin>", "<string>")):
            text = exc_value.text or ""
            rstrip = text.rstrip()
            if rstrip.startswith("!"):
                shline = rstrip.removeprefix("!")

                default_eq_sh = "sh"
                shpath = os.environ.get("SHELL", default_eq_sh)

                sys.stdout.flush()
                sys.stderr.flush()

                run = subprocess.run(shline if shline else shpath, shell=True)

                sys.stdout.flush()
                sys.stderr.flush()

                if run.returncode:
                    print(f"+ exit {run.returncode}", file=sys.stderr)
                    sys.stderr.flush()

                return

    sys_excepthook_pdb_pm(exc_type, exc_value=exc_value, exc_traceback=exc_traceback)

    # 'def sys_excepthook_shell_else_pdb_pm' last modified for py2def.py on 2026-07-10 or later


def sys_excepthook_pdb_pm(
    exc_type: type[BaseException] | None,  # aka .type
    exc_value: BaseException | None,  # aka .exc_obj aka .value
    exc_traceback: types.TracebackType | None,  # aka .exc_tb aka .traceback aka .tb
) -> None:
    """Tell an Uncaught Exception to launch the Py Repl, as if a Breakpoint were at the Raise"""

    # Do nothing after a SystemExit

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

            # todo: figure out when .last_exc is and isn't initted for us

    if exc_traceback is not None:
        if not hasattr(sys, "last_traceback"):
            setattr(sys, "last_traceback", exc_traceback)  # ducks out of confusing pdb.pm()

            # todo: figure out when .last_traceback is and isn't initted for us

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()  # launches the Py Repl of The Post-Mortem Debugger

    # 'def sys_excepthook_pdb_pm' last modified for py2def.py on 2026-07-09 or later


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()


# todo: objects for iterating over


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litpython.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
