#!/usr/bin/env python3

r"""
usage: cspbook.py [-h] [-i] [-c CODELINE] [--make-tests]

exec some lines of csp code

options:
  -h, --help    show this help message and exit
  -i            prompt and reply, loop loop till quit
  -c CODELINE   one line of csp code to exec
  --make-tests  update:  git diff csp/cspbook-py-readme.md

quirks:
  trusts you to press Return to continue, ⌃C to cancel, ⌃D to quit
  trusts your Terminal Shell tab to understand ⎋[⇧A ⎋[⇧K
  works like Python works:
    cspbook.py --help
    cspbook.py --
    cspbook.py -i -c ''
      dir()

examples:
  cspbook.py -i
  cspbook.py -c CTR
  cspbook.py -c CLOCK
  cspbook.py -c VMC
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
import io
import json
import os
import pathlib
import pdb
import re
import signal
import sys
import termios
import textwrap
import traceback
import tty
import types
import typing
import zoneinfo

# _: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


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

    except Exception:  # not KeyboardInterrupt  # not SystemExit

        PacificQuit = dt.datetime.now(Pacific)
        print(PacificQuit, PacificQuit - PacificLaunch)
        excepthook(*sys.exc_info())


def try_main() -> None:
    """Run from the Shell Command Line"""

    doc = __main__.__doc__
    assert doc, (doc,)

    parser = arg_doc_to_parser(doc)
    ns = parser.parse_args_if(sys.argv[1:])

    ct = CodeTalker()
    cw = ct.code_wrangler
    cw.import_module("builtins")

    pathname = sys.argv[0]
    str_version = pathname_read_hash_ymd_version(pathname)  # '0.4.39 (main, 2026-05-24)'

    cs = CodeSketcher(ct)
    if ns.make_tests:
        cs.update_md()

    if (not ns.c) and (not ns.i):
        if not ns.make_tests:  # if banner for '--'
            eprint(f"Csp Python {str_version}")

    if ns.c:
        codeline = ns.c
        ct.sys_exec(codeline)  # may raise SystemExit

    if ns.i:
        ct.sys_chat()
    elif ns.make_tests:
        pass
    else:  # if chat for '--'
        ct.sys_chat()


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Options & Positional Arguments"""

    parser = ArgDocParser(doc, add_help=True)

    i_help = "prompt and reply, loop loop till quit"
    c_help = "one line of csp code to exec"
    make_tests_help = "update:  git diff csp/cspbook-py-readme.md"

    parser.add_argument("-i", action="count", help=i_help)
    parser.add_argument("-c", metavar="CODELINE", help=c_help)
    parser.add_argument("--make-tests", action="count", help=make_tests_help)

    return parser


# ####### ####### ####### ####### ####### ####### ####### ####### ####### #######
# ####### ####### ####### ####### ####### ####### ####### ####### ####### #######
# ####### ####### ####### ####### ####### ####### ####### ####### ####### #######


#
# Update:  git diff csp/cspbook-py-readme.md
#


