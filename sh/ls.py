#!/usr/bin/env python3

"""
usage: ls.py [--help] [-h] [-l] [-A] [-F] [-r] [-t] [-d] [PATHNAME ...]

call 'ls', but default to -hlAF -rt for one Arg, and -d for more, and ask for --full-time

positional arguments:
  PATHNAME     a brick of the shell pipe

quirks:
  gives you -hlAF -rt --full-time results, no matter what you ask for, like even at:  ls.py --
  surfaces --full-time even at a macOS where 'ls --full-time' doesn't surface it
  shows engineering standard quick metric decimal round down, not Gnu quick metric binary round up
  separates columns by two or more spaces always, not just often and never just one
  calls 'ls -lAF -rt' to do most of the work, then finishes the work

options:
  --help  show this help message and exit
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


import subprocess

import litnotes


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    ow = OsWalker()

    ow.parse_args_if()
    ow.call_shell_ls_once()
    ow.scrape_columns()

    ow.count_bytes()
    ow.stamp_date_time()

    ow.print_table()


class OsWalker:

    tops: list[str] = list()  # the pathnames given
    ls_argv: list[str] = list()  # .split("ls -hlAF -rt") plus 0 or 1 Tops, or plus ["-d"] and Tops

    permissions: list[str] = list()  # ['-rw-r--r--', '-rw-r--r--@', 'drwxr-xr-x', etc ]
    hardlinks: list[int] = list()
    owners: list[str] = list()
    groups: list[str] = list()
    bytecounts: list[int] = list()
    fulltimes: list[str] = list()
    pathnames: list[str] = list()  # todo: report in common, extra, missing

    def parse_args_if(self) -> None:
        """Parse command line arguments"""
        ...

    def call_shell_ls_once(self) -> None:
        """Call the shell ls command once"""
        ...

    def scrape_columns(self) -> None:
        """Scrape columns from ls output"""
        ...

    def count_bytes(self) -> None:
        """Count bytes in the output"""
        ...

    def stamp_date_time(self) -> None:
        """Stamp date and time"""
        ...

    def print_table(self) -> None:
        """Print the formatted table"""
        ...


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/which.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
