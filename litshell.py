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

famously abbreviated bricks:
  -  0 1 2 3  F L O T U  a h i n o r s t u w x  nl pb

famously convenient bricks:
  awk bytes casefold chars counter data dent enumerate expandtabs
  float.max float.min float.sort head int.max int.min int.sort join
  len lines lower lstrip max md5sum min rev reverse rstrip set sha256
  shuf shuffle sort splitlines str strip sum tac tail text title
  undent upper words

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


class ShellGopher:
    """Init and run, once"""

    data: bytes | None  # 1 Sponge of 1 File of Bytes

    verbs: list[str]  # the brick names from the command line
    sep: str | None  # a separator, such as ' ' or ', '
    start: int | None  # a starting index, such as 0 or 1

    bricks: list[ShellBrick]  # Code that works over the Sponge
    sys_stdin_isatty: bool  # Dev Tty at Stdin means get Input Bytes from PasteBuffer
    sys_stdout_isatty: bool  # Dev Tty at Stdout means write Output Bytes back to PasteBuffer

    writing_file: bool | None  # Writing to ./0 after writing into |pbcopy
    writing_stdout: bool | None  # Writing to Stdout

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

        self.writing_file = None
        self.writing_stdout = None

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
        sys_stdin_isatty = self.sys_stdin_isatty

        # Choose what to write at exit

        assert self.writing_file is None, (self.writing_file,)
        self.writing_file = self._compile_writing_file_()

        assert self.writing_stdout is None, (self.writing_stdout,)
        self.writing_stdout = self._compile_writing_stdout_()

        # Add implied Bricks

        pipe_verbs = list()
        pipe_verbs.append("__enter__")
        pipe_verbs.extend(verbs)

        if not verbs[1:]:
            if sys_stdin_isatty:
                pipe_verbs.append("undent")
            # if sys_stdout_isatty:
            #     pipe_verbs.append("printable")  # todo1:

        pipe_verbs.append("__exit__")

        # Compile the plan

        for verb in pipe_verbs:
            if verb == "pb":  # todo2: say this more simply - pb could mean __enter__
                continue
            self._compile_brick_if_(verb)

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

    def _compile_brick_if_(self, verb: str) -> None:
        """Compile one Brick"""

        bricks = self.bricks

        brick = ShellBrick(self, verb=verb)

        if not brick.verb:
            print(f"Unknown Pipe Brick:  {verb!r}", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad Args

        bricks.append(brick)

    def sketch_pipe(self) -> None:
        """Sketch the Pipe as + |pb '...' |pb '...' ..."""

        bricks = self.bricks

        first = bricks[0].verb
        s = "+ |" + first

        for brick in bricks:
            verb = brick.verb
            func = brick.func

            doc = func.__doc__

            if verb in ("0", "1", "2", "3", "pb", "__enter__", "__exit__"):
                continue

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
    verb: str
    func: collections.abc.Callable[..., None]

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
            # "if":  # todo: not yet
            # "list":  # nope
            # "tuple":  # nope
            #
            "enumerate": self.for_line_enumerate,  # |n  # todo: -v1
            "lstrip": self.for_line_lstrip,
            "rstrip": self.for_line_rstrip,
            "strip": self.for_line_strip,
            # "for":  # todo: not yet
            #
            # Python Dotted Double Words
            #
            "int.max": self.from_lines_int_base_zero_max,
            "int.min": self.from_lines_int_base_zero_min,
            "int.sort": self.from_lines_int_base_zero_sort,
            "float.max": self.from_lines_numeric_max,
            "float.min": self.from_lines_numeric_min,
            "float.sort": self.from_lines_numeric_sort,
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
            # "split": self.from_text_split,  # already said above
            "splitlines": self.from_lines_as_lines,  # aka lines
            "str": self.from_text_as_texts,  # aka chars
            #
            # Shell Single Words working with all the Bytes / Lines, or with each Line
            #
            "md5sum": self.from_bytes_md5sum,
            "sha256": self.from_bytes_sha256,
            #
            "expand": self.from_text_expandtabs,
            #
            "head": self.from_lines_head,  # |h
            "shuf": self.from_lines_shuffle,
            "tail": self.from_lines_tail,  # |t
            "tac": self.from_lines_reverse,  # |r
            # "uniq": self.from_lines_uniq,  # differs from |u  # todo1:
            #
            # "$": self.for_line_suffix,  # |$ ...  # todo8
            # "^": self.for_line_prefix,  # |^ ...  # todo8
            "awk": self.for_line_awk_nth_slice,  # |a
            "nl": self.for_line_enumerate,  # although Shell defaults to --start=1
            "rev": self.for_line_reverse,
            #
            # Famously Abbreviated Single Character Aliases
            #
            "-": self.from_bytes_as_bytes,
            #
            "0": self.enter_as_pick_0th,
            "1": self.enter_as_pick_1th,
            "2": self.enter_as_pick_2th,
            "3": self.enter_as_pick_3th,
            #
            "F": self.from_text_casefold,  # |F for Fold
            "L": self.from_text_lower,
            "O": self.for_line_do_dent,  # |O for Outdent
            "T": self.from_text_title,
            "U": self.from_text_upper,
            #
            "a": self.for_line_awk_nth_slice,
            "h": self.from_lines_head,
            "i": self.from_text_split,
            "n": self.for_line_enumerate,
            "o": self.from_text_do_undent,  # |o because it rounds off ← ↑ → ↓
            "r": self.from_lines_reverse,
            "s": self.from_lines_sort,
            "t": self.from_lines_tail,
            "u": self.from_lines_counter,  # 'u' for '|uniq' but in the way of |awk '!d[$0]++'
            "w": self.from_lines_len,  # in the way of '|wc -l'
            "x": self.from_lines_join,  # in the way of '|xargs'
            #
            # Names for newer Shell Pipe Filter Bricks
            #
            "dent": self.for_line_do_dent,  # |O
            "undent": self.from_text_do_undent,  # |o
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
        sys_stdin_isatty = sg.sys_stdin_isatty
        writing_file = sg.writing_file
        writing_stdout = sg.writing_stdout

        data = sg.data
        assert data is not None

        fd = sys.stdout.fileno()

        if writing_file or not sys_stdin_isatty:  # as if sg.writing_pbcopy
            self.pbcopy(data)

        if writing_file:
            path = pathlib.Path(str(0))
            path.write_bytes(data)

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

    def from_bytes_md5sum(self) -> None:
        """hashlib.md5(bytes(sys.i)).hexdigest()"""

        idata = self.fetch_bytes()

        h = hashlib.md5()
        h.update(idata)
        lower_nybbles = h.hexdigest()
        oline = lower_nybbles + "  -"

        olines = [oline]
        self.store_olines(olines)

        # d41d8cd98f00b204e9800998ecf8427e  -

    def from_bytes_sha256(self) -> None:
        """hashlib.sha256(bytes(sys.i)).hexdigest()"""

        idata = self.fetch_bytes()

        h = hashlib.sha256()
        h.update(idata)
        lower_nybbles = h.hexdigest()
        oline = lower_nybbles + "  -"

        olines = [oline]
        self.store_olines(olines)

        # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 -

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

    def from_text_do_undent(self) -> None:
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
        """list(sys.i)[:9]"""

        ilines = self.fetch_ilines()
        olines = ilines[:9]
        self.store_olines(olines)

    def from_lines_int_base_zero_max(self) -> None:
        """max(list(sys.i), key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=int_base_zero, strict=False)
        m = max(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_int_base_zero_min(self) -> None:
        """min(list(sys.i), key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=int_base_zero, strict=False)
        m = min(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_int_base_zero_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: int..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=int_base_zero, strict=False)
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

    def from_lines_numeric_max(self) -> None:
        """max(list(sys.i), key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=numeric, strict=False)
        m = max(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_numeric_min(self) -> None:
        """min(list(sys.i), key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=numeric, strict=False)
        m = min(zip(icolumns, ilines))
        oline = m[-1]

        olines = [oline]
        self.store_olines(olines)

    def from_lines_numeric_sort(self) -> None:
        """list(sys.i).sort(key=lambda _: float..., _)"""

        ilines = self.fetch_ilines()

        icolumns = self._take_number_columns_(ilines, func=numeric, strict=False)
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

        icolumns = self._take_number_columns_(ilines, func=numeric, strict=True)
        ocolumns = list(sum(_) for _ in icolumns)
        oline = " ".join(str(_) for _ in ocolumns)

        olines = [oline]
        self.store_olines(olines)

    def from_lines_tail(self) -> None:
        """list(sys.i)[-9:]"""

        ilines = self.fetch_ilines()
        olines = ilines[-9:]
        self.store_olines(olines)

    #
    # Work from the File taken as Columns at Left and then a Text Remainder
    #

    def _take_number_columns_(
        self, lines: list[str], func: collections.abc.Callable[[str], float | int], strict: bool
    ) -> list[list[float | int]]:
        """Call Func to convert left of each Str to Floats and Ints"""

        ilines = lines

        if func.__name__ == "int_base_zero":
            functype = "int"  # |pb int.max, |pb int.min, |pb int.sort
        else:
            assert func.__name__ == "numeric"
            functype = "float nor int"  # |pb float.max, |pb float.min, |pb float.sort

        min_width = -1

        irows: list[list[float | int]] = list()  # rows
        for iline in ilines:
            isplits = iline.split()

            inumerics = list()
            for index, isplit in enumerate(isplits):
                if (min_width != -1) and (index >= min_width):
                    if strict:
                        raise ValueError(f"more than {min_width} columns in some rows")
                    break

                try:
                    inumeric = func(isplit)
                except ValueError:
                    if strict:
                        raise  # |pb sum
                    break

                inumerics.append(inumeric)

            if (min_width != -1) and (len(inumerics) < min_width):
                if strict:
                    raise ValueError(f"less than {min_width} columns in some rows")

            irows.append(inumerics)
            min_width = len(inumerics) if (min_width == -1) else min(min_width, len(inumerics))

        if lines and (min_width <= 0):
            print(f"pb: no {functype} columns to sort", file=sys.stderr)
            sys.exit(1)  # exits 1 for value error in taking up input

        ocolumns: list[list[float | int]] = list()  # columns
        for index in range(min_width):

            ocolumn: list[float | int] = list()
            for irow in irows:
                inumeric = irow[index]
                ocolumn.append(inumeric)  # todo: speedier transposition?

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

    def for_line_do_dent(self) -> None:
        """[""2*""] + list((4*" " + _ + 4*" ") for _ in list(sys.i)) + [2*""]"""

        ilines = self.fetch_ilines()
        width = max(len(_) for _ in ilines) if ilines else 0

        above = 2 * [""]
        ljust = width + 4
        rjust = ljust + 4
        below = 2 * [""]

        olines = above + list(_.ljust(ljust).rjust(rjust) for _ in ilines) + below
        self.store_olines(olines)

    def for_line_enumerate(self) -> None:
        """enumerate(list(sys.i), start=start)"""  # implicitly for _ in list(sys.i)

        sg = self.shell_gopher
        start = sg.start
        _start_ = 0 if (start is None) else start

        ilines = self.fetch_ilines()

        opairs = list(enumerate(ilines, start=_start_))
        kvlines = list(f"{k}\t{v}" for (k, v) in opairs)
        olines = kvlines

        self.store_olines(olines)

    def for_line_lstrip(self) -> None:
        """_.lstrip() for _ in list(sys.i)"""

        ilines = self.fetch_ilines()
        olines = list(_.lstrip() for _ in ilines)
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
# Amp up Import BuiltIns
#


def int_base_zero(lit: str) -> int:
    """Call int(_, base=0) but without forcing the Caller to pass in the 0"""

    i = int(lit, base=0)
    return i


def numeric(lit: str) -> float | int:  # todo0: float | int | bool
    """Convert a repr(float) or repr(int) or repr(bool) over to float or int"""

    if lit == "False":
        return 0

    if lit == "True":
        return 1

    numeric: float | int
    try:
        numeric = int(lit, base=0)
    except ValueError:
        numeric = float(lit)

    return numeric


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


# todo0: |pb decode  # replace to \uFFFD Replacement-Character to \x3F Question-Mark '?'
# todo0: sold as overcomes old macOS Unix flaming out

# todo0: |pb printable, to be explicit for that
# todo0: also transform to printable before writing to tty, unless people say |pb tty
# todo: do surrogate_escape repl ? before writing to tty

# todo0: |pb cut ... to |cut -c to fit width on screen but with "... " marks
# todo0: take -c at |cut, but don't require it

# todo0: |pb fmt ... just to do |fmt

# todo0: |pb column ... like' |column -t' but default to --sep='  ' for intake
# todo0: take -t at |column, but don't require it

# todo0: take --seed as unhelped to repeat random

# todo0: take -F as --sep at |awk
# todo0: reject -F or --sep without |pb join or |pb split or |pb awk

# todo0: take -v as --start at |nl
# todo0: reject --start without |pb enumerate or |pb nl

# todo0: |pb expandtabs 2

# todo0: add |uniq and |uniq -c because it's classic
# todo0: take -c at |uniq

#

# todo0: take -- as alt of sort/float.sort, uniq/'uniq -c', max/float.max, min.float.min, set/counter

#

# todo1: finish porting pelavarre/xshverb/ of bin/ a j k and of bin/ dt ht pq

# todo1: mess around with lineseps of \r \n \r\n
# todo1: mess around with double/ single line spacing of \n or \n\n

# todo1: more with 'comm' and 'paste' and ... ?

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

# todo9: |1 or |1| and same across 0, 1, 2, 3
# todo9: |pb _ like same _ as we have outside
# todo9: + mv 0 ... && pbpaste |pb upper |tee >(pbcopy) >./0
# todo9: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'


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

# todo: |wc -L into |pb line len max, |pb word len max

# todo: brief alias for stack peek/ dump at:  grep . ?


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
