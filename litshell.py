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
  0 'upper -h'
  1
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import __main__
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

    data: bytes = b""

    bricks: list[ShellBrick] = list()

    #
    # Make a Shell Pipe by stringing Bricks together in a Line
    #

    def compile_pipe_if(self, argv_minus: list[str]) -> None:
        """Compile each Brick"""

        if not argv_minus:
            self.print_help()
            sys.exit(0)  # exits 0 after printing Help

        self.compile_brick_if("__enter__")
        for arg in argv_minus:
            self.compile_brick_if(arg)
        self.compile_brick_if("__exit__")

    def compile_brick_if(self, arg: str) -> None:
        """Compile one Brick"""

        bricks = self.bricks

        if arg.startswith("--h") and "--help".startswith(arg):
            self.print_help()
            sys.exit(0)  # exits 0 after printing Help

        brick = ShellBrick(self, verb=arg)
        if not brick.func:
            print(f"Undefined Brick:  {arg!r}", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad Args

        bricks.append(brick)

    def print_help(self) -> None:
        """Print the Doc and exit zero, if '--help' in the Shell Args"""

        doc = __main__.__doc__
        assert doc, (doc,)
        text = textwrap.dedent(doc).strip()

        print(text, file=sys.stderr)

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
            "__enter__": self.run_enter,
            "__exit__": self.run_exit,
            #
            "0": self.run_digit_zero,
            "1": self.run_digit_one,
            "2": self.run_digit_two,
            "3": self.run_digit_three,
            #
            "casefold": self.run_str_casefold,
            "lower": self.run_str_lower,
            "title": self.run_str_title,
            "upper": self.run_str_upper,
        }

        default_eq_none = None
        func = func_by_verb.get(verb, default_eq_none)
        self.func = func

    def run_as_brick(self) -> None:
        """Run Self as a Shell Pipe Brick"""

        func = self.func
        assert func

        func()

    def run_exit(self) -> None:
        """Exit the Shell Pipe"""

        sg = self.shell_gopher
        data = sg.data

        self.pbcopy(data)

        path = pathlib.Path(str(0))
        path.write_bytes(data)

        fileno = sys.stdout.fileno()
        os.write(fileno, data)

    def run_enter(self) -> None:
        """Enter the Shell Pipe"""

        pass

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

        print(f"+ cat {n} |pbcopy", file=sys.stderr)
        path = pathlib.Path(str(n))
        data = path.read_bytes()
        self.pbcopy(data)

        self.run_digit_zero()

    def run_digit_zero(self) -> None:
        """Push the Paste Buffer into the Stack"""

        sg = self.shell_gopher

        print("+ mv 2 3 && mv 1 2 && mv 0 1 && touch 0", file=sys.stderr)
        self.push_paste_buffers()

        data = self.pbpaste()
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
            print(f"+ exit {returncode}", file=sys.stderr)
            sys.exit(returncode)

        data = run.stdout

        return data

    def pbcopy(self, data: bytes) -> None:
        """Push Bytes into the Os Copy/Paste Clipboard Buffer"""

        run = subprocess.run(["pbcopy"], input=data, check=True, stdout=subprocess.PIPE)

        returncode = run.returncode
        if returncode:
            print(f"+ exit {returncode}", file=sys.stderr)
            sys.exit(returncode)

    #
    # Work with the File as Bytes
    #

    def fetch_bytes(self) -> bytes:
        """Fetch the File as Bytes"""

        sg = self.shell_gopher
        data = sg.data

        return data

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
        """Change the File to be all Lower Case"""

        itext = self.fetch_str()
        otext = itext.casefold()
        self.store_str(otext)

    def run_str_lower(self) -> None:
        """Change the File to be all Lower Case"""

        itext = self.fetch_str()
        otext = itext.lower()
        self.store_str(otext)

    def run_str_title(self) -> None:
        """Change the File to be all Title Case"""

        itext = self.fetch_str()
        otext = itext.title()
        self.store_str(otext)

    def run_str_upper(self) -> None:
        """Change the File to be all Upper Case"""

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