class CodeSketcher:
    """Update:  git diff csp/cspbook-py-readme.md"""

    code_talker: CodeTalker

    def __init__(self, code_talker: CodeTalker) -> None:
        self.code_talker = code_talker

    def update_md(self) -> None:
        """Update:  git diff csp/cspbook-py-readme.md"""

        pathname = sys.argv[0]
        str_version = pathname_read_hash_ymd_version(pathname)  # '0.4.39 (main, 2026-05-24)'

        #

        _dir_ = os.path.dirname(__file__)
        iopathname = os.path.join(_dir_, "cspbook-py-readme.md")
        iopath = pathlib.Path(iopathname)

        itext = iopath.read_text()
        ilines = itext.splitlines()

        #

        dent = 4 * " "
        olines = list()

        i = 0
        n = 1
        while i < len(ilines):
            iline = ilines[i]
            i += 1

            olines.append(iline)

            # Number the demos

            if re.fullmatch(r"[0-9]+", string=iline):
                olines[-1] = str(n)
                n += 1
                continue

            # Add version trace

            dedented = iline.removeprefix(dent)
            if dedented == "% ./csp/cspbook.py --":
                jlines = self.drop_lines(ilines, i=i)
                i += len(jlines)

                olines.append(dent + f"Csp Python {str_version}")
                olines.append(dent + "csp> ".rstrip())
                olines.append(dent + "csp> ^D")  # '⌃' != '^'
                olines.append(dent + "% ".rstrip())
                olines.append("")

                continue

            # Add source & exec trace

            eline = dedented.removeprefix("csp> ")
            if eline != dedented:
                verb = eline.removesuffix("??")
                if verb != eline:
                    i = self.make_one_test(olines, ilines=ilines, i=i, verb=verb)

                    continue

        #

        otext = "\n".join(olines) + "\n"
        iopath.write_text(otext)

        return  # success

    def make_one_test(self, olines: list[str], ilines: list[str], i: int, verb: str) -> int:
        """Make one Test Result from one Verb"""

        ct = self.code_talker

        proc = ct.to_proc_from_name(procname=verb)
        n = self.count_stops(proc)
        execs = max(1, n)

        jlines = self.drop_lines(ilines, i=i)
        j = i + len(jlines)

        self.add_source_trace(olines=olines, verb=verb)
        for choice in Choice.selves:
            choice.eventnames.clear()

        for _ in range(execs):
            self.add_exec_trace(olines=olines, verb=verb, jlines=jlines)

        return j

    def count_stops(self, pj: object) -> int:
        """Count the STOP's in a Proc"""

        if isinstance(pj, dict):
            return sum(self.count_stops(_) for _ in pj.values())
        if isinstance(pj, list):
            return sum(self.count_stops(_) for _ in pj)
        if isinstance(pj, str):
            if pj == "STOP":
                return 1

        return 0

    def drop_lines(self, ilines: list[str], i: int) -> list[str]:
        """Drop the Lines of dented Grafs till next undented Graf"""

        assert i, (i,)

        iline = ilines[i - 1]
        ident = len(iline) - len(iline.lstrip())

        j = i

        jlines = list()
        while j < len(ilines):
            jline = ilines[j]
            j += 1

            jdent = len(jline) - len(jline.lstrip())
            if jline:
                if not jdent:
                    assert j > i, (i, j, jdent, ident, jline, iline)
                    break

            jlines.append(jline)

            ji = j - i
            assert ji < 100, (i, j, ji)

            assert j < len(ilines), (j, len(ilines), i)

        return jlines

    def add_source_trace(self, olines: list[str], verb: str) -> None:
        """Add one Trace of Prints of Source"""

        ct = self.code_talker

        dent = 4 * " "

        proc = ct.to_proc_from_name(procname=verb)
        plines = json.dumps(proc).splitlines()
        olines.extend((dent + _) for _ in plines)
        olines.append(dent + "csp> ".rstrip())
        olines.append("")

    def add_exec_trace(self, olines: list[str], verb: str, jlines: list[str]) -> None:
        """Add one Trace of Prints of Exec"""

        ct = self.code_talker

        # Count nonblank lines after the first Graf

        inputs = -1

        cancelling = False

        grafs = 0
        for jline in jlines:
            if not jline:
                grafs += 1
            elif grafs >= 1:
                lstrip = jline.lstrip()
                if lstrip:
                    if lstrip.startswith("csp>"):
                        pass
                    elif lstrip == "> ^C":  # '⌃' != '^'
                        cancelling = True
                    else:
                        inputs += 1

        assert inputs >= 0, (inputs, jlines, verb)

        itext = 123 * "\n"  # todo: arbitrarily large enough, maybe
        if cancelling:
            itext = inputs * "\n"
            itext += "\x03"  # emulates raising KeyboardInterrupt at ^C

        # Say how to collect outputs

        tprints = list()

        def _tprint_(text: str = "", end: str = "\n") -> None:
            tprints.append(text + end)

        # Start collecting outputs

        with_stdin = sys.stdin
        with_eprint = eprint

        module = sys.modules[__name__]
        assert not hasattr(module, "print")
        assert getattr(module, "eprint") is with_eprint

        sys.stdin = io.StringIO(itext)
        setattr(module, "print", _tprint_)
        setattr(module, "eprint", _tprint_)
        try:
            ct.sys_exec(verb)
        finally:
            sys.stdin = with_stdin
            delattr(module, "print")
            setattr(module, "eprint", with_eprint)

        dent = 4 * " "

        olines.append(dent + f"csp> {verb}")

        kprints = list(_ for _ in tprints if "\n" in _)
        ktext = "".join(kprints)
        klines = ktext.splitlines()
        olines.extend(((dent + _).rstrip()) for _ in klines)

        olines.append(dent + "csp> ".rstrip())
        olines.append("")


