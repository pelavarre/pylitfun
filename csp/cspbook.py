#!/usr/bin/env python3

r"""
usage: cspbook.py [-h] [-i] [-c CSP]

exec some lines of csp code

options:
  -h, --help  show this help message and exit
  -i          prompt and reply, loop loop till quit
  -c CSP      one line of csp code to exec

quirks:
  trusts you to press Return to continue, ⌃C to cancel, ⌃D to quit
  trusts your Terminal Shell tab to understand ⎋[⇧A ⎋[⇧K
  works like Python works:
    cspbook.py --help
    cspbook.py --
    cspbook.py -i -c ''
      dir()

examples:
  cspbook.py
  cspbook.py --help
  cspbook.py -c STOP
  cspbook.py -c CTR
  cspbook.py -c CLOCK1
  cspbook.py -c CH5B
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
import hashlib
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

    pathname = sys.argv[0]
    if (not ns.c) and (not ns.i):
        version = pathname_read_version(pathname)  # '0.15.255'
        ymd = PacificLaunch.strftime("%Y-%m-%d")
        eprint(f"Csp Python {version} (main, {ymd})", file=sys.stderr)

        # Csp Python 0.4.39 (main, 2026-05-24)

    if ns.c:
        csp = ns.c
        csp_exec(csp)  # may raise SystemExit

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
csp_globals: dict[str, typing.Any] = dict()


def csp_exec(csp: str) -> None:
    """Exec one line of csp code"""

    strip = csp.strip()

    csp_builtins = csp_sys_modules["builtins"]

    # Take 'dir()' as a meta-instruction

    if strip in ("exit", "exit()", "quit", "quit()"):
        sys.exit()

    # Take 'dir()' as a meta-instruction

    if strip == "dir()":
        procnames = list(csp_builtins.keys())
        print(procnames)

        return

    if strip.startswith("??") or strip.endswith("??"):
        procname = strip.strip("?")
        named = to_proc_from_name(procname)
        print(json.dumps(named))

        return

    # todo: Disentangle the Scopes of one Proc Def and the next

    csp_globals.clear()

    # Step through the Csp Code

    procname = strip
    named = to_proc_from_name(procname)

    while True:

        # Complete an Empty Proc

        if not named:
            print("STOP")
            break

        # Take a Global Proc Def, else an unnamed Seq

        if isinstance(named, list):

            seq = named

        elif isinstance(named, dict):
            keys = list(named.keys())
            assert len(keys) == 1, (keys, procname)

            procname = keys[-1]
            seq = named[procname]

            if procname in csp_globals.keys():
                eprint(f"Warning: Redefining Global Proc {procname!r}", file=sys.stderr)

            csp_globals[procname] = seq

        else:

            raise NotImplementedError(type(named), named)

        # Step into the Seq

        while True:

            assert seq[1:], (seq, procname)
            guards = seq[:-1]
            guarded = seq[-1]

            for eventname in guards:
                print(eventname)

                eprint("> ", end="", file=sys.stderr)
                ack = sys.stdin.readline()  # echoes to stdout

                if ack == "\n" or (ack.strip() == eventname):
                    eprint("\033[A" "\033[K", end="", file=sys.stderr)
                    continue

                    # ⎋[A Cursor Up (CUP)
                    # ⎋[K Erase in Line (EL)

                print()
                return

            if isinstance(guarded, str):
                procname = guarded
                named = to_proc_from_name(procname)
                break

            assert isinstance(guarded, list), (type(guarded), guarded)
            seq = guarded

            continue

        if named:
            print()  # shows the jump into the next Proc

        continue


def to_proc_from_name(procname: str) -> typing.Any:
    """Fetch the Body of a Proc Def"""

    csp_builtins = csp_sys_modules["builtins"]

    if procname in csp_globals.keys():
        named = csp_globals[procname]
    elif procname in csp_builtins.keys():
        named = csp_builtins[procname]
    else:
        raise NameError(f"name {procname!r} is not defined")

    return named


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

    keys = list(pj.keys())
    for k in keys:
        assert isinstance(k, str), (type(k), k)

    for k in keys:
        assert isinstance(k, str), (type(k), k)

        if k == "__doc__":  # keeps the Docstring
            continue

        if k.startswith("#"):  # drops each Comment
            del pj[k]
            continue

        if k.startswith("__") and k.endswith("__"):  # drops each Dunder Key, no matter if known
            del pj[k]
            continue

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

        eprint("csp> ", end="", file=sys.stderr)

        try:
            csp = sys.stdin.readline()  # echoes to stdout
        except KeyboardInterrupt:
            print()
            print("KeyboardInterrupt")
            continue

        if not csp:
            print()
            sys.stdout.flush()
            break

        if not csp.strip():
            continue

        try:
            csp_exec(csp)  # may raise SystemExit
        except KeyboardInterrupt:
            print()
            print("KeyboardInterrupt")
            continue

        continue


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
# Amp up Import HashLib
#


def pathname_read_version(pathname: str) -> str:
    """Hash the Bytes of a File down to a purely Decimal $Major.$Minor.$Micro Version Str"""

    path = pathlib.Path(pathname)
    path_bytes = path.read_bytes()

    hasher = hashlib.md5()
    hasher.update(path_bytes)
    hash_bytes = hasher.digest()

    str_hash = hash_bytes.hex()
    str_hash = str_hash.upper()  # such as 32 nybbles 'a451f4d7589110b33da89a2d173216e3'

    major = 0
    minor = int(str_hash[0], 0x10)  # 0..15
    micro = int(str_hash[1:][:2], 0x10)  # 0..255

    version = f"{major}.{minor}.{micro}"
    return version

    # 0.15.255


#
# Amp up Import Sys
#


def eprint(*args: object, end: str = "\n", file: typing.TextIO) -> None:
    """Print to Stderr without disordering Stdout"""

    sys.stdout.flush()  # especially when file is not sys.stdout
    print(*args, end=end, file=file)
    sys.stderr.flush()


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
