#!/usr/bin/env python3

"""
usage: litshell.py [-h] [-V] [-v] [-r] [--sep SEP] [--start START] [WORD ...]

read/ write the os copy/ paste clipboard buffer, write tty, and write files

positional arguments:
  WORD                  a brick or string or number, to build a sponge pipe with

options:
  -h, --help            show this help message and exit
  -V, --version         show version numbers and exit
  -v, --verbose         say more
  -r, --raw-control-ch  write Control Chars to Tty, don't replace with '¤' Currency-Symbol
  --sep SEP             an input or output separator, such as ' ' or ',' or ', '
  --start START         a starting index, such as 0 or 1

quirks:
  defaults to --start 0 for |enumerate, but --start 1 for |n or |nl
  defaults to pythonic isep=None for |awk and |split, but isep=: for |partition a la |grep -H
  defaults to wide osep='  ' for |awk and |columns and |join
  takes both isep and osep from --sep=SEP when given --sep=SEP, unlike |awk -F$sep -vOFS=$sep
  lets you mark the stop and stop of a string literal with any of , . /

pythonic bricks:
  append bytes casefold counter decode enumerate expandtabs if insert
  join len lower lstrip max md5 min ord printable removeprefix
  removesuffix reverse rstrip set sha256 shuffle slice sort split str
  strings strip sum title upper

classic bricks & fun bricks:
  cut head tail, dent eng frame unframe

alt bricks:
  .frame .head .len .max .md5 .min .reverse .sha256 .sort .tail

cryptic bricks:
  -  0 1 2 3  F L O T U  a h i j k n o r s t u w x  nl pb

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
# No name collision in |pb with: bin/[gp] sh/[defmv]
#

#
# No precedent yet in |pb or sh/ for [bclqwyz] but many Linux define [lw]
#

#
# Floods of aliases to forgive slightly creative spelling detailed only below help
#
#   --raw-control-chars exactly like Shell 'less' in place of --raw-control-ch
#
#   our ArgParse.Suppress work of |sort -f, |awk -F/, -vOFS=+ |nl -pba -v0
#
#   expand md5sum nl rev sha256sum shuf tac  # and --start=1 default for |nl
#
#   chars lines words  # vs str splitlines split
#   data text  # vs bytes str
#   splitlines  # taken as default
#
#   # vs .min .max .slice .sort
#   .reversed .sorted
#   float.max float.min float.sort float.sorted
#   for.len for.reverse for.reversed for.slice
#   reversed sorted
#
#   counter vs set
#   tac vs rev
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

    # Take in the Shell Environment

    sys_stdin_isatty: bool  # Dev Tty at Stdin means get Input Bytes from PasteBuffer
    sys_stdout_isatty: bool  # Dev Tty at Stdout means write Output Bytes back to PasteBuffer
    x_wide: int  # count of Terminal Screen Columns, else 25
    y_high: int  # count of Terminal Screen Rows, else 80

    # Take in the Shell Args

    words: list[str]  # the Shell Args that aren't Double-Dash Options and aren't Dash Options
    sep: str | None  # a separator, such as ' ' or ', '
    start: int | None  # a starting index, such as 0 or 1
    ignorecase: int | None  # nonzero to ignore case

    # Choose how to write the Bytes

    writing_pbcopy: bool | None  # Writing to PbCopy
    writing_file: bool | None  # Writing to ./0 after writing into |pbcopy
    writing_stdout: bool | None  # Writing to Stdout
    raw_control_chars: int | None  # False means translate Control Chars to ¤ when writing to Tty

    # Buffer the Bytes while editing, after reading, until writing

    data: bytes | None  # 1 Sponge of 1 File of Bytes
    bricks: list[ShellBrick]  # Code that works over the Sponge

    #

    def __init__(self) -> None:

        # Look around

        sys_stdin_isatty = sys.stdin.isatty()  # sampled only once
        sys_stdout_isatty = sys.stdout.isatty()  # likewise, sampled only once

        y_high, x_wide = (80, 25)
        try:
            fd = sys.stderr.fileno()
            x_wide, y_high = os.get_terminal_size(fd)  # Columns x Lines
        except OSError:
            pass  # todo: log how .get_terminal_size failed

        # Fill out a nearly blank Self

        self.sys_stdin_isatty = sys_stdin_isatty
        self.sys_stdout_isatty = sys_stdout_isatty
        self.x_wide = x_wide
        self.y_high = y_high

        self.words = list()
        self.sep = None
        self.start = None
        self.ignorecase = None

        self.writing_pbcopy = None
        self.writing_file = None
        self.writing_stdout = None
        self.raw_control_chars = None

        self.data = None
        self.bricks = list()

    def run_main_argv_minus(self, argv_minus: list[str]) -> None:  # noqa C901 too complex  # todo2:
        """Compile & run each Option or Positional Argument"""

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

            print(mmmyyyy, title, version)  # such as:  Feb/2026 LitShell·Py 0.8.185
            sys.exit(0)  # exits 0 after printing Version

        # Run differently because Options & Pos Args

        words = self.words
        words.extend(ns.words)

        if ns.verbose:
            verbose_because.append(True)

        #
        if ns.ignore_case is not None:  # -f, --ignore-case, mostly for |sort
            self.ignorecase = ns.ignore_case

        if ns.F is not None:  # -F mostly for |awk
            if self.sep is None:
                self.sep = str(ns.F)

        if ns.pba is not None:  # -pba mostly for |nl
            pass

        if ns.vOFS is not None:  # -vOFS=OFS mostly for |awk
            if self.sep is None:
                self.sep = str(ns.vOFS)

        # if ns.v is not None:  # -v=START mostly for |nl  # todo7:
        #     if self.start is None:
        #         self.start = int(ns.v, base=0)

        if ns.sep is not None:
            self.sep = str(ns.sep)
        if ns.start is not None:
            self.start = int(ns.start, base=0)

        r = ns.raw_control_ch or 0
        r += ns.raw_control_chars or 0
        if r:
            self.raw_control_chars = r

        # todo8: reject conflicts between --sep -F -vOFS

    def arg_doc_to_parser(self, doc: str) -> ArgDocParser:
        """Declare the Options & Positional Arguments"""

        # Spell out what --help says

        assert argparse.REMAINDER == "..."
        assert argparse.SUPPRESS == "==SUPPRESS=="
        assert argparse.ZERO_OR_MORE == "*"

        parser = ArgDocParser(doc, add_help=False)

        word_help = "a brick or string or number, to build a sponge pipe with"
        parser.add_argument("words", metavar="WORD", nargs="*", help=word_help)

        help_help = "show this help message and exit"
        raw_control_ch_help = "write Control Chars to Tty, don't replace with '¤' Currency-Symbol"
        version_help = "show version numbers and exit"
        verbose_help = "say more"

        parser.add_argument("-h", "--help", action="count", help=help_help)
        parser.add_argument("-V", "--version", action="count", help=version_help)
        parser.add_argument("-v", "--verbose", action="count", help=verbose_help)
        parser.add_argument("-r", "--raw-control-ch", action="count", help=raw_control_ch_help)

        sep_help = "an input or output separator, such as ' ' or ',' or ', '"
        start_help = "a starting index, such as 0 or 1"
        parser.add_argument("--sep", metavar="SEP", help=sep_help)
        parser.add_argument("--start", metavar="START", help=start_help)

        # Spell out what --help doesn't say  # like for |sort -f, etc

        parser.add_argument("-f", "--ignore-case", action="count", help=argparse.SUPPRESS)
        parser.add_argument("-F", help=argparse.SUPPRESS)  # |awk -F/
        parser.add_argument("-pba", action="count", help=argparse.SUPPRESS)  # |nl -pba -v0
        parser.add_argument("-vOFS", help=argparse.SUPPRESS)  # |awk vOFS=x
        # parser.add_argument("-t", help=argparse.SUPPRESS)  # |column -t
        # parser.add_argument("-v", help=argparse.SUPPRESS)  # |nl -pba -v0
        parser.add_argument("--raw-control-chars", action="count", help=argparse.SUPPRESS)

        # Succeed

        return parser

        # ns.raw_control_ch goes to ShellGopher.raw_control_chars
        # alongside ns.raw_control_chars goes to ShellGopher.raw_control_chars

    def shell_args_take_in(self, argv_minus: list[str], parser: ArgDocParser) -> argparse.Namespace:
        """Take in the Shell Args: first the Double-Dash or Dash Options, then Positional Args"""

        options = list()
        posargs = list()

        for index, arg in enumerate(argv_minus):
            if arg == "--":
                posargs.extend(argv_minus[index:])
                break

            if arg.startswith("-") and (arg != "-"):
                try:
                    _ = int(arg, base=0)
                except ValueError:
                    options.append(arg)
                    continue

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

        sys_stdin_isatty = self.sys_stdin_isatty
        words = self.words
        bricks = self.bricks

        # Choose what to write at exit

        assert self.writing_pbcopy is None, (self.writing_pbcopy,)
        assert self.writing_file is None, (self.writing_file,)
        assert self.writing_stdout is None, (self.writing_stdout,)

        writing_file = self._compile_writing_file_()

        self.writing_file = writing_file
        self.writing_pbcopy = self._compile_writing_pbcopy_(writing_file)
        self.writing_stdout = self._compile_writing_stdout_(writing_file)

        # Add implied Bricks

        lotsa_words: list[str] = list()
        lotsa_words.append("__enter__")
        lotsa_words.extend(words)

        if not words[1:]:
            if sys_stdin_isatty:
                lotsa_words.append("unframe")

        lotsa_words.append("__exit__")

        # Compile the plan

        assert not bricks, (bricks,)

        for index, word in enumerate(lotsa_words):

            if index == 0:
                assert word == "__enter__", (word,)

            if index == 1:  # todo3: say this more simply - pb could mean __enter__
                if word in ("cv", "pb"):
                    continue

            if index > 1:
                newborn = bricks[-1]

                dot = word
                if word == ".":
                    newborn.posargs += (dot,)
                    continue

                text: str | None = None
                if " " in word:  # such as ' ' in '0 '
                    text = word  # takes str
                else:
                    text = str_removeflanks_else(word, marks=",./")  # takes str

                if text is not None:
                    if not bricks:
                        newborn = self._compile_brick_if_("append")
                        bricks.append(newborn)

                    newborn.posargs += (text,)
                    continue

                number = parse_number_else(word)  # takes float | int | bool
                if number is not None:
                    newborn.posargs += (number,)
                    continue

                # todo8: accept 'None' as a Pos Arg of a Shell Brick ?
                # todo8: declare which Bricks take which Args, compile-time reject TypeError

            brick = self._compile_brick_if_(word)
            bricks.append(brick)

    def _compile_writing_pbcopy_(self, writing_file: bool) -> bool:
        """Choose to write into PbCopy at exit, or not"""

        words = self.words
        sys_stdin_isatty = self.sys_stdin_isatty

        writing_pbcopy = False
        if writing_file:
            writing_pbcopy = True
        elif (not sys_stdin_isatty) and (not words[1:]):  # |pb  # without Args
            writing_pbcopy = True

        return writing_pbcopy

    def _compile_writing_file_(self) -> bool:
        """Choose to write into ./0 at exit, or not"""

        words = self.words

        writing_file = False
        if words:
            word0 = words[0]
            if word0 in ("0", "1", "2", "3"):
                writing_file = True

        return writing_file

    def _compile_writing_stdout_(self, writing_file: bool) -> bool:
        """Choose to write into Stdout at exit, or not"""

        words = self.words
        sys_stdin_isatty = self.sys_stdin_isatty
        sys_stdout_isatty = self.sys_stdout_isatty

        writing_stdout = False
        if not writing_file:

            if sys_stdin_isatty or (not sys_stdout_isatty):
                writing_stdout = True  # not |pb  # pb, pb |, or |pb|

            if sys_stdout_isatty:
                if words[1:]:
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
        words = self.words

        first = "pb"
        if words:
            word0 = words[0]
            if word0 in ("0", "1", "2", "3"):
                first = word0

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
            "finditer": self.from_bytes_finditer,  # todo3: compare |grep -o
            "md5": self.from_bytes_md5,
            "sha256": self.from_bytes_sha256,
            "printable": self.from_bytes_printable,
            #
            "casefold": self.from_text_casefold,  # |F for Fold
            "expandtabs": self.from_text_expandtabs,
            "jq": self.from_text_jq,  # |j
            "lower": self.from_text_lower,  # |L
            "ord": self.from_text_ord,
            "replace": self.from_text_replace,
            # "sub": self.for_line_sub,  # todo0:
            "split": self.from_text_split,  # aka words
            "title": self.from_text_title,  # |T
            "upper": self.from_text_upper,  # |U
            #
            "counter": self.from_lines_counter,  # |u
            "join": self.for_line_join,  # |x
            "len": self.from_lines_len,  # |w
            "partition": self.from_lines_partition,
            "reverse": self.from_lines_reversed,  # |r
            "reversed": self.from_lines_reversed,  # our ["reversed"] aliases our ["reverse"]
            "shuffle": self.from_lines_shuffle,
            "set": self.for_line_set,  # |set as the ordered last half of |counter
            "sort": self.from_lines_sorted,  # |s
            "sorted": self.from_lines_sorted,  # our ["sorted"] aliases our ["sort"]
            "sum": self.from_lines_sum,
            # "list":  # nope
            # "tuple":  # nope
            #
            "append": self.for_line_append,
            "enumerate": self.for_line_enumerate,  # like |n or |cat -n but --start=0
            "if": self.for_line_if,
            "index": self.for_line_index,
            "insert": self.for_line_insert,
            "lstrip": self.for_line_lstrip,
            "max": self.for_line_max,
            "min": self.for_line_min,
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
            "float.max": self.from_lines_number_max,
            "float.min": self.from_lines_number_min,
            "float.sort": self.from_lines_number_sort,
            "float.sorted": self.from_lines_number_sort,
            #
            ".cut": self.for_line_cut,  # as wide as the Screen
            ".frame": self.for_line_do_frame,  # with .rstrip
            ".head": self.for_line_head,  # as tall as the Screen
            ".jq": self.from_text_jq,  # converts to Python
            ".len": self.for_line_len,  # width of Lines, not length of Lines
            ".max": self.from_lines_number_max,  # by Number not by Str
            ".md5": self.from_bytes_md5,  # Byte Length too, not just Hash
            ".min": self.from_lines_number_min,  # by Number not by Str
            ".reverse": self.for_line_reverse,  # reverse Characters in each Line, not all the Lines
            ".sha256": self.from_bytes_sha256,  # Byte Length too, not just Hash
            ".sort": self.from_lines_number_sort,  # by Number not by Str
            ".tail": self.for_line_tail,  # as tall as the Screen
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
            "text": self.from_text_as_characters,  # aka str
            #
            "bytes": self.from_bytes_as_ints,  # aka data  # 'bytes' is a Python Single Word
            "chars": self.from_text_as_characters,  # aka str
            "lines": self.from_lines_as_lines,  # aka splitlines
            "words": self.from_text_split,  # aka split
            #
            # "split": self.from_text_split,  # already said far above
            "splitlines": self.from_lines_as_lines,  # aka lines
            "str": self.from_text_as_characters,  # aka chars
            #
            # Shell Single Words working with all the Bytes / Lines, or with each Line
            #
            "expand": self.from_text_expandtabs,  # |expandtabs
            "column": self.from_lines_do_columns,
            "columns": self.from_lines_do_columns,
            "cut": self.for_line_cut,
            "head": self.for_line_head,  # |h
            "less": self.from_text_do_lots_less,  # |k
            "md5sum": self.from_bytes_md5,
            "sha256sum": self.from_bytes_sha256,
            "shuf": self.from_lines_shuffle,  # |shuffle
            "strings": self.from_bytes_finditer,  # |LC_ALL=C strings -n 4
            "tail": self.for_line_tail,  # |t
            "tac": self.from_lines_reversed,  # |r  # |reverse
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
            "h": self.for_line_head,
            "i": self.from_text_split,
            "j": self.from_text_jq,
            "k": self.from_text_do_lots_less,
            "n": self.for_line_enumerate,  # but defaulting to --start=1
            "o": self.from_text_do_unframe,  # |o because it rounds off ← ↑ → ↓
            "r": self.from_lines_reversed,
            "s": self.from_lines_sorted,
            "t": self.for_line_tail,
            "u": self.from_lines_counter,  # 'u' for '|uniq' but in the way of |awk '!d[$0]++'
            "w": self.from_lines_len,  # in the way of '|wc -l'
            "x": self.for_line_join,  # in the way of '|xargs'
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
        writing_pbcopy = sg.writing_pbcopy
        sys_stdin_isatty = sg.sys_stdin_isatty

        # Actually don't implicitly enter, when explicitly entering

        if writing_file:
            return

        # Else do implicitly enter

        assert sg.data is None, (len(sg.data),)
        assert not sg.writing_file, (sg.writing_file,)

        if sys_stdin_isatty:  # pb, pb |, pb -
            data = self.pbpaste()  # yep
            sg.data = data

        if not sys_stdin_isatty:  # |pb or |pb|  # but not |pb -
            data = sys.stdin.buffer.read()
            sg.data = data

            if writing_pbcopy:
                self.pbcopy(data)

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
        """Raise NotImplementedError"""

        verb = self.verb
        assert False, (verb,)  # could be raise NotImplementedError(verb)

    #
    # Work with the File taken as Bytes
    #

    def fetch_idata(self) -> bytes:
        """Fetch the bytes(sys.i)"""

        sg = self.shell_gopher
        data = sg.data
        assert data is not None

        return data

    def from_bytes_as_bytes(self) -> None:
        """bytes(sys.i)"""

        self.fetch_idata()  # todo: unneeded

    def from_bytes_as_ints(self) -> None:
        """list(bytes(sys.i))"""

        idata = self.fetch_idata()
        olines = list(str(_) for _ in idata)  # ['65', '66', '67']
        self.store_olines(olines)

    def from_bytes_decode(self) -> None:
        """bytes(sys.i).decode(errors="replace").replace("\ufffd", "¤")"""

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "¤"  # U+00A4 'Currency Sign'

        idata = self.fetch_idata()

        iotext = idata.decode(errors="replace")
        iotext = iotext.replace(ReplacementCharacter, repl)
        otext = iotext

        self.store_otext(otext)

        # todo8: |decode --sep='?'
        # todo8: |decode --sep=''
        # todo8: option of |printable /?/ and --repl='?' and ='💥' for decode/ printable/ textruns

    def from_bytes_md5(self) -> None:
        """hashlib.md5(bytes(sys.i)).hexdigest()"""

        verb = self.verb

        idata = self.fetch_idata()

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

    def from_bytes_printable(self) -> None:  # todo8: .__doc__ doesn't mention '\n' as printable
        """(_ if (_.isprintable() or (_ in "\n")) else "¤") for bytes(sys.i).decode(repl="¤")"""

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "¤"  # U+00A4 'Currency Sign'

        idata = self.fetch_idata()

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

        idata = self.fetch_idata()

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

    def from_bytes_finditer(self) -> None:
        """re.finditer(r"[ -~]{4,}", string=decode(bytes(sys.i), repl="¤"))"""

        idata = self.fetch_idata()

        iotext = idata.decode(errors="replace")

        ReplacementCharacter = "\ufffd"  # PyPi Black rejects \uFFFD
        repl = "¤"  # U+00A4 'Currency Sign'
        iotext = iotext.replace(ReplacementCharacter, repl)

        n = 4  # todo8: |strings -n 4
        regex = (n * r"[ -~]") + r"[ -~]*"  # todo8: |strings --of=isprintable

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

    def from_text_as_characters(self) -> None:
        """list(str(sys.i))"""

        itext = self.fetch_itext()
        olines = list(itext)
        self.store_olines(olines)

    def from_text_casefold(self) -> None:
        """str(sys.i).casefold()"""

        itext = self.fetch_itext()
        otext = itext.casefold()
        self.store_otext(otext)

    def from_text_do_lots_less(self) -> None:
        """_less_(list(sys.i)))"""  # todo8: better help of '|less'

        idata = self.fetch_idata()
        itext = self.fetch_itext()
        iwords = itext.split()
        ilines = itext.splitlines()

        n = len(ilines)
        m = (n // 2) + (n % 2)

        b = clip_int(len(idata))
        _n_ = clip_int(len(ilines))
        w = clip_int(len(iwords))
        c = clip_int(len(itext))

        repl = "¤"  # U+00A4 'Currency Sign'
        cc = "".join((_ if _.isprintable() else repl) for _ in collections.Counter(itext).keys())
        ccn = len(cc)

        _eq_cc = f" = {cc}" if ilines else ""

        iolines = list()
        iolines.append(f"1:{ilines[0]}" if n else "")
        iolines.append(f"2:{ilines[1]}" if (1 < n) else "")
        iolines.append("")
        iolines.append(f"{m}:{ilines[m - 1]}" if (n >= 5) else "")
        iolines.append("")
        iolines.append(f"{1 + n - 2}:{ilines[-2]}" if (n >= 4) else "")
        iolines.append(f"{1 + n - 1}:{ilines[-1]}" if (n >= 3) else "")
        iolines.append("")
        iolines.append(
            f"{b} Bytes of {_n_} Lines of {w} Words of {c} Copies of {ccn} Characters{_eq_cc}"
        )

        olines = list()
        if iolines:
            for i, ioline in enumerate(iolines):
                if ioline or (i and (iolines[i - 1])):
                    olines.append(ioline)

        self.store_olines(olines)

    def from_text_do_unframe(self) -> None:
        """_.rstrip() for _ in textwrap.dedent(str(sys.i)).rstrip().lstrip("\n").splitlines()"""

        itext = self.fetch_itext()

        otext = textwrap.dedent(itext).rstrip().lstrip("\n")

        olines = list(_.rstrip() for _ in otext.splitlines())
        self.store_olines(olines)

    def from_text_eng(self) -> None:
        """replace with clip_float(_).rjust for _: float in str(sys.i)"""

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

                iosplit = clip_float(f)

                osplit = iosplit
                if ijust:
                    osplit = (ijust * " ") + iosplit
                    if (ijust + len(iosplit)) < width:
                        osplit = iosplit.rjust(width)

                oline += osplit

            olines.append(oline)

        self.store_olines(olines)

        # string.printable endswith '\n\r\x0b\x0c' which all do str.splitlines

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
        """ord(_) for _ in str(sys.i)"""

        itext = self.fetch_itext()
        oints = list(ord(_) for _ in itext)
        olines = list(str(_) for _ in oints)
        self.store_olines(olines)

    def from_text_replace(self) -> None:
        """str(sys.i).replace(old, new)"""

        posargs = self.posargs

        pair = posargs[:2]  # todo8: reject extra args
        if not pair:
            pair = (" ", "  ")  # defaults to double U+0020 Space's
        elif not pair[1:]:
            pair = (pair[0], "")  # defaults to delete 1 Str

        stale, fresh = pair
        assert isinstance(stale, str), (stale,)
        assert isinstance(fresh, str), (fresh,)

        itext = self.fetch_itext()
        otext = itext.replace(stale, fresh)
        self.store_otext(otext)

        # todo2: '|replace' of >= 2 pos args and --sep, a la '|append' and '|insert'

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

    def from_lines_as_lines(self) -> None:
        """list(sys.i)"""

        self.fetch_ilines()  # todo: could be .fetch_itext()  # may raise UnicodeDecodeError

    def from_lines_counter(self) -> None:  # diff vs 'def for_line_set'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_ilines()

        opairs = list(collections.Counter(ilines).items())
        vklines = list(f"{v}\t{k}" for (k, v) in opairs)
        olines = vklines

        self.store_olines(olines)

    def from_lines_do_columns(self) -> None:
        """Justify Text or Numeric Columns split by Two Spaces or Tabs"""

        sg = self.shell_gopher
        sep = sg.sep
        osep = "  " if (sep is None) else sep

        itext = self.fetch_itext()

        # Take in Text Columns split by Two Spaces or Tabs

        iotext = itext.replace("\t", "  ")  # accepts Tabs in place of Two Spaces
        iolines = iotext.splitlines()

        # Split each Line into Columns independently

        textual_by_column_index = collections.defaultdict(bool)

        iorows = list()
        iowide = 0

        for ioline in iolines:

            iorow: list[str] = list()

            iosplits = ioline.split("  ")  # splits at each Two Spaces
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
        olines = list(osep.join(_) for _ in orows)

        # Succeed

        self.store_olines(olines)

        # todo0: do the l/r/just in '|columns' fail to grow more than 2 Columns leftward?

    def from_lines_len(self) -> None:
        """len(list(sys.i))"""

        ilines = self.fetch_ilines()
        oline = str(len(ilines))
        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_max(self) -> None:
        """max(list(sys.i), key=lambda _: float..., _)"""

        sg = self.shell_gopher
        ignorecase = sg.ignorecase

        ilines = self.fetch_ilines()
        icolumns = self._take_number_columns_(ilines, needy=True, strict=False)

        if not ignorecase:
            m = max(zip(*icolumns, ilines))
        else:
            m = max(zip(*icolumns, ilines), key=lambda _: _[:-1] + (_[-1].casefold(), _[-1]))

        oline = m[-1]
        olines = [oline]
        self.store_olines(olines)

    def from_lines_number_min(self) -> None:
        """min(list(sys.i), key=lambda _: float..., _)"""

        sg = self.shell_gopher
        ignorecase = sg.ignorecase

        ilines = self.fetch_ilines()
        icolumns = self._take_number_columns_(ilines, needy=True, strict=False)

        if not ignorecase:
            m = min(zip(*icolumns, ilines))
        else:
            m = min(zip(*icolumns, ilines), key=lambda _: _[:-1] + (_[-1].casefold(), _[-1]))

        oline = m[-1]
        olines = [oline]
        self.store_olines(olines)

    def from_lines_partition(self) -> None:  # classic Awk App
        """_.partition(sep) for _ in list(sys.i)"""  # todo8: help .partition meaningfully

        sep = ":"
        dent4 = 4 * " "

        ilines = self.fetch_ilines()

        # Tell each Tag to give its Lines exactly one Dent

        olines = list()
        iolines: list[str] = list()

        def iolines_rollover_into_olines() -> None:

            olines.append(iolines[0])

            iotext = "\n".join(iolines[1:])
            iotext = textwrap.dedent(iotext)  # no .strip()
            olines.extend((dent4 + _) for _ in iotext.splitlines())

            iolines.clear()

        # Pick the leftmost Tag out of each Line

        printed = None
        for iline in ilines:
            prefix, sep, suffix = iline.partition(sep)

            if prefix != printed:
                printed = prefix
                if iolines:
                    iolines_rollover_into_olines()
                iolines.append(prefix + sep)

            iolines.append(dent4 + suffix)

        if iolines:
            iolines_rollover_into_olines()

        # Succeed

        self.store_olines(olines)

        # todo8: alt isep for '|partition'
        # todo8: alt osep for '|partition'
        # todo8: '|rpartition'

    def from_lines_number_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: float..., _)"""

        sg = self.shell_gopher
        ignorecase = sg.ignorecase

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, needy=False, strict=False)
        sortables = list(zip(*icolumns, ilines))

        if not ignorecase:
            sortables.sort()
        else:
            sortables.sort(key=lambda _: _[:-1] + (_[-1].casefold(), _[-1]))

        olines: list[str] = list(_[-1] for _ in sortables)

        self.store_olines(olines)

    def from_lines_reversed(self) -> None:
        """reversed(list(sys.i))"""

        iolines = self.fetch_ilines()
        iolines.reverse()
        self.store_olines(olines=iolines)

        # quite different from 'def for_line_reverse'

    def from_lines_shuffle(self) -> None:
        """random.shuffle(list(sys.i))"""

        iolines = self.fetch_ilines()
        random.shuffle(iolines)
        self.store_olines(olines=iolines)

    def from_lines_sorted(self) -> None:
        """sorted(list(sys.i))"""

        sg = self.shell_gopher
        ignorecase = sg.ignorecase

        iolines = self.fetch_ilines()
        if not ignorecase:
            iolines.sort()
        else:
            iolines.sort(key=lambda _: _.casefold())  # todo0: ignorecase sorts often unstable?
        self.store_olines(olines=iolines)

    def from_lines_sum(self) -> None:
        """sum(list(sys.i)) of every column"""  # todo: help 'for every column' as Code

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, needy=True, strict=True)
        ocolumns = list(sum(_) for _ in icolumns)
        oline = " ".join(str(_) for _ in ocolumns)

        olines = [oline]
        self.store_olines(olines)

    #
    # Factor out some common parts of Shell Pipe Bricks
    #

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

    def _take_number_columns_(
        self, lines: list[str], needy: bool, strict: bool
    ) -> list[list[float | int | bool]]:
        """Convert Left Columns of each Str to Floats and Ints and Bools, else raise LitSystemExit"""

        ilines = lines
        assert needy or (not strict), (needy, strict)

        # Require Input Lines when Strict

        if not ilines:
            if not needy:  # for .sort but not .max .min .sum
                return list()

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
                    inumber = parse_number(isplit)
                except ValueError:
                    break
                inumbers.append(inumber)  # "at left of {iline!r}"

            # Require one or more Number Columns,
            # and require the same Number of Columns per Line when Strict

            width = len(inumbers)
            if not width:
                functypes = "float nor int nor bool"
                occasion = f"ValueError: Line {lineno} has no {functypes} Columns"
                raise LitSystemExit(code=1, occasion=occasion)  # .max, .min, .sort, sum of no cols

            elif i == 0:
                min_width = width

            elif not strict:  # for .max .min .sort but not .sum
                min_width = min(min_width, width)

            elif width != min_width:  # for strict .sum
                occasion = f"ValueError: Line {lineno}"
                occasion += f" has {width} Number Columns"
                occasion += f", not the Number {min_width} Columns of Line 1"
                raise LitSystemExit(code=1, occasion=occasion)  # .sum of ragged edge

            irows.append(inumbers)

        widths = list(len(_) for _ in irows)
        assert min_width >= 1, (min_width, widths, ilines)  # because >= 1 Lines visited

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
        """_.split(sep)[-1] for _ in list(sys.i) if _.split(sep)"""

        sg = self.shell_gopher
        sep = sg.sep  # .sep may be None
        posargs = self.posargs

        isep = sep  # .isep may be None
        osep = "  " if (sep is None) else sep  # defaults to Two Spaces

        ilines = self.fetch_ilines()

        indices = [-1]
        if posargs:
            indices = list(int(_) for _ in posargs)

        olines = list()
        for iline in ilines:
            splits = iline.split(isep)  # .sep may be None
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
                oline = osep.join(owords)
                olines.append(oline)

        self.store_olines(olines)

        # as if |awk 'NF{print $NF}'

    def for_line_append(self) -> None:
        """(_ + suffix) for _ in list(sys.i)"""

        posargs = self.posargs

        splits = [str(_) for _ in posargs] if posargs else ["$"]
        join = " ".join(splits)

        ilines = self.fetch_ilines()
        olines = list((_ + join) for _ in ilines)
        self.store_olines(olines)

    def for_line_cut(self) -> None:
        """(_[:72] + ' ...') for _ in list(sys.i)"""

        x_wide = self._take_dot_or_posargs_as_x_wide_minus_(default=249, minus=0)
        n = 5 if (x_wide < (5 + 1)) else x_wide - 5  # todo: '|cut' for extremely thin Screens

        ilines = self.fetch_ilines()

        olines = list()
        for iline in ilines:
            if len(iline) <= n:
                olines.append(iline)
                continue

            ichop, isuffix = tty_split_after(iline, width=n)
            assert (ichop + isuffix) == iline, (ichop + isuffix, iline)

            osuffix = " ..." if isuffix.startswith(" ") else "..."
            oline = ichop + osuffix

            olines.append(oline)

            # takes Negative PosArg in the way of classic Shell '|tail -9'

        self.store_olines(olines)

    def for_line_do_dent(self) -> None:
        """list((4*" " + _) for _ in list(sys.i))"""

        ilines = self.fetch_ilines()
        olines = list((4 * " " + _) for _ in ilines)
        self.store_olines(olines)

    def for_line_enumerate(self) -> None:
        """enumerate(list(sys.i), start=start)"""  # implicitly for _ in list(sys.i)

        sg = self.shell_gopher
        start = sg.start

        verb = self.verb

        _start_ = 0 if (start is None) else start
        if verb in ("n", "nl"):
            _start_ = 1 if (start is None) else start

        ilines = self.fetch_ilines()

        opairs = list(enumerate(ilines, start=_start_))
        kvlines = list(f"{k}\t{v}" for (k, v) in opairs)
        olines = kvlines

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

    def for_line_if(self) -> None:
        """_ for _ in list(sys.i) if _"""

        ilines = self.fetch_ilines()
        olines = list(_ for _ in ilines if _)
        self.store_olines(olines)

        # todo0: add '|.if' to .rstrip before if

    def for_line_index(self) -> None:
        """_ for _ in list(sys.i) try _.index(text)"""

        posargs = self.posargs

        text = posargs[0] if posargs else " "
        assert isinstance(text, str), (text,)

        ilines = self.fetch_ilines()
        olines = list(_ for _ in ilines if _.find(text) >= 0)
        self.store_olines(olines)

    def for_line_head(self) -> None:
        """list(sys.i)[:9]"""  # todo8: better help for '|.head' and '|head -n'

        n = self._take_dot_or_posargs_as_y_high_minus_(default=9, minus=2)

        ilines = self.fetch_ilines()
        olines = ilines[:n]
        self.store_olines(olines)

    def for_line_insert(self) -> None:
        """(prefix + _) for _ in list(sys.i)"""

        posargs = self.posargs

        splits = [str(_) for _ in posargs] if posargs else [4 * " "]
        join = " ".join(splits)

        ilines = self.fetch_ilines()
        olines = list((join + _) for _ in ilines)
        self.store_olines(olines)

        # todo: compare our .for_line_insert vs Python textwrap.indent

    def for_line_join(self) -> None:
        """sep.join(list(sys.i))"""  # .sep may be None, then works like " " single Space

        verb = self.verb
        sg = self.shell_gopher
        sep = sg.sep

        default_sep = " " if (verb == "x") else "  "
        osep = default_sep if (sep is None) else sep

        ilines = self.fetch_ilines()
        oline = osep.join(ilines)
        olines = [oline]

        self.store_olines(olines)

    def for_line_max(self) -> None:
        """max(list(sys.i))"""

        sg = self.shell_gopher
        ignorecase = sg.ignorecase

        ilines = self.fetch_ilines()

        if not ignorecase:
            oline = max(ilines)
        else:
            oline = max(ilines, key=lambda _: _.casefold())

        olines = [oline]
        self.store_olines(olines)

    def for_line_min(self) -> None:
        """min(list(sys.i))"""

        sg = self.shell_gopher
        ignorecase = sg.ignorecase

        ilines = self.fetch_ilines()

        if not ignorecase:
            oline = min(ilines)
        else:
            oline = min(ilines, key=lambda _: _.casefold())

        olines = [oline]
        self.store_olines(olines)

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

        # quite different from 'def from_lines_reversed'

    def for_line_set(self) -> None:  # diff vs 'def from_lines_counter'
        """collections.Counter(list(sys.i)).keys()"""

        ilines = self.fetch_ilines()
        olines = list(collections.Counter(ilines).keys())
        self.store_olines(olines)

    def for_line_strip(self) -> None:
        """_.strip() for _ in list(sys.i)"""

        ilines = self.fetch_ilines()
        olines = list(_.strip() for _ in ilines)
        self.store_olines(olines)

    def for_line_tail(self) -> None:
        """list(sys.i)[-9:]"""  # todo8: better help for '|.tail' and '|tail -n'

        n = self._take_dot_or_posargs_as_y_high_minus_(default=9, minus=2)

        ilines = self.fetch_ilines()
        olines = ilines[-n:]
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
# Amp up Import BuiltIns Int & Float
#


