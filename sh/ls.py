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
  ls.py ./  # ls -hlAF --full-time -rt .
  ls.py / ~/  # ls -hlAF --full-time -rt -d / -d ~

  TZ=Europe/London ls.py --  # TZ=Europe/London ls -hlAF --full-time -rt
  TZ=America/Los_Angeles ls.py --  # TZ=America/Los_Angeles ls -hlAF --full-time -rt
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard

#

import datetime as dt
import os
import pathlib
import shlex
import subprocess
import sys

import litnotes

#

#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    default_eq_none = None
    env_tz = os.environ.get("TZ", default_eq_none)

    ow = OsWalker(env_tz)

    litnotes.print_doc_and_exit_zero_if("examples:")
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
    hardlinks: list[int] = list()  # 1
    owners: list[str] = list()  # ['jqdoe']
    groups: list[str] = list()  # ['jqdoe']
    bytecounts: list[int] = list()  # 0
    stamps: list[tuple[str, str, str]] = list()  # ['Jan', '25', '08:21']
    pathname_plus_list: list[str] = list()  # ['folder/', 'file', 'symlink@']

    bytechops: list[str] = list()  # the 0 or more Chopped Bytecounts
    fulltimes: list[str] = list()  # the 0 or more Full Times

    def __init__(self, env_tz: str | None) -> None:

        self.env_tz = env_tz

    def parse_args_if(self) -> None:
        """Parse the Command Line Args"""

        tops = self.tops

        for i, arg in enumerate(sys.argv):
            if i == 0:
                continue
            if arg.startswith("-") and (arg != "--"):
                print("usage: ls.py [--help] [PATHNAME ...]", file=sys.stderr)
                sys.exit(2)  # exits 2 for bad args

            if arg == "--":
                tops.extend(sys.argv[(i + 1) :])
                break

            tops.append(arg)

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
            shline += "           ls -hlAF --full-time -rt".strip()  # the look I wear
            shargv = shlex.split("ls -lAF -rt")  # ................  # the code I call
        else:
            shline += "           ls -hlAF --full-time -rt -d".strip()
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
        pathname_plus_list = self.pathname_plus_list

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

            # Add to Columns

            assert len(splits) > maxsplit, (len(splits), maxsplit, splits, line)

            permissions.append(splits[0])
            hardlinks.append(int(splits[1]))
            owners.append(splits[2])
            groups.append(splits[3])
            bytecounts.append(int(splits[4]))

            s0, s1, s2 = tuple(splits[5:][:3])
            stamp = (s0, s1, s2)
            stamps.append(stamp)

            pathname_plus = splits[8]
            pathname_plus_list.append(pathname_plus)

    def count_bytes(self) -> None:
        """Count bytes in the output"""

        bytecounts = self.bytecounts
        bytechops = self.bytechops

        for bytecount in bytecounts:
            bytechop = clip_int(bytecount)
            bytechops.append(bytechop)

    def stamp_date_time(self) -> None:
        """Stamp date and time"""

        tops = self.tops

        pathname_plus_list = self.pathname_plus_list
        fulltimes = self.fulltimes

        for pathname_plus in pathname_plus_list:
            pathname = self.to_pathname_guess_from_plus(pathname_plus)
            if len(tops) == 1:
                pathname = os.path.join(tops[0], pathname)

            path = pathlib.Path(pathname)
            stat = path.stat(follow_symlinks=False)

            mtime_ns = stat.st_mtime_ns  # todo: .st_ctime for -c, and/or by default
            microsecond = int((mtime_ns / 1e3) % 1e6)
            nanosecond = int(mtime_ns % 1e9)

            aware = dt.datetime.fromtimestamp(mtime_ns / 1e9).astimezone()
            o = (aware.microsecond, microsecond, nanosecond)
            assert abs(aware.microsecond - microsecond) <= 1, o

            fulltime = aware.strftime("%Y-%m-%d %H:%M:%S" + f".{nanosecond:09d}" + " %z")
            fulltimes.append(fulltime)

            # todo: compare with the .stamps

    def to_pathname_guess_from_plus(self, pathname_plus: str) -> str:
        """Guess the Pathname from the Pathname Plus"""

        marks = "%*/=@|" if (sys.platform == "darwin") else "*/=>@|"

        p0 = pathname_plus
        p1, sep, _ = p0.partition(" -> ")

        p2 = p1
        suffix = p1[-1]
        if suffix in marks:
            p2 = p1.removesuffix(suffix)

        pathname = p2

        return pathname

    def print_table(self) -> None:
        """Print the formatted table"""

        permissions = self.permissions
        hardlinks = self.hardlinks
        owners = self.owners
        groups = self.groups
        bytechops = self.bytechops
        fulltimes = self.fulltimes
        pathname_plus_list = self.pathname_plus_list

        # Left-justify the Str's and right-justify the Int's

        datatypes = (str, int, str, str, float, str, str)

        columns: tuple[list[str] | list[int], ...] = (
            permissions,
            hardlinks,
            owners,
            groups,
            bytechops,
            fulltimes,
            pathname_plus_list,
        )

        str_columns = list(list(str(_) for _ in column) for column in columns)
        for datatype, column, str_column in zip(datatypes, columns, str_columns):
            assert len(column) == len(columns[0]), (len(column), len(columns[0]))

            max_len = max(len(_) for _ in str_column)
            if (datatype is float) or (datatype is int):
                str_column[::] = list(_.rjust(max_len) for _ in str_column)
            else:
                str_column[::] = list(_.ljust(max_len) for _ in str_column)

        str_rows = zip(*str_columns)
        for str_row in str_rows:
            sep = 2 * " "
            print(sep.join(str_row))


#
# Amp up Import BuiltIns Int
#


def clip_int(i: int) -> str:
    """Find the nearest Int Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    s = str(int(i))  # '-120789'

    _, sign, digits = s.rpartition("-")  # ('', '-', '120789')
    sci = len(digits) - 1  # 5  # scientific power of ten
    eng = 3 * (sci // 3)  # 3  # engineering power of ten

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, i)

    if not eng:
        return s  # drops 'e0'

    assert len(digits) >= 4, (len(digits), eng, sci, digits, i)
    assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, i)

    precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'  # significand, mantissa, multiplier
    nearby = precise[:4]  # '120.'
    worthy = nearby.rstrip("0").rstrip(".")  # '120'  # drops '.' or'.0' or '.00'

    assert "." in nearby, (nearby, precise, eng, sci, digits, i)

    return sign + worthy + "e" + str(eng)  # '-120e3'

    # -120789 --> -120e3, etc


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


# todo: sort by creation time
# except maybe i'll end up preferring to go for date/time-created over date/time-modified when those sort orders differ


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/which.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
