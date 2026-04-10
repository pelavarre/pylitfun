#!/usr/bin/env python3

"""
usage: uptime.py [-h] [-p]

speak time since last restart as years, weeks, days, hours, and minutes

options:
  -h, --help    show this help message and exit
  -p, --pretty  show as years & weeks, not just as days & hours

quirks:
  redundant with 'uptime --pretty' at many Linux and at few macOS

examples:
  uptime.py --pretty
  uptime.py --
  uptime.py --h
"""

import __main__
import datetime as dt
import os
import shlex
import subprocess
import sys
import textwrap

#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    parse_args_if()  # often prints help & exits zero

    # Sample when now is

    aware = dt.datetime.now(dt.timezone.utc)
    hms = aware.strftime("%H:%M:%S")

    yd, h, m = fetch_uptime_if()  # often exits nonzero, especially before 1 Day of Up Time

    # Format when now is

    y = yd // 365  # one more leap day off of standard time, every four years
    wd = yd % 365

    w = wd // 7
    d = wd % 7

    years = "year" if (y == 1) else "years"
    weeks = "week" if (w == 1) else "weeks"
    days = "day" if (d == 1) else "days"
    hours = "hour" if (h == 1) else "hours"
    minutes = "minute" if (m == 1) else "minutes"

    cells = list()

    if y:
        cells.append(f"{y} {years}")
    if w:
        cells.append(f"{w} {weeks}")
    if d:
        cells.append(f"{d} {days}")
    if h:
        cells.append(f"{h} {hours}")

    if m or not cells:
        cells.append(f"{m} {minutes}")

    # Print when now is

    print(hms, "", "up", ", ".join(str(_) for _ in cells))


def parse_args_if() -> None:
    """Parse the Command Line Args"""

    # Find the docs

    doc = __main__.__doc__
    assert doc

    helpdoc = doc.strip()

    usage = helpdoc.splitlines()[0]

    testdoc = "\n".join(doc[doc.index("examples:") :].splitlines()[1:])
    testdoc = textwrap.dedent(testdoc).strip()

    # Return happy, if can do

    alfa = sys.argv[1:]

    if alfa == ["--"]:
        return

    if alfa == ["-p"]:
        return

    if len(alfa) == 1:
        alfa0 = alfa[0]
        if alfa0.startswith("--") and "--pretty".startswith(alfa0):
            return

    # Else print examples

    if not alfa:

        print()
        print(testdoc)
        print()

        sys.exit(0)  # exits 0 after printing examples

    # Else print Help Lines

    if len(alfa) == 1:
        alfa0 = alfa[0]
        if (alfa0 == "-h") or (alfa0.startswith("--") and "--help".startswith(alfa0)):
            print(helpdoc)
            sys.exit(0)  # exits 0 after printing Help

    # Else print one Usage Line

    print(usage)
    sys.exit(2)  # exits 2 after bad Args


def fetch_uptime_if() -> tuple[int, int, int]:
    """Run 'uptime' and scrape days, hours, & minutes since last restart, else exit"""

    shline = "uptime"
    argv = shlex.split(shline)

    # print(f"+ {shline}", file=sys.stderr)

    run = subprocess.run(argv, input=b"", stdout=subprocess.PIPE)
    stdout = run.stdout

    returncode = run.returncode
    if not returncode:

        decode = stdout.decode()
        lines = decode.splitlines()
        if len(lines) == 1:

            line = lines[-1]
            words = line.split()
            if words[4:]:

                stamp, up, _yd_, days, hhmm = words[:5]
                if stamp and _yd_ and hhmm:
                    if (up, days) == ("up", "days,"):

                        yd = int(_yd_)  # counts days of one or more years

                        hh, mm = hhmm.split(":")
                        h = int(hh)
                        m = int(mm.removesuffix(","))

                        return (yd, h, m)

    os.write(sys.stdout.fileno(), run.stdout)

    if returncode:
        print(f"+ exit {returncode}", file=sys.stderr)
        sys.exit(returncode)

    sys.exit(1)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/which.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
