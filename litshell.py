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
  -  0 1 2 3  F L O T U  a h i n o r s t u w x  pb
  awk bytes casefold chars counter data dent enumerate expandtabs
  float.sort head int.sort join lines len lower lstrip md5sum rev
  reverse rstrip set sha256 shuffle splitlines strip sort str sum tac
  tail title undent upper words

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

# no collision with our sh/ b d e f m v z

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
import random
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
    shg.sketch_pipe()
    shg.run_pipe()

    #

    # todo1: |pb _ like same _ as we have outside

    # todo1: |pb cut ... to |cut -c to fit on screen but with "... " marks
    # todo1: |pb fmt ... just to do |fmt
    # todo1: |pb column ... but default to --sep='  ' for intake
    # todo1: more with 'comm' and 'paste' and ... ?

    # todo1: |pb decode  # replace to \uFFFD Replacement-Character to \x3F Question-Mark '?'
    # todo1: sold as overcomes old macOS Unix flaming out

    # todo1: finish porting pelavarre/xshverb/ of bin/ a j k and of bin/ dt ht pq

    # todo1: take -F and -d as unhelped --sep for |awk
    # todo1: take --seed to repeat random

    #

    # todo1: |pb choice

    # todo1: block 0 1 2 3 as verbs after first verbs, take as ints, for |pb awk, for |pb expandtabs
    # todo1: but block ints/floats as first verbs
    # todo1: signed/ unsigned floats before ints before verbs
    # todo1: int ranges 1..4
    # todo1: --start=0 for |awk when you want that, else 0 for the whole in between the rest

    # todo: default output into a 1-page pager of 9 lines - wc counts - chars set sort

    # todo2: |pb dt datetime struggle to convert input into date/time-stamps
    # todo2: timedelta absolute local """astimezone""
    # todo2: timedelta absolute utc """fromtimestamp""
    # todo2: timedelta relative previous """timedelta"""  # """dt.timedelta(_[0] - _[-1] for _ in zip)"""
    # todo2: timedelta relative t0 """- _[0]"""  # """dt.timedelta(_ - list(sys.i)[0])""
    # todo2: test with our favourite TZ=America/Los_Angeles TZ=Europe/Prague TZ=Asia/Kolkata

    # todo2: |pb range - defaults to 1 2 3
    # todo2: |pb random - defaults to 9 dice - random 100 - random 0 100 1 - head 9 head -9

    # todo8: |pb echo ...
    # todo8: |pb ^ prefix
    # todo8: |pb $ suffix
    # todo8: |pb removeprefix 'prefix'
    # todo8: |pb removesuffix 'prefix'
    # todo8: |pb prefix 'prefix'
    # todo8: |pb suffix 'suffix'
    # todo8: |pb insertprefix 'prefix'
    # todo8: |pb appendsuffix 'suffix'
    # todo8: |sed 's,^,...,'
    # todo8: |sed 's,$,...,'
    # todo8: |'sys.oline = "pre fix" + sys.iline'

    # todo9: + mv 0 ... && pbpaste |pb upper |tee >(pbcopy) >./0


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

        _ = self.shadowing_pbcopy  # checks attribute exists  # type: ignore[unused-ignore]
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
            if verb == "pb":  # todo2: say this more simply - pb could mean __enter__
                continue
            self.compile_brick_if(verb)

        # todo: do surrogate_escape repl ? in the default |pb undent

        # todo: reject --sep without |pb join or |pb split or |pb awk
        # todo: reject --start without |pb enumerate

        # todo: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'

    def compile_brick_if(self, verb: str) -> None:
        """Compile one Brick"""

        bricks = self.bricks

        brick = ShellBrick(self, verb=verb)
        func_name = brick.func_name()

        if not func_name:
            print(f"Unknown Pipe Brick:  {verb!r}", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad Args

        bricks.append(brick)

    def sketch_pipe(self) -> None:
        """Sketch the Pipe as + |pb '...' |pb '...' ..."""

        bricks = self.bricks

        first = bricks[0].func_name()
        brief_by_name = {
            "digit_zero": "0",
            "digit_one": "1",
            "digit_two": "2",
            "digit_three": "3",
            "pipe_enter": "pb",
        }
        brief = brief_by_name[first]

        last = bricks[-1].func_name()
        assert last == "pipe_exit", (last,)

        s = "+ |" + brief
        for brick in bricks[1:-1]:
            func = brick.func
            doc = func.__doc__
            s += " " + repr(doc)

        print(s, file=sys.stderr)

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
    func: collections.abc.Callable[..., None]
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
            "-": self.run_bytes_often_pass,
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
            "data": self.run_bytes_to_ints,  # aka bytes
            "chars": self.run_str_to_texts,  # aka str
            "lines": self.run_list_str_often_pass,
            "words": self.run_str_split,  # aka split
            #
            "expand": self.run_str_expandtabs,
            "reversed": self.run_list_str_reverse,  # |r
            "sorted": self.run_list_str_sort,  # |s
            #
            # Python Single Words
            #
            "bytes": self.run_bytes_to_ints,  # like for wc -c via |bytes len  # aka data
            "counter": self.run_list_str_counter,  # |u
            "dent": self.run_list_str_do_dent,  # |O
            "enumerate": self.run_list_str_enumerate,  # |n  # todo: -v1
            "join": self.run_list_str_join,  # |x
            "len": self.run_list_str_len,  # |w
            "reverse": self.run_list_str_reverse,  # |r
            "shuffle": self.run_list_str_shuffle,  # |r
            "set": self.run_list_str_set,  # |set is the last half of |counter
            "splitlines": self.run_list_str_often_pass,
            "sort": self.run_list_str_sort,  # |s
            "sum": self.run_list_str_sum,
            #
            "lstrip": self.run_list_str_lstrip,
            "rstrip": self.run_list_str_rstrip,
            "strip": self.run_list_str_strip,
            #
            "casefold": self.run_str_casefold,  # |F for Fold
            "expandtabs": self.run_str_expandtabs,
            "lower": self.run_str_lower,  # |L
            "str": self.run_str_to_texts,  # like for wc -m via |str  # aka chars
            "split": self.run_str_split,  # aka words
            "title": self.run_str_title,  # |T
            "undent": self.run_str_do_undent,  # |o
            "upper": self.run_str_upper,  # |U
            #
            # Python Dotted Double Words
            #
            "int.sort": self.run_list_str_int_sort,
            "float.sort": self.run_list_str_float_sort,
            #
            # Bash Single Words
            #
            "md5sum": self.run_bytes_md5sum,
            "sha256": self.run_bytes_sha256,
            #
            # "$": self.run_list_str_suffix,  # |$ ...  # todo8
            # "^": self.run_list_str_prefix,  # |^ ...  # todo8
            "awk": self.run_list_str_awk,  # |a
            "head": self.run_list_str_head,  # |h
            "tail": self.run_list_str_tail,  # |t
            "tac": self.run_list_str_reverse,  # |r
            #
            "rev": self.run_list_str_str_reverse,
            #
        }

        default = self._raise_not_implemented_error_
        func = func_by_verb.get(verb, default)
        self.func = func

    def func_name(self) -> str:
        """Form the Name of the Brick's Func"""

        func = self.func

        name = func.__name__

        name = name.removeprefix("run_str_")
        name = name.removeprefix("run_list_str_")
        name = name.removeprefix("do_")
        name = name.removeprefix("run_")

        name = name.removesuffix("_often_pass")

        if name == "_raise_not_implemented_error_":
            name = ""

        return name

    def _raise_not_implemented_error_(self) -> None:
        """Raise NotImplementedError for the Brick"""

        verb = self.verb
        raise NotImplementedError(verb)

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
        func_name = self.func_name()
        assert func_name, (func_name,)

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
        verbs = sg.verbs
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

        #

        sorted_set_verbs = sorted(set(verbs))

        writing_stdout = False
        if sys_stdin_isatty or (not sys_stdout_isatty):  # pb, pb |, or |pb|  # not |pb
            writing_stdout = True
        if sys_stdout_isatty:
            if not shadowing_pbcopy:
                if sorted_set_verbs not in (["pb"], ["-", "pb"]):
                    writing_stdout = True

        #

        if writing_stdout:

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
        """Fetch the bytes(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        return data

    def run_bytes_to_ints(self) -> None:
        """list(bytes(sys.i))"""

        idata = self.fetch_bytes()
        olines = list(str(_) for _ in idata)  # ['65', '66', '67']
        self.store_list_str(olines)

    def run_bytes_often_pass(self) -> None:
        """bytes(sys.i)"""

        pass

    def run_bytes_md5sum(self) -> None:
        """hashlib.md5(bytes(sys.i)).hexdigest()"""

        idata = self.fetch_bytes()

        h = hashlib.md5()
        h.update(idata)
        lower_nybbles = h.hexdigest()

        olines = [lower_nybbles + "  -"]
        self.store_list_str(olines)

        # d41d8cd98f00b204e9800998ecf8427e  -

    def run_bytes_sha256(self) -> None:
        """hashlib.sha256(bytes(sys.i)).hexdigest()"""

        idata = self.fetch_bytes()

        h = hashlib.sha256()
        h.update(idata)
        lower_nybbles = h.hexdigest()

        olines = [lower_nybbles + "  -"]
        self.store_list_str(olines)

        # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 -

    #
    # Work with the File as List[Str]
    #

    def fetch_list_str(self) -> list[str]:
        """Fetch the list(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        idecode = data.decode()  # may raise UnicodeDecodeError
        ilines = idecode.splitlines()
        return ilines

    def store_list_str(self, lines: list[str]) -> None:
        """Store the list(sys.i)"""

        sg = self.shell_gopher
        otext = ("\n".join(lines) + "\n") if lines else ""
        oencode = otext.encode()  # may raise UnicodeEncodeError

        sg.data = oencode

    def run_list_str_len(self) -> None:
        """len(list(sys.i))"""

        ilines = self.fetch_list_str()
        olines = [str(len(ilines))]
        self.store_list_str(olines)

    def run_list_str_awk(self) -> None:
        """(_.split()[-1] if sep else _.split(sep)[-1]) for _ in list(sys.i)"""

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
        """[""2*""] + list((4*" " + _ + 4*" ") for _ in list(sys.i)) + [2*""]"""

        ilines = self.fetch_list_str()
        width = max(len(_) for _ in ilines) if ilines else 0

        above = 2 * [""]
        ljust = width + 4
        rjust = ljust + 4
        below = 2 * [""]

        olines = above + list(_.ljust(ljust).rjust(rjust) for _ in ilines) + below
        self.store_list_str(olines)

    def run_list_str_counter(self) -> None:  # diff vs 'def run_list_str_set'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_list_str()
        opairs = list(collections.Counter(ilines).items())
        vklines = list(f"{v}\t{k}" for (k, v) in opairs)
        self.store_list_str(vklines)

    def run_list_str_enumerate(self) -> None:
        """enumerate(list(sys.i))"""

        sg = self.shell_gopher
        start = sg.start
        _start_ = 0 if (start is None) else start

        ilines = self.fetch_list_str()
        opairs = list(enumerate(ilines, start=_start_))
        kvlines = list(f"{k}\t{v}" for (k, v) in opairs)
        self.store_list_str(kvlines)

    def run_list_str_float_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: float(..."""

        ilines = self.fetch_list_str()

        min_width = -1

        ilists: list[list[float]] = list()
        for iline in ilines:
            isplits = iline.split()

            ifloats = list()
            for isplit in isplits:
                try:
                    ifloat = float(isplit)  # rejects int literals of base != 10
                except ValueError:
                    break

                ifloats.append(ifloat)

            ilists.append(ifloats)
            min_width = len(ifloats) if (min_width < 0) else min(min_width, len(ifloats))

        assert len(ilists) == len(ilines), (len(ilists), len(ilines))

        if ilists and not min_width:
            print("pb: no float columns to sort", file=sys.stderr)
            sys.exit(1)  # exits 1 for value error in taking up input

        sortables: list[tuple[list[float], str]] = list()
        for ilist, iline in zip(ilists, ilines):
            sortable = (ilist[:min_width], iline)
            sortables.append(sortable)

        sortables.sort()

        olines: list[str] = list(oline for (_, oline) in sortables)
        self.store_list_str(olines)

        # todo: share more Code between .run_list_str_int_sort and .run_list_str_float_sort

    def run_list_str_head(self) -> None:
        """list(sys.i)[:9]"""

        ilines = self.fetch_list_str()
        olines = ilines[:9]
        self.store_list_str(olines)

    def run_list_str_int_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: int(..."""

        ilines = self.fetch_list_str()

        min_width = -1

        ilists: list[list[int]] = list()
        for iline in ilines:
            isplits = iline.split()

            iints = list()
            for isplit in isplits:
                try:
                    iint = int(isplit, base=0)
                except ValueError:
                    break

                iints.append(iint)

            ilists.append(iints)
            min_width = len(iints) if (min_width < 0) else min(min_width, len(iints))

        assert len(ilists) == len(ilines), (len(ilists), len(ilines))

        if ilists and not min_width:
            print("pb: no int columns to sort", file=sys.stderr)
            sys.exit(1)  # exits 1 for value error in taking up input

        sortables: list[tuple[list[int], str]] = list()
        for ilist, iline in zip(ilists, ilines):
            sortable = (ilist[:min_width], iline)
            sortables.append(sortable)

        sortables.sort()

        olines: list[str] = list(oline for (_, oline) in sortables)
        self.store_list_str(olines)

        # todo: share more Code between .run_list_str_float_sort and .run_list_str_int_sort

    def run_list_str_join(self) -> None:
        """sep.join(list(sys.i))"""  # this .sep defaults to " ", not None

        sg = self.shell_gopher
        sep = sg.sep
        _sep_ = "  " if (sep is None) else sep

        ilines = self.fetch_list_str()
        olines = [_sep_.join(ilines)]
        self.store_list_str(olines)

    def run_list_str_lstrip(self) -> None:
        """_.lstrip() for _ in list(sys.i)"""

        ilines = self.fetch_list_str()
        olines = list(_.lstrip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_often_pass(self) -> None:
        """list(sys.i)"""

        self.fetch_str()  # may raise UnicodeDecodeError

    def run_list_str_set(self) -> None:  # diff vs 'def run_list_str_counter'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_list_str()
        klines = list(collections.Counter(ilines).keys())
        self.store_list_str(klines)

    def run_list_str_reverse(self) -> None:
        """list(sys.i).reverse()"""

        iolines = self.fetch_list_str()
        iolines.reverse()
        self.store_list_str(iolines)

    def run_list_str_rstrip(self) -> None:
        """list(_.rstrip() for _ in list(sys.i))"""

        ilines = self.fetch_list_str()
        olines = list(_.rstrip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_shuffle(self) -> None:
        """random.shuffle(list(sys.i))"""

        iolines = self.fetch_list_str()
        random.shuffle(iolines)
        self.store_list_str(iolines)

    def run_list_str_str_reverse(self) -> None:
        """list("".join(reversed(_)) for _ in list(sys.i))"""

        ilines = self.fetch_list_str()
        olines = list("".join(reversed(_)) for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_sort(self) -> None:
        """list(sys.i).sort()"""

        iolines = self.fetch_list_str()
        iolines.sort()
        self.store_list_str(iolines)

    def run_list_str_strip(self) -> None:
        """_.strip() for _ in list(sys.i)"""

        ilines = self.fetch_list_str()
        olines = list(_.strip() for _ in ilines)
        self.store_list_str(olines)

    def run_list_str_sum(self) -> None:
        """sum(list(sys.i))"""

        ilines = self.fetch_list_str()
        istrips = list(_.strip() for _ in ilines)
        itruths = list(_ for _ in istrips if _)

        oint = 0
        if itruths:
            oint = sum(int(_, base=0) for _ in itruths)

        olines = [str(oint)]
        self.store_list_str(olines)

    def run_list_str_tail(self) -> None:
        """list(sys.i)[-9:]"""

        ilines = self.fetch_list_str()
        olines = ilines[-9:]
        self.store_list_str(olines)

    #
    # Work with the File as Str
    #

    def fetch_str(self) -> str:
        """Fetch the str(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        idecode = data.decode()  # may raise UnicodeDecodeError
        return idecode

    def store_str(self, text: str) -> None:
        """Store the str(sys.i)"""

        sg = self.shell_gopher
        oencode = text.encode()  # may raise UnicodeEncodeError

        sg.data = oencode

    def run_str_casefold(self) -> None:
        """str(sys.i).casefold()"""

        itext = self.fetch_str()
        otext = itext.casefold()
        self.store_str(otext)

    def run_str_do_undent(self) -> None:
        """_.rstrip() for _ in textwrap.dedent(str(sys.i)).strip().splitlines()"""

        itext = self.fetch_str()
        otext = textwrap.dedent(itext).strip()
        olines = list(_.rstrip() for _ in otext.splitlines())
        self.store_list_str(olines)

    def run_str_expandtabs(self) -> None:  # todo1: |pb expandtabs 2
        """str(sys.i).expandtabs()"""

        itext = self.fetch_str()
        otext = itext.expandtabs()
        self.store_str(otext)

    def run_str_lower(self) -> None:
        """str(sys.i).lower()"""

        itext = self.fetch_str()
        otext = itext.lower()
        self.store_str(otext)

    def run_str_split(self) -> None:
        """str(sys.i).split(sep)"""  # .sep may be None

        sg = self.shell_gopher
        sep = sg.sep

        itext = self.fetch_str()
        olines = itext.split() if (sep is None) else itext.split(sep)

        self.store_list_str(olines)

    def run_str_title(self) -> None:
        """str(sys.i).title()"""

        itext = self.fetch_str()
        otext = itext.title()
        self.store_str(otext)

    def run_str_to_texts(self) -> None:
        """list(str(sys.i))"""

        itext = self.fetch_str()
        olines = list(itext)
        self.store_list_str(olines)

    def run_str_upper(self) -> None:
        """str(sys.i).upper()"""

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
