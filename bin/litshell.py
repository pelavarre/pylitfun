#!/usr/bin/env python3

"""
usage: litshell.py [-h] [-V] [-r] [-v] [--sep SEP] [--start START] [BRICK ...]

read/ write the os copy/ paste clipboard buffer, write tty, and write files

positional arguments:
  BRICK                 a brick of the shell pipe

options:
  -h, --help            show this help message and exit
  -V, --version         show version numbers and exit
  -r, --raw-control-ch  write Control Chars to Tty, don't replace with '?' Question-Mark
  -v, --verbose         say more
  --sep SEP             a separator, such as ' ' or ',' or ', '
  --start START         a starting index, such as 0 or 1

quirks:
  separates output same as input, as if you wrote |awk -F$sep -vOFS=$sep

small bricks:
  + -  0 1 2 3  F L O T U  a h i n o r s t u w x  nl pb

memorable bricks:
  append bytes casefold counter decode dent enumerate expandtabs frame
  head if insert join len lower lstrip max md5 min printable removeprefix
  removesuffix reverse rstrip set sha256 shuffle slice sort split str
  strings strip sum tail title unframe upper

alt bricks:
  .frame .head .len .max .md5 .min .reverse .sha256 .sort .tail

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

#
# Floods of aliases to forgive slightly creative spelling detailed only below help
#
#   --raw-control-chars exactly like Shell 'less' in place of --raw-control-ch
#
#   expand md5sum nl rev sha256sum shuf tac  # and --start=1 default for |pb nl
#
#   chars lines words  # vs str splitlines split
#   data text  # vs bytes str
#   splitlines  # taken as default
#
#   for.len for.reverse for.reversed for.slice  # vs .min .max .slice .sort
#   int.max int.min int.sort int.sorted float.max float.min float.sort
#   .reversed .sorted reversed sorted int.sorted float.sorted
#
#   counter vs set
#   tac vs rev
#
#   -F$sep  # --sep mainly for |pb awk, but also:  .slice join slice split
#   -vOFS=$sep  # likewise
#   -pba -v$start  # --start mainly for |pb nl, but also:  enumerate
#
#   our Small Bricks don't collide with our sh/ b d e f m v z
#

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import argparse
import collections
import collections.abc  # .collections.abc is not .abc & collections.abc.Callable is not typing.Callable
import dataclasses
import datetime as dt
import difflib
import hashlib
import os
import pathlib
import random
import re
import shutil
import signal
import subprocess
import sys  # doesn't limit launch to >= Oct/2020 Python 3.9
import textwrap

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


#
# Run from the Shell Command Line
#


verbose = list()


def main() -> None:
    """Run from the Shell Command Line"""

    shg = ShellGopher()

    shg.run_main_argv_minus(sys.argv[1:])
    shg.compile_pipe_if()
    shg.sketch_pipe()

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
    raw_control_chars: bool | None  # False means translate Control Chars to ? when writing to Tty

    writing_pbcopy: bool | None  # Writing to PbCopy
    writing_file: bool | None  # Writing to ./0 after writing into |pbcopy
    writing_stdout: bool | None  # Writing to Stdout

    x_wide: int  # count of Terminal Screen Columns, else 25
    y_high: int  # count of Terminal Screen Rows, else 80

    def __init__(self) -> None:

        # Look around

        sys_stdin_isatty = sys.stdin.isatty()  # sampled only once
        sys_stdout_isatty = sys.stdout.isatty()  # likewise, sampled only once

        (y_high, x_wide) = (80, 25)
        try:
            fd = sys.stderr.fileno()
            size = os.get_terminal_size(fd)  # Columns x Lines
            x_wide = size.columns
            y_high = size.lines
        except OSError:
            pass  # todo: log how .get_terminal_size failed

        # Fill out Self

        self.data = None

        self.verbs = list()
        self.sep = None
        self.start = None

        self.bricks = list()
        self.sys_stdin_isatty = sys_stdin_isatty
        self.sys_stdout_isatty = sys_stdout_isatty
        self.raw_control_chars = None

        self.writing_pbcopy = None
        self.writing_file = None
        self.writing_stdout = None

        self.x_wide = x_wide
        self.y_high = y_high

    def run_main_argv_minus(self, argv_minus: list[str]) -> None:  # noqa C901 too complex  # todo2:
        """Compile & run each Option or Positional Argument"""

        verbs = self.verbs

        doc = __main__.__doc__
        assert doc, (doc,)

        parser = self.arg_doc_to_parser(doc)
        ns = self.shell_args_take_in(argv_minus, parser=parser)
        if ns.help:
            parser.print_help()
            sys.exit(0)

        if ns.verbose:
            verbose.append(True)

        for arg in sys.argv[1:]:
            number = str_to_number_if(arg)
            if number is None:
                text = str_removeflanks_if(arg, marks=",./")
                if text is None:
                    if arg.startswith("-") and (arg != "-"):
                        continue

            verbs.append(arg)

            # todo1: tighter discards of Dash and Dash-Dash Options

        if ns.F is not None:  # -F mostly for |pb awk
            if self.sep is None:
                self.sep = str(ns.F)

        if ns.pba is not None:  # -pba mostly for |pb nl
            pass

        if ns.vOFS is not None:  # -vOFS=OFS mostly for |pb awk
            if self.sep is None:
                self.sep = str(ns.vOFS)

        # if ns.v is not None:  # -v=START mostly for |pb nl  # todo0:
        #     if self.start is None:
        #         self.start = int(ns.v, base=0)

        if ns.sep is not None:
            self.sep = str(ns.sep)
        if ns.start is not None:
            self.start = int(ns.start, base=0)

        if ns.raw_control_ch:
            self.raw_control_chars = True

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

        # todo8: reject conflicts between --sep -F -vOFS

    def arg_doc_to_parser(self, doc: str) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

        assert argparse.REMAINDER == "..."
        assert argparse.SUPPRESS == "==SUPPRESS=="
        assert argparse.ZERO_OR_MORE == "*"

        parser = ArgDocParser(doc, add_help=False)

        brick_help = "a brick of the shell pipe"
        parser.add_argument("bricks", metavar="BRICK", nargs="*", help=brick_help)

        help_help = "show this help message and exit"
        raw_control_chars_help = "write Control Chars to Tty, don't replace with '?' Question-Mark"
        version_help = "show version numbers and exit"
        verbose_help = "say more"

        parser.add_argument("-h", "--help", action="count", help=help_help)
        parser.add_argument("-V", "--version", action="count", help=version_help)
        parser.add_argument("-r", "--raw-control-ch", action="count", help=raw_control_chars_help)
        parser.add_argument("-v", "--verbose", action="count", help=verbose_help)

        sep_help = "a separator, such as ' ' or ',' or ', '"
        start_help = "a starting index, such as 0 or 1"
        parser.add_argument("--sep", metavar="SEP", help=sep_help)
        parser.add_argument("--start", metavar="START", help=start_help)

        parser.add_argument("-F", help=argparse.SUPPRESS)
        parser.add_argument("-pba", action="count", help=argparse.SUPPRESS)
        parser.add_argument("-vOFS", help=argparse.SUPPRESS)
        # parser.add_argument("-v", help=argparse.SUPPRESS)  # todo0: -v=START for |pb nl etc
        parser.add_argument("--raw-control-chars", action="count", help=argparse.SUPPRESS)

        return parser

        # ns.raw_control_ch goes to ShellGopher.raw_control_chars
        # alongside ns.raw_control_chars goes to ShellGopher.raw_control_chars

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

    #
    # Make a Shell Pipe by stringing Bricks together in a Line
    #

    def compile_pipe_if(self) -> None:
        """Compile each Brick"""

        verbs = self.verbs
        sys_stdin_isatty = self.sys_stdin_isatty
        bricks = self.bricks

        # Choose what to write at exit

        assert self.writing_pbcopy is None, (self.writing_pbcopy,)
        assert self.writing_file is None, (self.writing_file,)
        assert self.writing_stdout is None, (self.writing_stdout,)

        self.writing_pbcopy = self._compile_writing_pbcopy_()
        self.writing_file = self._compile_writing_file_()
        self.writing_stdout = self._compile_writing_stdout_()

        # Add implied Bricks

        pipe_verbs = list()
        pipe_verbs.append("__enter__")
        pipe_verbs.extend(verbs)

        if not verbs[1:]:
            if sys_stdin_isatty:
                pipe_verbs.append("unframe")

        pipe_verbs.append("__exit__")

        # Compile the plan

        for index, verb in enumerate(pipe_verbs):

            if index == 0:
                assert verb == "__enter__", (verb,)

            if index == 1:
                if verb == "pb":  # todo2: say this more simply - pb could mean __enter__
                    continue

            if index > 1:
                newborn = bricks[-1]

                number = str_to_number_if(verb)  # takes float | int | bool
                if number is not None:
                    newborn.posargs += (number,)
                    continue

                text = str_removeflanks_if(verb, marks=",./")  # takes str
                if text is not None:
                    if index == 2:
                        newborn = self._compile_brick_if_("append")
                        bricks.append(newborn)

                    newborn.posargs += (text,)
                    continue

                # todo0: accept 'None' as a Pos Arg of a Shell Brick ?
                # todo0: declare which Bricks take which Args, compile-time reject TypeError

            brick = self._compile_brick_if_(verb)
            bricks.append(brick)

    def _compile_writing_pbcopy_(self) -> bool:
        """Choose to write into PbCopy at exit, or not"""

        verbs = self.verbs
        sys_stdin_isatty = self.sys_stdin_isatty

        writing_file = self._compile_writing_file_()  # todo: calculate once, not twice

        writing_pbcopy = False
        if writing_file:
            writing_pbcopy = True
        elif (not sys_stdin_isatty) and (not verbs[1:]):  # |pb  # without Args
            writing_pbcopy = True

        return writing_pbcopy

    def _compile_writing_file_(self) -> bool:
        """Choose to write into ./0 at exit, or not"""

        verbs = self.verbs

        writing_file = False
        if verbs:
            verb0 = verbs[0]
            if verb0 in ("0", "1", "2", "3"):
                writing_file = True

        return writing_file

    def _compile_writing_stdout_(self) -> bool:
        """Choose to write into Stdout at exit, or not"""

        verbs = self.verbs
        sys_stdin_isatty = self.sys_stdin_isatty
        sys_stdout_isatty = self.sys_stdout_isatty

        writing_stdout = False

        if sys_stdin_isatty or (not sys_stdout_isatty):
            writing_stdout = True  # not |pb  # pb, pb |, or |pb|

        if sys_stdout_isatty:
            if verbs[1:]:
                writing_stdout = True  # |pb ...

        return writing_stdout

    def _compile_brick_if_(self, verb: str) -> ShellBrick:
        """Compile one Brick"""

        brick = ShellBrick(self, verb=verb)

        if not brick.verb:
            print(f"Unknown Pipe Brick: {verb!r}", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad Args

        return brick

    def sketch_pipe(self) -> None:
        """Sketch the Pipe as + |pb '...' |pb '...' ..."""

        bricks = self.bricks
        verbs = self.verbs

        first = "pb"
        if verbs:
            verb0 = verbs[0]
            if verb0 in ("0", "1", "2", "3"):
                first = verb0

        s = "+ |" + first

        for brick in bricks:
            verb = brick.verb
            func = brick.func

            doc = func.__doc__

            if verb in ("0", "1", "2", "3", "pb", "__enter__", "__exit__"):
                continue

            s += " " + repr(doc)

        if verbose:
            print(s, file=sys.stderr)  # todo1: delay help till after first input

        # doesn't show when inferring 'tee >(pbcopy)' and/or '|pb printable'

    #
    # Run the compiled Shell Pipe
    #

    def run_pipe(self) -> None:
        """Run each Compiled Brick in order"""

        bricks = self.bricks

        for brick in bricks:
            brick.run_as_brick()


class ShellBrick:
    """Run well as 1 Shell Pipe Filter Brick"""

    shell_gopher: ShellGopher
    verb: str
    func: collections.abc.Callable[..., None]
    posargs: tuple[str | float | int | bool, ...]

    #
    # Init
    #

    def __init__(self, shell_gopher: ShellGopher, verb: str) -> None:

        self.shell_gopher = shell_gopher

        func_by_verb = self._form_func_by_verb_()

        default = self._assert_false_
        if verb not in func_by_verb.keys():
            self.verb = ""
            self.func = default
            return

        self.verb = verb

        func = func_by_verb.get(verb, default)
        self.func = func

        self.posargs = tuple()

    def _form_func_by_verb_(self) -> dict[str, collections.abc.Callable[[], None]]:
        """Give one or a few Names to each Shell Pipe Filter Brick"""

        func_by_verb = {
            #
            # Framework
            #
            "__enter__": self.run_pipe_enter_if,
            "__exit__": self.run_pipe_exit,
            #
            # Python Single Words working with all the Bytes / Text / Lines, or with each Line
            #
            "decode": self.from_bytes_decode,
            "md5": self.from_bytes_md5,
            "md5sum": self.from_bytes_md5,
            "sha256": self.from_bytes_sha256,
            "sha256sum": self.from_bytes_sha256,
            "printable": self.from_bytes_printable,
            #
            "casefold": self.from_text_casefold,  # |F for Fold
            "expandtabs": self.from_text_expandtabs,
            "lower": self.from_text_lower,  # |L
            "split": self.from_text_split,  # aka words
            "title": self.from_text_title,  # |T
            "upper": self.from_text_upper,  # |U
            #
            "counter": self.from_lines_counter,  # |u
            "join": self.from_lines_join,  # |x
            "len": self.from_lines_len,  # |w
            "max": self.from_lines_max,
            "min": self.from_lines_min,
            "reverse": self.from_lines_reverse,  # |r
            "reversed": self.from_lines_reverse,  # our ["reversed"] aliases our ["reverse"]
            "shuffle": self.from_lines_shuffle,
            "set": self.from_lines_set,  # |set as the ordered last half of |counter
            "sort": self.from_lines_sort,  # |s
            "sorted": self.from_lines_sort,  # our ["sorted"] aliases our ["sort"]
            "sum": self.from_lines_sum,
            # "list":  # nope
            # "tuple":  # nope
            #
            "append": self.for_line_append,
            "enumerate": self.for_line_enumerate,  # |n  # todo: -v1
            "if": self.for_line_if,
            "insert": self.for_line_insert,
            "lstrip": self.for_line_lstrip,
            "removeprefix": self.for_line_removeprefix,
            "removesuffix": self.for_line_removesuffix,
            "rstrip": self.for_line_rstrip,
            "strip": self.for_line_strip,  # unrelated to Shell "which strip" and "man strip"
            #
            # Python Dotted Double Words
            #
            "for.len": self.for_line_len,
            "for.reverse": self.for_line_reverse,
            "for.reversed": self.for_line_reverse,
            "int.max": self.from_lines_int_base_zero_max,
            "int.min": self.from_lines_int_base_zero_min,
            "int.sort": self.from_lines_int_base_zero_sort,
            "int.sorted": self.from_lines_int_base_zero_sort,
            "float.max": self.from_lines_number_max,
            "float.min": self.from_lines_number_min,
            "float.sort": self.from_lines_number_sort,
            "float.sorted": self.from_lines_number_sort,
            #
            ".frame": self.for_line_do_frame,  # without any ".dent":
            ".head": self.from_lines_head,
            ".len": self.for_line_len,
            ".max": self.from_lines_number_max,
            ".md5": self.from_bytes_md5,
            ".min": self.from_lines_number_min,
            ".reverse": self.for_line_reverse,
            ".sha256": self.from_bytes_sha256,
            ".sort": self.from_lines_number_sort,  # |LC_ALL=C sort
            ".tail": self.from_lines_tail,
            #
            ".md5sum": self.from_bytes_md5,  # not ".md5":
            ".sha256sum": self.from_bytes_sha256,  # not ".sha256":
            ".reversed": self.for_line_reverse,  # not ".reverse":
            ".sorted": self.from_lines_number_sort,  # not ".sort":
            #
            # Python & Shell names for data types of the File, most especially for |pb ... len,
            # tipping the hat to variable names, Shell 'wc' data types, Python result datatypes
            #
            "data": self.from_bytes_as_ints,  # aka bytes
            "text": self.from_text_as_texts,  # aka str
            #
            "bytes": self.from_bytes_as_ints,  # aka data  # 'bytes' is a Python Single Word
            "chars": self.from_text_as_texts,  # aka str
            "lines": self.from_lines_as_lines,  # aka splitlines
            "words": self.from_text_split,  # aka split
            #
            # "split": self.from_text_split,  # already said far above
            "splitlines": self.from_lines_as_lines,  # aka lines
            "str": self.from_text_as_texts,  # aka chars
            #
            # Shell Single Words working with all the Bytes / Lines, or with each Line
            #
            # "md5sum": self.from_bytes_md5,  # already said far above
            # "sha256sum": self.from_bytes_sha256,  # already said far above
            #
            "expand": self.from_text_expandtabs,  # |pb expandtabs
            #
            "head": self.from_lines_head,  # |h
            "shuf": self.from_lines_shuffle,  # |pb shuffle
            "strings": self.from_bytes_textruns,  # |LC_ALL=C strings -n 4
            "tail": self.from_lines_tail,  # |t
            "tac": self.from_lines_reverse,  # |r  # |pb reverse
            # "uniq": self.from_lines_uniq,  # differs from our |u  # |LC_ALL=C uniq  # todo1:
            #
            # "$": self.for_line_suffix,  # |$ ...  # todo8
            # "^": self.for_line_prefix,  # |^ ...  # todo8
            "awk": self.for_line_awk_nth_slice,  # |a
            "nl": self.for_line_enumerate,  # although Shell defaults to --start=1
            "rev": self.for_line_reverse,
            #
            # Famously Abbreviated Single Character Aliases
            #
            "$": self.for_line_append,
            "+": self.from_lines_sum,
            "-": self.from_bytes_as_bytes,
            "^": self.for_line_insert,
            #
            "0": self.enter_as_pick_0th,
            "1": self.enter_as_pick_1th,
            "2": self.enter_as_pick_2th,
            "3": self.enter_as_pick_3th,
            #
            "F": self.from_text_casefold,  # |F for Fold
            "L": self.from_text_lower,
            "O": self.for_line_do_frame,  # |O for Outdent
            "T": self.from_text_title,
            "U": self.from_text_upper,
            #
            "a": self.for_line_awk_nth_slice,
            "h": self.from_lines_head,
            "i": self.from_text_split,
            "n": self.for_line_enumerate,
            "o": self.from_text_do_unframe,  # |o because it rounds off ← ↑ → ↓
            "r": self.from_lines_reverse,
            "s": self.from_lines_sort,
            "t": self.from_lines_tail,
            "u": self.from_lines_counter,  # 'u' for '|uniq' but in the way of |awk '!d[$0]++'
            "w": self.from_lines_len,  # in the way of '|wc -l'
            "x": self.from_lines_join,  # in the way of '|xargs'
            #
            # Names for newer Shell Pipe Filter Bricks
            #
            "dent": self.for_line_do_dent,  # per line without .rstrip
            "frame": self.for_line_do_frame,  # the |O which is not |0
            "unframe": self.from_text_do_unframe,  # |o
            #
        }

        return func_by_verb

    #
    # Run Self as a Shell Pipe Filter Brick
    #

    def run_as_brick(self) -> None:
        """Run Self as a Shell Pipe Filter Brick"""

        verb = self.verb
        assert verb, (verb,)

        func = self.func
        try:
            func()
        except Exception:
            print(f"{verb=}", file=sys.stderr)
            raise

    #
    # Enter & exit entirely outside our Stack of 4 Revisions of the Paste Buffer
    #

    def run_pipe_enter_if(self) -> None:
        """Implicitly enter the Shell Pipe"""

        sg = self.shell_gopher
        writing_file = sg.writing_file
        sys_stdin_isatty = sg.sys_stdin_isatty

        # Actually don't implicitly enter, when explicitly entering

        if writing_file:
            return

        # Else do implicitly enter

        assert sg.data is None, (len(sg.data),)
        assert not sg.writing_file, (sg.writing_file,)

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

        sys_stdout_isatty = sg.sys_stdout_isatty
        raw_control_chars = sg.raw_control_chars

        writing_pbcopy = sg.writing_pbcopy
        writing_file = sg.writing_file
        writing_stdout = sg.writing_stdout

        pdata = sg.data
        assert pdata is not None

        fd = sys.stdout.fileno()

        if writing_pbcopy:
            self.pbcopy(pdata)

        fdata = pdata
        if writing_file:
            path = pathlib.Path(str(0))
            path.write_bytes(fdata)

        if writing_stdout:

            data = pdata
            if sys_stdout_isatty:
                if not raw_control_chars:
                    self.from_bytes_printable()

                    assert sg.data is not None, (sg.data,)
                    data = sg.data

                    # tested by:  echo $' \t\n\r\x0b\x0c' |pb -

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

    def enter_as_pick_1th(self) -> None:
        self._enter_as_pick_n_(1)

    def enter_as_pick_2th(self) -> None:
        self._enter_as_pick_n_(2)

    def enter_as_pick_3th(self) -> None:
        self._enter_as_pick_n_(3)

    def _enter_as_pick_n_(self, n: int) -> None:
        """Push a copy of the Nth Old Revision of the Paste Buffer into the Stack"""

        path = pathlib.Path(str(n))
        if not path.exists():
            print(f"./{n} file not found", file=sys.stderr)
            sys.exit(1)

        data = path.read_bytes()
        self.pbcopy(data)

        self.enter_as_pick_0th()  # todo: forward the .data but not via pbcopy then pbpaste

    def enter_as_pick_0th(self) -> None:
        """Push the Paste Buffer into the Stack"""

        sg = self.shell_gopher
        sys_stdin_isatty = sg.sys_stdin_isatty
        writing_file = sg.writing_file

        self.push_paste_buffers()

        if sys_stdin_isatty:
            data = self.pbpaste()
            sg.data = data

        if not sys_stdin_isatty:  # |pb or |pb|
            data = sys.stdin.buffer.read()
            self.pbcopy(data)
            sg.data = data

        assert writing_file, (writing_file,)

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
    # Decline to work with the File
    #

    def _assert_false_(self) -> None:
        """Raise NotImplementedError for the Brick"""

        verb = self.verb
        assert False, (verb,)  # could be raise NotImplementedError(verb)

    #
    # Work with the File taken as Bytes
    #

    def fetch_bytes(self) -> bytes:
        """Fetch the bytes(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        return data

    def from_bytes_as_ints(self) -> None:
        """list(bytes(sys.i))"""

        idata = self.fetch_bytes()
        olines = list(str(_) for _ in idata)  # ['65', '66', '67']
        self.store_olines(olines)

    def from_bytes_as_bytes(self) -> None:
        """bytes(sys.i)"""

        self.fetch_bytes()  # todo: unneeded

    def from_bytes_decode(self) -> None:
        """bytes(sys.i).decode(errors="replace").replace("\ufffd", "?")"""

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "?"  # todo0:  repl: str = "?"

        idata = self.fetch_bytes()

        iotext = idata.decode(errors="replace")
        iotext = iotext.replace(ReplacementCharacter, repl)
        otext = iotext

        self.store_otext(otext)

        # todo0: default '|pb decode' to "¤"  # --sep='?'  # --sep=''

    def from_bytes_md5(self) -> None:
        """hashlib.md5(bytes(sys.i)).hexdigest()"""

        verb = self.verb

        idata = self.fetch_bytes()

        h = hashlib.md5()
        h.update(idata)
        lower_nybbles = h.hexdigest()

        oline = lower_nybbles
        if verb.startswith("."):
            oline += f"  {len(idata)}"
        oline += "  -"

        olines = [oline]
        self.store_olines(olines)

        # d41d8cd98f00b204e9800998ecf8427e  0  -

    def from_bytes_printable(self) -> None:  # todo: .__doc__ doesn't mention '\n' as printable
        """Replace with ? till decodable, and then till str.isprintable"""  # todo: code up as Code

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD

        idata = self.fetch_bytes()

        iotext = idata.decode(errors="replace")
        iotext = iotext.replace(ReplacementCharacter, "?")

        otext = ""
        for t in iotext:
            if t == "\n":
                otext += t
            elif t.isprintable():
                otext += t
            else:
                otext += "?"

        self.store_otext(otext)

        # runs 'printable' as "\n" or str.isprintable, not precisely just str.isprintable
        # doesn't run 'printable' as found in the 100 characters of string.printable

        # 154_810 == len(list(_ for _ in range(0x10FFFF + 1) if chr(_).isprintable()))  #
        # 959_302 == len(list(_ for _ in range(0x10FFFF + 1) if not chr(_).isprintable()))

    def from_bytes_sha256(self) -> None:
        """hashlib.sha256(bytes(sys.i)).hexdigest()"""

        verb = self.verb

        idata = self.fetch_bytes()

        h = hashlib.sha256()
        h.update(idata)
        lower_nybbles = h.hexdigest()

        oline = lower_nybbles
        if verb.startswith("."):
            oline += f" {len(idata)}"
        oline += "  -"

        olines = [oline]
        self.store_olines(olines)

        # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 0 stdin

    def from_bytes_textruns(self) -> None:
        """textruns(decode(bytes(sys.i), repl="¤"), floor=4, of="ascii")"""

        idata = self.fetch_bytes()

        iotext = idata.decode(errors="replace")

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "¤"  # U+00A4 'Currency Sign'
        iotext = iotext.replace(ReplacementCharacter, repl)

        n = 4  # todo0: |pb strings -n 4
        regex = (n * r"[ -~]") + r"[ -~]*"  # todo0: |pb --of=isprintable

        olines = list()
        for m in re.finditer(regex, string=iotext):
            oline = m.group(0)
            olines.append(oline)

        self.store_olines(olines)

    #
    # Work from the File taken as 1 Str
    #

    def fetch_itext(self) -> str:
        """Fetch the str(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        idecode = data.decode()  # may raise UnicodeDecodeError

        return idecode

    def store_otext(self, otext: str) -> None:
        """Store the str(sys.i)"""

        sg = self.shell_gopher
        oencode = otext.encode()  # may raise UnicodeEncodeError
        sg.data = oencode

    def from_text_casefold(self) -> None:
        """str(sys.i).casefold()"""

        itext = self.fetch_itext()
        otext = itext.casefold()
        self.store_otext(otext)

    def from_text_do_unframe(self) -> None:
        """_.rstrip() for _ in textwrap.dedent(str(sys.i)).strip().splitlines()"""

        itext = self.fetch_itext()
        otext = textwrap.dedent(itext).strip()
        olines = list(_.rstrip() for _ in otext.splitlines())
        self.store_olines(olines)

    def from_text_expandtabs(self) -> None:
        """str(sys.i).expandtabs()"""

        itext = self.fetch_itext()
        otext = itext.expandtabs()
        self.store_otext(otext)

    def from_text_lower(self) -> None:
        """str(sys.i).lower()"""

        itext = self.fetch_itext()
        otext = itext.lower()
        self.store_otext(otext)

    def from_text_split(self) -> None:
        """str(sys.i).split(sep)"""  # .sep may be None

        sg = self.shell_gopher
        sep = sg.sep

        itext = self.fetch_itext()
        olines = itext.split(sep)  # .sep may be None

        self.store_olines(olines)

    def from_text_title(self) -> None:
        """str(sys.i).title()"""

        itext = self.fetch_itext()
        otext = itext.title()
        self.store_otext(otext)

    def from_text_as_texts(self) -> None:
        """list(str(sys.i))"""

        itext = self.fetch_itext()
        olines = list(itext)
        self.store_olines(olines)

    def from_text_upper(self) -> None:
        """str(sys.i).upper()"""

        itext = self.fetch_itext()
        otext = itext.upper()
        self.store_otext(otext)

    #
    # Work from the File taken as 1 List[Str] of Lines
    #

    def fetch_ilines(self) -> list[str]:
        """Fetch the list(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        idecode = data.decode()  # may raise UnicodeDecodeError
        ilines = idecode.splitlines()
        return ilines

    def store_olines(self, olines: list[str]) -> None:
        """Store the list(sys.i)"""

        sg = self.shell_gopher
        otext = ("\n".join(olines) + "\n") if olines else ""
        oencode = otext.encode()  # may raise UnicodeEncodeError

        sg.data = oencode

    def from_lines_len(self) -> None:
        """len(list(sys.i))"""

        ilines = self.fetch_ilines()
        oline = str(len(ilines))
        olines = [oline]
        self.store_olines(olines)

    def from_lines_counter(self) -> None:  # diff vs 'def from_lines_set'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_ilines()

        opairs = list(collections.Counter(ilines).items())
        vklines = list(f"{v}\t{k}" for (k, v) in opairs)
        olines = vklines

        self.store_olines(olines)

    def from_lines_head(self) -> None:
        """list(sys.i)[:9]"""  # todo1: help .head correctly

        n = self._take_dot_or_posargs_as_y_high_(default=9)

        ilines = self.fetch_ilines()
        olines = ilines[:n]
        self.store_olines(olines)

    def _take_dot_or_posargs_as_y_high_(self, default: int) -> int:
        """Take Default, or a Dot Verb as Y High Minus 4, or Negative PosArg"""

        sg = self.shell_gopher
        y_high = sg.y_high
        verb = self.verb
        posargs = self.posargs

        if not posargs:
            n = (y_high - 4) if verb.startswith(".") else default
        else:
            assert not verb.startswith("."), (verb,)
            option_int = self._take_posargs_as_one_int_()

            assert option_int < 0, (option_int,)
            n = -option_int

        assert n >= 1, (n, y_high)
        return n

    def _take_posargs_as_one_int_(self) -> int:
        """Take the one Pos Arg as an Int, else raise an Exception"""

        posargs = self.posargs
        assert len(posargs) == 1, (posargs,)
        posarg = posargs[-1]
        assert isinstance(posarg, int), (posarg,)

        return posarg

    def from_lines_int_base_zero_max(self) -> None:
        """max(list(sys.i), key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_based_int, strict=False)
        m = max(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_int_base_zero_min(self) -> None:
        """min(list(sys.i), key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_based_int, strict=False)
        m = min(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_int_base_zero_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_based_int, strict=False)
        sortables = list(zip(icolumns, ilines))
        sortables.sort()
        olines: list[str] = list(oline for (_, oline) in sortables)

        self.store_olines(olines)

    def from_lines_join(self) -> None:
        """sep.join(list(sys.i))"""  # .sep may be None, then works like " " single Space

        sg = self.shell_gopher
        sep = sg.sep
        _sep_ = "  " if (sep is None) else sep

        ilines = self.fetch_ilines()
        oline = _sep_.join(ilines)
        olines = [oline]
        self.store_olines(olines)

    def from_lines_max(self) -> None:
        """max(list(sys.i))"""

        ilines = self.fetch_ilines()
        oline = max(ilines)
        olines = [oline]
        self.store_olines(olines)

    def from_lines_min(self) -> None:
        """min(list(sys.i))"""

        ilines = self.fetch_ilines()
        oline = min(ilines)
        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_max(self) -> None:
        """max(list(sys.i), key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=False)
        m = max(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_min(self) -> None:
        """min(list(sys.i), key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=False)
        m = min(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=False)
        sortables = list(zip(icolumns, ilines))
        sortables.sort()
        olines: list[str] = list(oline for (_, oline) in sortables)

        self.store_olines(olines)

    def from_lines_as_lines(self) -> None:
        """list(sys.i)"""

        self.fetch_ilines()  # todo: could be .fetch_itext()  # may raise UnicodeDecodeError

    def from_lines_set(self) -> None:  # diff vs 'def from_lines_counter'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_ilines()
        olines = list(collections.Counter(ilines).keys())
        self.store_olines(olines)

    def from_lines_reverse(self) -> None:
        """list(sys.i).reverse()"""

        iolines = self.fetch_ilines()
        iolines.reverse()
        self.store_olines(olines=iolines)

    def from_lines_shuffle(self) -> None:
        """random.shuffle(list(sys.i))"""

        iolines = self.fetch_ilines()
        random.shuffle(iolines)
        self.store_olines(olines=iolines)

    def from_lines_sum(self) -> None:
        """sum(list(sys.i)) for each column"""  # todo: code up 'for each column' as Code

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=True)
        ocolumns = list(sum(_) for _ in icolumns)
        oline = " ".join(str(_) for _ in ocolumns)

        olines = [oline]
        self.store_olines(olines)

    def from_lines_tail(self) -> None:
        """list(sys.i)[-9:]"""  # todo1: help .tail correctly

        n = self._take_dot_or_posargs_as_y_high_(default=9)

        ilines = self.fetch_ilines()
        olines = ilines[-n:]
        self.store_olines(olines)

    #
    # Work from the File taken as Columns at Left and then a Text Remainder
    #

    def _take_number_columns_(
        self,
        lines: list[str],
        func: collections.abc.Callable[[str], float | int | bool],
        strict: bool,
    ) -> list[list[float | int | bool]]:
        """Call Func to convert left of each Str to Floats and Ints"""

        ilines = lines

        if func.__name__ == "str_to_based_int":
            functype = "int"  # |pb int.max, int.min, int.sort
        else:
            assert func.__name__ == "str_to_number", (func.__name__,)
            functype = "float nor int nor bool"  # |pb .max, .min, .sort, sum

        min_width = -1

        irows: list[list[float | int | bool]] = list()  # rows
        for iline in ilines:
            isplits = iline.split()

            inumbers: list[float | int | bool] = list()
            for index, isplit in enumerate(isplits):
                if (min_width != -1) and (index >= min_width):
                    if strict:
                        raise ValueError(f"more than {min_width} columns in some rows")
                    break

                try:
                    inumber = func(isplit)
                except ValueError:
                    if strict:
                        raise  # |pb sum
                    break

                inumbers.append(inumber)

            if (min_width != -1) and (len(inumbers) < min_width):
                if strict:
                    raise ValueError(f"less than {min_width} columns in some rows")

            irows.append(inumbers)
            min_width = len(inumbers) if (min_width == -1) else min(min_width, len(inumbers))

        if lines and (min_width <= 0):
            print(f"pb: no {functype} columns to sort", file=sys.stderr)
            sys.exit(1)  # exits 1 for value error in taking up input

        ocolumns: list[list[float | int | bool]] = list()  # columns
        for index in range(min_width):

            ocolumn: list[float | int | bool] = list()
            for irow in irows:
                inumber = irow[index]
                ocolumn.append(inumber)  # todo: speedier transposition?

            assert len(ocolumn) == len(ilines), (len(ocolumn), len(ilines))
            ocolumns.append(ocolumn)

        return ocolumns

    #
    # Work from the File taken as each 1 of N Lines
    #

    def for_line_awk_nth_slice(self) -> None:
        """_.split(sep)[-1]) for _ in list(sys.i)"""  # .sep may be None

        sg = self.shell_gopher
        sep = sg.sep

        ilines = self.fetch_ilines()

        olines = list()
        for iline in ilines:
            splits = iline.split(sep)  # .sep may be None
            if splits:
                olines.append(splits[-1])

        self.store_olines(olines)

        # as if |awk 'NF{print $NF}'

    def for_line_append(self) -> None:
        """(_ + sep.join(sys.argv[1:])) for _ in list(sys.i)"""  # not _ + sep + sep...

        posargs = self.posargs
        sg = self.shell_gopher
        sep = sg.sep

        _sep_ = "  " if (sep is None) else sep
        splits = [str(_) for _ in posargs] if posargs else ["$"]
        join = _sep_.join(splits)

        ilines = self.fetch_ilines()
        olines = list((_ + join) for _ in ilines)
        self.store_olines(olines)

    def for_line_do_dent(self) -> None:
        """list((4*" " + _) for _ in list(sys.i))"""

        ilines = self.fetch_ilines()
        olines = list((4 * " " + _) for _ in ilines)
        self.store_olines(olines)

    def for_line_do_frame(self) -> None:
        """[""2*""] + list((4*" " + _ + 4*" ") for _ in list(sys.i)) + [2*""]"""

        verb = self.verb

        ilines = self.fetch_ilines()
        width = max(len(_) for _ in ilines) if ilines else 0

        above = 2 * [""]
        ljust = width + 4
        rjust = ljust + 4
        below = 2 * [""]

        olines = above + list(_.ljust(ljust).rjust(rjust) for _ in ilines) + below
        if verb.startswith("."):
            olines = list(_.rstrip() for _ in olines)

        self.store_olines(olines)

    def for_line_enumerate(self) -> None:
        """enumerate(list(sys.i), start=start)"""  # implicitly for _ in list(sys.i)

        sg = self.shell_gopher
        start = sg.start

        _start_ = 0 if (start is None) else start
        if self.verb == "nl":
            _start_ = 1 if (start is None) else start

        ilines = self.fetch_ilines()

        opairs = list(enumerate(ilines, start=_start_))
        kvlines = list(f"{k}\t{v}" for (k, v) in opairs)
        olines = kvlines

        self.store_olines(olines)

    def for_line_if(self) -> None:
        """_ for _ in list(sys.i) if _"""

        ilines = self.fetch_ilines()
        olines = list(_ for _ in ilines if _)
        self.store_olines(olines)

    def for_line_insert(self) -> None:
        """(sep.join(sys.argv[1:]) + _) for _ in list(sys.i)"""  # not _ + sep... + sep

        posargs = self.posargs
        sg = self.shell_gopher
        sep = sg.sep

        _sep_ = "  " if (sep is None) else sep
        splits = [str(_) for _ in posargs] if posargs else [4 * " "]
        join = _sep_.join(splits)

        ilines = self.fetch_ilines()
        olines = list((join + _) for _ in ilines)
        self.store_olines(olines)

        # todo: compare our .for_line_insert vs Python textwrap.indent

    def for_line_len(self) -> None:
        """len(_) for _ in list(sys.i)"""

        ilines = self.fetch_ilines()
        olines = list(str(len(_)) for _ in ilines)
        self.store_olines(olines)

    def for_line_lstrip(self) -> None:
        """_.lstrip() for _ in list(sys.i)"""

        ilines = self.fetch_ilines()
        olines = list(_.lstrip() for _ in ilines)
        self.store_olines(olines)

    def for_line_removeprefix(self) -> None:
        """(_.removeprefix(sys.argv[1]) for _ in list(sys.i)"""

        posargs = self.posargs
        prefix = str(posargs[0])

        ilines = self.fetch_ilines()
        olines = list(_.removeprefix(prefix) for _ in ilines)
        self.store_olines(olines)

    def for_line_removesuffix(self) -> None:
        """(_.removeprefix(sys.argv[1]) for _ in list(sys.i)"""

        posargs = self.posargs
        suffix = str(posargs[0])

        ilines = self.fetch_ilines()
        olines = list(_.removesuffix(suffix) for _ in ilines)
        self.store_olines(olines)

    def for_line_rstrip(self) -> None:
        """list(_.rstrip() for _ in list(sys.i))"""

        ilines = self.fetch_ilines()
        olines = list(_.rstrip() for _ in ilines)
        self.store_olines(olines)

    def for_line_reverse(self) -> None:
        """list("".join(reversed(_)) for _ in list(sys.i))"""

        ilines = self.fetch_ilines()
        olines = list("".join(reversed(_)) for _ in ilines)
        self.store_olines(olines)

    def from_lines_sort(self) -> None:
        """list(sys.i).sort()"""

        iolines = self.fetch_ilines()
        iolines.sort()
        self.store_olines(olines=iolines)

    def for_line_strip(self) -> None:
        """_.strip() for _ in list(sys.i)"""

        ilines = self.fetch_ilines()
        olines = list(_.strip() for _ in ilines)
        self.store_olines(olines)


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
    print_help: collections.abc.Callable[[], None]
    print_usage: collections.abc.Callable[[], None]

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
        self.print_help = parser.print_help
        self.print_usage = parser.print_usage

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
# Amp up Import BuiltIns
#


def str_to_based_int(lit: str) -> int:
    """Call int(_, base=0) but without forcing the Caller to pass in the 0"""

    i = int(lit, base=0)
    return i


def str_to_number_if(lit: str) -> float | int | bool | None:
    """Take a repr(float) or repr(int) or repr(bool) as a float | int | bool, else return None"""

    try:
        number = str_to_number(lit)
    except ValueError:
        return None

    return number


def str_to_number(lit: str) -> float | int | bool:
    """Take a repr(float) or repr(int) or repr(bool) as a float | int | bool"""

    number: float | int | bool

    if lit == "False":
        number = False  # bool
    elif lit == "True":
        number = True  # bool
    else:
        try:
            number = int(lit, base=0)
        except ValueError:
            number = float(lit)  # may raise a new ValueError

    return number


def str_removeflanks_if(lit: str, marks: str) -> str | None:
    """Remove the same Mark once from both ends, else return None"""

    if lit[1:]:
        a = lit[0]
        z = lit[-1]
        if a == z:
            if a in marks:
                return lit[1:-1]

    return None


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


# todo's

#

# todo0: sh/which.py, finish up how we've begun offline

# todo0: confusion in having 'pb --sep=-' work while 'pb split /-/' quietly doesn't

#

# todo0: .jq to give full path find of each object ["top"]["branch"]["leaf"] = 'repr'
# todo0: .jq to create each dict explicitly
# todo0: .head .uniq .sort .tail
# todo0: .make copies in my ~/bin/Makefile to run it, if no ./Makefile

#

# todo0: write pipe-bricks.md in terms of what's too fiddly without them
# todo0: suppose you don't like how your the 'foo' in your shell goes wrong, and you fix it
# todo0: how do you remember where you put the fix, when next you need it again, a week from now
# todo0: well, you can put it nearby
# todo0: like you can put it into => function .od () { echo od ...; }
# todo0: like you can put it into 'foo.py --'
# todo0: and you can mention it at 'foo.py'

# todo0: repro and explain '@' marks on 'ls -l' permissions of tracked Files in local Git Clone

#

# todo0: .uptime to sh/uptime.py -- to give us --pretty at macOS

#

# todo1: sh/cal.py --, for to say 3 months at a time
# todo1: sh/cal.py to mention part of year
# todo1: sh/cal.py to mention how to start on Mondays or Sundays
# todo1: sh/cal.py to prefer python3 -m calendar

# todo1: |sh/nl.py --, for to say |nl -pba -v0
# todo1: default --start=0 for |pb nl because -v1 is nonnegotiable at |cat -n, can't cat -n0
# todo1: trace |pb nl as '|nl -pba -v0', and accept the '-pba -v1' as input shline

#

# todo2: |pb cut ... to |cut -c to fit width on screen but with "... " marks
# todo2: take -c at |cut, but don't require it, but do reject -c misplaced

# todo2: |pb expandtabs 2

# todo2: default output into a 1-page pager of 9 lines - wc counts - chars set sort

#

# todo3: finish porting pelavarre/xshverb/ of bin/ a j k and of bin/ dt ht pq
# todo3: dt as date && date -u && time

#

# todo4: |pb clean up -F$sep vs -F=$sep especially for |pb awk

# todo4: |pb slice for --sep=None --start=0, still defaulting to NF{$NF}
# todo4: |pb a raises IndexError for slice out of range, such as 4 rather than 4,5 or 4..4
# todo4: |pb a --sep=None --start=1 implied
# todo4: |pb a 2,4,1 is the 2..3  # |pb a 0 --start=1 takes 0 as 1..
# todo4: |pb a 3.. 1..3 -4 2 3 4 0 0..  # |pb a 0 1..  # the 0.. is intact, not a join
# todo4: |pb nl -pba -v1 implied

# todo4: block 0 1 2 3 as verbs after first verbs, take as ints, for |pb awk, for |pb expandtabs
# todo4: but block ints/floats as first verbs
# todo4: signed/ unsigned floats before ints before verbs
# todo4: int ranges 1..4
# todo4: --start=0 for |awk when you want that, else 0 for the whole in between the rest

# todo4: |pb replace .stale. .fresh.
# todo4: |pb sub .pattern. .repl.

# todo4: |pb translate .from. .to.
# todo4: |pb remove .from.

#

# todo5: |pb dt datetime struggle to convert input into date/time-stamps
# todo5: timedelta absolute local """astimezone""
# todo5: timedelta absolute utc """fromtimestamp""
# todo5: timedelta relative previous """timedelta"""  # """dt.timedelta(_[0] - _[-1] for _ in zip)"""
# todo5: timedelta relative t0 """- _[0]"""  # """dt.timedelta(_ - list(sys.i)[0])""
# todo5: test with our favourite TZ=America/Los_Angeles TZ=Europe/Prague TZ=Asia/Kolkata
# todo5: pb for work with date/time's as utc floats in order - rel & abs & utc & zone & float

#

# todo6: take --seed as unhelped to repeat random

# todo6: brick helps

# todo6: reject -F misplaced
# todo6: reject -v misplaced
# todo6: reject -vOFS= misplaced

#

# todo7: fill out 'pb .' so as to retire 'pq .'

#

# todo8: mess with what 'pb --' and '|pb --' means

# todo8: pb hexdump, especially for a -C, especially a memorizable 128 glyph set

# todo8: |pb textwrap.wrap textwrap.fill or some such
# todo8: |pb fmt ... just to do |fmt, or more a la |fold -sw $W
# todo8: |pb column ... like' |column -t' but default to --sep='  ' for intake
# todo8: take -t at |column, but don't require it
# todo8: reject -t without |column

# todo8: |wc -L into |pb .len .max, |pb split .len .max

# todo8: dir(str)

# todo8: pb for reorder and transpose arrays of tsv, for split into tsv
# todo8: pb for work with tsv's
# todo8: tables

# todo8: mess around with lineseps of \r \n \r\n
# todo8: mess around with double/ single line spacing of \n or \n\n

# todo8: add |uniq and |uniq -c because it's classic
# todo8: |pb unexpand
# todo8: str.ljust str.rjust str.center
# todo8: |pb choice, vs |pb shuffle head -$N
# todo8: more with 'comm' and 'paste' and ... ?

# todo8: |pb sha256 -  # todo8: who gets the '-' as a pos arg?
# todo8: brief alias for stack peek/ dump at:  grep . ?

# todo8: |1 or |1| and same across 0, 1, 2, 3
# todo8: |pb _ like same _ as we have outside

#

# todo9: adopt the complex -R, --RAW-CONTROL-CHARS from |less, not only the simple -r from |less
# todo9: + mv 0 ... && pbpaste |pb upper |tee >(pbcopy) >./0
# todo9: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'

# todo9: drop the int.max int.min int.sort because float. accepts those inputs?
# todo9: drop all the unhelped verbs?


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
