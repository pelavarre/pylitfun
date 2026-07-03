#!/usr/bin/env python3

"""
usage: json_loads_object_pairs_hook.py --

find key:value pairs of json files that contradict one another

options:
  -h, --help   show this help message and exit
  --strict     also show duplications, not only contradictions

examples:
  echo "{}" >j.json
  json_loads_object_pairs_hook.py --  # surfaces contradictions
  json_loads_object_pairs_hook.py --strict  # surfaces contradictions & duplications
  echo "{}" >j.json && cat j.json |json_loads_object_pairs_hook.py --strict  # shows checking a file
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import collections
import datetime as dt
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


# Pacific = zoneinfo.ZoneInfo("America/Los_Angeles")
# PacificLaunch = dt.datetime.now(Pacific)

Launch = dt.datetime.now()


def main() -> None:
    """Run from the Shell, but tell uncaught Exceptions to launch the Py Repl"""

    # sys.excepthook = sys_excepthook  # catches SystemExit, KeyboardInterrupt, etc
    # try_main()

    pass  # FIXME: todo0: come meet our __main__.__doc__ spec

    print("litjson.py: passed supercalifragilistically", file=sys.stderr)


#
# Amp up Import Json
#


def json_loads_object_pairs_hook(pairs: list[tuple[object, object]]) -> object | None:
    """Shout out each same or different Value discarded by duplicates of a Key"""

    d = dict(pairs)

    keys = list()
    for k, v in pairs:
        if d[k] != v:
            keys.append(k)
            print(f"KeyError: [{k!r}] = {v!r} for awhile", file=sys.stderr)

    for k in collections.Counter(keys):
        print(f"KeyError: [{k!r}] = {d[k]!r} last of all", file=sys.stderr)

    return d

    # 'def json_loads_object_pairs_hook' last modified for py2def.py on 2026-06-27 or later


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litjson.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
