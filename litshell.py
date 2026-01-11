#!/usr/bin/env python3

"""
usage: litshell.py [--help] [BRICK ...]

greatly abbreviate Shell commands, but do show them in full

positional arguments:
  BRICK            the Name of a Brick of the Shell Pipe (or a quoted Command Line for it)

options:
  --help           show this help message and exit (-h is for a Brick, not for LitShell·Py)

examples:
  0
  0 upper
  1

more examples:
  cat README.md |pb
  pb str set join
  pb str sort set join
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
import collections
import os
import pathlib
import shutil
import signal
import subprocess
import sys
import textwrap
import typing

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


def main() -> None:
    """Run from the Shell Command Line"""

    shg = ShellGopher()
    shg.compile_pipe_if(sys.argv[1:])
    shg.run_pipe()


class ShellGopher:
    """Init and run, once"""

    data: bytes  # 1 Sponge of 1 File of Bytes
    bricks: list[ShellBrick]  # Code that works over the Sponge
    stacking_revisions: bool  # Stacking means Input from and Output to our Stack of Revisions
    sys_stdin_isatty: bool  # Dev Tty at Stdin means get Input Bytes from PasteBuffer
    sys_stdout_isatty: bool  # Dev Tty at Stdout means write Output Bytes back to PasteBuffer

    def __init__(self) -> None:

        sys_stdin_isatty = sys.stdin.isatty()  # sampled only once
        sys_stdout_isatty = sys.stdout.isatty()  # likewise, sampled only once

        self.data = b""
        self.bricks = list()
        self.stacking_revisions = False
        self.sys_stdin_isatty = sys_stdin_isatty
        self.sys_stdout_isatty = sys_stdout_isatty

    #
    # Make a Shell Pipe by stringing Bricks together in a Line
    #

    def compile_pipe_if(self, argv_minus: list[str]) -> None:
        """Compile each Brick"""

        bricks = self.bricks

        if not argv_minus:
            self.print_help()
            sys.exit(0)  # exits 0 after printing Help

        if argv_minus:
            arg0 = argv_minus[0]
            if arg0 in ("0", "1", "2", "3"):
                self.stacking_revisions = True

        self.compile_brick_if("__enter__")

        for arg in argv_minus:
            self.compile_brick_if(arg)

        if len(bricks) <= 2:  # default to do the '|pb strip' work
            self.compile_brick_if("strip")

        self.compile_brick_if("__exit__")

        # todo: more than one of ("0", "1", "2", "3"), such as Shell ? while 'ls -C ?' is '0 1 2 3'

    def compile_brick_if(self, arg: str) -> None:
        """Compile one Brick"""

        bricks = self.bricks

        if arg.startswith("--h") and "--help".startswith(arg):
            self.print_help()
            sys.exit(0)  # exits 0 after printing Help

        brick = ShellBrick(self, verb=arg)
        if not brick.func:
            print(f"Unknown Pipe Brick:  {arg!r}", file=sys.stderr)
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
    func: typing.Callable[..., None] | None
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
            "bytes": self.run_bytes_list,  # like for wc -c via |bytes len
            #
            "awk": self.run_list_str_awk,  # |a
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

        # todo: pb --start=1 n

        # todo: pb --sep=', ' x
        # todo: pb --sep=, split
        # todo: pb --sep str set join

        # todo: pb --sep=/ 'a 1 -2 3'

        # todo: pb floats sum
        # todo: pb hexdump

        # todo: brick helps

        # todo: brief alias for stack dump at:  grep . ?

        # todo: 'pb splitlines set', 'pb str set', 'pb list', 'pb tuple', 'pb pass', ...
        # todo: 'pb for strip' like to strip each line

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

        ilines = self.fetch_list_str()
        opairs = list(enumerate(ilines))
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

        # print("|str.join", file=sys.stderr)

        ilines = self.fetch_list_str()
        olines = [" ".join(ilines)]
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

        # print("|str.split", file=sys.stderr)

        itext = self.fetch_str()
        olines = itext.split()
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
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