def clip_int(i: int) -> str:
    """Find the nearest Int Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    clip = _clip_int_(i)
    assert _clip_int_(int(float(clip))) == clip, (_clip_int_(int(float(clip))), clip, i)

    return clip


def _clip_int_(i: int) -> str:

    s = str(int(i))  # '-120789'

    _, dash, digits = s.rpartition("-")  # ('', '-', '120789')
    sci = len(digits) - 1  # 5  # scientific power of ten
    eng = 3 * (sci // 3)  # 3  # engineering power of ten

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, i)

    if not eng:
        clip = s
        return clip  # drops 'e0'

    assert len(digits) >= 4, (len(digits), eng, sci, digits, i)
    assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, i)

    precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'  # significand, mantissa, multiplier
    nearby = precise[:4]  # '120.'
    worthy = nearby.rstrip("0").rstrip(".")  # '120'  # drops '.' or'.0' or '.00'

    assert "." in nearby, (nearby, precise, eng, sci, digits, i)

    clip = dash + worthy + "e" + str(eng)  # '-120e3'

    return clip

    # -120789 --> -120e3, etc


def clip_float(f: float) -> str:
    """Find the nearest Float Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    clip = _clip_float_(f)
    assert _clip_float_(float(clip)) == clip, (_clip_float_(float(clip)), clip, f)

    return clip


