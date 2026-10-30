#!/usr/bin/env python3

"""
usage: litint.py --

chop ints down to 3 Digits and an SI Prefix (or a multiple-of-three Exponent)

examples:
  bin/litint.py --  # runs tests
  from litint import decimal_int_chop_to_eng_metric as imetric
  from litint import decimal_int_chop_to_eng as ichop
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import decimal
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'

_: object  # blocks Mypy from narrowing the Datatype of '_ =' at first mention


def main() -> None:
    """Run from the Shell"""

    _self_test_()


#
# Amp up Import Decimal
#


def decimal_int_chop_to_eng_metric(n: int, one: str) -> str:
    """Convert 9876 to '9.87µs' when one == '1ns', and so on"""

    # Pick apart exactly how to style an 'n' of 1

    si_quanta = tuple("qryzafpnµm") + ("",) + tuple("kMGTPEZYRQ")  # the SI Prefixes since Nov/2022

    numeral, quantum, unit = (one[0], "", one[1:])  # from one == '1'  # from one == '1Ω'
    if one[2:]:
        numeral, quantum, unit = (one[0], one[1], one[2:])  # from one == '1nH'
        if one[1] not in si_quanta:
            numeral, quantum, unit = (one[0], "", one[1:])  # from one == '1Hz'

            # caller must append 'Pa', 'min', 'mol', etc to duck P=10**15 m=10**-3 etc

    assert numeral == "1", (numeral, quantum, unit, one)
    quantum_index = si_quanta.index(quantum)
    quanta = si_quanta[quantum_index:]

    # Clip the 'n' value

    chop = decimal_int_chop_to_eng(n)  # raises ValueError when a Float breaks our ': int' contract

    before, sep, after = chop.partition("e")
    assert bool(sep) == bool(after), (sep, after, before, chop, n)

    # Restyle the clipped 'n' value

    i = 0
    if sep:
        exp = int(after)
        assert (exp % 3) == 0, (exp, before, sep, after, chop, n)
        i = exp // 3
        assert i >= 1, (i, exp, before, sep, after, chop, n)

    q = quanta[i]  # (q) may be Empty Str
    rep = before + q + unit  # (q + unit) may be Empty Str

    # Succeed

    return rep  # '0Ω'  # '12ns'  # '9.87µH'  # '654ms'

    # 'def decimal_int_chop_to_eng_metric' last modified for py2def.py on 2026-10-28 or later


# (coded for quick review = without docstring, without comments, & without asserts
def __(n: int) -> str:

    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)
    D = ctx.create_decimal

    clip = D(n).to_eng_string().lower().replace("e+", "e")

    return clip


# (coded in full)
def decimal_int_chop_to_eng(n: int) -> str:
    """Rep the exact Int, else chop down to 3 Digits at an explicit Multiple-of-Three Exponent"""

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)  # the towards-zero kind of "Down"
    D = ctx.create_decimal  # truncating is not ceiling, floor, half down/up, half even, nor 0 5 up

    clip = D(i).to_eng_string().lower().replace("e+", "e")

    if -(2**53) < i < 2**53:
        aif = abs(int(float(clip)))
        assert aif <= abs(i), (aif, abs(i), i, n)

    return clip  # int(float(clip)) == n, or near to n but a little closer to zero

    # raises ValueError above n = 10**4300 - 1

    # '-9.99e3'  # '-2'  # '0'  # '1'  # '987'  # '1.00e3'  # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of float, int, int, int, int, float, float, float, float
    # with the unsigned 'e' standing in place of the int digits we did chop off

    # Python's hex int("987e3", 0x10) == 0x9_87E3 does nearly collide with our '987e3' lacking '.'
    # Python Floats overflow out beyond '179e306', but we correctly clip '180 * 10**306' and above

    # 'def decimal_int_chop_to_eng' last modified for py2def.py on 2026-08-25 or later


# (coded to run without 'import decimal')
def repr_int_chop_to_eng(n: int) -> str:
    """Rep the exact Int, else chop down to 3 Digits at an explicit Multiple-of-Three Exponent"""

    i = int(repr(n))  # raises ValueError when a Float breaks our ': int' contract
    s = repr(i)  # '-120789'
    _, dash, digits = s.rpartition("-")  # ('', '-', '120789')

    sci = len(digits) - 1  # 5
    eng = 3 * (sci // 3)  # 3

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, n)

    clip = s
    if eng:

        assert len(digits) >= 4, (len(digits), eng, sci, digits, n)
        assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, n)

        precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'
        nearby = precise[:4]  # '120.'  # significand, mantissa, multiplier  # with a dot included
        worthy = nearby.rstrip(".")  # '120' # drops a single trailing '.'

        assert "." in nearby, (nearby, precise, eng, sci, digits, n)

        clip = dash + worthy + "e" + str(eng)  # '-120e3' as a way of saying -120*10**3

    if -(2**53) < i < 2**53:
        aif = abs(int(float(clip)))
        assert aif <= abs(i), (aif, abs(i), i, n)

    return clip

    # raises ValueError above n = 10**4300 - 1

    # '-9.99e3'  # '-2'  # '0'  # '1'  # '987'  # '1.00e3'  # '9.87e3'  # '98.7e3'  # '987e3'
    # as if repr of float, int, int, int, int, float, float, float, float
    # with the unsigned 'e' standing in place of the int digits we did chop off

    # Python's hex int("987e3", 0x10) == 0x9_87E3 does nearly collide with our '987e3' lacking '.'
    # Python Floats overflow out beyond '179e306', but we correctly clip '180 * 10**306' and above

    # 'def repr_int_chop_to_eng' last modified for py2def.py on 2026-08-22 or later


#
# Test things
#


def _self_test_() -> None:
    """Test things"""

    # import litsys
    # sys.excepthook = litsys.sys_excepthook_pdb_pm

    for i_one, s in _imetric_str_by_int_str_.items():
        i, one = i_one

        imetric = decimal_int_chop_to_eng_metric
        _s_ = imetric(i, one=one)  # works near 'import decimal'
        assert _s_ == s, (_s_, s)

    for i, s in _ichop_str_by_int_.items():

        ichop = decimal_int_chop_to_eng
        _s_ = ichop(i)  # works near 'import decimal'
        assert _s_ == s, (_s_, s)

        ichop = repr_int_chop_to_eng
        _s_ = repr_int_chop_to_eng(i)  # works without 'import decimal'
        assert _s_ == s, (_s_, s)

    print("litint.py: passed supercalifragilistically", file=sys.stderr)


_imetric_str_by_int_str_ = {
    (0, "1Ω"): "0Ω",
    (12, "1ns"): "12ns",
    (9879, "1nH"): "9.87µH",
    (654_654, "1µs"): "654ms",
    (1000, "1"): "1.00k",  # not "1.00K"  # caller can append whatever unit
    (1000, "1Pa"): "1.00Ea",  # sadly, not "1.00kPa", caller must append such units
    (1219 * 10**6, "1Hz"): "1.21GHz",  # close to the famous 1.21GW
}

# sorted by int of digits of str

# caller must append 'Pa', 'min', 'mol', etc to duck P=10**15 m=10**-3 etc


_ichop_str_by_int_ = {
    -9999: "-9.99e3",  # not '-1e+04'
    -2: "-2",
    0: "0",  # not '0e0'  # not '0.0'
    1: "1",
    42: "42",
    288: "288",  # not '2.9e+02'
    999: "999",  # not '1.00e+03'
    1000: "1.00e3",  # not '1e+03'
    3652: "3.65e3",
    9876: "9.87e3",
    98765: "98.7e3",
    104999: "104e3",  # not '1.05e+05'
    120789: "120e3",  # not '1.21e+05'
    987654: "987e3",  # not '9.88e+05'
}

# sorted by int


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litint.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
