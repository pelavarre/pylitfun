#!/usr/bin/env python3

"""
usage: litshell.py [-h] [-V] [--sep SEP] [--start START] [BRICK ...]

greatly abbreviate Shell commands, but do show them in full

positional arguments:
  BRICK          a brick of the shell pipe

options:
  -h, --help     show this help message and exit
  -V, --version  show version numbers and exit
  --sep SEP      a separator, such as ' ' or ',' or ', '
  --start START  a starting index, such as 0 or 1

famous bricks:
  0 1 2 3  F L O T U  a h i n o r s t u w x  pb
  awk bytes chars counter data dent enumerate head join lines len
  reverse reversed set splitlines strip sort sorted sum tail words

examples:1
  cat README.md |pb
  pb |wc -l
  pb str set join
  pb str set sort join
  pb str set sort join --sep=''
  echo Hello Shell Pipe Filter Brick World |pbcopy
  pb
  0
  0 upper
  1
  1
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import collections
import collections.abc  # .collections.abc is not .abc  # typing.Callable isn't here either
import dataclasses
import datetime as dt
import difflib
import hashlib
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import textwrap

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


def main() -> None:
    """Run from the Shell Command Line"""

    shg = ShellGopher()
    shg.run_main_argv_minus(sys.argv[1:])
    shg.compile_pipe_if()
    shg.run_pipe()


class ShellGopher:
    """Init and run, once"""

    data: bytes  # 1 Sponge of 1 File of Bytes

    verbs: list[str]  # the brick names from the command line
    sep: str | None  # a separator, such as ' ' or ', '
    start: int | None  # a starting index, such as 0 or 1

    bricks: list[ShellBrick]  # Code that works over the Sponge
    stacking_revisions: bool  # Stacking means Input from and Output to our Stack of Revisions
    sys_stdin_isatty: bool  # Dev Tty at Stdin means get Input Bytes from PasteBuffer
    sys_stdout_isatty: bool  # Dev Tty at Stdout means write Output Bytes back to PasteBuffer

    def __init__(self) -> None:

        sys_stdin_isatty = sys.stdin.isatty()  # sampled only once
        sys_stdout_isatty = sys.stdout.isatty()  # likewise, sampled only once

        self.data = b""

        self.verbs = list()
        self.sep = None
        self.start = None

        self.bricks = list()
        self.stacking_revisions = False
        self.sys_stdin_isatty = sys_stdin_isatty
        self.sys_stdout_isatty = sys_stdout_isatty

    def arg_doc_to_parser(self, doc: str) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

        assert argparse.REMAINDER == "..."
        assert argparse.ZERO_OR_MORE == "*"

        parser = ArgDocParser(doc, add_help=True)

        brick_help = "a brick of the shell pipe"
        parser.add_argument("bricks", metavar="BRICK", nargs="*", help=brick_help)

        version_help = "show version numbers and exit"
        parser.add_argument("-V", "--version", action="count", help=version_help)

        sep_help = "a separator, such as ' ' or ',' or ', '"
        start_help = "a starting index, such as 0 or 1"
        parser.add_argument("--sep", metavar="SEP", help=sep_help)
        parser.add_argument("--start", metavar="START", help=start_help)

        return parser

    def shell_args_take_in(self, argv_minus: list[str], parser: ArgDocParser) -> argparse.Namespace:
        """Take in the Shell Args: first the Dash Options and then the Positional Args"""

        options = list()
        posargs = list()

        for index, arg in enumerate(argv_minus):
            if arg == "--":
                posargs.extend(argv_minus[index:])
                break

            if arg.startswith("-") and (arg != "-"):
                options.append(arg)
            else:
                posargs.append(arg)

        args = options + posargs
        ns = parser.parse_args_if(args)  # often prints help & exits zero

        return ns

        # ArgParse requires reordering else raises 'error: unrecognized arguments'

    def run_main_argv_minus(self, argv_minus: list[str]) -> None:
        """Compile & run each Option or Positional Argument"""

        verbs = self.verbs

        doc = __main__.__doc__
        assert doc, (doc,)

        parser = self.arg_doc_to_parser(doc)
        ns = self.shell_args_take_in(argv_minus, parser=parser)

        verbs.extend(ns.bricks)

        if ns.sep is not None:
            self.sep = str(ns.sep)
        if ns.start is not None:
            self.start = int(ns.start, base=0)

        if ns.version:
            pathname = __file__
            path = pathlib.Path(pathname)

            mtime = path.stat().st_mtime
            maware = dt.datetime.fromtimestamp(mtime).astimezone()

            mmmyyyy = maware.strftime("%b/%Y")
            title = "Lit" + path.name.removeprefix("lit").title().replace(".", "·")
            version = pathlib_path_read_version(pathname)

            print(mmmyyyy, title, version)
            sys.exit(0)

    #
    # Make a Shell Pipe by stringing Bricks together in a Line
    #

    def compile_pipe_if(self) -> None:
        """Compile each Brick"""

        verbs = self.verbs
        bricks = self.bricks

        if verbs:
            verb0 = verbs[0]
            if verb0 in ("0", "1", "2", "3"):
                self.stacking_revisions = True

        self.compile_brick_if("__enter__")

        for verb in verbs:
            self.compile_brick_if(verb)

        if len(bricks) <= 2:  # default to do the '|pb strip' work
            self.compile_brick_if("strip")

        self.compile_brick_if("__exit__")

        # todo: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'

        # todo: reject --sep without |pb join or |pb split
        # todo: reject --start without |pb enumerate

    def compile_brick_if(self, verb: str) -> None:
        """Compile one Brick"""

        bricks = self.bricks

        brick = ShellBrick(self, verb=verb)
        if not brick.func:
            print(f"Unknown Pipe Brick:  {verb!r}", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad Args

        bricks.append(brick)

    def print_help(self) -> None:
        """Print the Main Doc to Stdout and exit zero, like for '--help'"""

        doc = __main__.__doc__
        assert doc, (doc,)
        text = textwrap.dedent(doc).strip()

        print(text)

    #
    # Run the compiled Shell Pipe
    #

    def run_pipe(self) -> None:
        """Run each Compiled Brick in order"""

        bricks = self.bricks

        for brick in bricks:
            brick.run_as_brick()


class ShellBrick:
    """Say how to call a Shell Verb"""

    shell_gopher: ShellGopher
    func: collections.abc.Callable[..., None] | None
    verb: str

    #
    # Init, enter, & exit
    #

    def __init__(self, shell_gopher: ShellGopher, verb: str) -> None:
        self.shell_gopher = shell_gopher
        self.verb = verb

        func_by_verb = {
            #
            # Framework
            #
            "__enter__": self.run_pipe_enter,
            "__exit__": self.run_pipe_exit,
            #
            # Single Character Aliases
            #
            "0": self.run_digit_zero,
            "1": self.run_digit_one,
            "2": self.run_digit_two,
            "3": self.run_digit_three,
            #
            "F": self.run_str_casefold,  # |F for Fold
            "L": self.run_str_lower,
            "O": self.run_list_str_dent,  # |O for Outdent
            "T": self.run_str_title,
            "U": self.run_str_upper,
            #
            "a": self.run_list_str_awk,
            "h": self.run_list_str_head,
            "i": self.run_str_split,
            "n": self.run_list_str_enumerate,
            "o": self.run_str_undent,  # |o because it rounds off ← ↑ → ↓
            "r": self.run_list_str_reverse,
            "s": self.run_list_str_sort,
            "t": self.run_list_str_tail,
            "u": self.run_list_str_counter,  # 'u' for '|uniq' but in the way of |awk '!d[$0]++'
            "w": self.run_list_str_len,  # in the way of '|wc -l'
            "x": self.run_list_str_join,  # in the way of '|xargs'
            #
            # Two Character Aliases
            #
            "pb": self.run_bytes_pass,
            #
            # Aliases of three or more Characters
            #
            "data": self.run_bytes_list,
            "chars": self.run_str_list,
            "lines": self.run_list_str_pass,
            "reversed": self.run_list_str_reverse,  # |r
            "sorted": self.run_list_str_sort,  # |s
            "words": self.run_str_split,
            #
            # Python Single Words
            #
            "awk": self.run_list_str_awk,  # |a
            "bytes": self.run_bytes_list,  # like for wc -c via |bytes len
            "counter": self.run_list_str_counter,  # |u
            "dent": self.run_list_str_dent,  # |O
            "enumerate": self.run_list_str_enumerate,  # |n  # todo: -v1
            "head": self.run_list_str_head,  # |h
            "join": self.run_list_str_join,  # |x
            "len": self.run_list_str_len,  # |w
            "reverse": self.run_list_str_reverse,  # |r
            "set": self.run_list_str_set,  # |set is the last half of |counter
            "splitlines": self.run_list_str_pass,
            "strip": self.run_list_str_strip,
            "sort": self.run_list_str_sort,  # |s
            "sum": self.run_list_str_sum,
            "tail": self.run_list_str_tail,  # |t
            #
            "casefold": self.run_str_casefold,  # |F for Fold
            "lower": self.run_str_lower,  # |L
            "str": self.run_str_list,  # like for wc -m via |str
            "title": self.run_str_title,  # |T
            "undent": self.run_str_undent,  # |o
            "upper": self.run_str_upper,  # |U
            #
        }

        default_eq_none = None
        func = func_by_verb.get(verb, default_eq_none)
        self.func = func

        # todo1: code up the bin/? from pipe-bricks.md into sh/
        # todo1: and retire those from => ls ../pelavarre/xshverb/bin/?

        # todo1: |pb expand |pb expandtabs

        # todo: pb for work with date/time's as utc floats in order - rel & abs & utc & zone & float

        # todo: pb for reorder and transpose arrays of tsv, for split into tsv

        # todo: brick helps

        # todo: pb --sep=/ 'a 1 -2 3'

        # todo: pb floats sum
        # todo: pb hexdump
        # todo: pb for work with tsv's

        # todo: brief alias for stack dump at:  grep . ?

        # todo: 'pb splitlines set', 'pb list', 'pb tuple', 'pb pass', ...

    def run_as_brick(self) -> None:
        """Run Self as a Shell Pipe Brick"""

        func = self.func
        assert func

        func()

    def run_pipe_enter(self) -> None:
        """Enter the Shell Pipe"""

        sg = self.shell_gopher
        stacking_revisions = sg.stacking_revisions
        sys_stdin_isatty = sg.sys_stdin_isatty

        if stacking_revisions:  # 0 1 2 3
            return

        if sys_stdin_isatty:  # pb, pb |

            # print("+ pbpaste |", file=sys.stderr)
            data = self.pbpaste()  # yep
            sg.data = data

        if not sys_stdin_isatty:  # |pb or |pb|

            # print("+ pbcopy </dev/stdin", file=sys.stderr)
            data = sys.stdin.buffer.read()
            self.pbcopy(data)
            sg.data = data

    def run_pipe_exit(self) -> None:
        """Exit the Shell Pipe"""

        sg = self.shell_gopher
        stacking_revisions = sg.stacking_revisions
        sys_stdin_isatty = sg.sys_stdin_isatty
        sys_stdout_isatty = sg.sys_stdout_isatty

        data = sg.data

        self.pbcopy(data)

        if stacking_revisions:

            path = pathlib.Path(str(0))
            path.write_bytes(data)

        if sys_stdin_isatty or (not sys_stdout_isatty):  # pb, pb |, or |pb|  # not |pb

            fileno = sys.stdout.fileno()
            os.write(fileno, data)

    #
    # Work with our Stack of 4 Revisions of the Paste Buffer
    #

    def run_digit_one(self) -> None:
        self._run_digit_n_(1)

    def run_digit_two(self) -> None:
        self._run_digit_n_(2)

    def run_digit_three(self) -> None:
        self._run_digit_n_(3)

    def _run_digit_n_(self, n: int) -> None:
        """Push a copy of the Nth Old Revision of the Paste Buffer into the Stack"""

        # print(f"+ cat {n} |pbcopy", file=sys.stderr)
        path = pathlib.Path(str(n))
        data = path.read_bytes()
        self.pbcopy(data)

        self.run_digit_zero()

        # todo: |1 or |1|

    def run_digit_zero(self) -> None:
        """Push the Paste Buffer into the Stack"""

        sg = self.shell_gopher
        sys_stdin_isatty = sg.sys_stdin_isatty

        # print("+ mv 2 3 && mv 1 2 && mv 0 1 && touch 0", file=sys.stderr)
        self.push_paste_buffers()

        if sys_stdin_isatty:
            # print("+ pbpaste |", file=sys.stderr)
            data = self.pbpaste()
            sg.data = data

        if not sys_stdin_isatty:  # |pb or |pb|

            # print("+ pbcopy </dev/stdin", file=sys.stderr)
            data = sys.stdin.buffer.read()
            self.pbcopy(data)
            sg.data = data

    def push_paste_buffers(self) -> None:
        """Push one Empty File into the Stack"""

        # Bring the 4 Cells of the Stack into existence, if need be

        for pathindex in (3, 2, 1, 0):
            path = pathlib.Path(str(pathindex))
            if not path.exists():
                path.write_text("")

        # Keep 3 Cells of the Stack

        for pathindex in (3, 2, 1):
            from_pathindex = pathindex - 1
            shutil.move(src=str(from_pathindex), dst=str(pathindex))

        # Push an one Empty File

        path = pathlib.Path(str(0))
        path.write_text("")

    def pbpaste(self) -> bytes:
        """Pull Bytes from the Os Copy/Paste Clipboard Buffer"""

        run = subprocess.run(
            ["pbpaste"], stdin=subprocess.DEVNULL, check=True, stdout=subprocess.PIPE
        )

        returncode = run.returncode
        if returncode:
            print(f"+ pbpaste + exit {returncode}", file=sys.stderr)
            sys.exit(returncode)

        data = run.stdout

        return data

    def pbcopy(self, data: bytes) -> None:
        """Push Bytes into the Os Copy/Paste Clipboard Buffer"""

        run = subprocess.run(["pbcopy"], input=data, check=True, stdout=subprocess.PIPE)

        returncode = run.returncode
        if returncode:
            print(f"+ pbcopy + exit {returncode}", file=sys.stderr)
            sys.exit(returncode)

    #
    # Work with the File as Bytes
    #

    def fetch_bytes(self) -> bytes:
        """Fetch the File as Bytes"""

        sg = self.shell_gopher
        data = sg.data

        return data

    def run_bytes_list(self) -> None:
        """Unabbreviate & run list(bytes(_))"""

        # print("|bytes.list", file=sys.stderr)

        idata = self.fetch_bytes()
        olines = list(str(_) for _ in idata)  # ['65', '66', '67']
        self.store_list_str(olines)

    def run_bytes_pass(self) -> None:
        """Unabbreviate & run bytes(data)"""

        # print("|bytes.pass", file=sys.stderr)

    #
    # Work with the File as List[Str]
    #

    def fetch_list_str(self) -> list[str]:
        """Fetch the File as List[Str]"""

        sg = self.shell_gopher
        data = sg.data

        decode = data.decode()  # may raise UnicodeDecodeError
        lines = decode.splitlines()
        return lines

    def store_list_str(self, lines: list[str]) -> None:
        """Store the File from List[Str]"""

        sg = self.shell_gopher
        text = "\n".join(lines) + "\n"
        encode = text.encode()  # may raise UnicodeEncodeError

        sg.data = encode

    def run_list_str_len(self) -> None:
        """Unabbreviate & run len(_)"""

        # print("|list.str.len", file=sys.stderr)

        ilines = self.fetch_list_str()
        olines = [str(len(ilines))]
        self.store_list_str(olines)

    def run_list_str_awk(self) -> None:
        """Unabbreviate & run |awk 'NF{print $NF}'"""

        # print("|list.str.awk", file=sys.stderr)

        ilines = self.fetch_list_str()

        olines = list()
        for line in ilines:
            splits = line.split()
            if splits:
                olines.append(splits[-1])

        self.store_list_str(olines)

    def run_list_str_dent(self) -> None:
        """Add four Columns and two Rows of Blank Spaces, no matter if already present or not"""

        # print("|list.str.dent", file=sys.stderr)

        ilines = self.fetch_list_str()
        width = max(len(_) for _ in ilines) if ilines else 0

        above = 2 * [""]
        ljust = width + 4
        rjust = ljust + 4
        below = 2 * [""]

        olines = above + list(_.ljust(ljust).rjust(rjust) for _ in ilines) + below
        self.store_list_str(olines)

    def run_list_str_counter(self) -> None:
        """Unabbreviate & run list(collections.Counter(_).items())"""

        # print("|list.str.collections.Counter", file=sys.stderr)

        ilines = self.fetch_list_str()
        opairs = list(collections.Counter(ilines).items())
        vklines = list(f"{v}\t{k}" for (k, v) in opairs)
        self.store_list_str(vklines)

    def run_list_str_enumerate(self) -> None:
        """Unabbreviate & run list(enumerate(_))"""

        # print("|list(enumerate(_))", file=sys.stderr)

        sg = self.shell_gopher
        start = sg.start
        _start_ = 0 if (start is None) else start

        ilines = self.fetch_list_str()
        opairs = list(enumerate(ilines, start=_start_))
        kvlines = list(f"{k}\t{v}" for (k, v) in opairs)
        self.store_list_str(kvlines)

    def run_list_str_head(self) -> None:
        """Unabbreviate & run _[:9]"""

        # print("|list.str.head", file=sys.stderr)

        ilines = self.fetch_list_str()
        olines = ilines[:9]
        self.store_list_str(olines)

    def run_list_str_join(self) -> None:
        """Unabbreviate & run str.join(_)"""

        sg = self.shell_gopher
        sep = sg.sep
        _sep_ = "  " if (sep is None) else sep

        # print("|str.join", file=sys.stderr)

        ilines = self.fetch_list_str()
        olines = [_sep_.join(ilines)]
        self.store_list_str(olines)

    def run_list_str_pass(self) -> None:
        """Unabbreviate & run list(str(_))"""

        # print("|list.str.pass", file=sys.stderr)

    def run_list_str_set(self) -> None:
        """Unabbreviate & run set-like list(collections.Counter(_).keys())"""

        ilines = self.fetch_list_str()
        vlines = list(collections.Counter(ilines).keys())
        self.store_list_str(vlines)

    def run_list_str_reverse(self) -> None:
        """Unabbreviate & run _.reverse()"""

        # print("|list.str.reverse", file=sys.stderr)

        iolines = self.fetch_list_str()
        iolines.reverse()
        self.store_list_str(iolines)

    def run_list_str_sort(self) -> None:
        """Unabbreviate & run _.sort()"""

        # print("|list.str.sort", file=sys.stderr)

        iolines = self.fetch_list_str()
        iolines.sort()
        self.store_list_str(iolines)

    def run_list_str_strip(self) -> None:
        """Unabbreviate & run _.strip()"""

        # print("|list.str.strip", file=sys.stderr)

        ilines = self.fetch_list_str()
        olines = list(_.strip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_sum(self) -> None:
        """Unabbreviate & run sum(_)"""

        ilines = self.fetch_list_str()
        istrips = list(_.strip() for _ in ilines)
        itruths = list(_ for _ in istrips if _)

        oint = 0
        if itruths:
            oint = sum(int(_, base=0) for _ in itruths)

        olines = [str(oint)]
        self.store_list_str(olines)

    def run_list_str_tail(self) -> None:
        """Unabbreviate & run _[:9]"""

        # print("|list.str.tail", file=sys.stderr)

        ilines = self.fetch_list_str()
        olines = ilines[-9:]
        self.store_list_str(olines)

    #
    # Work with the File as Str
    #

    def fetch_str(self) -> str:
        """Fetch the File as Str"""

        sg = self.shell_gopher
        data = sg.data

        decode = data.decode()  # may raise UnicodeDecodeError
        return decode

    def store_str(self, text: str) -> None:
        """Store the File from Str"""

        sg = self.shell_gopher
        encode = text.encode()  # may raise UnicodeEncodeError

        sg.data = encode

    def run_str_casefold(self) -> None:
        """Unabbreviate & run str.casefold(_)"""

        # print("|str.casefold", file=sys.stderr)

        itext = self.fetch_str()
        otext = itext.casefold()
        self.store_str(otext)

    def run_str_list(self) -> None:
        """Unabbreviate & run list(str(_))"""

        # print("|str.list", file=sys.stderr)

        itext = self.fetch_str()
        olines = list(itext)
        self.store_list_str(olines)

    def run_str_lower(self) -> None:
        """Unabbreviate & run str.lower(_)"""

        # print("|str.lower", file=sys.stderr)

        itext = self.fetch_str()
        otext = itext.lower()
        self.store_str(otext)

    def run_str_split(self) -> None:
        """Unabbreviate & run str.split(_)"""

        sg = self.shell_gopher
        sep = sg.sep

        # print("|str.split", file=sys.stderr)

        itext = self.fetch_str()

        if sep is None:
            olines = itext.split()
        else:
            olines = itext.split(sep)

        self.store_list_str(olines)

    def run_str_title(self) -> None:
        """Unabbreviate & run str.title(_)"""

        # print("|str.title", file=sys.stderr)

        itext = self.fetch_str()
        otext = itext.title()
        self.store_str(otext)

    def run_str_undent(self) -> None:
        """Strip leading & trailing Blank Rows & Columns, and trailing Blanks from each Row"""

        # print("|str.undent", file=sys.stderr)

        itext = self.fetch_str()
        otext = textwrap.dedent(itext).strip()
        olines = list(_.rstrip() for _ in otext.splitlines())
        self.store_list_str(olines)

    def run_str_upper(self) -> None:
        """Unabbreviate & run str.upper(_)"""

        # print("|str.upper", file=sys.stderr)

        itext = self.fetch_str()
        otext = itext.upper()
        self.store_str(otext)


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
# Amp up Import PathLib
#


def pathlib_path_read_version(pathname: str) -> str:
    """Hash the Bytes of a File down to a purely Decimal $Major.$Minor.$Micro Version Str"""

    path = pathlib.Path(pathname)
    path_bytes = path.read_bytes()

    hasher = hashlib.md5()
    hasher.update(path_bytes)
    hash_bytes = hasher.digest()

    str_hash = hash_bytes.hex()
    str_hash = str_hash.upper()  # such as 32 nybbles 'C24931F77721476EF76D85F3451118DB'

    major = 0
    minor = int(str_hash[0], base=0x10)  # 0..15
    micro = int(str_hash[1:][:2], base=0x10)  # 0..255

    version = f"{major}.{minor}.{micro}"
    return version

    # 0.15.255


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