def _clip_float_(f: float) -> str:

    if math.isnan(f):
        return "NaN"  # unsigned as neither positive nor negative

    if math.isinf(f):
        absclip = "Inf"
        clip = ("-" + absclip) if (f < 0) else absclip
        return clip

    if not f:
        clip = "-0e0" if (math.copysign(1e0, f) < 0e0) else "0"
        return clip

    absclip = _clip_positive_float_(abs(f))
    clip = ("-" + absclip) if (f < 0) else absclip

    if f == int(f):
        assert clip_int(int(f)) == clip, (f, clip_int(int(f)), clip)

    return clip

    # never says '0' except to mean exactly precisely Float +0e0 or Int 0
    # never ends with '.' nor '.0' nor '.00' nor 'e+0'

    # could return .clip_int for Floats equal to Ints, but doesn't


def _clip_positive_float_(f: float) -> str:
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

    clip = f"{worthy}e{eng}".removesuffix("e0")  # may lack both '.' and 'e'

    # But never wander far

    alt_f = float(clip)

    diff = f - alt_f
    precision = 10 ** (eng - 3 + span)
    assert diff < precision, (diff, precision, f, alt_f, clip, eng, span, worthy, triple, span, f)

    return clip

    # "{:.3g}".format(9876) and "{:.3g}".format(1006) talk like this but say 'e+0' & round up

    # math.trunc leaps too far, all the way down to the int ceil/ floor


