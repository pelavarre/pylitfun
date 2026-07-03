#!/usr/bin/env python3

"""
usage: litmath.py --

show how we clip ints and floats when very large or very small

examples:
  litmath.py --  # runs tests
"""

from __future__ import annotations  # backports new Datatype Syntaxes into old Pythons

import math
import re
import sys

if not __debug__:
    raise NotImplementedError([__debug__])  # 'better python3 without -O than with -O'


def main() -> None:
    """Run from the Shell"""

    # import litsys
    # sys.excepthook = litsys.sys_excepthook

    try_math_int_step_clips()
    try_math_float_int_clips()

    print("litmath.py: passed supercalifragilistically", file=sys.stderr)


#
# Try some Testcases of .math_int_metric_clip and .math_int_bimetric_clip
#


def try_math_int_step_clips() -> None:
    """Try some Testcases of .math_int_metric_clip and .math_int_bimetric_clip"""

    for i, k, ki in _math_int_step_clips_i_o_:

        try:
            _k_ = math_int_metric_clip(i)
        except ValueError:
            _k_ = ""

        try:
            _ki_ = math_int_bimetric_clip(i)
        except ValueError:
            _ki_ = ""

        assert _k_ == k, (_k_, k, i)
        assert _ki_ == ki, (_ki_, ki, i)


Qi = 2**100

_math_int_step_clips_i_o_: tuple[tuple[int, str, str], ...] = (
    (0, "0", "0"),
    (1, "1", "1"),
    (999, "999", "999"),
    (1_000, "1k", "1000"),
    (1_023, "1.02k", "1023"),
    (1_024, "1.02k", "1Ki"),
    (1_029, "1.02k", "1Ki"),
    (10_239, "10.2k", "9.99Ki"),
    (999_000, "999k", "975Ki"),
    (17_500_000, "17.5M", "16.6Mi"),
    (999_000_000_000_000, "999T", "908Ti"),
    (9_999_999_999_999_998, "9.99P", "8.88Pi"),
    (999_000_000_000_000_000, "999P", "887Pi"),
    (999_000_000_000_000_000_000, "999E", "866Ei"),
    (999_999_999_999_999_999_999, "999E", "867Ei"),
    (1_000_000_000_000_000_000_000, "1Z", "867Ei"),
    (998_999_999_999_999_960_154_112, "998Z", "846Zi"),
    (Qi, "1.26Q", "1Qi"),
    (int(999.876 * 10**30), "999Q", "788Qi"),
    (1000 * 10**30, "", "788Qi"),
    (1023 * Qi, "", "1023Qi"),
    (1024 * Qi - 1, "", "1023Qi"),
    (1024 * Qi, "", ""),
    (10**308, "", ""),
)


#
# Try some Testcases of .math_float_clip and .math_int_clip
#


def try_math_float_int_clips() -> None:
    """Try some Testcases of .math_float_clip and .math_int_clip"""

    for before, after in _math_float_int_clips_i_o_:

        # Fetch input

        s, f, i = before
        o = after[-1]

        _match_s_with_f_i_(s, f=f, i=i)

        # Check output

        if f is not None:

            fr = math_float_clip(f)
            assert o == fr, (o, fr, s)

            if q <= f < float(1000 * Q):
                _ = math_metric_float_clip(f)  # 'better called without check than untested'

        if i is not None:

            try:
                float(i)
            except OverflowError:
                assert False, (o, s)

            if f is not None:
                fir = math_float_clip(i)
                assert o == fir, (o, fir, s)

            oi = o.replace("+", "")
            ir = math_int_clip(i)
            assert oi == ir, (o, oi, ir, s)


def _match_s_with_f_i_(s: str, f: float | None, i: int | None) -> None:
    """Require Str consistent with Float and Int"""

    # Run some Tests near to Exponential Ints

    m = re.fullmatch(r"([0-9.]+)[*]10[*][*]([0-9]+)", string=s)
    if m:
        sx = m.group(1)
        sy = m.group(2)
        y = int(sy)

        # Choose between a Float near an Exponential Int, else an exact Exponential Int

        if "." in sx:
            fx = float(sx)
            _is_ = fx * 10**y
        else:
            x = int(sx)
            _is_ = x * 10**y

        # Require the tested Int to match the Str

        if i is not None:
            assert _is_ == i, (_is_, i, s)

        # Require the tested Float to match the Str

        if f is not None:

            overflow = None
            try:
                float(_is_)
            except OverflowError as exc:
                overflow = exc

            if not overflow:
                assert float(_is_) == f, (f, _is_, s)
            else:
                assert math.isinf(f), (f, _is_, s)

    # Run some Tests at particular Floats

    if not m:

        if f is not None:
            _fs_ = float(s)
            if not math.isnan(_fs_):
                assert _fs_ == f, (_fs_, f, s)
            else:
                assert math.isnan(f), (f, s)

        if i is not None:
            try:
                _is_ = int(s)
            except ValueError:
                _fs_ = float(s)
                _is_ = int(_fs_)

            assert _is_ == i, (_is_, i, s)


