#!/usr/bin/env python3

"""
usage: grep.py [--shfile=SHFILE] SHWORD [SHWORD ...]

call Grep but as |grep -ai -e ... -e ...

positional arguments:
  SHWORD           option or positional argument of Grep

options:
  --help           show this help message and exit (-h is for Grep, not for Grep·Py)
  --shfile SHFILE  a filename as the Git alias to decode (default: '/dev/null/g')

quirks:
  tunes to presume text, ignore case, and match >= 1 patterns (like for 2025, in place of 1973)

examples:
  cat bin/*.py |g -nw def print
  cat bin/*.py |grep.py --shfile=$HOME/bin/g -nw def print
  cat bin/*.py |grep -ai -nw -e def -e print
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import __main__
import os
import shlex
import subprocess
import sys
import typing

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


def main() -> None:

    gg = GrepGopher()
    gg.go_for_it()


class GrepGopher:

    def go_for_it(self) -> None:

        # Find the Shell Verb and the Shell Args after it

        self.exit_if_dash_dash_help()

        shfile_shargv = self.dash_dash_shfile_shargv(sys.argv, default="/dev/null/g")

        shverb = os.path.basename(shfile_shargv[0])
        assert shverb, (shfile_shargv, shverb)
        shverb_shargv = (shverb, *shfile_shargv[1:])

        alt_shverb = shverb_shargv[0]
        if alt_shverb != "g":
            _ = NotImplementedError(alt_shverb)
            print(f"NotImplementedError: {alt_shverb!r} in a pipe", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        if not shverb_shargv[1:]:
            print("usage: |grep.py SHWORD [SHWORD ...]", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        argv = list()
        argv.append("grep")
        argv.extend(self._shargs_grep_expand_ai_e_(shverb_shargv[1:]))

        join = shlex.join(argv)
        print("|" + join, file=sys.stderr)

        run = subprocess.run(argv)
        if run.returncode:
            print("+ exit", run.returncode, file=sys.stderr)

        sys.exit(run.returncode)

    def exit_if_dash_dash_help(self) -> None:
        """Print the Doc and exit zero, if '--help' in the Shell Args"""

        if "--help" in sys.argv[1:]:
            print(__main__.__doc__, file=sys.stderr)
            sys.exit(0)  # exits 0 after printing Help

        # todo: merge .exit_if_dash_dash_help with git.GitGopher

    def dash_dash_shfile_shargv(
        self, sys_argv: typing.Iterable[str], default: str
    ) -> tuple[str, ...]:
        """Move the '--shfile FILE' into ArgV 0 when given as 1 or 2 Shell Args"""

        tuple_sys_argv = tuple(sys_argv)
        assert tuple_sys_argv, (tuple_sys_argv,)

        # Fail if no Shell Args

        default_shargv = (default, *tuple_sys_argv[1:])
        if not tuple_sys_argv[1:]:
            return default_shargv

        # Fail if the '--shfile' option isn't the leading Shell Arg

        sys_argv_1 = tuple_sys_argv[1]
        (head, sep, tail) = sys_argv_1.partition("--shfile=")
        if head or (not sep):
            return default_shargv

        # Fail if the '--shfile' option carries no Pathname

        pathname = tail  # like from --shfile=/dev/null/g
        shargv = (pathname, *tuple_sys_argv[2:])

        if not tail:
            if not tuple_sys_argv[2:]:
                return default_shargv

            sys_argv_2 = tuple_sys_argv[1]

            pathname = sys_argv_2  # like from --shfile /dev/null/g
            shargv = (pathname, *sys.argv[3:])

        # Fail if the --shfile=Pathname carries no Basename

        shverb = os.path.basename(pathname)
        if not shverb:
            return default_shargv

        # Else succeed

        return shargv

        # todo: merge .dash_dash_shfile_shargv with git.GitGopher

    def _shargs_grep_expand_ai_e_(self, shargs: tuple[str, ...]) -> tuple[str, ...]:
        """Tune to presume text, ignore case, and match >= 1 patterns"""

        strs = list()
        strs.append("-ai")  # -a = --text  # -i = --ignore-case
        for i, arg in enumerate(shargs):
            if arg == "--":
                strs.extend(shargs[i:])
                break
            elif arg.startswith("-"):
                strs.append(arg)
            else:
                strs.append("-e")
                strs.append(arg)

        argv = tuple(strs)
        return argv

        # todo: merge ._shargs_grep_expand_ai_e_ with git.GitGopher


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/grep.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
