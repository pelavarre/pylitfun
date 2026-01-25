#!/usr/bin/env python3

"""
usage: ls.py [-h] [-l] [-A] [-F] [-r] [-t] [-d] [PATHNAME ...]

call 'ls', but default to -hlAF -rt for one Arg, and -d for more, and ask for --full-time

positional arguments:
  PATHNAME     a relative or absolute Pathname of a Folder or File or Device or whatever

quirks:
  gives you -hlAF -rt --full-time results, no matter what you ask for, like even at:  ls.py --
  surfaces --full-time even at a macOS where 'ls --full-time' doesn't surface it
  shows engineering standard quick metric decimal round down, not Gnu quick metric binary round up
  separates columns by two or more spaces always, not just often and never just one
  calls 'ls -lAF -rt' to do most of the work, then finishes the work

options:
  -h      give byte counts as quick metric round, not exact
  -l      long lines of permissions, hardlinks, owner, group, size, full-time, and pathname
  -A      don't show . and .., do show the rest, evem when hidden by name starts with '.' Dot
  -F      add a suffix to pick apart '/' dir, '*' executable, '@' symlink, etc
  -r      sort the most recent work to the bottom, near to the next shell prompt after exit
  -t      sort by date/time last-modified
  -d      show the directory itself, not its contents

examples:

  ls.py --  # ls -hlAF --full-time -rt
  ls.py ~  # ls -hlAF --full-time -rt ~
  ls.py / ~  # ls -hlAF --full-time -rt -d / -d ~

  TZ=Europe/London ls.py --  # TZ=Europe/London ls -hlAF --full-time -rt
  TZ=America/Los_Angeles ls.py --  # TZ=America/Los_Angeles ls -hlAF --full-time -rt
"""

# todo: sort by creation time
# except maybe i'll end up preferring to go for date/time-created over date/time-modified when those sort orders differ

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import datetime as dt
import math
import os
import pathlib
import shlex
import subprocess
import sys

import litnotes


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    default_eq_none = None
    env_tz = os.environ.get("TZ", default_eq_none)

    ow = OsWalker(env_tz)

    ow.parse_args_if()
    ow.call_shell_ls_once()
    ow.scrape_columns()

    ow.count_bytes()
    ow.stamp_date_time()

    ow.print_table()


