#!/usr/bin/env python3


import difflib
import typing


def list_assert_eq(
    a: typing.Iterable[object], b: typing.Iterable[object], occasion: object = None
) -> None:
    """Assert A and B are equal when taken as List[Str]"""

    o = occasion

    aa = list(a)  # narrows to List, not Tuple/ Iterator/ Dict Keys/ Dict Values/ etc
    bb = list(b)

    strs_a = list(str(_) for _ in aa)  # defaults to Str, not Repr,
    strs_b = list(str(_) for _ in bb)  # although caller may send us Repr

    diffs = list(difflib.unified_diff(a=strs_a, b=strs_b, fromfile="a", tofile="b", lineterm=""))

    a_set = set(strs_a)
    b_set = set(strs_b)
    ao = sorted(a_set - b_set)
    bo = sorted(b_set - a_set)

    if aa == bb:  # does require List Eq  # does Not require Zero Diffs in Strs of List
        return

    print("\n".join(diffs))  # prints the Diffs in Strs of List, no matter if empty
    assert diffs, (strs_a, strs_b, aa, bb)  # requires not empty, only after printing

    if len(repr(strs_a) + repr(strs_b)) >= 100:  # raises only the Lengths, when many Diffs
        if o is not None:  # raises with Occasion
            assert not diffs, (o, len(aa), len(bb), len(ao), len(bo), ao, bo)
        assert not diffs, (len(aa), len(bb), len(ao), len(bo), ao, bo)  # raises without Occasion

    if o is not None:  # raises with Occasion and with Repr's
        assert not diffs, (o, len(aa), len(bb), len(ao), len(bo), ao, bo, aa, bb)
    assert not diffs, (len(aa), len(bb), len(ao), len(bo), ao, bo, aa, bb)  # raises with Repr's

    # todo: still prints and raises too much of large Diffs?

    # 'def list_assert_eq' last modified for py2def.py on 2026-11-07 or later


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litlist.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