#
# Amp up Import BuiltIns Str
#


def parse_int(lit: str) -> int:
    """Evaluate an Int Literal of Base in (0b10, 0o10, 10, 0x10), else raise ValueError"""

    i = int(lit, base=0)

    return i


def parse_number_else(lit: str) -> float | int | bool | None:
    """Evaluate a Float or Int or Bool Literal, else return None"""

    try:
        number = parse_number(lit)
    except ValueError:
        return None

    return number


def parse_number(lit: str) -> float | int | bool:
    """Evaluate a Float or Int or Bool Literal, else raise ValueError"""

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

    # could call ast.literal_eval but doesn't
    # does raise ValueError if not isinstance(number, (float, int, bool))


def str_removeflanks_else(lit: str, marks: str) -> str | None:
    """Remove the same Mark once from both ends, else return None"""

    if lit[1:]:
        a = lit[0]  # first Mark, no matter if is Letter or Digit not Punc
        z = lit[-1]  # last Mark
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
    pylines.append("print(json.dumps(j))  # from |.jq")

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

            assert (chop + suffix) == text, (chop, suffix, text)
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
    assert (chop + suffix) == text, (chop, suffix, text)

    return (chop, suffix)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# big todo0's

# todo0: teach '|pb columns' to cope with Markdown Tables as input