class OsWalker:
    """Scrape from 'ls -lAF -rt' to improve calculation & distribution of -h and --full-time"""

    env_tz: str | None

    tops: list[str] = list()  # the 0 or more Pathname's given
    lines: list[str] = list()  # the Lines of Text from the Shell ls Command

    headlines: list[str] = list()  # the 0 or 1 Head Lines

    permissions: list[str] = list()  # ['-rw-r--r--', '-rw-r--r--@', 'drwxr-xr-x', etc ]
    hardlinks: list[int] = list()
    owners: list[str] = list()
    groups: list[str] = list()
    bytecounts: list[int] = list()
    stamps: list[tuple[str, str, str]] = list()
    pathnames: list[str] = list()  # todo: report in common, extra, missing

    bytechops: list[str] = list()  # the 0 or more Chopped Bytecounts
    fulltimes: list[str] = list()  # the 0 or more Full Times

    def __init__(self, env_tz: str | None) -> None:

        self.env_tz = env_tz

    def parse_args_if(self) -> None:
        """Parse the Command Line Args"""

        tops = self.tops

        for arg in sys.argv[1:]:
            if arg == "--":
                break
            if arg.startswith("-"):
                print(f"usage: ls.py [--help] [PATHNAME ...]", file=sys.stderr)
                sys.exit(2)  # exits 2 for bad Args

        tops.extend(sys.argv[1:])

    def call_shell_ls_once(self) -> None:
        """Call the Shell 'ls' command exactly once"""

        env_tz = self.env_tz
        tops = self.tops  # todo: quote .top as "~/..." when it fits
        lines = self.lines

        stderr_fileno = sys.stderr.fileno()

        # Trace how to call the Shell 'ls' command, where it is distributed well

        shline = ""
        if env_tz:
            shline += f"TZ={shlex.quote(env_tz)} "  # _calmly not needed

        if not tops[1:]:
            shline += "ls -hlAF --full-time -rt"
            shargv = shlex.split("ls -lAF -rt")
        else:
            shline += "ls -hlAF --full-time -rt -d"
            shargv = shlex.split("ls -lAF -rt -d")

        shline += " " + " ".join(shlex_quote_calmly(_) for _ in tops)
        shargv += tops

        print(f"+ {shline}", file=sys.stderr)

        # Call the Shell 'ls' command exactly once

        run = subprocess.run(
            shargv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if run.stderr:
            os.write(stderr_fileno, run.stderr)

        if run.returncode or run.stderr:
            print(f"+ exit {run.returncode}", file=sys.stderr)
            sys.exit(run.returncode)

        #

        stdout = run.stdout
        decode = stdout.decode()
        splitlines = decode.splitlines()

        lines.extend(splitlines)

    def scrape_columns(self) -> None:
        """Scrape the 9 Columns from the 'ls' output"""

        lines = self.lines

        headlines = self.headlines

        permissions = self.permissions
        hardlinks = self.hardlinks
        owners = self.owners
        groups = self.groups
        bytecounts = self.bytecounts
        stamps = self.stamps
        pathnames = self.pathnames

        maxsplit = 8
        assert len("permission hardlink owner group bytecount stamp stamp stamp".split()) == 8

        for index, line in enumerate(lines):
            splits = line.split(maxsplit=maxsplit)

            # Shrug off the one Total Line at the Start

            if len(splits) == 2:
                assert index == 0, (index, line)
                assert splits[0] == "total", (splits, line)
                total = int(splits[1])
                assert total >= 0, (total,)

                headlines.append(line)

                continue

            # Else take up a Pathname

            assert len(splits) > maxsplit, (len(splits), maxsplit, splits, line)

            permissions.append(splits[0])
            hardlinks.append(int(splits[1]))
            owners.append(splits[2])
            groups.append(splits[3])
            bytecounts.append(int(splits[4]))

            (s0, s1, s2) = tuple(splits[5:][:3])
            stamp = (s0, s1, s2)
            stamps.append(stamp)

            pathnames.append(splits[8])

    def count_bytes(self) -> None:
        """Count bytes in the output"""

        bytecounts = self.bytecounts
        bytechops = self.bytechops

        for bytecount in bytecounts:
            bytechop = chop(bytecount)
            bytechops.append(bytechop)

    def stamp_date_time(self) -> None:
        """Stamp date and time"""

        pathnames = self.pathnames
        fulltimes = self.fulltimes

        for pathname in pathnames:
            path = pathlib.Path(pathname)

            stat = path.stat()

            mtime_ns = stat.st_mtime_ns  # todo: .st_ctime for -c, and/or by default
            microsecond = int((mtime_ns / 1e3) % 1e6)
            nanosecond = int(mtime_ns % 1e9)

            aware = dt.datetime.fromtimestamp(mtime_ns / 1e9).astimezone()
            o = (aware.microsecond, microsecond, nanosecond)
            assert abs(aware.microsecond - microsecond) <= 1, o

            fulltime = aware.strftime("%Y-%m-%d %H:%M:%S" + f".{nanosecond:09d}" + " %z")
            fulltimes.append(fulltime)

            # todo: compare with the .stamps

    def print_table(self) -> None:
        """Print the formatted table"""

        permissions = self.permissions
        hardlinks = self.hardlinks
        owners = self.owners
        groups = self.groups
        bytechops = self.bytechops
        fulltimes = self.fulltimes
        pathnames = self.pathnames

        # Left-justify the Str's and right-justify the Int's

        columns: tuple[list[str] | list[int], ...] = (permissions, hardlinks, owners, groups, bytechops, fulltimes, pathnames)

        str_columns = list(list(str(_) for _ in column) for column in columns)
        for column, str_column in zip(columns, str_columns):
            assert len(column) == len(columns[0]), (len(column), len(columns[0]))

            max_len = max(len(_) for _ in str_column)
            if isinstance(column[0], int):
                str_column[::] = list(_.rjust(max_len) for _ in str_column)
            else:
                str_column[::] = list(_.ljust(max_len) for _ in str_column)

        str_rows = zip(*str_columns)
        for str_row in str_rows:
            sep = 2 * " "
            print(sep.join(str_row))


#
# Amp up Import BuiltIns Float
#


def chop(f: float) -> str:
    """Find a nonzero Float Literal closer to zero with <= 3 Digits"""

    if not f:
        lit = "-0e0" if (math.copysign(1e0, f) < 0e0) else "0"
        return lit

    s = ("-" + _chop_nonnegative_(-f)) if (f < 0) else _chop_nonnegative_(f)

    return s

    # never says '0' except to mean Float +0e0 and Int 0
    # values your ink & time properly, by never saying '.' nor '.0' nor '.00' nor 'e+0'


def _chop_nonnegative_(f: float) -> str:
    """Find a nonnegative nonzero Float Literal closer to zero with <= 3 Digits"""

    assert f > 0, (f,)

    # Form the Scientific Notation

    sci = int(math.floor(math.log10(f)))
    mag = f / (10**sci)
    assert 1 <= mag < 10, (mag, f)

    # Choose a Floor, in the way of Engineering Notation

    triple = str(int(100 * mag))  # 100 == 10 ** 2
    assert "100" <= triple <= "999", (triple, mag, sci, f)

    eng = 3 * (sci // 3)  # ..., -6, -3, 0, 3, 6, ...
    span = 1 + sci - eng
    assert 1 <= span <= 3, (span, triple, mag, eng, sci, f)

    # Stand on the chosen Floor, but never say '.' nor '.0' nor '.00'

    dotted = triple[:span] + "." + triple[span:]
    dotted = dotted.rstrip("0").rstrip(".")  # lacks '.' if had only '.' or'.0' or '.00'

    # And never say 'e0' either

    lit = f"{dotted}e{eng}".removesuffix("e0")  # may lack both '.' and 'e'

    # But never wander far

    float_lit = float(lit)

    diff = f - float_lit
    precision = 10 ** (eng - 3 + span)
    assert diff <= precision, (diff, precision, f, sci, mag, triple, eng, span, dotted, lit)

    return lit

    # Python math.trunc is a round towards zero, but can be zero, and leaps to the int ceil/ floor


def _try_chop_() -> None:

    pairs = [
        (0, "0"),
        (0e0, "0"),
        (-0e0, "-0e0"),
        #
        (1e-4, "100e-6"),
        (1e-3, "1e-3"),
        (1.2e-3, "1.2e-3"),
        (9.876e-3, "9.87e-3"),  # not '9.88e-3'
        (1e-2, "10e-3"),
        (1e-1, "100e-3"),
        #
        (1e0, "1"),
        (1e1, "10"),
        (1.2e1, "12"),
        (9.876e1, "98.7"),  # not '98.8'
        (1e2, "100"),
        (1.23e2, "123"),
        #
        (1e3, "1e3"),
        #
    ]

    for f, lit in pairs:

        chop_f = chop(f)
        assert chop_f == lit, (chop_f, lit, f"{f:.2e}", f)

        if f:
            chop_minus_f = chop(-f)
            assert chop_minus_f == (f"-{lit}"), (chop_f, lit, f"{f:.2e}", f)


_try_chop_()


#
# Amp up Import ShLex
#


assert shlex.quote("HEAD~1") == "'HEAD~1'", (shlex.quote("HEAD~1"),)


def shlex_quote_calmly(arg: str) -> str:
    """Quote like ShLex Quote, but not more carefully at ~ than at @, except for starts with ~"""

    quote = shlex.quote(arg)

    at_quotable = arg.replace("~", "@")
    at_quote = shlex.quote(at_quotable)

    if at_quote == at_quotable:
        if not arg.startswith("~"):
            return arg

    return quote


assert shlex_quote_calmly("HEAD~1") == "HEAD~1", (shlex_quote_calmly("HEAD~1"),)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/which.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
