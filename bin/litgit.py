#!/usr/bin/env python3

"""
usage: litgit.py [-h] SHFILE [SHWORD ...]

unabbreviate subcommands to call Git, but trace them in full

positional arguments:
  SHFILE      disclose who is calling (often a pathname of bin/git-verb/g*)
  SHWORD      option or positional argument of Git

options:
  -h, --help  show this help message and exit

quirks:
  do dozens of good things that Git Aliases can only do when coded as Scripts of the Shell $PATH
  see also bin/git-verbs/, where we solve these same puzzles, but as Shell Scripts, not as Python

examples:
  : gg ... && git grep -ai -w -e gg -e ggl
    litgit.py ~/gg -- -w gg ggl
      gg -w gg ggl
  : gla && git log --pretty=fuller --no-decorate --color-moved --numstat --author=jqdoe -p
    litgit.py ~/gla -- -p
      gla -p
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import argparse
import collections.abc
import dataclasses
import datetime as dt
import difflib
import os
import shlex
import signal
import subprocess
import sys
import textwrap

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


# Run from the Shell Command Line


def main() -> None:
    """Run from the Shell Command Line"""

    parser = arg_doc_to_parser(__doc__ or "")

    argv_minus = sys.argv[1:]
    ns = shell_args_take_in(argv_minus, parser=parser)

    # Require a known Sh File Basename

    gg = GitGopher(shfile=ns.shfile, shwords=ns.shwords)
    keys = sorted(gg.func_by_verb.keys())

    pathname = gg.shfile
    basename = os.path.basename(pathname)

    if basename not in keys:
        print(f"don't choose {basename!r}, do choose from {keys}", file=sys.stderr)
        sys.exit(2)

    func = gg.func_by_verb[basename]

    # Go for it

    returncode = func()

    if returncode:
        sys.exit(returncode)


def arg_doc_to_parser(doc: str) -> ArgDocParser:
    """Declare the Options & Positional Arguments"""

    assert argparse.ZERO_OR_MORE == "*"

    # Spell out what our --help says

    parser = ArgDocParser(doc, add_help=True)

    shfile_help = "disclose who is calling (often a pathname of bin/git-verb/g*)"
    shword_help = "option or positional argument of Git"

    parser.add_argument("shfile", metavar="SHFILE", help=shfile_help)
    parser.add_argument("shwords", metavar="SHWORD", nargs="*", help=shword_help)

    # Succeed

    return parser


def shell_args_take_in(argv_minus: list[str], parser: ArgDocParser) -> argparse.Namespace:
    """Take in the Shell Args"""

    ns = parser.parse_args_if(argv_minus)  # often prints help & exits zero

    return ns


class GitGopher:
    """Init and run, once"""

    shfile: str
    shwords: list[str]
    stdout_isatty: bool

    func_by_verb: dict[str, collections.abc.Callable[..., int]]

    def __init__(self, shfile: str, shwords: list[str]) -> None:

        self.shfile = shfile
        self.shwords = shwords
        self.stdout_isatty = sys.stdout.isatty()  # sampled once

        self.func_by_verb = self._form_func_by_verb_()

    def _form_func_by_verb_(self) -> dict[str, collections.abc.Callable[..., int]]:
        """Say how to abbreviate each verb phrase"""

        d = {
            "gcl": self.git_clean_dffx,
            "grhu": self.git_reset_hard_upstream,
            "gsis": self.git_status_ignored_short,
        }

        return d

    def git_clean_dffx(self) -> int:  # gcl
        """
        usage: gcl [-h] [-n]

        remove untracked files from the working tree

        options:
          -h, --help  show this help message and exit
          -n          dry run, to show what would be deleted, without deleting anything

        works as one of:
          : gcl && echo Press ⌃D && cat - >/dev/null && git clean -dffxq
          : grhu && echo Press ⌃D && cat - >/dev/null && git reset --hard @{upstream}
          : gsis && git status --ignored --short

        defaults to git ops choices:
          -d = delete untracked dirs
          -ff = delete untracked nested .git/ dirs and other files and dirs, without asking again
          -x = delete the untracked files of 'git status --ignored', not only unignored files
          -q = don't print the name of each deleted dir or file

        quirks:
          asks for ⌃D to auth (or ⌃C to quit), before deleting anything, when you don't say -n

        examples:
          gcl
          gcl -n
          git clean -ndffx
        """

        doc = self.git_clean_dffx.__doc__
        parser = ArgDocParser(doc or "", add_help=True)

        n_help = "dry run, to show what would be deleted, without deleting anything"
        parser.add_argument("-n", action="count", help=n_help)

        shwords = self.shwords
        if not shwords and not sys.argv[2:]:
            ns = parser.parse_args_if([])  # often prints help & exits zero
        else:
            ns = parser.parse_args_if(shwords or ["--"])  # often prints help & exits zero

        # Guess what happens if auth'ed

        if ns.n:

            print(": gcl -n && git clean -ndffx", file=sys.stderr)

            shline = "git clean -ndffx"

            run = subprocess.run(shlex.split(shline))
            returncode = run.returncode

            return returncode

        # Call on Git only if auth'ed, if not cancelled

        shline = "git clean -dffxq"
        print(f": gcl && echo Press ⌃D && cat - >/dev/null && {shline}", file=sys.stderr)
        print(f"Press ⌃D to auth:  {shline}", file=sys.stderr)

        assert int(0x80 + signal.SIGINT) == 130
        try:
            sys.stdin.read()
        except KeyboardInterrupt:  # macOS prints "^" and "C" without a "\r\n"
            returncode = 130
            return returncode

        run = subprocess.run(shlex.split(shline))
        returncode = run.returncode

        return returncode

        # git clean -ndffx
        # ... && git clean -dffxq

    def git_reset_hard_upstream(self) -> int:  # grhu
        """
        usage: grhu [-h]

        roll back to what you last fetched and checked out

        options:
          -h, --help  show this help message and exit

        works lots more simply after:
          git rebase --abort
          git cherry-pick --abort
          git checkout main

        quirks:
          asks for ⌃D to auth (or ⌃C to quit), before overwriting or deleting files

        examples:
          grhu
        """

        doc = self.git_reset_hard_upstream.__doc__
        parser = ArgDocParser(doc or "", add_help=True)

        shwords = self.shwords
        if not shwords and not sys.argv[2:]:
            parser.parse_args_if([])  # often prints help & exits zero
        else:
            parser.parse_args_if(shwords or ["--"])  # often prints help & exits zero

        # Call on Git only if auth'ed, if not cancelled

        shline = "git reset --hard @{upstream}"
        print(f": grhu && echo Press ⌃D && cat - >/dev/null && {shline}", file=sys.stderr)
        print(f"Press ⌃D to auth:  {shline}", file=sys.stderr)

        assert int(0x80 + signal.SIGINT) == 130
        try:
            sys.stdin.read()
        except KeyboardInterrupt:  # macOS prints "^" and "C" without a "\r\n"
            returncode = 130
            return returncode

        run = subprocess.run(shlex.split(shline))
        returncode = run.returncode

        return returncode

        # ... && git reset --hard @{upstream}

    def git_status_ignored_short(self) -> int:  # gsis
        """
        usage: gsis [-h]

        lists untracked files to remove from (or add to) the working tree

        options:
          -h, --help  show this help message and exit

        works as one of:
          : gcl && echo Press ⌃D && cat - >/dev/null && git clean -dffxq
          : gsis && git status --ignored --short

        quirks:
          doesn't list
            find . -type p  # untracked named pipes
            find . -type d -empty -not -path '*/.git/*'  # empty dirs

        examples:
          gsis
          git clean -ndffx
        """

        doc = self.git_status_ignored_short.__doc__
        parser = ArgDocParser(doc or "", add_help=True)

        shwords = self.shwords
        if not shwords and not sys.argv[2:]:
            parser.parse_args_if([])  # often prints help & exits zero
        else:
            parser.parse_args_if(shwords or ["--"])  # often prints help & exits zero

        # Say how to list some untracked things that Git Status refuses to list

        print("+ : find . -type p", file=sys.stderr)
        print("+ : find . -type d -empty -not -path '*/.git/*'", file=sys.stderr)

        # Call Git Status Ignored Short

        print(": gsis && git status --ignored --short", file=sys.stderr)
        shline = "git status --ignored --short"

        run = subprocess.run(shlex.split(shline))
        returncode = run.returncode

        return returncode

        # : find . -type p
        # && : find . -type d -empty -not -path '*/.git/*'
        # && git status --ignored --short


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
# Amp up Import DateTime as DT
#


def dt_timedelta_strftime(td: dt.timedelta, depth: int = 2, str_zero: str = "0s") -> str:
    """Give 'w d h m s ms us ms' to mean 'weeks=', 'days=', etc"""

    # Pick Weeks out of Days, Minutes out of Seconds, and Millis out of Micros

    w = td.days // 7
    d = td.days % 7

    h = td.seconds // 3600
    h_s = td.seconds % 3600
    m = h_s // 60
    s = h_s % 60

    ms = td.microseconds // 1000
    us = td.microseconds % 1000

    # Catenate Value-Key Pairs in order, but strip leading and trailing Zeroes,
    # and choose one unit arbitrarily when speaking of any zeroed TimeDelta

    keys = "w d h m s ms us".split()
    values = (w, d, h, m, s, ms, us)
    pairs = list(zip(keys, values))

    chars = ""
    count = 0
    for index, (k, v) in enumerate(pairs):
        if (chars or v) and any(values[index:]):
            chars += "{}{}".format(v, k)
            count += 1

            if count >= depth:  # truncates, does Not round up
                break

    str_zeroes = list((str(0) + _) for _ in keys)
    if not chars:
        assert str_zero in str_zeroes, (str_zero, str_zeroes)
        chars = str_zero

    # Succeed

    return chars  # '9ms331us' to mean 9ms 331us <= t < 9ms 333us


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


_ = """  # todo's

# todo: fetch the per-verb help in the caller

# todo: next port = "grl": "git reflog --date=relative --numstat",
# todo: grl, grl --, grl -4

# todo: port ever more of our three dozen Git Aliases at bin/git.py
# todo: port the --make-bin work into here from bin/git.py

"""


# 3456789_123456789_123456789_123456789 123456789_123456789_123456789_123456789 123456789_123456789

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litgit.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