# todo0: refresh the pipe-bricks.md sorts to look more like the def's here

# todo0: rewrite the git.py to distribute via ~/bin/git-*
# todo0: demo 'glv' of can rewrite the git.py to distribute via ~/bin/git-*


# lil todo's

# todo0: |pb g /SESS/ for the Python RegEx effect of |grep -ai -e /SESS/
# todo0: |pb find /SESS/ for str.find of literal text

# todo0: the |.eng should give us metric units in place of 'e' and 'e-'

# todo0: add a litprofile.py to run from ~/.zprofile
# todo0: first up, tell me when Settings Json Backup has gone stale

# todo0: debug
# % pb awk 5 join --sep=' '
#      plavarre plavarre
# % pb awk 5 |join --sep=' '
# 1415 1378 818 716 1568 288 3652 10747 282 1632
# %

# todo0: split and cross-ref '|.max' '|.min' '|reverse' into Char-by-Char & Line-by-Line

# todo0: into litpython.py, doc which Python Version we scraped Importable Names from
# todo0: like rescrape from latest and mention that

# todo0: |sub .pattern. .repl.
# todo0: |remove .from.

# todo0: .uptime to sh/uptime.py -- to give us --pretty at macOS

#

# todo1: sh/cal.py --, for to say 3 months at a time
# todo1: sh/cal.py to mention part of year
# todo1: sh/cal.py to mention how to start on Mondays or Sundays
# todo1: sh/cal.py to prefer python3 -m calendar

