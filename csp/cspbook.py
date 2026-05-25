#!/usr/bin/env python3

r"""
usage: cspbook.py [-h] [-i] [-c CSP]

exec some lines of csp code

options:
  -h, --help  show this help message and exit
  -i          prompt and reply, loop loop till quit
  -c CSP      one line of csp code to exec

examples:
  cspbook.py
  cspbook.py -i -c ''
  cspbook.py -c STOP
"""

# code reviewed by People, Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import bdb
import collections.abc
import dataclasses
import datetime as dt
import difflib
import json
import os
import pathlib
import pdb
import signal
import sys
import textwrap
import traceback
import types
import typing
import zoneinfo

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


Pacific = zoneinfo.ZoneInfo("America/Los_Angeles")
PacificLaunch = dt.datetime.now(Pacific)


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    sys.excepthook = excepthook

    try:
        try_main()
    except Exception:  # not KeyboardInterrupt nor SystemExit
        PacificQuit = dt.datetime.now(Pacific)
        print(PacificQuit, PacificQuit - PacificLaunch)
        excepthook(*sys.exc_info())


def try_main() -> None:
    """Run from the Shell Command Line"""

    doc = __main__.__doc__
    assert doc, (doc,)

    parser = arg_doc_to_parser(doc)
    ns = parser.parse_args_if(sys.argv[1:])

    _ = import_csp_module("builtins")

    if ns.c:
        csp = ns.c
        csp_exec(csp)

    if ns.i or not ns.c:
        csp_chat()


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Options & Positional Arguments"""

    parser = ArgDocParser(doc, add_help=True)

    i_help = "prompt and reply, loop loop till quit"
    c_help = "one line of csp code to exec"

    parser.add_argument("-i", action="count", help=i_help)
    parser.add_argument("-c", metavar="CSP", help=c_help)

    return parser


#
# Run through a Csp Program
#


csp_sys_modules: dict[str, typing.Any] = dict()


def csp_exec(csp: str) -> None:
    """Exec one line of csp code"""

    builtins = csp_sys_modules["builtins"]

    if csp not in builtins.keys():
        raise NameError(f"name {csp!r} is not defined")

    pj = builtins[csp]
    print(json.dumps(pj, indent=2))


def import_csp_module(modulename: str) -> object:
    """Import one Csp Module at most once per Linux Process"""

    # Import at most once

    if modulename in csp_sys_modules.keys():
        return csp_sys_modules[modulename]

    # Require exactly one Source File found

    pathnames = which_csp_module(modulename)

    if not pathnames:
        raise ModuleNotFoundError(f"No module named {modulename!r}")  # in os.getcwd()

    if pathnames[1:]:
        n = len(pathnames)
        raise ModuleNotFoundError(f"name {modulename!r} has {n} definitions: {pathnames}")

    # Take as 1 Json Object

    pathname = pathnames[-1]

    path = pathlib.Path(pathname)
    text = path.read_text()

    pj = dict()
    if text:
        try:
            pj = json.loads(text)
        except Exception as exc:
            raise SyntaxError(f"name {modulename!r} at {pathname!r}") from exc

    # Start mutating the Json Object

    csp_sys_modules[modulename] = pj

    # Succeed

    return pj


def which_csp_module(modulename: str) -> list[str]:
    """Find all the Pathnames of a Csp Module Name"""

    pathnames = list()

    filename = f"{modulename}.json"
    casefold = filename.casefold()

    for dirpath, dirnames, filenames in os.walk("."):
        dirnames.sort()  # no matter if hidden dir
        filenames.sort()

        casefolds = list(_.casefold() for _ in filenames)
        if casefold in casefolds:  # no matter if hidden file
            pathname = os.path.join(dirpath, filename)

            pathnames.append(pathname)

    return pathnames  # maybe empty, maybe multiple


#
# Prompt and reply, loop loop till quit
#


def csp_chat() -> None:
    """Prompt and reply, loop loop till quit"""

    while True:

        sys.stdout.flush()
        print("csp> ", end="", file=sys.stderr)
        sys.stderr.flush()

        csp = sys.stdin.readline()  # echoes to stdout

        if not csp:
            print()
            sys.stdout.flush()

            break

        csp_exec(csp)


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


def excepthook(  # last modified on 2026-05-14 or later
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

            # todo: figure out when .last_exc is and isn't initted for us

    if exc_traceback is not None:
        if not hasattr(sys, "last_traceback"):
            setattr(sys, "last_traceback", exc_traceback)  # ducks out of confusing pdb.pm()

            # todo: figure out when .last_traceback is and isn't initted for us

    print(">" ">" "> pdb.pm()", file=with_stderr)  # (3 * ">") spelled unlike a Git Conflict
    pdb.pm()


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()


# todo: objects for iterating over


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litpython.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