class CodeTalker:
    """Run Code and walk through Code"""

    code_wrangler: CodeWrangler

    def __init__(self) -> None:

        cw = CodeWrangler()
        self.code_wrangler = cw

    #
    # Prompt and reply, loop loop till quit
    #

    def sys_chat(self) -> None:
        """Prompt and reply, loop loop till quit"""

        while True:

            eprint("csp> ", end="")

            try:
                csp = sys.stdin.readline()  # reads and echoes
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
                self.sys_exec(csp)  # may raise SystemExit
            except KeyboardInterrupt:
                print()
                print("KeyboardInterrupt")
                continue

            continue

    #
    # Run through a Csp Program
    #

    def sys_exec(self, codeline: str) -> None:
        """Exec one line of Csp code"""

        strip = codeline.strip()
        join = "".join(codeline.split())

        cw = self.code_wrangler
        sys_globals = cw.sys_globals
        sys_modules = cw.sys_modules
        sys_builtins = sys_modules["builtins"]

        sys_globals.clear()  # todo2: Disentangle the Scopes of one Proc Def and the next

        sys_locals = sys_globals
        sys_locals["__builtins__"] = sys_globals
        sys_locals["__doc__"] = None

        # Take 'quit()' etc as a meta-instruction

        if join in ("exit", "exit()", "quit", "quit()"):
            sys.exit()

        # Take 'dir()' and 'dir(__builtins__)' as meta-instructions

        if join == "__doc__":  # todo2: find "__doc__" in ._locals_ and quit before ._builtins_
            return

        if join == "dir()":
            procnames = list(sys_locals)  # 'better copied than aliased'
            print(procnames)
            return

        if join == "dir(__builtins__)":
            procnames = list(sys_builtins)  # 'better copied than aliased'
            print(procnames)
            return

        if join == "__builtins__.__doc__":
            print(repr(sys_builtins["__doc__"]))
            return

        # Take suffix or prefix '??' as a meta-instruction

        if strip.startswith("??") or strip.endswith("??"):

            procname = strip.strip(" ?")
            proc = self.to_proc_from_name(procname)
            print(json.dumps(proc))

            for choice in Choice.selves:
                choice.eventnames.clear()

            return

        # Single Step through the Csp Code of 1 Proc Def

        procname = strip
        self.procname_single_step(procname)

    def procname_single_step(self, procname: str) -> None:  # todo0:  # noqa C901 complex (19)
        """Walk through the Events of 1 Named Process"""

        cw = self.code_wrangler
        sys_globals = cw.sys_globals

        proc = self.to_proc_from_name(procname)

        while True:

            # Complete an Empty Proc

            if not proc:
                break

            # Walk through a named Sequence

            if isinstance(proc, Sequence):
                seq = proc
                proc = self.seq_single_step(seq)
                if proc:
                    continue
                break

            # Dive into Shorthand

            if isinstance(proc, Shorthand):

                items = list(proc.items())
                assert len(items) == 1, (len(items), items)

                item = items[-1]
                k = item[0]
                v = item[-1]

                if k in sys_globals.keys():
                    eprint(f"Warning: Redefining Global Proc {k!r}")

                sys_globals[k] = v

                # Walk through a Sequence named by Shorthand

                if isinstance(v, Sequence):
                    seq = v
                    proc = self.seq_single_step(seq)
                    if proc:
                        continue
                    break

                # Walk through a Choice named by Shorthand of Shorthand

                if isinstance(v, Choice):
                    choice = v
                    proc = self.choice_single_step(choice)
                    if proc:
                        continue
                    break

                # Dive into Shorthand named by Shorthand

                if isinstance(v, Shorthand):

                    v_items = list(v.items())
                    assert len(v_items) == 1, (len(v_items), v_items)

                    v_item = v_items[-1]
                    v_k = v_item[0]
                    v_v = v_item[-1]

                    if v_k in sys_globals.keys():
                        eprint(f"Warning: Redefining Global Proc {v_k!r}")

                    sys_globals[v_k] = v_v

                    # Walk through a Sequence named by Shorthand of Shorthand

                    if isinstance(v_v, Sequence):
                        seq = v_v

                        proc = self.seq_single_step(seq)
                        if proc:
                            continue
                        break

                    # Walk through a Choice named by Shorthand of Shorthand

                    assert isinstance(v_v, Choice), (type(v_v), v_v)
                    choice = v_v

                    proc = self.choice_single_step(choice)
                    if proc:
                        continue
                    break

                # Else give up on something named by Shorthand

                raise NotImplementedError(type(v), v)

            # Make a choice

            if isinstance(proc, Choice):
                choice = proc
                proc = self.choice_single_step(choice)
                if proc:
                    continue
                break

            # Else give up on something named by Scope

            raise NotImplementedError(type(proc), proc)

        assert not proc, (proc,)
        if proc is not False:
            print("STOP")

    def seq_single_step(self, seq: Sequence) -> object:
        """Single Step through the Csp Code of 1 Sequence"""

        # Step into the Seq

        while True:

            assert seq[1:], (seq,)
            guards = seq[:-1]
            ward = seq[-1]

            for guard in guards:  # todo9: choices=choices to skip ahead
                assert isinstance(guard, str), (type(guard), guard)

                eventname = self.take_name(names=[guard], default=guard)
                if not eventname:
                    return False

            if isinstance(ward, Mention):
                procname = ward
                proc = self.to_proc_from_name(procname)
                if proc:
                    print()
                break

            if isinstance(ward, Choice):
                choice = ward
                proc = self.choice_single_step(choice)
                break

            assert isinstance(ward, Sequence), (type(ward), ward)
            seq = ward

            continue

        return proc

    def take_name(self, names: list[str], default: str) -> str:
        """Prompt with an Event Name, and take the same."""

        assert default, (default,)
        assert default in names, (default, names)

        eprint(default)

        while True:

            eprint("> ", end="")
            try:
                ack = _sys_sydin_readline_()  # echoes to stdout
            except KeyboardInterrupt:
                eprint()
                return ""

            if ack == "\x03":  # emulates raising KeyboardInterrupt at ^C
                eprint("> ^C")  # '⌃' != '^'
                return ""

            if not ack:
                eprint("^D")  # '⌃' != '^'
                return ""

            eprint("\r" "\033[A" "\033[K", end="")

            strip = ack.strip()
            if (ack == "\n") or (strip == default):
                return default

            if strip in names:
                eprint("\r" "\033[A" "\033[K", end="")
                eprint(strip)
                return strip

            continue

        # \r Carriage Return (CR)
        # ⎋[A Cursor Up (CUP)
        # ⎋[K Erase in Line (EL)

    def choice_single_step(self, choice: Choice) -> object:
        """Single Step through the Csp Code of 1 Choice"""

        while True:
            names = list(choice.keys())

            eventnames = choice.eventnames
            if not eventnames:
                eventnames.extend(names)

            default = eventnames.pop(0)
            eventname = self.take_name(names=names, default=default)
            if not eventname:
                return False

            chosen = choice[eventname]
            if isinstance(chosen, Sequence):
                proc = chosen
                return proc

            if isinstance(chosen, Choice):
                choice = chosen
                continue

            assert isinstance(chosen, Mention), (type(chosen), chosen)
            procname = chosen
            proc = self.to_proc_from_name(procname)
            if proc:
                print()
                return proc

            return proc

    def to_proc_from_name(self, procname: str) -> typing.Any:
        """Fetch the Body of a Proc Def"""

        cw = self.code_wrangler
        sys_globals = cw.sys_globals
        sys_modules = cw.sys_modules

        _builtins_ = sys_modules["builtins"]

        if procname in sys_globals.keys():  # todo2: pick apart sys_locals vs sys_globals
            proc = sys_globals[procname]
        elif procname in _builtins_.keys():
            proc = _builtins_[procname]
        else:
            raise NameError(f"name {procname!r} is not defined")

        return proc