# todo1: |sh/nl.py --, for to say |nl -pba -v0

# todo1: sh/which.py, finish up how we've begun offline

#

# todo2: finish porting pelavarre/xshverb/ of bin/ k and of bin/ dt ht pq
# todo2: dt as date && date -u && time

# todo2: |translate .from. .to.

# todo2: |eng '* 512' '1/_' to alter before reformatting

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

# todo7: |slice for --sep=None --start=0, still defaulting to NF{$NF}
# todo7: |a raises IndexError for slice out of range, such as 4 rather than 4,5 or 4..4
# todo7: |a --sep=None --start=1 implied
# todo7: |a 2,4,1 is the 2..3  # |a 0 --start=1 takes 0 as 1..
# todo7: |a 3.. 1..3 -4 2 3 4 0 0..  # |a 0 1..  # the 0.. is intact, not a join
# todo7: |nl -pba -v1 implied

# todo7: block 0 1 2 3 as verbs after first verbs, take as ints, for |awk, for |expandtabs
# todo7: but block ints/floats as first verbs
# todo7: signed/ unsigned floats before ints before verbs
# todo7: int ranges 1..4
# todo7: --start=0 for |awk when you want that, else 0 for the whole in between the rest

#

# todo8: mess with what 'pb --' and '|pb --' means