#
# Amp up Import Math for BuiltIns Float
#


Inf = float("inf")  # implicitly also defines -Inf and +Inf
NaN = float("nan")  # actually implies NaN != NaN


def math_metric_float_clip(f: float) -> str:
    """Clip to Three Digits but add a Metric Prefix Multiplier, not an 'e' Decimal Exponent"""

    metrics = "qryzafpnμm.kMGTPEZYRQ"  # https://en.wikipedia.org/wiki/Metric_prefix

    fclip = math_float_clip(f)  # .clip_float often raises ValueError outside of +- 1e-27 .. 1e27

    if math.isnan(f):  # todo: raise (f, fclip) in place of (f)?
        raise ValueError(f)  # can't clip NaN
    if math.isinf(f):
        raise ValueError(f)  # can't clip Inf
    if (not f) and (math.copysign(1, f) < 0):
        return "-0"  # doesn't lose the minus sign, and doesn't speak of "e0"

    fmag, _, fexp = fclip.partition("e")
    if not fexp:
        clip = fclip
        return clip

    exp = int(fexp if fexp else "0")

    index = 10 + (exp // 3)
    try:
        metric = metrics[index]
    except IndexError:
        raise ValueError(f)

    clip = f"{fmag}{metric}" if exp else fmag
    return clip  # -120789 --> '-120k', etc

    # raises ValueError for Floats that 2025 SI Metric Prefixes can't count out

    # see also fixed-point litdatetime.datetime_timedelta_clip

    # 'def math_metric_float_clip' last modified for py2def.py on 2026-02-25 or later


def math_float_clip(f: float) -> str:
    """Clip the Float down to Three Digits or less, and down to a Multiple-of-Three Exponent"""

    # Clip 0 and -0e0 and -Inf and Inf and NaN directly

    r = _math_clip_to_name_(f)
    if r:
        return r

    # Clip to 3 Digits and a Dot, except drop trailing Dot and Zeroes, and drop trailing Dot
    # Round the Exponent down to a Multiple of 3, when Float reps the Number with an Exponent

    flip = "-" if f < 0 else ""

    g = abs(f + 0e0)  # may raise OverflowError: int too large to convert to float
    r = repr(g)

    if "e" not in r:
        unsigned = _math_clip_to_unsigned_with_out_exp_(g)
    else:
        unsigned = _math_clip_to_unsigned_with__exp_(r)

    clip = f"{flip}{unsigned}"
    return clip

    # 'def math_float_clip' last modified for py2def.py on 2026-07-02 or later


def _math_clip_to_name_(f: float) -> str:
    """Clip 0 and -0e0 and -Inf and Inf and NaN directly"""

    if not f:
        if math.copysign(1e0, f) < 0:
            return "-0e0"  # not '-0e+0'  # not '-0.0'
        return "0"  # not '0e0'  # not '0e+0'  # not '0.0'

    if math.isinf(f):
        return "-Inf" if (f < 0) else "Inf"  # not '-inf'  # not '+Inf'  # not 'inf'

    if math.isnan(f):
        return "NaN"  # not 'nan'

    return ""


def _math_clip_to_unsigned_with_out_exp_(f: float) -> str:
    """Clip to 3 Digits and a Dot, except drop trailing Dot and Zeroes, and drop trailing Dot"""

    assert f > 0e0, (f,)

    exps = list(_ for _ in range(-99, 99, 3) if 10**_ <= f) or [0]  # todo: no need for 'or [0]'?
    exp = exps[-1]

    g = f / 10**exp  # often 1e0 <= g < 10e0  # todo: often and always?

    precise = f"{g:.99f}"
    assert "e" not in precise, (precise, g, exp, f)
    nearby = precise[:4]  # keeps 3 Digits plus 1 Dot  # todo: do we never round up here?
    assert "." in nearby, (nearby, g, exp, f)
    worthy = nearby.rstrip("0").rstrip(".")
    assert worthy, worthy

    clip = worthy
    if exp:
        clip += f"e{exp}" if exp < 0 else f"e+{exp}"

    return clip


def _math_clip_to_unsigned_with__exp_(r: str) -> str:
    """Clip the Exponent down to a Multiple of 3, when Float reps the Number with an Exponent"""

    m = re.fullmatch(r"(-?[1-9][0-9]*([.][0-9]+)?)((e)([+-]0*[1-9][0-9]*))", string=r)
    assert m, (m, r)  # ......... 2 .......... 34  5
    mg1 = m.group(1)
    mg5 = m.group(5)

    head, _, tail = mg1.partition(".")
    assert head, (head, tail, mg1, mg5, r)

    exp = int(mg5)

    while len(head) > 1:  # places the Dot just past the first Digit
        tail = head[-1] + tail
        head = head[:-1]
        exp += 1

    while exp % 3:  # moves the Dot right, to snap the Exponent down to a Multiple of 3
        head = head + (tail + "00")[0]
        tail = tail[1:]
        exp -= 1

    while len(head + tail) > 3:  # chops to 3 Digits or less
        assert tail, (tail, head, exp, mg1, mg5, r)
        tail = tail[:-1]

    mag = f"{head}.{tail}".rstrip("0").rstrip(".")  # drops trailing Dot and Zeroes
    plus = "" if exp < 0 else "+"  # always signs the Exponent
    clip = f"{mag}e{plus}{exp}"

    return clip

    # '0', '15e-9', '4e-3', '17.5e+6'
    # '-0e+0', '-42'

    # eng_clip(9_999_999_999_999_998 + 0e0) == '9.99e+15', add 1 to reach '10e+15'


Qi = 2**100

_math_float_int_clips_i_o_: tuple[tuple[tuple[str, float | None, int | None], tuple[str]], ...] = (
    #
    # -Inf .. -1
    #
    (("-Inf", -Inf, None), ("-Inf",)),
    (("-1e999", -Inf, None), ("-Inf",)),
    (("-1e309", -1e309, None), ("-Inf",)),
    (("-1e308", -1e308, int(-1e308)), ("-100e+306",)),
    (("-1000e18", -1e21, -1_000_000_000_000_000_000_000), ("-1e+21",)),
    (("-999e21", -9.99e23, None), ("-999e+21",)),
    (("-999e21", None, int(-999e21)), ("-998e21",)),  # 998 not 999
    (("-999e18", -9.99e20, -999_000_000_000_000_000_000), ("-999e+18",)),
    (("-999e3", -999000e0, -999_000), ("-999e+3",)),
    (("-999", -999e0, -999), ("-999",)),
    (("-1000", -1000e0, -1_000), ("-1e+3",)),
    (("-42", -42e0, -42), ("-42",)),
    (("-1", -1e0, -1), ("-1",)),
    #
    # -1+ .. 0 .. +1-
    #
    (("-0.001", -0.001, None), ("-1e-3",)),
    (("-1e-9", -1e-09, None), ("-1e-9",)),
    (("-1e-12", -1e-12, None), ("-1e-12",)),
    (("-1e-15", -1e-15, None), ("-1e-15",)),
    (("-1e-18", -1e-18, None), ("-1e-18",)),
    (("-1e-21", -1e-21, None), ("-1e-21",)),
    (("-1e-24", -1e-24, None), ("-1e-24",)),
    (("-1e-27", -1e-27, None), ("-1e-27",)),
    (("-1e-323", -1e-323, None), ("-10e-324",)),
    (("-10e-324", -1e-323, None), ("-10e-324",)),
    (("-1e-324", -0e0, None), ("-0e0",)),
    (("-1e-999", -0e0, None), ("-0e0",)),
    (("-0e0", -0e0, None), ("-0e0",)),
    (("0", 0e0, 0), ("0",)),
    (("0e0", 0e0, None), ("0",)),
    (("1e-999", 0e0, None), ("0",)),
    (("1e-324", 0e0, None), ("0",)),
    (("1e-323", 1e-323, None), ("10e-324",)),
    (("1e-27", 1e-27, None), ("1e-27",)),
    (("1e-24", 1e-24, None), ("1e-24",)),
    (("1e-21", 1e-21, None), ("1e-21",)),
    (("1e-15", 1e-15, None), ("1e-15",)),
    (("1e-12", 1e-12, None), ("1e-12",)),
    (("15e-9", 1.5e-08, None), ("15e-9",)),
    (("1e-9", 1e-09, None), ("1e-9",)),
    (("1e-6", 1e-06, None), ("1e-6",)),
    (("0.001", 0.001, None), ("1e-3",)),
    (("0.004", 0.004, None), ("4e-3",)),
    #
    # 1 .. Inf, and then NaN too
    #
    (("1", 1e0, 1), ("1",)),
    (("999", 999e0, 999), ("999",)),
    (("1000", 1000e0, 1_000), ("1e+3",)),
    (("1023", 1023e0, 1_023), ("1.02e+3",)),
    (("1024", 1024e0, 1_024), ("1.02e+3",)),
    (("1029", 1029e0, 1_029), ("1.02e+3",)),
    (("10239", 10239e0, 10_239), ("10.2e+3",)),
    (("999e3", 999000e0, 999_000), ("999e+3",)),
    (("17.5e6", 17500000e0, 17_500_000), ("17.5e+6",)),
    (("999e12", 999000000000000e0, 999_000_000_000_000), ("999e+12",)),
    (("9_999_999_999_999_998", 9_999_999_999_999_998 + 0e0, 9_999_999_999_999_998), ("9.99e+15",)),
    (("9_999_999_999_999_999", 9_999_999_999_999_999 + 0e0, None), ("10e+15",)),
    (("999e15", 9.99e17, 999_000_000_000_000_000), ("999e+15",)),
    (("999e18", 9.99e20, 999_000_000_000_000_000_000), ("999e+18",)),
    (("999_999_999_999_999_999_999", 1e21, None), ("1e+21",)),
    (("999_999_999_999_999_999_999", None, 999_999_999_999_999_999_999), ("999e18",)),
    (("1000*10**18", 1e21, None), ("1e+21",)),
    (("1000*10**18", None, 1_000_000_000_000_000_000_000), ("1e21",)),
    (("999e21", 9.99e23, None), ("999e+21",)),
    (("999e21", None, 998_999_999_999_999_960_154_112), ("998e21",)),  # 998 not 999
    (("1267650600228229401496703205376", float(Qi), Qi), ("1.26e+30",)),
    (("999.876*10**30", 9.99876e32, int(999.876 * 10**30)), ("999e+30",)),
    (("1000*10**30", float(1000 * 10**30), 1000 * 10**30), ("1e+33",)),
    (("1296806564033478677731127379099648", float(1023 * Qi), 1023 * Qi), ("1.29e+33",)),
    (("1298074214633706907132624082305023", float(1024 * Qi - 1), 1024 * Qi - 1), ("1.29e+33",)),
    (("1298074214633706907132624082305024", float(1024 * Qi), 1024 * Qi), ("1.29e+33",)),
    (("1*10**308", 1e308, 10**308), ("100e+306",)),
    (("1*10**309", Inf, None), ("Inf",)),
    (("1*10**999", Inf, None), ("Inf",)),
    (("Inf", Inf, None), ("Inf",)),
    (("NaN", NaN, None), ("NaN",)),
)


#
# Amp up Import Math for BuiltIns Int
#


def math_int_clip(i: int) -> str:
    """Clip the Int down to Three Digits or less, and down to a Multiple-of-Three Exponent"""

    s = str(int(i))  # '-120789'

    _, flip, digits = s.rpartition("-")  # ('', '-', '120789')
    sci = len(digits) - 1  # 5  # scientific power of ten
    eng = 3 * (sci // 3)  # 3  # engineering power of ten

    assert eng in (sci, sci - 1, sci - 2), (eng, sci, digits, i)

    if not eng:
        clip = s
        assert abs(int(float(clip))) <= abs(i), (abs(int(float(clip))), abs(i), i)
        return clip  # drops 'e0'

    assert len(digits) >= 4, (len(digits), eng, sci, digits, i)
    assert 1 <= (len(digits) - eng) <= 3, (len(digits), eng, sci, digits, i)

    precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'  # significand, mantissa, multiplier
    nearby = precise[:4]  # '120.'
    worthy = nearby.rstrip("0").rstrip(".")  # '120'  # drops '.' or'.0' or '.00'

    assert "." in nearby, (nearby, precise, eng, sci, digits, i)

    clip = flip + worthy + "e" + str(eng)  # like '-120e3' said, to rep -120*10**3

    if -1e21 < i < 1e21:
        assert abs(int(float(clip))) <= abs(i), (abs(int(float(clip))), abs(i), i)

    return clip

    # '0'  # '1'  # '1e3'  # '10e3'  # '987'  # '9.87e3'  # '98.7e3'  # '987e3'
    # -120789 --> '-120e3'

    # 'def math_int_clip' last modified for py2def.py on 2026-02-24 or later


#
# Amp up Import Math for Decimal Metric Units and Binary Metric Units
#


q = 10**-30  # 'qryzafpnμm' from https://en.wikipedia.org/wiki/Metric_prefix
r = 10**-27
y = 10**-24
z = 10**-21
a = 10**-18
f = 10**-15
p = 10**-12
n = 10**-9
μ = u = 10**-6
m = 10**-3

k = 10**3  # 'kMGTPEZYRQ' from https://en.wikipedia.org/wiki/Metric_prefix
M = 10**6
G = 10**9
T = 10**12
P = 10**15
E = 10**18
Z = 10**21
Y = 10**24
R = 10**27
Q = 10**30


Ki = 2**10  # "KMGTPE" + 'i' at https://physics.nist.gov/cuu/Units/binary.html
Mi = 2**20
Gi = 2**30
Ti = 2**40
Pi = 2**50
Ei = 2**60
Zi = 2**70  # "KMGTPEZYRQ" + 'i' at https://en.wikipedia.org/wiki/Binary_prefix
Yi = 2**80
Ri = 2**90
Qi = 2**100


def math_int_metric_clip(i: int) -> str:
    """Clip the Int down to Three Digits or less, and down to a Decimal Metric Exponent"""

    clip = _math_int_step_clip_(i, step=1000)
    return clip

    # see also fixed-point litdatetime.datetime_timedelta_clip

    # 'def math_int_metric_clip' last modified for py2def.py on 2026-03-31 or later


def math_int_bimetric_clip(i: int) -> str:
    """Clip the Int down to Three Digits or less, and down to a Binary Metric Exponent"""

    clip = _math_int_step_clip_(i, step=0x400)
    return clip

    # 'def math_int_bimetric_clip' last modified for py2def.py on 2026-03-01 or later


def _math_int_step_clip_(i: int, step: int) -> str:
    """Clip the Int down to a Metric or Bimetric Step of 1000 or 0x400 and append that Prefix"""

    # Reject too negative

    if i < 0:
        raise ValueError(i)  # can't count negatively many things

    # Reject too positive

    uncountable = 1000 * 10**30  # 1000 Q
    assert step in (1000, 0x400), (step,)
    if step == 0x400:
        uncountable = 0x400 * 2**100  # 1024 Qi

    if i >= uncountable:
        raise ValueError(i)  # can't count larger than Quebi

    # List the Prefixes

    metrics = "kMGTPEZYRQ"  # https://en.wikipedia.org/wiki/Metric_prefix

    prefixes = [""] + list(metrics)
    assert step in (1000, 0x400), (step,)
    if step == 0x400:
        prefixes = [""] + list((_.upper() + "i") for _ in metrics)

        # "KMGTPE" + 'i' at https://physics.nist.gov/cuu/Units/binary.html
        # "KMGTPEZYRQ" + 'i' at https://en.wikipedia.org/wiki/Binary_prefix

    # Raise the Multiplier till just before it goes above the Int

    multiplier = 1  # Value of the Prefix
    for prefix in prefixes:
        below = multiplier // step
        above = multiplier * step

        if i >= above:
            multiplier = above
            continue

        # Clip to the Multiplier

        if multiplier == 1:
            f = i / multiplier
        else:
            i_below = i // below  # snaps down to speak the same of all Ints inside a Step
            f = i_below / step

        assert 0 <= f < step, (f, multiplier, i)

        # Succeed

        if f >= 100:
            mag = str(int(f))  # (1024 * 1024 - 1) -> '1023Ki'
        else:
            mag = str(f)[:4].rstrip("0").rstrip(".")  # 10230 -> '9.99Ki'

        clip = f"{mag}{prefix}"  # (1024 * 1024) -> '1Mi'

        return clip  # 102399 --> '99.9Ki', etc

    # Cope after loop breaks to say Prefix Not Found

    assert False, (i,)  # unreached, doesn't raise ValueError(i)

    # raises ValueError for Ints that 2025 SI Metric Binary Prefixes can't count out


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/litmath.py
# copied from:  git clone https://github.com/pelavarre/litpython.git