#
# Wrangle Code
#


class CodeWrangler:
    """Wrangle Code"""

    sys_modules: dict[str, Scope] = dict()  # like Python sys.modules
    sys_globals: dict[str, object] = dict()  # like Python globals()

    def import_module(self, modulename: str) -> None:
        """Import one Csp Module at most once per Linux Process"""

        sys_modules = self.sys_modules

        # Import at most once

        if modulename in sys_modules.keys():
            return

        # Import one Csp Module Json

        pj = self.import_module_json(modulename)

        # Convert to an Abstract Syntax Tree

        scope = Scope(pj)

        # path = pathlib.Path("j.json")
        # path.write_text(json.dumps(scope, indent=2) + "\n")

        # Start mutating the Json Object

        sys_modules[modulename] = scope

    def import_module_json(self, modulename: str) -> dict[str, object]:
        """Import one Csp Module Json"""

        # Require exactly one Source File found

        pathnames = self.which_module_json(modulename)

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

            if k.startswith("__") and k.endswith("__"):  # drops any other Dunder Key
                del pj[k]
                continue

            if k.startswith("#"):  # drops each Comment
                del pj[k]
                continue

        # Succeed

        return pj

    def which_module_json(self, modulename: str) -> list[str]:
        """Find all the Pathnames of a Csp Module Name"""

        pathnames = list()

        filename = f"{modulename}.json"
        casefold = filename.casefold()

        for dirpath, dirnames, filenames in os.walk("."):
            dirnames.sort()  # no matter if hidden dir
            filenames.sort()  # 'better ordered than muddled'

            casefolds = list(_.casefold() for _ in filenames)
            if casefold in casefolds:  # no matter if hidden file
                pathname = os.path.join(dirpath, filename)

                pathnames.append(pathname)

        return pathnames  # maybe empty, maybe multiple


