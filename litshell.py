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
  awk bytes casefold chars counter data dent enumerate expandtabs
  head join lines len lower lstrip reverse rstrip set splitlines strip
  sort str sum tail title undent upper words

examples:
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
    # todo: shg.sketch_pipe() - 9 lines - wc counts - chars set sort
    shg.run_pipe()


class ShellGopher:
    """Init and run, once"""

    data: bytes | None  # 1 Sponge of 1 File of Bytes

    verbs: list[str]  # the brick names from the command line
    sep: str | None  # a separator, such as ' ' or ', '
    start: int | None  # a starting index, such as 0 or 1

    bricks: list[ShellBrick]  # Code that works over the Sponge
    sys_stdin_isatty: bool  # Dev Tty at Stdin means get Input Bytes from PasteBuffer
    sys_stdout_isatty: bool  # Dev Tty at Stdout means write Output Bytes back to PasteBuffer

    shadowing_pbcopy: bool | None  # Writing to ./0 after writing into |pbcopy

    def __init__(self) -> None:

        sys_stdin_isatty = sys.stdin.isatty()  # sampled only once
        sys_stdout_isatty = sys.stdout.isatty()  # likewise, sampled only once

        self.data = None

        self.verbs = list()
        self.sep = None
        self.start = None

        self.bricks = list()
        self.sys_stdin_isatty = sys_stdin_isatty
        self.sys_stdout_isatty = sys_stdout_isatty

        self.shadowing_pbcopy = None

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

        # Choose to end by writing into ./0 after |PbCopy, or not

        shadowing_pbcopy = False
        if verbs:
            verb0 = verbs[0]
            if verb0 in ("0", "1", "2", "3"):
                shadowing_pbcopy = True

        _ = self.shadowing_pbcopy
        self.shadowing_pbcopy = shadowing_pbcopy

        # Choose how to start, how to fill out the middle, how to end

        implied_verbs = list()
        if not shadowing_pbcopy:
            implied_verbs.append("__enter__")

        implied_verbs.extend(verbs)

        if not verbs[1:]:
            implied_verbs.append("undent")

        implied_verbs.append("__exit__")

        # Compile the plan

        for verb in implied_verbs:
            self.compile_brick_if(verb)

        # todo: do surrogate_escape repl ? in the default |pb undent

        # todo: reject --sep without |pb join or |pb split or |pb awk
        # todo: reject --start without |pb enumerate

        # todo: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'

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
            "O": self.run_list_str_do_dent,  # |O for Outdent
            "T": self.run_str_title,
            "U": self.run_str_upper,
            #
            "a": self.run_list_str_awk,
            "h": self.run_list_str_head,
            "i": self.run_str_split,
            "n": self.run_list_str_enumerate,
            "o": self.run_str_do_undent,  # |o because it rounds off ← ↑ → ↓
            "r": self.run_list_str_reverse,
            "s": self.run_list_str_sort,
            "t": self.run_list_str_tail,
            "u": self.run_list_str_counter,  # 'u' for '|uniq' but in the way of |awk '!d[$0]++'
            "w": self.run_list_str_len,  # in the way of '|wc -l'
            "x": self.run_list_str_join,  # in the way of '|xargs'
            #
            # Two Character Aliases
            #
            "pb": self.run_bytes_often_pass,
            #
            # Aliases of three or more Characters
            #
            "data": self.run_bytes_to_ints,
            "chars": self.run_str_to_texts,
            "lines": self.run_list_str_often_pass,
            "words": self.run_str_split,
            #
            "expand": self.run_str_expandtabs,
            "reversed": self.run_list_str_reverse,  # |r
            "sorted": self.run_list_str_sort,  # |s
            #
            # Python Single Words
            #
            "awk": self.run_list_str_awk,  # |a
            "bytes": self.run_bytes_to_ints,  # like for wc -c via |bytes len
            "counter": self.run_list_str_counter,  # |u
            "dent": self.run_list_str_do_dent,  # |O
            "enumerate": self.run_list_str_enumerate,  # |n  # todo: -v1
            "head": self.run_list_str_head,  # |h
            "join": self.run_list_str_join,  # |x
            "len": self.run_list_str_len,  # |w
            "lstrip": self.run_list_str_lstrip,
            "reverse": self.run_list_str_reverse,  # |r
            "rstrip": self.run_list_str_rstrip,
            "set": self.run_list_str_set,  # |set is the last half of |counter
            "splitlines": self.run_list_str_often_pass,
            "strip": self.run_list_str_strip,
            "sort": self.run_list_str_sort,  # |s
            "sum": self.run_list_str_sum,
            "tail": self.run_list_str_tail,  # |t
            #
            "casefold": self.run_str_casefold,  # |F for Fold
            "expandtabs": self.run_str_expandtabs,
            "lower": self.run_str_lower,  # |L
            "str": self.run_str_to_texts,  # like for wc -m via |str
            "title": self.run_str_title,  # |T
            "undent": self.run_str_do_undent,  # |o
            "upper": self.run_str_upper,  # |U
            #
        }

        default_eq_none = None
        func = func_by_verb.get(verb, default_eq_none)
        self.func = func

        # todo: brick helps

        # todo: pb for work with date/time's as utc floats in order - rel & abs & utc & zone & float

        # todo: pb for reorder and transpose arrays of tsv, for split into tsv
        # todo: pb for work with tsv's
        # todo: tables
        # todo: str.ljust str.rjust str.center

        # todo: pb --sep=/ 'a 1 -2 3'
        # todo: pb --alt chars len, --alt v, --alt e

        # todo: dir(str)
        # todo: |pb unexpand
        # todo: pb hexdump

        # todo: pb floats sum
        # todo: pb int max
        # todo: |wc -L into |pb line len max, |pb word len max
        # todo: sys.oline = len(sys.iline)

        # todo: brief alias for stack dump at:  grep . ?

        # todo: 'pb list', 'pb tuple', 'pb pass', ...

    def run_as_brick(self) -> None:
        """Run Self as a Shell Pipe Brick"""

        func = self.func
        assert func

        try:
            func()
        except Exception:
            print(f"{func=}", file=sys.stderr)
            raise

    def run_pipe_enter(self) -> None:
        """Implicitly enter the Shell Pipe"""

        sg = self.shell_gopher
        sys_stdin_isatty = sg.sys_stdin_isatty

        assert sg.data is None, (len(sg.data),)
        assert not sg.shadowing_pbcopy, (sg.shadowing_pbcopy,)

        if sys_stdin_isatty:  # pb, pb |

            data = self.pbpaste()  # yep
            sg.data = data

        if not sys_stdin_isatty:  # |pb or |pb|

            data = sys.stdin.buffer.read()
            self.pbcopy(data)
            sg.data = data

    def run_pipe_exit(self) -> None:
        """Implicitly exit the Shell Pipe"""

        sg = self.shell_gopher
        sys_stdin_isatty = sg.sys_stdin_isatty
        sys_stdout_isatty = sg.sys_stdout_isatty
        shadowing_pbcopy = sg.shadowing_pbcopy

        data = sg.data
        assert data is not None

        fd = sys.stdout.fileno()

        if shadowing_pbcopy or not sys_stdin_isatty:
            self.pbcopy(data)

        if shadowing_pbcopy:
            path = pathlib.Path(str(0))
            path.write_bytes(data)

        if sys_stdin_isatty or (not sys_stdout_isatty):  # pb, pb |, or |pb|  # not |pb

            assert int(0x80 + signal.SIGPIPE) == 141
            try:
                os.write(fd, data)
            except BrokenPipeError:
                sys.exit(141)  # 0x80 + signal.SIGPIPE

            # tested by:  set -o pipefail && seq 123456 |pb && pb |head; echo + exit $?
            # else:  BrokenPipeError: [Errno 32] Broken pipe

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

        path = pathlib.Path(str(n))
        if not path.exists():
            print(f"./{n} file not found", file=sys.stderr)
            sys.exit(1)

        data = path.read_bytes()
        self.pbcopy(data)

        self.run_digit_zero()  # todo: forward the .data but not via pbcopy then pbpaste

        # pb no implicit feedback into pb
        # todo: |1 or |1|

    def run_digit_zero(self) -> None:
        """Push the Paste Buffer into the Stack"""

        sg = self.shell_gopher
        sys_stdin_isatty = sg.sys_stdin_isatty
        shadowing_pbcopy = sg.shadowing_pbcopy

        self.push_paste_buffers()

        if sys_stdin_isatty:
            data = self.pbpaste()
            sg.data = data

        if not sys_stdin_isatty:  # |pb or |pb|
            data = sys.stdin.buffer.read()
            self.pbcopy(data)
            sg.data = data

        assert shadowing_pbcopy, (shadowing_pbcopy,)

    def push_paste_buffers(self) -> None:
        """Push one Empty File into the Stack"""

        # Push the top 3 Cells of the Stack down, but leave them as sparse as they are

        for pathindex in (2, 1, 0):
            to_pathindex = pathindex + 1
            path = pathlib.Path(str(pathindex))
            if path.exists():
                shutil.move(src=str(pathindex), dst=str(to_pathindex))

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
        assert data is not None

        return data

    def run_bytes_to_ints(self) -> None:
        """sys.oints = list(_ for _ in sys.ibytes)"""

        idata = self.fetch_bytes()
        olines = list(str(_) for _ in idata)  # ['65', '66', '67']
        self.store_list_str(olines)

    def run_bytes_often_pass(self) -> None:
        """sys.obytes = sys.ibytes"""

        pass

    #
    # Work with the File as List[Str]
    #

    def fetch_list_str(self) -> list[str]:
        """Fetch the File as List[Str]"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        decode = data.decode()  # may raise UnicodeDecodeError
        lines = decode.splitlines()
        return lines

    def store_list_str(self, lines: list[str]) -> None:
        """Store the File as List[Str]"""

        sg = self.shell_gopher
        text = "\n".join(lines) + "\n"
        encode = text.encode()  # may raise UnicodeEncodeError

        sg.data = encode

    def run_list_str_len(self) -> None:
        """sys.oint = len(sys.ilines)"""

        ilines = self.fetch_list_str()
        olines = [str(len(ilines))]
        self.store_list_str(olines)

    def run_list_str_awk(self) -> None:
        """sys.oline = sys.iline.split(sep)[-1]  # or .split()[-1] without sep"""

        sg = self.shell_gopher
        sep = sg.sep

        ilines = self.fetch_list_str()

        olines = list()
        for iline in ilines:
            splits = iline.split() if (sep is None) else iline.split(sep)
            if splits:
                olines.append(splits[-1])

        self.store_list_str(olines)

    def run_list_str_do_dent(self) -> None:
        """sys.otext = textwrap_dent(sys.itext)"""

        ilines = self.fetch_list_str()
        width = max(len(_) for _ in ilines) if ilines else 0

        above = 2 * [""]
        ljust = width + 4
        rjust = ljust + 4
        below = 2 * [""]

        olines = above + list(_.ljust(ljust).rjust(rjust) for _ in ilines) + below
        self.store_list_str(olines)

    def run_list_str_counter(self) -> None:
        """sys.oitems = collections.Counter(_).items() but flipped to (v, k)"""

        ilines = self.fetch_list_str()
        opairs = list(collections.Counter(ilines).items())
        vklines = list(f"{v}\t{k}" for (k, v) in opairs)
        self.store_list_str(vklines)

    def run_list_str_enumerate(self) -> None:
        """sys.oitems = enumerate(_)"""

        sg = self.shell_gopher
        start = sg.start
        _start_ = 0 if (start is None) else start

        ilines = self.fetch_list_str()
        opairs = list(enumerate(ilines, start=_start_))
        kvlines = list(f"{k}\t{v}" for (k, v) in opairs)
        self.store_list_str(kvlines)

    def run_list_str_head(self) -> None:
        """sys.olines = sys.ilines[:9]"""

        ilines = self.fetch_list_str()
        olines = ilines[:9]
        self.store_list_str(olines)

    def run_list_str_join(self) -> None:
        """sys.olines = [sep.join(sys.ilines)]"""

        sg = self.shell_gopher
        sep = sg.sep
        _sep_ = "  " if (sep is None) else sep

        ilines = self.fetch_list_str()
        olines = [_sep_.join(ilines)]
        self.store_list_str(olines)

    def run_list_str_lstrip(self) -> None:
        """sys.oline = sys.iline.lstrip()"""

        ilines = self.fetch_list_str()
        olines = list(_.lstrip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_often_pass(self) -> None:
        """sys.olines = sys.ilines"""

        self.fetch_str()  # may raise UnicodeDecodeError

    def run_list_str_set(self) -> None:
        """sys.olines = collections.Counter(sys.ilines).keys()"""

        ilines = self.fetch_list_str()
        klines = list(collections.Counter(ilines).keys())
        self.store_list_str(klines)

    def run_list_str_reverse(self) -> None:
        """sys.iolines.reverse()"""

        iolines = self.fetch_list_str()
        iolines.reverse()
        self.store_list_str(iolines)

    def run_list_str_rstrip(self) -> None:
        """sys.oline = sys.iline.lstrip()"""

        ilines = self.fetch_list_str()
        olines = list(_.rstrip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_sort(self) -> None:
        """sys.iolines.sort()"""

        iolines = self.fetch_list_str()
        iolines.sort()
        self.store_list_str(iolines)

    def run_list_str_strip(self) -> None:
        """sys.oline = sys.iline.strip()"""

        ilines = self.fetch_list_str()
        olines = list(_.strip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_sum(self) -> None:
        """sys.oint = sum(sys.iints)"""

        ilines = self.fetch_list_str()
        istrips = list(_.strip() for _ in ilines)
        itruths = list(_ for _ in istrips if _)

        oint = 0
        if itruths:
            oint = sum(int(_, base=0) for _ in itruths)

        olines = [str(oint)]
        self.store_list_str(olines)

    def run_list_str_tail(self) -> None:
        """sys.olines = sys.ilines[-9:]"""

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
        assert data is not None

        decode = data.decode()  # may raise UnicodeDecodeError
        return decode

    def store_str(self, text: str) -> None:
        """Store the File as Str"""

        sg = self.shell_gopher
        encode = text.encode()  # may raise UnicodeEncodeError

        sg.data = encode

    def run_str_casefold(self) -> None:
        """sys.otext = sys.itext.casefold()"""

        itext = self.fetch_str()
        otext = itext.casefold()
        self.store_str(otext)

    def run_str_do_undent(self) -> None:
        """sys.otext = textwrap_undent(sys.itext)"""

        itext = self.fetch_str()
        otext = textwrap.dedent(itext).strip()
        olines = list(_.rstrip() for _ in otext.splitlines())
        self.store_list_str(olines)

    def run_str_expandtabs(self) -> None:
        """sys.otext = sys.itext.expandtabs()"""

        itext = self.fetch_str()
        otext = itext.expandtabs()
        self.store_str(otext)

    def run_str_lower(self) -> None:
        """sys.otext = sys.itext.lower()"""

        itext = self.fetch_str()
        otext = itext.lower()
        self.store_str(otext)

    def run_str_split(self) -> None:
        """sys.olines = sys.itext.split() if (sep is None) else sys.itext.split(sep)"""

        sg = self.shell_gopher
        sep = sg.sep

        itext = self.fetch_str()
        olines = itext.split() if (sep is None) else itext.split(sep)

        self.store_list_str(olines)

    def run_str_title(self) -> None:
        """sys.otext = sys.itext.title()"""

        itext = self.fetch_str()
        otext = itext.title()
        self.store_str(otext)

    def run_str_to_texts(self) -> None:
        """sys.olines = list(sys.itext)"""

        itext = self.fetch_str()
        olines = list(itext)
        self.store_list_str(olines)

    def run_str_upper(self) -> None:
        """sys.otext = sys.itext.upper()"""

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
