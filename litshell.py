#!/usr/bin/env python3

"""
usage: pylitfun/litshell.py [--help] [--shfile SHFILE] [SHWORD ...]

abbreviate Shell commands, but do show them in full

positional arguments:
  SHWORD           option or positional argument of Shell

options:
  --help           show this help message and exit (-h is for Shell, not for LitShell·Py)
  --shfile SHFILE  a filename as the Shell alias to decode (default: '/dev/null/p')

examples:
  p
  ./litshell.py --shfile=~/p
  : p ... && python3 -i -c ''
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import __main__
import difflib
import os
import signal
import sys
import typing

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


# Disclose two dozen everyday Shell Idioms

ShlinePlusByShverb = {  # sorted by key
    #
    "a": "|awk 'NF{print $NF}'",  # todo: awk.py
    "b": "env -i bash --noprofile --norc",
    "c": "|cat -",  # todo: cat.py
    "d": "diff -brpu a b",  # todo: spell out what -b -r -p -u mean
    "e": "emacs -nw --no-splash --eval '(menu-bar-mode -1)'",  # -Q
    #
    "f": "find .",  # todo: find.py
    "g": "|grep.py ...",  # ==> |grep -ai -e ... -e ...
    "h": "head -9",
    "i": "tr ' ' '\n'",  # as in Python str.split(" "), unlike Python str.split()
    "j": "|jq .",  # todo: jq.py
    #
    "k": "|less -FIRX",  # todo: spell out what -F -I -R -X mean
    "l": "ls -hlAF -rt",  # unlike the subculture of alias l='ls -CF'
    "m": "",  # todo vs "m": "make help"
    "n": "|nl -pba -v0 |expand",  # todo: spell out what -p -b -a -v0 mean  # todo: take -v as arg
    "o": "|textwrap.py ↓ → ← ↑",  # just '→' for textwrap.dedent, not '→ →' for str.lstrip
    #
    "p": "python.py -i -c ''",  # todo: hint an awkish python program to write & run  # p line len
    "q": "",
    "r": "|tac or |tail -r",
    "s": "LC_ALL=C sort -n",  # todo: sort.py
    "t": "tail -9",
    #
    "u": "|uniq -c |expand",  # todo: spell out what -c means
    "v": "vim -u /dev/null -y",  # todo: spell out what -u -y mean
    "w": "wc -l",  # todo: uncollide with /usr/bin/w
    "x": "|xargs",  # todo: spell out what -n -P mean
    "y": "yes|",  # todo: yq.py
    "z": "env -i zsh -f",  # todo: spell out what -f means
    #
}


_a_ = list(ShlinePlusByShverb.keys())
_b_ = sorted(_a_)
_diffs_ = list(difflib.unified_diff(a=_a_, b=_b_, fromfile="a", tofile="b", lineterm=""))
if _diffs_:
    print("\n".join(_diffs_), file=sys.stderr)
assert not _diffs_, (_diffs_,)


def main() -> None:

    shg = ShellGopher()
    shg.go_for_it()


class ShellGopher:

    def go_for_it(self) -> None:

        # Fail if no Shell Args

        if not sys.argv[1:]:
            print("usage: litshell.py [--help] [--shfile SHFILE] [SHWORD ...]", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        # Find the Shell Verb and the Shell Args after it

        self.exit_if_dash_dash_help()

        shfile_shargv = self.dash_dash_shfile_shargv(sys.argv, default="/dev/null/g")

        shverb = os.path.basename(shfile_shargv[0])
        assert shverb, (shfile_shargv, shverb)
        shverb_shargv = (shverb, *shfile_shargv[1:])

        print(shverb_shargv)

    def exit_if_dash_dash_help(self) -> None:
        """Print the Doc and exit zero, if '--help' in the Shell Args"""

        if "--help" in sys.argv[1:]:
            print(__main__.__doc__, file=sys.stderr)
            sys.exit(0)  # exits 0 after printing Help

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


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/litshell.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