class Scope(dict[str, object]):
    """A Scope is a Dict of Shorthand's"""

    def __init__(self, pj: dict[str, object]) -> None:
        super().__init__(pj)

        items = list(self.items())
        for item in items:
            k, v = item

            if k == "__doc__":
                assert isinstance(v, str), (type(v), v)
                continue

            if isinstance(v, list):
                sequence = Sequence(v)
                self[k] = sequence
                continue

            assert isinstance(v, dict), (type(v), v)

            if len(v.keys()) == 1:
                shorthand = Shorthand(v)
                self[k] = shorthand
                continue

            choice = Choice(v)
            self[k] = choice
            continue

        assert pj == self, (pj, self)


class Shorthand(dict[str, object]):
    """A Shorthand is Part given a Mentionable Name"""

    def __init__(self, pj: dict[str, object]) -> None:
        super().__init__(pj)

        assert isinstance(pj, dict), (type(pj), pj)

        keys = list(pj.keys())
        assert len(keys) == 1, (len(keys), keys, pj)

        k = keys[-1]
        v = pj[k]

        if isinstance(v, list):
            sequence = Sequence(v)
            self[k] = sequence
            return

        assert isinstance(v, dict), (type(v), v)
        choice = Choice(v)
        self[k] = choice

        assert pj == self, (pj, self)


class Choice(dict[str, object]):
    """A Choice is a Dict of Events guarding Processes"""

    selves: list[Choice] = list()

    eventnames: list[str]

    def __init__(self, pj: dict[str, object]) -> None:
        super().__init__(pj)

        Choice.selves.append(self)

        self.eventnames = list()

        items = list(pj.items())
        if items:
            assert len(items) >= 2, (len(items), pj.keys())

        for k, v in items:

            if isinstance(v, list):
                sequence = Sequence(v)
                self[k] = sequence
                continue

            if isinstance(v, dict):
                assert len(v.keys()) >= 2, (len(v.keys()), v.keys())
                choice = Choice(v)
                self[k] = choice
                continue

            assert isinstance(v, str), (type(v), v)
            self[k] = Mention(v)
            continue

        assert pj == self, (pj, self)


class Sequence(list[object]):
    """A Sequence is a Tuple of Events and a Mention of Shorthand"""

    def __init__(self, pj: list[object]) -> None:
        super().__init__(pj)

        if not pj:
            return

        assert len(pj) >= 2, (len(pj), pj)

        for k, v in enumerate(pj[:-1]):
            assert isinstance(v, str), (type(v), v)
            _v_ = Event(v)
            self[k] = _v_

        index = -1
        tail = pj[index]
        if isinstance(tail, list):
            self[index] = Sequence(tail)
        elif isinstance(tail, str):
            self[index] = Mention(tail)
        else:
            assert isinstance(tail, dict), (type(tail), tail)
            assert len(tail.keys()) > 1, (len(tail.keys()), tail.keys(), tail)
            self[index] = Choice(tail)

        assert pj == self, (pj, self)


