#!/usr/bin/env python3

"""
usage: litshell.py [-h] [-V] [-r] [-v] [--sep SEP] [--start START] [BRICK ...]

read/ write the os copy/ paste clipboard buffer, write tty, and write files

positional arguments:
  BRICK                 a brick of the shell pipe

options:
  -h, --help            show this help message and exit
  -V, --version         show version numbers and exit
  -r, --raw-control-ch  write Control Chars to Tty, don't replace with '¤' Currency-Symbol
  -v, --verbose         say more
  --sep SEP             a separator, such as ' ' or ',' or ', '
  --start START         a starting index, such as 0 or 1

quirks:
  separates output same as input, as if you wrote |awk -F$sep -vOFS=$sep

small bricks:
  -  0 1 2 3  F L O T U  a h i j n o r s t u w x  nl pb

memorable bricks:
  append bytes casefold counter cut decode dent eng enumerate expandtabs
  frame head if insert join len lower lstrip max md5 min ord printable
  removeprefix removesuffix reverse rstrip set sha256 shuffle slice
  sort split str strings strip sum tail title unframe upper

alt bricks:
  .enumerate .frame .head .len .max .md5 .min .reverse .sha256 .sort .tail

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
import json
import math
import os
import pathlib
import random
import re
import shutil
import signal
import subprocess
import sys  # doesn't limit launch to >= Oct/2020 Python 3.9
import textwrap
import traceback
import unicodedata

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


_os_environ_get_cloud_shell_ = os.environ.get("CLOUD_SHELL", "")

assert int(0x80 + signal.SIGINT) == 130


class LitSystemExit(SystemExit):
    """Exit with a Nonzero Process Exit Status Return Code, with a Message or not"""

    occasion: object | None

    def __init__(self, code: int, occasion: object | None) -> None:
        super().__init__(code)
        self.occasion = occasion


#
# Run from the Shell Command Line
#


verbose_because = list()


def main() -> None:
    """Run from the Shell Command Line"""

    shg = ShellGopher()
    shg.run_main_argv_minus(sys.argv[1:])

    try:
        shg.compile_pipe_if()
        shg.sketch_pipe()
        shg.run_pipe()
    except LitSystemExit as exc:
        if exc.occasion is not None:
            print(str(exc.occasion), file=sys.stderr)
        sys.exit(exc.code)


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

        y_high, x_wide = (80, 25)
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

        # Take Options & Pos Args in from the Shell Command Line

        parser = self.arg_doc_to_parser(__main__.__doc__ or "")
        ns = self.shell_args_take_in(argv_minus, parser=parser)

        if ns.help:
            parser.print_help()
            sys.exit(0)  # exits 0 after printing Help Doc

        if ns.version:
            pathname = __file__
            path = pathlib.Path(pathname)

            mtime = path.stat().st_mtime
            maware = dt.datetime.fromtimestamp(mtime).astimezone()

            mmmyyyy = maware.strftime("%b/%Y")
            title = "Lit" + path.name.removeprefix("lit").title().replace(".", "·")
            version = pathlib_path_read_version(pathname)

            print(mmmyyyy, title, version)
            sys.exit(0)  # exits 0 after printing Version

        # Run differently because Options & Pos Args

        if ns.verbose:
            verbose_because.append(True)

        for arg in sys.argv[1:]:
            number = str_to_number_if(arg)
            if number is None:
                text = str_removeflanks_if(arg, marks=",./")
                if text is None:
                    if arg.startswith("-") and (arg != "-"):
                        continue

            verbs.append(arg)

            # todo8: tighter discards of Dash and Dash-Dash Options

        if ns.F is not None:  # -F mostly for |pb awk
            if self.sep is None:
                self.sep = str(ns.F)

        if ns.pba is not None:  # -pba mostly for |pb nl
            pass

        if ns.vOFS is not None:  # -vOFS=OFS mostly for |pb awk
            if self.sep is None:
                self.sep = str(ns.vOFS)

        # if ns.v is not None:  # -v=START mostly for |pb nl  # todo7:
        #     if self.start is None:
        #         self.start = int(ns.v, base=0)

        if ns.sep is not None:
            self.sep = str(ns.sep)
        if ns.start is not None:
            self.start = int(ns.start, base=0)

        if ns.raw_control_ch:
            if not ns.raw_control_chars:
                ns.raw_control_chars = 1
            else:
                ns.raw_control_chars += 1

        # todo8: reject conflicts between --sep -F -vOFS

    def arg_doc_to_parser(self, doc: str) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

        # Spell out what --help says

        assert argparse.REMAINDER == "..."
        assert argparse.SUPPRESS == "==SUPPRESS=="
        assert argparse.ZERO_OR_MORE == "*"

        parser = ArgDocParser(doc, add_help=False)

        brick_help = "a brick of the shell pipe"
        parser.add_argument("bricks", metavar="BRICK", nargs="*", help=brick_help)

        help_help = "show this help message and exit"
        raw_control_chars_help = "write Control Chars to Tty, don't replace with '¤' Currency-Symbol"
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

        # Spell out what --help doesn't say

        parser.add_argument("-F", help=argparse.SUPPRESS)  # |pb awk -F/
        parser.add_argument("-pba", action="count", help=argparse.SUPPRESS)  # |pb nl -pba -v0
        parser.add_argument("-vOFS", help=argparse.SUPPRESS)  # |pb awk vOFS=x
        # parser.add_argument("-t", help=argparse.SUPPRESS)  # |pb column -t
        # parser.add_argument("-v", help=argparse.SUPPRESS)  # |pb nl -pba -v0
        parser.add_argument("--raw-control-chars", action="count", help=argparse.SUPPRESS)

        # Succeed

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

            if index == 1:  # todo3: say this more simply - pb could mean __enter__
                if verb in ("cv", "pb"):
                    continue

            if index > 1:
                newborn = bricks[-1]

                dot = verb
                if verb == ".":
                    newborn.posargs += (dot,)
                    continue

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

                # todo8: accept 'None' as a Pos Arg of a Shell Brick ?
                # todo8: declare which Bricks take which Args, compile-time reject TypeError

            brick = self._compile_brick_if_(verb)
            bricks.append(brick)

    def _compile_writing_pbcopy_(self) -> bool:
        """Choose to write into PbCopy at exit, or not"""

        verbs = self.verbs
        sys_stdin_isatty = self.sys_stdin_isatty

        writing_file = self._compile_writing_file_()  # todo2: calculate once, not twice

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
            occasion = f"NameError: name '{verb}' is not defined"
            raise LitSystemExit(code=1, occasion=occasion)  # NameError of a Brick

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

            if verb in ("0", "1", "2", "3", "cv", "pb", "__enter__", "__exit__"):
                continue

            s += " " + repr(doc)

        if verbose_because:  # todo8: remember --verbose could do good things
            print(s, file=sys.stderr)  # todo8: delay trace till after first input

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
            # Hp Calculator  Words
            #
            "eng": self.from_text_eng,
            #
            # Python Single Words working with all the Bytes / Text / Lines, or with each Line
            #
            "decode": self.from_bytes_decode,
            "md5": self.from_bytes_md5,
            "sha256": self.from_bytes_sha256,
            "printable": self.from_bytes_printable,
            #
            "casefold": self.from_text_casefold,  # |F for Fold
            "expandtabs": self.from_text_expandtabs,
            "jq": self.from_text_jq,  # |j
            "lower": self.from_text_lower,  # |L
            "ord": self.from_text_ord,
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
            "enumerate": self.for_line_enumerate,  # like |n or |cat -n but --start=0
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
            ".enumerate": self.for_line_enumerate,  # like |n or |cat -n and with --start=1
            ".cut": self.from_lines_cut,  # as wide as the Screen
            ".frame": self.for_line_do_frame,  # with .rstrip
            ".head": self.from_lines_head,  # as tall as the Screen
            ".jq": self.from_text_jq,  # converts to Python
            ".len": self.for_line_len,  # width of Lines, not length of Lines
            ".max": self.from_lines_number_max,  # by Number not by Str
            ".md5": self.from_bytes_md5,  # Byte Length too, not just Hash
            ".min": self.from_lines_number_min,  # by Number not by Str
            ".nl": self.for_line_enumerate,  # like |nl but --start=1
            ".reverse": self.for_line_reverse,  # reverse Characters in each Line, not all the Lines
            ".sha256": self.from_bytes_sha256,  # Byte Length too, not just Hash
            ".sort": self.from_lines_number_sort,  # by Number not by Str
            ".tail": self.from_lines_tail,  # as tall as the Screen
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
            "expand": self.from_text_expandtabs,  # |pb expandtabs
            "column": self.from_lines_do_columns,
            "columns": self.from_lines_do_columns,
            "cut": self.from_lines_cut,
            "head": self.from_lines_head,  # |h
            "md5sum": self.from_bytes_md5,
            "sha256sum": self.from_bytes_sha256,
            "shuf": self.from_lines_shuffle,  # |pb shuffle
            "strings": self.from_bytes_textruns,  # |LC_ALL=C strings -n 4
            "tail": self.from_lines_tail,  # |t
            "tac": self.from_lines_reverse,  # |r  # |pb reverse
            # "uniq": self.from_lines_uniq,  # differs from our |u  # |LC_ALL=C uniq  # todo8:
            #
            "awk": self.for_line_awk_nth_slice,  # |a
            "nl": self.for_line_enumerate,  # like |.nl but --start=0
            "rev": self.for_line_reverse,
            #
            # Famously Abbreviated Single Character Aliases
            #
            "$": self.for_line_append,
            # "+": self.from_lines_sum,
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
            "j": self.from_text_jq,
            "n": self.for_line_enumerate,  # but defaulting to --start=1
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

        sg = self.shell_gopher
        stdin_isatty = sg.sys_stdin_isatty

        verb = self.verb
        assert verb, (verb,)

        func = self.func
        try:

            func()

        except UnicodeDecodeError as exc:

            if not stdin_isatty:
                texts = traceback.format_exception(exc, limit=0)  # colorize=sys.stderr.isatty()
                assert len(texts) == 1, (texts,)
                raise LitSystemExit(code=1, occasion=texts[0].rstrip())  # UnicodeDecodeError of |pb

            print(f"{verb=}", file=sys.stderr)
            raise  # UnicodeDecodeError from Brick Func while .stdin_isatty

        except Exception:

            print(f"{verb=}", file=sys.stderr)
            raise  # Exception from Brick Func

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
                raise LitSystemExit(code=141, occasion=None)  # 0x80 + signal.SIGPIPE

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
            occasion = f"./{n} file not found"
            raise LitSystemExit(code=1, occasion=occasion)  # pb stack entry not found

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

        assert not run.returncode  # because .check=True

        data = run.stdout

        return data

    def pbcopy(self, data: bytes) -> None:
        """Push Bytes into the Os Copy/Paste Clipboard Buffer"""

        run = subprocess.run(["pbcopy"], input=data, check=True, stdout=subprocess.PIPE)
        assert not run.returncode  # because .check=True

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
        """bytes(sys.i).decode(errors="replace").replace("\ufffd", "¤")"""

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "¤"  # U+00A4 'Currency Sign'

        idata = self.fetch_bytes()

        iotext = idata.decode(errors="replace")
        iotext = iotext.replace(ReplacementCharacter, repl)
        otext = iotext

        self.store_otext(otext)

        # todo8: |pb decode --sep='?'
        # todo8: |pb decode --sep=''
        # todo8: option of |pb printable /?/ and --repl='?' and ='💥' for decode/ printable/ textruns

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
        """Replace with ¤ till decodable, and then till str.isprintable"""  # todo: help as Code

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "¤"  # U+00A4 'Currency Sign'

        idata = self.fetch_bytes()

        iotext = idata.decode(errors="replace")
        iotext = iotext.replace(ReplacementCharacter, repl)

        otext = ""
        for t in iotext:
            if t == "\n":
                otext += t
            elif t.isprintable():
                otext += t
            else:
                otext += repl

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

        n = 4  # todo8: |pb strings -n 4
        regex = (n * r"[ -~]") + r"[ -~]*"  # todo8: |pb strings --of=isprintable

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

    def from_text_eng(self) -> None:
        """replace with chop(_).rjust for _: float in str(sys.i)"""

        itext = self.fetch_itext()
        expandtabs = itext.expandtabs()
        ilines = expandtabs.splitlines()

        olines = list()
        for iline in ilines:

            oline = ""
            for m in re.finditer("[ ]*[^ ]*", string=iline):
                isplit = m.group(0)

                width = len(isplit)
                ident = len(isplit) - len(isplit.lstrip())
                ijust = min(ident, 2)  # 0, 1, or 2

                osplit = isplit
                try:
                    f = float(isplit)
                except ValueError:
                    oline += osplit
                    continue

                iosplit = chop(f)

                osplit = iosplit
                if ijust:
                    osplit = (ijust * " ") + iosplit
                    if (ijust + len(iosplit)) < width:
                        osplit = iosplit.rjust(width)

                oline += osplit

            olines.append(oline)

        self.store_olines(olines)

        # string.printable endswith '\n\r\x0b\x0c' which all do str.splitlines

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

    def from_text_jq(self) -> None:
        """json.dumps(json.loads(str(sys.i)), indent=2)"""

        verb = self.verb

        itext = self.fetch_itext()

        otext = itext
        if itext:
            loads = json.loads(itext)

            otext = json.dumps(loads, indent=2) + "\n"
            if verb in ("j", ".jq"):
                otext = json_dumps_as_py(loads)

        self.store_otext(otext)

    def from_text_lower(self) -> None:
        """str(sys.i).lower()"""

        itext = self.fetch_itext()
        otext = itext.lower()
        self.store_otext(otext)

    def from_text_ord(self) -> None:
        """(ord(_) for _ in str(sys.i))"""

        itext = self.fetch_itext()
        oints = list(ord(_) for _ in itext)
        olines = list(str(_) for _ in oints)
        self.store_olines(olines)

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

    def from_lines_counter(self) -> None:  # diff vs 'def from_lines_set'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_ilines()

        opairs = list(collections.Counter(ilines).items())
        vklines = list(f"{v}\t{k}" for (k, v) in opairs)
        olines = vklines

        self.store_olines(olines)

    def from_lines_cut(self) -> None:
        """list(sys.i)[:72] + ' ...'"""  # todo8: help .cut correctly

        x_wide = self._take_dot_or_posargs_as_x_wide_minus_(default=72, minus=0)
        n = 5 if (x_wide < (5 + 1)) else x_wide - 5  # todo: '|pb cut' for extremely thin Screens

        ilines = self.fetch_ilines()

        olines = list()
        for iline in ilines:
            if len(iline) <= n:
                olines.append(iline)
                continue

            ichop, isuffix = tty_split_after(iline, width=n)

            osuffix = " ..." if isuffix.startswith(" ") else "..."
            oline = ichop + osuffix

            olines.append(oline)

            # takes Negative PosArg in the way of classic Shell '|tail -9'

        self.store_olines(olines)

    def _take_dot_or_posargs_as_x_wide_minus_(self, default: int, minus: int) -> int:
        """Take Default, or a Dot Verb as X Wide minus enough, or Negative PosArg"""

        sg = self.shell_gopher
        x_wide = sg.x_wide
        verb = self.verb
        posargs = self.posargs

        if not posargs:
            n = (x_wide - minus) if verb.startswith(".") else default
        else:
            assert not verb.startswith("."), (verb,)
            option_int = self._take_posargs_as_one_int_()

            assert option_int < 0, (option_int,)
            n = -option_int

        assert n >= 1, (n, x_wide)
        return n

    def _take_posargs_as_one_int_(self) -> int:
        """Take the one Pos Arg as an Int, else raise an Exception"""

        posargs = self.posargs
        assert len(posargs) == 1, (posargs,)
        posarg = posargs[-1]
        assert isinstance(posarg, int), (posarg,)

        return posarg

    def from_lines_do_columns(self) -> None:
        """Justify Text Columns split by Two Spaces or Tabs, and Numeric Columns too"""

        itext = self.fetch_itext()

        # Take in Text Columns split by Two Spaces or Tabs

        iotext = itext.replace("\t", "  ")
        iolines = iotext.splitlines()

        # Split each Line into Columns independently

        textual_by_column_index = collections.defaultdict(bool)

        iorows = list()
        iowide = 0

        for ioline in iolines:

            iorow: list[str] = list()

            iosplits = ioline.split("  ")
            for iosplit in iosplits:
                iowords = iosplit.split()

                for i, ioword in enumerate(iowords):

                    # Take each Numeric Word into its own Column

                    try:
                        _ = float(ioword)
                    except ValueError:

                        # Mark the Text Columns as Text as they grow

                        c = len(iorow)
                        textual_by_column_index[c] = True

                        osplit = " ".join(iowords[i:])
                        iorow.append(osplit)

                        break

                    iorow.append(ioword)

            iorows.append(iorow)
            iowide = max(iowide, len(iorow))

        for iorow in iorows:
            missing = iowide - len(iorow)
            iorow.extend(missing * [""])

        # Transpose and measure Column Width and right-align Numerics but left-align Texts

        iocolumns = zip(*iorows)

        ocolumns = list()
        for c, iocolumn in enumerate(iocolumns):
            ojust = max(len(_) for _ in iocolumn)

            if textual_by_column_index[c]:
                ocolumn = list(_.ljust(ojust) for _ in iocolumn)
            else:
                ocolumn = list(_.rjust(ojust) for _ in iocolumn)

            ocolumns.append(ocolumn)

        # Stitch the Columns back together, separated by Two Spaces (never yet by Tabs)

        orows = zip(*ocolumns)
        olines = list("  ".join(_) for _ in orows)

        # Succeed

        self.store_olines(olines)

    def from_lines_head(self) -> None:
        """list(sys.i)[:9]"""  # todo8: help .head correctly

        n = self._take_dot_or_posargs_as_y_high_minus_(default=9, minus=2)

        ilines = self.fetch_ilines()
        olines = ilines[:n]
        self.store_olines(olines)

    def _take_dot_or_posargs_as_y_high_minus_(self, default: int, minus: int) -> int:
        """Take Default, or a Dot Verb as Y High minus enough, or Negative PosArg"""

        sg = self.shell_gopher
        y_high = sg.y_high
        verb = self.verb
        posargs = self.posargs

        if not posargs:
            n = (y_high - minus) if verb.startswith(".") else default
        else:
            assert not verb.startswith("."), (verb,)
            option_int = self._take_posargs_as_one_int_()

            assert option_int < 0, (option_int,)
            n = -option_int

            # takes Negative PosArg in the way of classic Shell '|head -9'

        assert n >= 1, (n, y_high)
        return n

    def from_lines_int_base_zero_max(self) -> None:
        """max(list(sys.i), key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_based_int, strict=False)
        m = max(zip(*icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_int_base_zero_min(self) -> None:
        """min(list(sys.i), key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_based_int, strict=False)
        m = min(zip(*icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_int_base_zero_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_based_int, strict=False)
        sortables = list(zip(*icolumns, ilines))
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

    def from_lines_len(self) -> None:
        """len(list(sys.i))"""

        ilines = self.fetch_ilines()
        oline = str(len(ilines))
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
        m = max(zip(*icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_min(self) -> None:
        """min(list(sys.i), key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=False)
        m = min(zip(*icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=False)
        sortables = list(zip(*icolumns, ilines))
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
        """sum(list(sys.i)) for each column"""  # todo: help 'for each column' as Code

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=str_to_number, strict=True)
        ocolumns = list(sum(_) for _ in icolumns)
        oline = " ".join(str(_) for _ in ocolumns)

        olines = [oline]
        self.store_olines(olines)

    def from_lines_tail(self) -> None:
        """list(sys.i)[-9:]"""  # todo8: help .tail correctly

        n = self._take_dot_or_posargs_as_y_high_minus_(default=9, minus=2)

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
        """Convert Left Columns of each Str to Floats and Ints and Bools, else raise LitSystemExit"""

        ilines = lines

        if func.__name__ == "str_to_based_int":
            functype = "int"  # |pb int.max, int.min, int.sort
        else:
            assert func.__name__ == "str_to_number", (func.__name__,)
            functype = "float nor int nor bool"  # |pb .max, .min, .sort, sum

        # Require Input Lines when Strict

        if not ilines:
            if strict:
                occasion = "ValueError: No Lines of Columns"
                raise LitSystemExit(code=1, occasion=occasion)  # .sum of no rows

        # Visit each Input Line

        min_width = -1

        irows = list()  # rows
        for i, iline in enumerate(ilines):
            lineno = 1 + i

            # Count out its Number Columns

            isplits = iline.split()

            inumbers: list[float | int | bool] = list()
            for index, isplit in enumerate(isplits):
                try:
                    inumber = func(isplit)
                except ValueError:
                    break
                inumbers.append(inumber)

            # Require one or more Number Columns,
            # and require the same Number of Columns per Line when Strict

            width = len(inumbers)
            if not width:
                occasion = f"ValueError: Line {lineno} has no {functype} Columns"
                raise LitSystemExit(code=1, occasion=occasion)  # .max, .min, .sort, sum of no cols

            elif i == 0:
                min_width = width

            elif not strict:
                min_width = min(min_width, width)

            elif width != min_width:
                occasion = f"ValueError: Line {lineno} has {width} Columns"
                occasion += f", not the {min_width} Columns of Line 1"
                raise LitSystemExit(code=1, occasion=occasion)  # .sum of ragged edge

            irows.append(inumbers)

        assert min_width >= 1, (min_width,)  # because >= 1 Lines visited

        # Pick out the Whole Columns filled by every Line

        ocolumns: list[list[float | int | bool]] = list()  # columns
        for index in range(min_width):

            ocolumn: list[float | int | bool] = list()
            for irow in irows:
                inumber = irow[index]
                ocolumn.append(inumber)  # todo: speedier transposition?

            assert len(ocolumn) == len(ilines), (len(ocolumn), len(ilines))
            ocolumns.append(ocolumn)

        # Succeed

        return ocolumns

    #
    # Work from the File taken as each 1 of N Lines
    #

    def for_line_awk_nth_slice(self) -> None:
        """_.split(sep)[-1]) for _ in list(sys.i) if _.split(sep)"""

        sg = self.shell_gopher
        sep = sg.sep  # .sep may be None
        posargs = self.posargs

        joinable = "  " if (sep is None) else sep  # defaults to Two Spaces

        ilines = self.fetch_ilines()

        indices = [-1]
        if posargs:
            indices = list(int(_) for _ in posargs)

        olines = list()
        for iline in ilines:
            splits = iline.split(sep)  # .sep may be None
            n = len(splits)

            found = False

            owords = list()
            for index in indices:
                index_minus = index - 1

                if index == 0:
                    found = found or bool(splits)
                    owords.extend(splits)
                elif -n < index < 0:
                    found = True
                    oword = splits[index]
                    owords.append(oword)
                elif 0 <= index_minus < n:
                    found = True
                    oword = splits[index_minus]
                    owords.append(oword)
                else:
                    owords.append("")

            if found:
                oline = joinable.join(owords)
                olines.append(oline)

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

        verb = self.verb

        _start_ = 0 if (start is None) else start
        if verb in (".enumerate", "n", ".nl"):
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
# Amp up Import BuiltIns Float and BuiltIns Int
#


Inf = float("inf")  # implicitly also defines -Inf and +Inf

NaN = float("nan")  # actually implies NaN != NaN


def int_chop(i: int) -> str:  # 'chop' as in drop excess precision
    """Find the nearest Int Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    s = str(int(i))  # '-120789'

    _, sign, digits = s.rpartition("-")  # ('', '-', '120789')
    sci = len(digits) - 1  # 5  # scientific power of ten
    eng = 3 * (sci // 3)  # 3  # engineering power of ten

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, i)

    if not eng:
        return s

    assert len(digits) >= 4, (len(digits), eng, sci, digits, i)
    assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, i)

    precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'  # significand, mantissa, multiplier
    nearby = precise[:4]  # '120.'
    worthy = nearby.rstrip("0").rstrip(".")  # '120'  # drops '.' or'.0' or '.00'

    assert "." in nearby, (nearby, precise, eng, sci, digits, i)

    return sign + worthy + "e" + str(eng)  # '-120e3'


_int_chops_ = [
    #
    (0, "0"),
    (99, "99"),
    (999, "999"),
    #
    (9000, "9e3"),  # not '9.00e3'  # not '9e+03'
    (9800, "9.8e3"),  # not '9.0e3'
    (9870, "9.87e3"),
    (9876, "9.87e3"),  # not rounded up to '9.88e3'
    #
]


def _try_int_chops_() -> None:
    for i, lit in _int_chops_:
        assert int_chop(i) == lit, (int_chop(i), lit, i)

        # print(i, lit, f"{i:.3g}")

    # not 9e+03, 9.8e+03, 9.87e+03, 9.88e+03


def chop(f: float) -> str:  # 'chop' as in drop excess precision
    """Find the nearest Float Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    if math.isnan(f):
        return "NaN"  # unsigned as neither positive nor negative
    elif math.isinf(f):
        s = "-Inf" if (f < 0) else "Inf"  # unsigned as positive
        return s

    if not f:
        lit = "-0e0" if (math.copysign(1e0, f) < 0e0) else "0"
        return lit

    s = ("-" + _positive_float_chop_(-f)) if (f < 0) else _positive_float_chop_(f)

    if f == int(f):
        assert int_chop(int(f)) == s, (f, int_chop(int(f)), s)

    return s

    # never says '0' except to mean Float +0e0 and Int 0
    # never ends with '.' nor '.0' nor '.00' nor 'e+0' - values your ink & time properly instead


def _positive_float_chop_(f: float) -> str:
    """Find the nearest Positive Float Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    assert f > 0, (f,)

    # Form the Scientific Notation

    sci = int(math.floor(math.log10(f)))
    precise = f / (10**sci)
    assert 1 <= precise < 10, (precise, f)

    # Choose a Floor, in the way of Engineering Notation,
    # but do round up the distortions introduced by 'mag = f / (10**sci)'

    triple = str(int(100 * precise + 0.000123))  # arbitrary 0.000123
    assert "100" <= triple <= "999", (triple, precise, sci, f)

    eng = 3 * (sci // 3)  # ..., -6, -3, 0, 3, 6, ...

    span = 1 + sci - eng  # 1, 2, or 3
    assert 1 <= span <= 3, (span, triple, precise, eng, sci, f)

    # Stand on the chosen Floor, except never say '.' nor '.0' nor '.00'

    nearby = triple[:span] + "." + triple[span:]
    worthy = nearby.rstrip("0").rstrip(".")  # lacks '.' if had only '.' or'.0' or '.00'

    # And never say 'e0' either

    lit = f"{worthy}e{eng}".removesuffix("e0")  # may lack both '.' and 'e'

    # But never wander far

    alt_f = float(lit)

    diff = f - alt_f
    precision = 10 ** (eng - 3 + span)
    assert diff < precision, (diff, precision, f, alt_f, lit, eng, span, worthy, triple, span, f)

    return lit

    # "{:.3g}".format(9876) and "{:.3g}".format(1006) talk like this but say 'e+0' & round up

    # math.trunc leaps too far, all the way down to the int ceil/ floor


_float_chops_ = [  # not str(f)  # not f"{f:.3g}"  # not f"{f:.3f}"
    #
    (1e-4, "100e-6"),  # not '0.0001'  # not '0.000'
    (1e-3, "1e-3"),  # not '0.001'
    (1.2e-3, "1.2e-3"),  # not '0.0012'  # not '0.001'
    (9.876e-3, "9.87e-3"),  # not '9.88e-3'  # not '0.009876'  # not '0.00988'  # not '0.010'
    (1e-2, "10e-3"),  # not '0.01'  # not '0.010'
    (1e-1, "100e-3"),  # not '0.1'  # not '0.100'
    #
    (1e0, "1"),  # not '1.0'  # not '1.000'
    (1e1, "10"),  # not '10.0'  # not '10.000'
    (1.2e1, "12"),  # not '12.0'  # not '12.000'
    (9.876e1, "98.7"),  # not '98.76'  # not '98.8'  # not '98.760'
    (1e2, "100"),  # not '100.0'  # not '100.000'
    (1.23e2, "123"),  # not '123.0'  # not '123.000'
    (987, "987"),  # not '987.000'
    #
    (1e3, "1e3"),  # not '1000.0'  # not '1e+03'  # not '1000.000'
    #
    (0, "0"),  # not '0.000'
    (0e0, "0"),  # not '0.0'  # not '0.000'
    (-0e0, "-0e0"),  # not '-0.0'  # not '-0.000'  # and never the inequivalent '-0' of f"{-0e0:g}"
    #
    (float("-inf"), "-Inf"),  # not '-inf'
    (float("+inf"), "Inf"),  # not 'inf'
    (float("nan"), "NaN"),  # not 'nan'
    #
]


def _try_float_chops_() -> None:

    float_chops = list()

    for i in range(1000):
        f = float(i)
        lit = str(i)
        float_chop = (f, lit)
        float_chops.append(float_chop)

    float_chops.extend(_float_chops_)

    for f, lit in _float_chops_:
        assert chop(f) == lit, (chop(f), lit, f)

        if f > 0:
            chop_minus_f = chop(-f)
            assert chop_minus_f == (f"-{lit}"), (chop_minus_f, f"-{lit}", f)

        # print(f, lit, f"{f:.3g}", f"{f:.3f}")


# related explorations

_ = """

    ints = list(range(1000))
    strs = list(str(int((_ / 100) * 100)) for _ in ints)
    diffs = list(_ for _ in zip(ints, strs) if str(_[0]) != _[-1])
    len(diffs)  # more than five dozen found

"""

_ = """

    wholes = list(range(1000))
    tenths = list((_ / 10) for _ in range(1000))
    hundredths = list((_ / 100) for _ in range(1000))

    floats = wholes + tenths + hundredths

    strs = list(str(_ / 1) for _ in wholes)
    strs += list(str((_ / 10) * 10) for _ in tenths)
    strs += list(str((_ / 100) * 100) for _ in hundredths)

    diffs = list(_ for _ in zip(floats, strs) if _[0] != float(_[-1]))
    len(diffs)  # 235 found

"""


#
# Amp up Import BuiltIns Str
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
# Amp up Import Json
#


def json_dumps_as_py(j: object) -> str:
    """Print a Python Program that forms a copy of this Object"""

    object_pylines = list()

    if isinstance(j, dict):
        object_pylines.append("j: typing.Any = dict()")
        dict_pylines = json_dumps_items_as_py_lines(j, keys=list())
        object_pylines.extend(dict_pylines)
    else:
        raise NotImplementedError(type(j))

    pylines = list()

    pylines.append("import json")
    if " = textwrap." in "\n".join(object_pylines):  # a little too often
        pylines.append("import textwrap")
    pylines.append("import typing")
    pylines.append("")

    pylines.extend(object_pylines)

    pylines.append("")
    pylines.append("print(json.dumps(j))  # from |pb .jq")

    py = "\n".join(pylines) + "\n"
    return py

    # often agrees with Flake8, Mypy Strict, and:  black --line-length=1001 p.py


def json_dumps_items_as_py_lines(
    j: list[object] | dict[str, object], keys: list[str | int]
) -> list[str]:
    """Print a Python Program that forms a copy of this Dict"""

    q = str_int_quote_as_flat_py

    above = "".join(("[" + q(_) + "]") for _ in keys)

    jitems: list[tuple[str | int, object]] = list()
    if isinstance(j, list):
        jitems = list(enumerate(j))
    else:
        assert isinstance(j, dict), (type(j),)
        jitems = list(j.items())

    pylines = list()
    for k, v in jitems:
        assert isinstance(k, (int, str)), (type(k), keys)
        keys_plus = list(keys) + [k]

        py = f"j{above}[{q(k)}]"

        if isinstance(v, (bool, int, float, type(None))):
            pylines.append(f"{py} = {v}")
            continue

        if isinstance(v, str):
            tall_py = str_quote_as_tall_py_if(v)
            if tall_py:
                for index, pyline in enumerate(tall_py.splitlines()):
                    if index == 0:
                        pylines.append(f"{py} = {pyline}")
                    else:
                        pylines.append(f"{pyline}")
            else:
                pylines.append(f"{py} = {q(v)}")
            continue

        if isinstance(v, list):
            if not v:
                pylines.append(f"{py} = list()")
                continue

            n = len(v)
            pylines.append(f"{py} = {n} * [None]")
            list_pylines = json_dumps_items_as_py_lines(j=v, keys=keys_plus)
            pylines.extend(list_pylines)
            continue

        if isinstance(v, dict):
            pylines.append(f"{py} = dict()")
            dict_pylines = json_dumps_items_as_py_lines(j=v, keys=keys_plus)
            pylines.extend(dict_pylines)
            continue

        raise NotImplementedError(type(v), keys)

    return pylines


def str_quote_as_tall_py_if(s: str) -> str:
    """Quote as TextWrap DeDent Strip if it fits"""

    # Give up a little too often

    if "\n" not in s:
        return ""

    if s != s.lstrip():
        return ""

    if s != s.rstrip():
        return ""

    if '"""' in s:
        return ""

    # Quote by way of >= 1 Unquoted Line-Break's

    dent4 = 4 * " "

    pylines = list()
    pylines.append('textwrap.dedent("""')
    for pyline in s.splitlines():
        pylines.append(f"{dent4}{pyline}")  # could .rstrip, and doesn't
    pylines.append('""").strip()')

    # Succeed

    py = "\n".join(pylines)  # doesn't end with + "\n"
    return py


def str_int_quote_as_flat_py(o: str | int) -> str:
    """Quote like Repr but default to U+0022 Quotation-Mark"""

    r = repr(o)

    if r.startswith("'") and ('"' not in r):
        assert r.endswith("'"), (
            r[-1:],
            r,
        )
        r2 = '"' + r.removeprefix("'").removesuffix("'") + '"'
        return r2

    return r


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
# Amp up Import Tty
#


def tty_len(text: str) -> int:
    """Count the Screen Columns of the Printable Characters of a Text"""

    width = 0
    for t in text:
        if not t.isprintable():  # '\n', or '\t', etc
            continue

        width += 1

        eaw = unicodedata.east_asian_width(t)
        if eaw in ("Fullwidth"[0], "Wide"[0]):
            if not _os_environ_get_cloud_shell_:
                width += 1

    return width

    # guesses that Google Cloud Shell counts each Character as 1 Column


def tty_split_after(text: str, width: int) -> tuple[str, str]:
    """Split a Text after a Width of Columns, after counting each Csi Sequence as 0 Columns wide"""

    csi = "\033["

    # Visit each Character

    chop = ""

    i = 0
    column_x = 1
    while i < len(text):

        # Take what fits

        if column_x >= width:
            suffix = text[i:]
            return (chop, suffix)

        if not text[i:].startswith(csi):
            t = text[i]

            chop += text[i]
            i += len(t)  # takes 1 Character

            column_x += tty_len(t)

            continue

        # Count each Csi Sequence as 0 Screen Columns wide

        chop += csi
        i += len(csi)

        while i < len(text):
            t = text[i]
            code = ord(t)

            if code < 0x20:
                break

            chop += t
            i += len(t)  # takes 1 Character

            if 0x20 <= code < 0x40:
                continue

            break

    suffix = ""

    return (chop, suffix)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# todo's

#

# todo0: .make copies in my ~/bin/Makefile to run it, if no ./Makefile

# todo0: |pb for the grep -H thing of visually group the Hits by File

# todo0: |eng '* 512' '1/_' to alter before reformatting

#

# todo1: .uptime to sh/uptime.py -- to give us --pretty at macOS

# todo1: default output into a 1-page pager of 9 lines - wc counts - chars set sort

# todo1: sh/cal.py --, for to say 3 months at a time
# todo1: sh/cal.py to mention part of year
# todo1: sh/cal.py to mention how to start on Mondays or Sundays
# todo1: sh/cal.py to prefer python3 -m calendar

# todo1: |sh/nl.py --, for to say |nl -pba -v0

# todo1: sh/which.py, finish up how we've begun offline

#

# todo2: finish porting pelavarre/xshverb/ of bin/ k and of bin/ dt ht pq
# todo2: dt as date && date -u && time

# todo2: |pb replace .stale. .fresh.
# todo2: |pb sub .pattern. .repl.

# todo2: |pb translate .from. .to.
# todo2: |pb remove .from.

#

# todo3: 'pb' vs 'pb -' @ pb split sort |fmt -n |sed 's,^,  ,' |pb -; pb
# todo3: dream up some great way to pass Bytes through |pbcopy
# todo3: repro and explain '@' marks on 'ls -l' permissions of tracked Files in local Git Clone

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

#

# todo7: fill out 'pb .' so as to retire 'pq .'

# todo7: add Hp Calculator Words:  fix, sci, ...

# todo7: |pb slice for --sep=None --start=0, still defaulting to NF{$NF}
# todo7: |pb a raises IndexError for slice out of range, such as 4 rather than 4,5 or 4..4
# todo7: |pb a --sep=None --start=1 implied
# todo7: |pb a 2,4,1 is the 2..3  # |pb a 0 --start=1 takes 0 as 1..
# todo7: |pb a 3.. 1..3 -4 2 3 4 0 0..  # |pb a 0 1..  # the 0.. is intact, not a join
# todo7: |pb nl -pba -v1 implied

# todo7: block 0 1 2 3 as verbs after first verbs, take as ints, for |pb awk, for |pb expandtabs
# todo7: but block ints/floats as first verbs
# todo7: signed/ unsigned floats before ints before verbs
# todo7: int ranges 1..4
# todo7: --start=0 for |awk when you want that, else 0 for the whole in between the rest

#

# todo8: mess with what 'pb --' and '|pb --' means

# todo8: pb hexdump, especially for a -C, especially a memorizable 128 glyph set

# todo8: brick helps

# todo8: |pb expandtabs 2
# todo8: confusion in having 'pb --sep=-' work while 'pb split /-/' quietly doesn't
# todo8: |pb textwrap.wrap textwrap.fill or some such
# todo8: |pb fmt ... just to do |fmt, or more a la |fold -sw $W
# todo8: reject -t without |column
# todo8: take -c at |cut, but don't require it, but do reject -c misplaced
# todo8: trace |pb nl as '|nl -pba -v0', and accept the '-pba -v1' as input shline
# todo8: |pb clean up -F$sep vs -F=$sep especially for |pb awk
# todo8: reject -F misplaced
# todo8: reject -v misplaced
# todo8: reject -vOFS= misplaced

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


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
