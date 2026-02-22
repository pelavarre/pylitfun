<!-- omit in toc -->
# clipped-numbers.md

Beware, this is a technical rant: strong opinions & working code

### Contents

- [Why we care](#why-we-care)
- [The problem and our solution](#the-problem-and-our-solution)
  - [Show the problem](#show-the-problem)
  - [Show our solution](#show-our-solution)
  - [Show this problem left broken by 'ls -lh'](#show-this-problem-left-broken-by-ls--lh)
  - [Say what fix solves the four bugs](#say-what-fix-solves-the-four-bugs)
  - [You might find more peace, if you don't accept these bugs](#you-might-find-more-peace-if-you-dont-accept-these-bugs)
- [One main takeaway](#one-main-takeaway)
- [Fixes known, and not yet well known](#fixes-known-and-not-yet-well-known)
  - [Fix for Ints](#fix-for-ints)
    - [Ints of Python](#ints-of-python)
    - [Ints of Google Sheets or Microsoft Excel](#ints-of-google-sheets-or-microsoft-excel)
  - [Fix for Floats](#fix-for-floats)
    - [Floats of Python](#floats-of-python)
    - [Floats of Google Sheets or Microsoft Excel](#floats-of-google-sheets-or-microsoft-excel)
      - [Do they know you need this?](#do-they-know-you-need-this)
      - [Provenance](#provenance)
- [Traps laid to catch you, and your friends](#traps-laid-to-catch-you-and-your-friends)
  - [Floats too close to zero](#floats-too-close-to-zero)
  - [Not-a-Number in Google Sheets and Microsoft Excel](#not-a-number-in-google-sheets-and-microsoft-excel)
  - [You've got a friend](#youve-got-a-friend)
- [Future Work](#future-work)
  - [Detail on why trust our Simd Formula for Floats](#detail-on-why-trust-our-simd-formula-for-floats)
  - [Detail on when to round up, not clip](#detail-on-when-to-round-up-not-clip)
    - [Detail on why rounding up well for us is hard](#detail-on-why-rounding-up-well-for-us-is-hard)


# Why we care

Last century's conventions for formatting numbers suit analog engineering plenty well. But for the digital age, we need new conventions

What's changed is that we now commonly count more than 1000 digital things at a time

Like you might have 2 billion (2e9), while she has 3 billion (3e9), and he has just 74. Well, in that corner, it's an unhelpful lie for you to say he has 0. We practically always need you to say he has more than zero

That's the first tiny distinction that often matters. But we've gone and looked for more. We've found four distinctions we need your formatting to make, lest you lead us astray, into miscounting digital things

Your digital numbers have grown big. You making time to format them well matters now


# The problem and our solution


## Show the problem


A familiar Terminal Shell Experience is

```sh
|| ... || Bytes || Date/ Time || Pathname ||
```

```sh
% ls -l
...   1378 Feb 14 09:10 0
...    818 Feb 13 17:22 1
...    716 Feb 13 17:22 2
...   1568 Feb 13 16:24 bin
...    288 Feb 14 09:05 docs
...   3652 Feb  7 18:46 Makefile
...  10747 Feb  3 09:40 README.md
...    282 Feb  1 12:32 requirements.txt
...   1632 Feb 13 16:24 sh
%
```

But have your eyes learned to prefer

```sh
|| ... || Bytes || Date/ Time || Pathname ||
```

```sh
% ls -l |pb eng replace columns
...  1.37e3  Feb  14  09:10  0
...     818  Feb  13  17:22  1
...     716  Feb  13  17:22  2
...  1.56e3  Feb  13  16:24  bin
...     288  Feb  14  09:05  docs
...  3.65e3  Feb   7  18:46  Makefile
...  10.7e3  Feb   3  09:40  README.md
...     282  Feb   1  12:32  requirements.txt
...  1.63e3  Feb  13  16:24  sh
%
```

?

## Show our solution

The big difference here is in the Byte Counts, classically spoken as precise decimal int literals

Watch what happens to your visual perception when we lay out a copy of just this one column of numbers

```sh
% ls -l |pb awk 5 join
1415  1378  818  716  1568  288  3652  10747  282  1632
%
```

When you invite us to clip these numbers back to three digits each, then they split themselves apart naturally, into two piles

```sh
% ls -l |pb eng awk 5 join
1.41e3  1.37e3  818  716  1.56e3  288  3.65e3  10.7e3  282  1.63e3
%
```

You see the visual effect at play here?

The smaller numbers naturally more fade away, because they lack the "e3" marks

```sh
% ls -l |pb eng awk 5 split |grep -v e3 |pb join
818  716  288  282
%
```

The big numbers more naturally stand out and step forward, because they have "e3" marks

```sh
% ls -l |pb eng awk 5 split |grep e3 |pb join
1.41e3  1.37e3  1.56e3  3.65e3  10.7e3  1.63e3
%
```

Next now, watch what happens to your visual perception when we just correct the format of these numbers, but leave them in place in their rows. You see? They quite naturally come and split their rows across this same dividing line

The extra ink of the "e3" mark visually brings forward the rows of the big numbers

```sh
% ls -l |pb eng replace columns |grep e3
...  1.41e3  Feb  14  09:11  0
...  1.37e3  Feb  14  09:10  1
...  1.56e3  Feb  13  16:24  bin
...  3.65e3  Feb   7  18:46  Makefile
...  10.7e3  Feb   3  09:40  README.md
...  1.63e3  Feb  13  16:24  sh
%
```

The careful lack of the "e3" ink visually pushes back the rows of the small numbers

```sh
% ls -l |pb eng replace columns |grep -v e3
total        72
...     818  Feb  13  17:22  2
...     716  Feb  13  17:22  3
...     288  Feb  14  09:05  docs
...     282  Feb   1  12:32  requirements.txt
%
```

You don't have to make time to read through the meaningless detail of particular digits spoken in place of the summary "e3" mark. You can decline to struggle. You can make it a job for the Bots to clip away the meaningless detail for you

Clipping your numbers down to three digits marks the rows to sort themselves by the size of their engineering exponent. Significantly helpful. These clipped numbers speak into your eyes more quickly, more easily, and more accurately


## Show this problem left broken by 'ls -lh'

Linux & macOS do try to help you in just this way, by offering 'ls -lh' alongside 'ls -l'. But they get it significantly wrong

```sh
% ls -lh
total 72
...   976B Feb 14 09:46 0
...   1.4K Feb 14 09:11 1
...   1.3K Feb 14 09:10 2
...   818B Feb 13 17:22 3
...   1.5K Feb 13 16:24 bin
...   288B Feb 14 09:05 docs
...   3.6K Feb  7 18:46 Makefile
...    10K Feb  3 09:40 README.md
...   282B Feb  1 12:32 requirements.txt
...   1.6K Feb 13 16:24 sh
%
```

You see? They give you a Column of malformed Byte Counts

```sh
% ls -lh |pb eng awk 5 split |pb join
976B  1.4K  1.3K  818B  1.5K  288B  3.6K  10K  282B  1.6K
%
```

Four bugs

1 ) Do your eyes reliably pick "888" apart from "88B"?

Mine don't. And I don't need a "B" Suffix on screen to tell me there are no more digits there. This "B" Suffix is a waste of ink. And their "B" Suffix too often becomes a lie, like by almost saying "2888" when meaning to say "288" and a "B". Please make it stop

2 ) Have you already memorized the k, M, G, etc metric prefixes that mean e3, e6, e9, etc?

Well and good, but if your memory is precise then you'll feel annoyed when you notice they put an unconventional upper 'K' in place of the standard lower 'k'

3 ) Have you memorized the exact values of the metric prefixes?

They get these wrong. Since 1999, our standard has been clear: Ki is 1024 and k is 1000, and they get it wrong, We can show how wrong they go with just one testcase. Let's just try counting out 3652 bytes

- Correct = 3.65k (decimal, base 10)
- Also correct = 3.56Ki (binary, base 1024)
- What `ls -lh` says = 3.6K (wrong on multiple counts)

Why so wrong? Well, they rounded 3.56Ki up to 3.6Ki, then mislabeled it as '3.6K'. This comes out upside-down. They rounded UP but reported a number that's LESS than the actual value (3.6 < 3.65). This is confusing. This is wrong

4 ) How many digits do you need to see?

2 digits is not enough, and 4 digits is too many, I am saying. Here I stand. True for your eyes too?

Last century's 'ls -h' does me wrong. It gives me 2 digits and stopping there. All the while the only 3652 known to me is the 3.65e3. I need its name spoken in that familiar way. Aye fair enough, in real life I do quickly autocorrect their wrongs on the fly, but I'm posting this rant because I do wish they'd stop shoving their wrongs at me. Take out their own trash, why can't they. Keep it away from me


## Say what fix solves the four bugs

A **well-clipped number** obeys four rules:

1 ) **Zero means Zero**
   - Says 0 only to mean precisely 0

2 ) **Zero doesn't mean Epsilon**
   - Doesn't say 0 to mean a tiny nonzero value like 1e-123

3 ) **Empty details fade away**
   - Doesn't end with '.', '.0', '.00', or 'e0', and doesn't start with '+', and doesn't mention 'e+'

4 ) **Gives me my first three digits**
   - Show three significant digits when three or more exist, no less and no more
   - Never sacrifices accuracy to round up to a rounder number
   - Never claims to have counted things that don't exist

These four rules make it easier to read numbers correctly and harder to read them wrong


## You might find more peace, if you don't accept these bugs

"A bug becomes a bug when it bothers someone who matters"

Please beware

If you don't yet feel these 4 bugs are bugs, please stop, and give yourself a moment to feel a fitting degree of fear. I can only teach you to start seeing, I can't teach you to stop. I can't even stop myself seeing

**Is it worth it?**

Learning to see the more common wrongs can cost you peace every day of your life

It's only worth it if you're building with numbers, or finding some other reward by working well with numbers. Only then do you need to learn to reject lying numbers quickly, simply, and accurately. As we do here


# One main takeaway

You can have "correct at a glance" precision. Ask for it persistently, and they will eventually come and give it to you

| Format    | 3652   | 104999 | 288   | Precision  | Acuity |
|-----------|--------|--------|-------|----------- |--------|
| ls -l     | 3652   | 104999 | 288   | Too Much   | Weak   |
| ls -lh    | 3.6K   | 103K   | 288B  | Too Litle  | Weak   |
| pb eng    | 3.65e3 | 10.4e3 | 288   | Helpful    | Strong |

Do you feel you get it? Do you see how our first century of Software Traditions for clipping numbers do lead us astray?


# Fixes known, and not yet well known

To get your numbers well-clipped, you can download & run our code, or you can write your own code. We show our code below, to help you write your own code in its place, or to help you trust ours

The run-time costs of adopting this code are near zero. This code runs in scratch time, and requires nearly zero memory


## Fix for Ints

How do I make 'ls -lh' say what it should mean in 2026? I drop out the old & misconceived -h, and push my counts through our '|pb eng' instead

```sh
ls -l |pb eng replace columns
```

It's the '|pb eng' part that fixes up the counts

```sh
ls -l |pb eng
```

The 'replace columns' part turns the text into a conventional table of left-aligned texts and right-aligned numbers


### Ints of Python

You can call on Python to clip a count back to three digits. You don't have to let it whisper lies into your eyes

You can download and run this. It picks out a leading negative sign, if present. It calculates the scientific exponent, and then finds the engineering exponent nearby. It gives you your first three digits

It never says 'e0'. It never ends with "." or ".0" or ".00". It never adds on a confusion of "8" vs "B". It always chooses unsigned metric exponents like "e3", never a scientific exponent like "e+2" or "e1" or "e-0". It always calculates powers of 10 as the Base of "e", not powers of the 10th power of 2 (1024)

```python
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
```

Our code produces correct Int answers. Our code here formats Int Counts humanely, to speak only truths into my eyes

```python
(0, "0"),
(99, "99"),
(999, "999"),

(9000, "9e3"),  # not '9.00e3'  # not '9e+03'
(9800, "9.8e3"),  # not '9.0e3'
(9870, "9.87e3"),  # not '9.870e3'
(9876, "9.87e3"),  # not rounded up to '9.88e3'
```

Looks good? You feel you know where to put your copy of this Python code, and when to call it?


### Ints of Google Sheets or Microsoft Excel

Google Sheets and Microsoft Excel can clip Ints as accurately as Python

As you know, their oldest convention is to code up every new idea as a Simd Formula. Here is our idea, so coded. You can download and run this. This code picks out a leading negative sign, if present. It calculates the scientific exponent, and then finds the engineering exponent nearby. It gives you your first three digits

This same code works just as well in both Microsoft Excel and in Google Sheets

```excel
=IF(A1=0, "0",
  IF(LEN(TEXT(ABS(A1),"0"))<=3, TEXT(A1,"0"),
    LET(
      sign, IF(A1<0, "-", ""),
      digits, TEXT(ABS(A1),"0"),
      sci, LEN(digits)-1,
      eng, 3*INT(sci/3),
      precise, LEFT(digits, LEN(digits)-eng) & "." & RIGHT(digits, eng),
      nearby, LEFT(precise, 4),
      worthy, REGEXREPLACE(REGEXREPLACE(nearby, "0+$", ""), "\.$", ""),
      sign & worthy & "e" & TEXT(eng,"0")
    )
  )
)
```

Put this code into a Google Sheet or Excel Sheet, and we can contrast your results with their defaults. Their default is to speak the larger Ints with a reckless excess of precision

```
'0 '9 '999  '9000 '9800 '9870 '9876
```

Our code tells the Sheet to speak with more consideration for your true needs and fading eyesight

```
'0 '9 '999  '9e3 '9.8e3 '9.87e3 '9.87e3
```

And you can tell Sheet to give the name 'int.clip' to this Formula so as to call your code far more directly and clearly

```excel
=int.clip(9876)  # '9.87e3
```

Looks good? You feel you know where to put your copy of this Simd Formula, and when to call it?


## Fix for Floats

We showed you our fix for Ints first, because it's simpler than our fix for Floats. You can learn to trust it more quickly yourself, and you can push it through Code Review faster

But we have also solved Floats. We've actually found a solution that does solve both Ints and Floats. Floats add the edges cases of -Inf, -0e0, Inf, & NaN. But the same four rules of well-clipped numbers apply: Zero means Zero, Zero doesn't mean Epsilon, don't waste ink, and give me my three digits

### Floats of Python

Python does count some things as Floats. Python doesn't count all things as Ints

Like Python says the 'time.time()' difference between two moments is a float

```python
>>> import time
>>> t0 = time.time()
>>> t1 = time.time()
>>> t1t0 = t1 - t0
>>> print(t1t0)
0.0001989060512
>>> print(type(t1t0).__name__.title())
Float
>>>
```

But when you count a thing as Float, then I still need you to format your Float Counts carefully to speak only truths into my eyes, just like I need you to format your Int Counts carefully to speak only truths into my eyes

Our code here meets all the same specs for humane truth-speaking formats as does the Python we wrote for formatting Int Counts, but our code here solves both Int Counts and Float Counts

```python
def clip_float(f: float) -> str:
    """Find the nearest Float Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    if math.isnan(f):
        return "NaN"  # unsigned as neither positive nor negative

    if math.isinf(f):
        absclip = "Inf"
        clip = ("-" + absclip) if (f < 0) else absclip
        return clip

    if not f:
        clip = "-0e0" if (math.copysign(1e0, f) < 0e0) else "0"
        return clip

    absclip = _clip_positive_float_(abs(f))
    clip = ("-" + absclip) if (f < 0) else absclip

    return clip

    # never says '0' except to mean exactly precisely Float +0e0 or Int 0
    # never ends with '.' nor '.0' nor '.00' nor 'e+0'

    # could return .clip_int for Floats equal to Ints, but doesn't


def _clip_positive_float_(f: float) -> str:
    """Find the nearest Positive Float Literal, as small or smaller, with 1 or 2 or 3 Digits"""

    assert f > 0, (f,)

    # Form the Scientific Notation

    sci = int(math.floor(math.log10(f)))
    precise = f / (10**sci)
    assert 1 <= precise < 10, (precise, f)

    # Choose a Floor, in the way of Engineering Notation,
    # but do round up the distortions introduced by 'mag = f / (10**sci)'

    triple = str(int(100 * precise + 0.000123))  # arbitrary 0.000123
    assert "100" <= triple <= "999", (triple, precise, sci, f)

    eng = 3 * (sci // 3)  # ..., -6, -3, 0, 3, 6, ...

    span = 1 + sci - eng  # 1, 2, or 3
    assert 1 <= span <= 3, (span, triple, precise, eng, sci, f)

    # Stand on the chosen Floor, except never say '.' nor '.0' nor '.00'

    nearby = triple[:span] + "." + triple[span:]
    worthy = nearby.rstrip("0").rstrip(".")  # lacks '.' if had only '.' or'.0' or '.00'

    # And never say 'e0' either

    clip = f"{worthy}e{eng}".removesuffix("e0")  # may lack both '.' and 'e'

    # But never wander far

    alt_f = float(clip)

    diff = f - alt_f
    precision = 10 ** (eng - 3 + span)
    assert diff < precision, (diff, precision, f, alt_f, clip, eng, span, worthy, triple, span, f)

    return clip

    # "{:.3g}".format(9876) and "{:.3g}".format(1006) talk like this but say 'e+0' & round up

    # math.trunc leaps too far, all the way down to the int ceil/ fl∏oor
```

You could claim copyright on your revision of our arbitrary 0.000123 fudge factor in here. The answers come out the same for most choices of what to add. You very nearly only need to add something nonzero and smaller than one. Like you could add in a significant date-time, if you want. Like you could add Tank Man's 1989-06-05 12th Hour, spoke of as 0.1989060512

Our code here produces correct Float answers. Our code here formats Float Counts and Int Counts humanely, to speak only truths into my eyes

```python
(1e-4, "100e-6"),  # not '0.0001'  # not '0.000'
(1e-3, "1e-3"),  # not '0.001'
(1.2e-3, "1.2e-3"),  # not '0.0012'  # not '0.001'
(9.876e-3, "9.87e-3"),  # not '9.88e-3'  # not '0.009876'  # not '0.00988'  # not '0.010'
(1e-2, "10e-3"),  # not '0.01'  # not '0.010'
(1e-1, "100e-3"),  # not '0.1'  # not '0.100'
#
(1e0, "1"),  # not '1.0'  # not '1.000'
(1e1, "10"),  # not '10.0'  # not '10.000'
(1.2e1, "12"),  # not '12.0'  # not '12.000'
(9.876e1, "98.7"),  # not '98.76'  # not '98.8'  # not '98.760'
(1e2, "100"),  # not '100.0'  # not '100.000'
(1.23e2, "123"),  # not '123.0'  # not '123.000'
(987, "987"),  # not '987.000'
#
(1e3, "1e3"),  # not '1000.0'  # not '1e+03'  # not '1000.000'
#
(0, "0"),  # not '0.000'
(0e0, "0"),  # not '0.0'  # not '0.000'
(-0e0, "-0e0"),  # not '-0.0'  # not '-0.000'  # and never the inequivalent '-0' of f"{-0e0:g}"
#
(float("-inf"), "-Inf"),  # not '-inf'
(float("+inf"), "Inf"),  # not 'inf'
(float("nan"), "NaN"),  # not 'nan'
```

Looks good? You feel you know where to put your copy of this Python code, and when to call it?


### Floats of Google Sheets or Microsoft Excel

Google Sheets and Microsoft Excel can clip Floats about as accurately as Python

Our Simd Formula here does the same kind of work as the Simd Formula we wrote above to format Ints, and does this work in 14 Lines of Code, about as simply as in the 14 Lines of Code we wrote for Ints. But this Formula works for both Ints and Floats

This same code works just as well in both Microsoft Excel and in Google Sheets

```excel
=IF(A1 = 0, "0",
LET(
    sign, IF(A1 < 0, "-", ""),
    f, ABS(A1),
    sci, INT(FLOOR(LOG10(f))),
    precise, f / (10^sci),
    triple, TEXT(INT(100 * precise + 0.000123), "000"),
    eng, 3 * INT(sci / 3),
    span, 1 + sci - eng,
    nearby, LEFT(triple, span) & "." & MID(triple, span + 1, 100),
    worthy, REGEXREPLACE(REGEXREPLACE(nearby, "0+$", ""), "\.$", ""),
    clip, REGEXREPLACE(worthy & "e" & eng, "e0$", ""),
    sign & clip
)
```

Put this code into a Google Sheet or Excel Sheet, and we can contrast your results with their defaults. Their default is to speak the larger and smaller Floats with a reckless excess of precision

```
'0.001 '0.0001 '0.00001  '9000 '9870
```

Our code tells the g Sheet to speak with more consideration for your true needs and fading eyesight

```
'1e-3 '100e-6 '10e-6  '9e3 '9.87e3
```

And you can tell g Sheets to give the name 'float.clip' to this Formula so as to call your code far more directly and clearly

```excel
=float.clip(9876.0)  # '9.87e3
```

Looks good? You feel you know where to put your copy of this Simd Formula, and when to call it?


#### Do they know you need this?

I don't understand why Google & Microsoft don't give out '=float.clip' as a standard part to build with. Do you know someone who knows someone who can get 'float.clip' added as a standard part of g Sheets? If Microsoft & Google resist, can we wake up Amazon & Apple?


#### Provenance

Myself, I first wrote =Let and =Lambda Simd Formulae for Microsoft Excel, years before I tried them inside of Google Sheets. The =Let and =Lambda Simd Formula Functions first reached me in a Microsoft Excel

My Feb/2026 pitch for how best to introduce the =Let and =Lambda Simd Formulae to new people is
> https://social.vivaldi.net/@pelavarre/116066365378672153

I think that's the best I've got. I rewrote it from a copy of the onboarding welcome I posted in Jun/2021 as
> https://github.com/pelavarre/like-py-xlsx/blob/main/README.md


# Traps laid to catch you, and your friends

Pitfalls, with spikes in them


## Floats too close to zero

Trouble waits to catch you out, when next you try working with numbers too close for zero

Python and Google Sheets and Microsoft Excel will corrupt a very small input of '1e-999' or '-1e-999', by silently substituting an actual zero. By contrast, they do at least poison very large inputs of positive '1e999' or negative '-1e999'

That is, they say the bounds checking of the very smallest numbers is on you, not on them

They say it's on you to stay perfectly inside a range of like 1e-300 to 1e300 to keep answers reasonable

A Python example of unreasonable is

    >>> repr(7e-324)[0]
    '5'
    >>> 7e-324
    5e-324
    >>> 3e-324
    5e-324
    >>> 2e-324
    0.0
    >>>

The Oct/1985 IEEE 754 Standard for Floating-Point Arithmetic shoves on them to work this way. I sure can argue it's due for an update


## Not-a-Number in Google Sheets and Microsoft Excel

Trouble waits to catch you out, when next you try working with the Not-a-Number idea of Google Sheets and Microsoft Excel

When you ask our code to format their =NA() form of not-a-number, then our Formulae produce their conventional =NA() as our Result. That's what they expect, and that's what we do

But that's not the String '#N/A that would be more of a transliteration of the Python convention of looking always to narrow a Result Datatype to Str from Str | Float | None

As you move back and forth between Google Sheets and Microsoft Excel and Python, you'll have to bring this slippery bit of difference back into mind, often enough


## You've got a friend

Who needs to hear about these fixes? How should we push the word out?


# Future Work

Five hopes

1 ) Help people speak e3, e-3, e6, e-6, etc as metric prefixes of k, m, M, Greek μ, etc

2 ) Help people separate when to clip a number sharply, vs when to forward all the precision they've got. APIs for data interchange copy out lots of precision for good reasons through standard file formats: .csv, .json, etc

3 ) Figure out why solving Floats or Ints in g Sheets and Excel takes just 14 Lines. Why can't we solve Ints even more simply?

4 ) Do more homework to show who should trust our Simd Formula for Floats

5 ) Help people appreciate when to round up, not clip

## Detail on why trust our Simd Formula for Floats

Outside of this paper, we have shown ourselves that our two Formulae do agree across the Ints from -1000 to 1000, and across a few thousand Random Ints

As for Ints below -1000 and above 1000, we give ourselves inductive algebraic arguments as reasons to believe our Float and Int Formulae always do produce the same correct answers

But what about all the other Floats? Who has a complete argument and a definitive proof?

## Detail on when to round up, not clip

You need to round up when you need to make room, when you're allocating space or resources

Like you do need to round up to 10 KiB, if you need to store 9999 Bytes and your allocation unit is 1 KiB (1024 Bytes). The margin here - the extra 24 Bytes per 1000 Bytes - it matters. You can't get by on allocating even 1 less than your 9999 Bytes

But when you're just reporting a measure, you don't need to round up. You're left free to choose to carefully never report more than you measured

### Detail on why rounding up well for us is hard

You can't round up well by yourself, on your own, independently. You can't decide the margin for me. You need to know:

- How much margin we add (5 Bytes? 1 MiB?)
- What unit we round up to (1 KiB? 4 KiB? 0.5 KiB?)

Only then can you round up correctly for us


<!-- omit in toc -->
# Links

- [GitHub Repository](https://github.com/pelavarre/pylitfun)
- [Questions/ Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre+%23PyLitFun)


<!--

Posted in Feb/2026 with Type Hints on the Monospaced Examples, because GitHub Md renders the Python & Excel & Sh Type Hints well, even while VsCode renders them horribly, especially in Lightmode

GitHub Md also gives Horizontal Scrolling to Portrait Displays of our ```python Examples, vs VsCode renders them wrapped

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/clipped-numbers.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
