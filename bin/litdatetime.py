#!/usr/bin/env python3

"""
usage: litdatetime.py --

show how we clip a date time delta
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import datetime as dt
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run from the Shell"""

    s = 1
    m = 60 * s
    h = 60 * m
    d = 24 * h

    clip_by_seconds_depth: dict[tuple[int, int | None], str] = {
        (0, None): "0s",
        (4 * m, None): "4m",
        (4 * m + 29 * s, None): "4m29s",
        (d, None): "1d",
        (d + 23 * h + 59 * m + 59 * s, 1): "1d",
        (d + 23 * h + 59 * m + 59 * s, None): "1d23h",
        (d + 23 * h + 59 * m + 59 * s, -1): "1d23h59m59s",
    }

    for seconds_depth, clip in clip_by_seconds_depth.items():
        clip_seconds, clip_depth = seconds_depth

        timedelta = dt.timedelta(seconds=clip_seconds)
        if clip_depth is None:
            _clip_ = datetime_timedelta_clip(timedelta)
        else:
            _clip_ = datetime_timedelta_clip(timedelta, depth=clip_depth)

        assert _clip_ == clip, (_clip_, timedelta, clip_seconds, seconds_depth)

    print("litdatetime.py: passed supercalifragilistically", file=sys.stderr)


#
# Amp up Import DateTime
#


def datetime_timedelta_clip(td: dt.timedelta, depth: int = 2) -> str:
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

            if depth >= 1:
                if count >= depth:  # truncates, does Not round up
                    break

    str_zero = "0s"
    str_zeroes = list((str(0) + _) for _ in keys)
    if not chars:
        assert str_zero in str_zeroes, (str_zero, str_zeroes)
        chars = str_zero

    # Succeed

    return chars  # '4m29s'

    # 'def datetime_timedelta_clip' last modified for py2def.py on 2026-01-09 or later


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litdatetime.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