# todo8: pb hexdump, especially for a -C, especially a memorizable 128 glyph set

# todo8: brick helps

# todo8: |expandtabs 2
# todo8: confusion in having 'pb --sep=-' work while 'pb split /-/' quietly doesn't
# todo8: |textwrap.wrap textwrap.fill or some such
# todo8: |fmt ... just to do |fmt, or more a la |fold -sw $W
# todo8: reject -t without |column
# todo8: take -c at |cut, but don't require it, but do reject -c misplaced
# todo8: trace |nl as '|nl -pba -v0', and accept the '-pba -v1' as input shline
# todo8: |clean up -F$sep vs -F=$sep especially for |awk
# todo8: reject -F misplaced
# todo8: reject -v misplaced
# todo8: reject -vOFS= misplaced

# todo8: |wc -L into |.len .max, |split .len .max

# todo8: dir(str)

# todo8: pb for reorder and transpose arrays of tsv, for split into tsv
# todo8: pb for work with tsv's
# todo8: tables

# todo8: mess around with lineseps of \r \n \r\n
# todo8: mess around with double/ single line spacing of \n or \n\n

# todo8: add |uniq and |uniq -c because it's classic
# todo8: |unexpand
# todo8: str.ljust str.rjust str.center
# todo8: |choice, vs |shuffle head -$N
# todo8: more with 'comm' and 'paste' and ... ?

# todo8: |sha256 -  # todo8: who gets the '-' as a pos arg?
# todo8: brief alias for stack peek/ dump at:  grep . ?

# todo8: |1 or |1| and same across 0, 1, 2, 3
# todo8: |_ like same _ as we have outside

#

# todo9: adopt the complex -R, --RAW-CONTROL-CHARS from |less, not only the simple -r from |less
# todo9: + mv 0 ... && pbpaste |upper |tee >(pbcopy) >./0
# todo9: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'

# todo9: drop all the unhelped verbs?


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