class Event(str):
    """An Event has a Name"""


class Mention(str):
    """A Mention is the Name of a Shorthand"""


# ####### ####### ####### ####### ####### ####### ####### ####### ####### #######
# ####### ####### ####### ####### ####### ####### ####### ####### ####### #######
# ####### ####### ####### ####### ####### ####### ####### ####### ####### #######


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


def pathname_read_hash_ymd_version(pathname: str) -> str:
    """Give this revision of this Python Program a Version Date & Name"""

    path = pathlib.Path(pathname)
    mtime = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone()
    ymd_version = mtime.strftime("%Y-%m-%d")

    hash_version = pathname_read_version(pathname)  # '0.15.255'

    str_version = f"{hash_version} (main, {ymd_version})"  # '0.4.39 (main, 2026-05-24)'
    return str_version


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


def eprint(*args: object, end: str = "\n") -> None:
    """Print to Stderr without disordering Stdout"""

    sys.stdout.flush()  # especially when file is not sys.stdout
    print(*args, end=end, file=sys.stderr)
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
# Amp up Import Termios & Import Tty
#


def _sys_sydin_readline_() -> str:
    """Read one Line from Stdin without echo if not Tty, else from Terminal with echo"""

    isatty = sys.stdin.isatty()
    if not isatty:
        readline = sys.stdin.readline()
        return readline

    with TerminalIO() as tty:
        readline = tty.readline()
        return readline


class TerminalIO:

    stdio: typing.TextIO  # sys.__stderr__
    fileno: int  # 2
    tcgetattr: list[int | list[bytes | int]]  # replaced by .__enter__ and by .__exit__

    def __init__(self) -> None:

        assert sys.__stderr__, (sys.__stderr__,)

        stdio = sys.__stderr__
        self.stdio = stdio
        self.fileno = stdio.fileno()
        self.tcgetattr = list()

    def __enter__(self) -> TerminalIO:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        stdio.flush()

        assert not tcgetattr, (tcgetattr,)

        tcgetattr = termios.tcgetattr(fileno)
        assert tcgetattr, (tcgetattr,)
        self.tcgetattr = tcgetattr  # replaces

        tty.setraw(fileno, when=termios.TCSADRAIN)

        return self

    def __exit__(self, *exc_info: object) -> None:

        stdio = self.stdio
        fileno = self.fileno
        tcgetattr = self.tcgetattr

        assert tcgetattr, (tcgetattr,)

        stdio.flush()  # before 'termios.tcsetattr' of TerminalStudio.__exit__

        fd = fileno
        when = termios.TCSADRAIN
        attributes = tcgetattr
        termios.tcsetattr(fd, when, attributes)

        self.tcgetattr = list()  # replaces

    def readline(self) -> str:
        """Read one Line, from fresh Keyboard Entry or Keyboard Editing of History"""

        while True:

            b = self.read_one_byte()

            if b == b"\x03":
                eprint("^C", end="")  # '⌃' != '^'
                raise KeyboardInterrupt()

            if b == b"\x04":
                eprint("^D", end="")  # '⌃' != '^'
                return ""

            if b == b"\x0d" == b"\r":
                eprint("", end="\r\n")
                return "\n"

            # eprint(repr(b), end="\r\n")

    def read_one_byte(self) -> bytes:
        """Read one Byte"""

        fileno = self.fileno

        fd = fileno
        length = 1
        read = os.read(fd, length)

        assert len(read) == 1, (read,)  # todo: test os.read returns empty

        return read


#
# Run from the Shell Command Line, if not imported
#

if __name__ == "__main__":
    main()


# todo: find more todo0:

# todo1: when TerminalIO owned, adopt ⌃ U+2303 Up Arrowhead in place of ^ U+005E Circumflex Accent

# todo2: dream up how to run through, not step through, all the traces of VMC etc
# todo2: think more through when to clear history of walking Choice's at return to top-level


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litpython.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
