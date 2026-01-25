#!/usr/bin/env python3

"""
usage: grep.py SHFILE [SHWORD ...]

call Grep but as |grep -ai -e ... -e ...

positional arguments:
  SHFILE  disclose who is calling (often a pathname of bin/g)
  SHWORD  option or positional argument of Grep

options:
  --help  show this help message and exit (-h is for Grep, not for Grep·Py)

quirks:
  tunes to presume text, ignore case, and match >= 1 patterns (like for 2025, in place of 1973)

examples:
  cat bin/*.py |g -nw def print
  cat bin/*.py |grep.py $HOME/bin/g -nw def print
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
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


def main() -> None:
    """Run from the Shell Command Line"""

    gg = GrepGopher()
    gg.go_for_it()


class GrepGopher:
    """Init and run, once"""

    def go_for_it(self) -> None:

        # Fail if no Shell Args

        usage = "usage: grep.py SHFILE [SHWORD ...]"

        if not sys.argv[1:]:
            print(usage)
            sys.exit(2)  # exits 2 for bad args

        # Find the Shell Verb and the Shell Args after it

        self.exit_if_dash_dash_help()

        shfile_shargv = shfile_shargv = sys.argv[1:]

        shverb = os.path.basename(shfile_shargv[0])
        assert shverb, (shfile_shargv, shverb)
        shverb_shargv = (shverb, *shfile_shargv[1:])

        alt_shverb = shverb_shargv[0]
        if alt_shverb != "g":
            _ = NotImplementedError(alt_shverb)
            print(
                f"grep.py: NotImplementedError: |{alt_shverb} in a pipe, not from </dev/tty",
                file=sys.stderr,
            )
            sys.exit(2)  # exits 2 for bad args

        if not shverb_shargv[1:]:
            print("usage: |grep.py SHWORD [SHWORD ...]", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        argv = list()
        argv.append("grep")
        argv.extend(self._shargs_grep_expand_ai_e_(shverb_shargv[1:]))

        join = shlex.join(argv)
        print("|" + join, file=sys.stderr)

        pass_fds = tuple(int(_) for _ in os.listdir("/dev/fd"))
        run = subprocess.run(argv, pass_fds=pass_fds)
        if run.returncode:
            print("+ exit", run.returncode, file=sys.stderr)

        sys.exit(run.returncode)

        # todo: do we ever call Grep so that it needs its Stdin & Stdin Fd cut off ?

        #
        # Passing down the 'pass_fds=' ducks out of this kind of failure
        #
        #   % echo |bin/grep.py alf brav -- <(echo alfa bravo)
        #   |grep -ai -e alf -e brav -- /dev/fd/12
        #   grep: /dev/fd/12: Bad file descriptor
        #   + exit 2
        #   %
        #

    def exit_if_dash_dash_help(self) -> None:
        """Print the Doc and exit zero, if '--help' in the Shell Args"""

        if "--help" in sys.argv[1:]:
            print(__main__.__doc__, file=sys.stderr)
            sys.exit(0)  # exits 0 after printing Help

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
