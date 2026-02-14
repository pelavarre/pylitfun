<!-- omit in toc -->
# clipped-numbers.md

Contents

- [Show \& tell](#show--tell)
  - [Show](#show)
  - [First Tell](#first-tell)
  - [Second Tell](#second-tell)
  - [What is a Well Clipped Number?](#what-is-a-well-clipped-number)
  - [How much Space do I need?](#how-much-space-do-i-need)
- [Fixed for Ints](#fixed-for-ints)
  - [Ints of Python](#ints-of-python)
  - [Ints of Google Sheets](#ints-of-google-sheets)
  - [Ints of Microsoft Excel](#ints-of-microsoft-excel)
- [Fixed for Floats](#fixed-for-floats)
  - [Floats of Python](#floats-of-python)
  - [Floats of Google Sheets](#floats-of-google-sheets)
  - [Floats of Microsoft Excel](#floats-of-microsoft-excel)
  - [Traps laid for you by Google Sheets \& Microsoft Excel](#traps-laid-for-you-by-google-sheets--microsoft-excel)
    - [Near Infinities](#near-infinities)
    - [Not-a-Number](#not-a-number)
- [Links](#links)


# Show & tell

Beware, this is a technical rant: strong opinions & working code


## Show


A familiar Terminal Shell Experience is

```sh
|| Permissions || Hardlinks || Owner || Group || Bytes || Date/ Time || Pathname ||
```

```sh
% ls -l
total 64
-rw-r--r--@  1 jqdoe  staff   1378 Feb 14 09:10 0
-rw-r--r--@  1 jqdoe  staff    818 Feb 13 17:22 1
-rw-r--r--@  1 jqdoe  staff    716 Feb 13 17:22 2
drwxr-xr-x  49 jqdoe  staff   1568 Feb 13 16:24 bin
drwxr-xr-x   9 jqdoe  staff    288 Feb 14 09:05 docs
-rw-r--r--   1 jqdoe  staff   3652 Feb  7 18:46 Makefile
-rw-r--r--@  1 jqdoe  staff  10747 Feb  3 09:40 README.md
-rw-r--r--@  1 jqdoe  staff    282 Feb  1 12:32 requirements.txt
drwxr-xr-x  51 jqdoe  staff   1632 Feb 13 16:24 sh
%
```

But have your eyes learned to prefer

```sh
|| Permissions || Hardlinks || Owner || Group || Bytes || Date/ Time || Pathname ||
```

```sh
% ls -l |pb eng replace columns
total        64
-rw-r--r--@   1  jqdoe  staff  1.37e3  Feb  14  09:10  0
-rw-r--r--@   1  jqdoe  staff     818  Feb  13  17:22  1
-rw-r--r--@   1  jqdoe  staff     716  Feb  13  17:22  2
drwxr-xr-x   49  jqdoe  staff  1.56e3  Feb  13  16:24  bin
drwxr-xr-x    9  jqdoe  staff     288  Feb  14  09:05  docs
-rw-r--r--    1  jqdoe  staff  3.65e3  Feb   7  18:46  Makefile
-rw-r--r--@   1  jqdoe  staff  10.7e3  Feb   3  09:40  README.md
-rw-r--r--@   1  jqdoe  staff     282  Feb   1  12:32  requirements.txt
drwxr-xr-x   51  jqdoe  staff  1.63e3  Feb  13  16:24  sh
%
```

?

## First Tell

The big difference here is in the Byte Counts, spoken as precise decimal int literals. Like so long as you do keep the Byte Counts detailed out to the last digit, then they are

```sh
% ls -l |pb && pb awk 5 |pb join --sep=' '
1415 1378 818 716 1568 288 3652 10747 282 1632
%
```

But who has time for that? When made more meaningful, these Numbers catch up some structure. They naturally split into two piles

First the Small Numbers

```sh
% ls -l |pb
%

% pb eng awk 5 split |grep -v e3 |pb join
818  716  288  282
%
```

And also, separately, the Big Numbers

```sh
% pb eng awk 5 split |grep e3 |pb join
1.41e3  1.37e3  1.56e3  3.65e3  10.7e3  1.63e3
%
```

Keep these Numbers inside their Rows, and then they easily split the Rows exactly across this same boundary

First the Rows of the Small Numbers

```sh
% ls -l |pb eng replace columns |grep e3
-rw-r--r--@   1  jqdoe  staff  1.41e3  Feb  14  09:11  0
-rw-r--r--@   1  jqdoe  staff  1.37e3  Feb  14  09:10  1
drwxr-xr-x   49  jqdoe  staff  1.56e3  Feb  13  16:24  bin
-rw-r--r--    1  jqdoe  staff  3.65e3  Feb   7  18:46  Makefile
-rw-r--r--@   1  jqdoe  staff  10.7e3  Feb   3  09:40  README.md
drwxr-xr-x   51  jqdoe  staff  1.63e3  Feb  13  16:24  sh
%
```

And then also the Rows of the Big Numbers

```sh
% ls -l |pb eng replace columns |grep -v e3
total        72
-rw-r--r--@   1  jqdoe  staff     818  Feb  13  17:22  2
-rw-r--r--@   1  jqdoe  staff     716  Feb  13  17:22  3
drwxr-xr-x    9  jqdoe  staff     288  Feb  14  09:05  docs
-rw-r--r--@   1  jqdoe  staff     282  Feb   1  12:32  requirements.txt
%
```


## Second Tell

Senior people will tell you that Linux & macOS do try to help you in just this way

That's true. Linux & macOS do mean well. But they get it significantly wrong. It looks to me like they stopped thinking, got stuck in the past, since 1998

```sh
% ls -lh
total 72
-rw-r--r--@  1 jqdoe  staff   976B Feb 14 09:46 0
-rw-r--r--@  1 jqdoe  staff   1.4K Feb 14 09:11 1
-rw-r--r--@  1 jqdoe  staff   1.3K Feb 14 09:10 2
-rw-r--r--@  1 jqdoe  staff   818B Feb 13 17:22 3
drwxr-xr-x  49 jqdoe  staff   1.5K Feb 13 16:24 bin
drwxr-xr-x   9 jqdoe  staff   288B Feb 14 09:05 docs
-rw-r--r--   1 jqdoe  staff   3.6K Feb  7 18:46 Makefile
-rw-r--r--@  1 jqdoe  staff    10K Feb  3 09:40 README.md
-rw-r--r--@  1 jqdoe  staff   282B Feb  1 12:32 requirements.txt
drwxr-xr-x  51 jqdoe  staff   1.6K Feb 13 16:24 sh
%
```

Egregiously wrong in four ways

1 ) How old are your eyes? Do your eyes reliably pick out "888" from "88B"? Mine don't. I greatly dislike this waste of ink. I don't need a "B" on screen to tell me zero more digits are there. And half the time this "B" comes into my brain as a lie, as when saying "2888" where it meant "288". Please make it stop

2 ) I do appreciate the metric units:  k, M, G, etc to mean e3, e6, e8, etc. But I feel annoyed as often as I notice they put an unconventional 'K' in place of the standard 'k'

3 ) I do so wish they would calculate standard units. We solved this late last century. We spelled out that Ki is 1025 and k is 1000. So our example of 3652 is more than 3.65k and more than 3.56Ki. But they distort this. They claim '3.6K' to talk of the 3.56Ki Floor by adding in 34.4 Bytes. What in the world is 0.4 of a Byte, and why are we spending my time on it?? Their lies mislead me, and so I dislike their lies

4 ) Their abbreviation is 50% excessive, besides being slightly wrong. I practically always need to see three digits to feel I know the size of the thing. Two digits is not enough, and four digits is too many, but they give me two and stop. The 3652 who I know is the 3.65e3. I need its name spoken in that familiar way

If you don't yet feel these wrongs are egregious, beware

I can only teach you to start seeing, I can't teach you to stop. It'll be like me teaching you to notice bad keming. Learning to see more wrong will poison your life. It's only worth it if you're building with numbers, or getting paid in some other way to work with numbers. Only then do you need to learn to reject lying numbers quickly, simply, and accurately. As we do here


## What is a Well Clipped Number?

When you speak the name I know best of a number that works as a count of things, then I say you have spoken a well-clipped number

You say 0 only to mean 0

You don't say 0 to mean 1

You don't waste ink on mentioning 'e+' or 'e0' or a trailing '.' or '.0' or '.00'. Instead, you show your respect for the time I spend reading every character of what you wrote, exactly by holding back from giving me the kinds of extra characters that I never need

You don't round up to some fabricated ideal of a rounder number. Aye, you do give me three digits and done, but you do it by backing off from demanding I give you credit for the last few things you counted. You don't round up and send me wrong by giving me the lie of you having counted things that you never actually saw


## How much Space do I need?

People who study Maths talk of a "Floor" when you slam a Float down to the next smaller Int, and a "Ceil" when you slam the Float up to the next larger Int. Yes, yes, there is a place in Engineering and Science for Ceil's, not only for Floors

But in the Engineering place for Ceil, there I also need Margin. When I'm involving myself in the careful allocation of Space, then I have to add Margin. I must round Counts plus Margin up to whole Allocations

Ok. Now look back at our Software Traditions for clipping numbers. There's practically never any real need for speaking of 9999 as 10000, because that margin is tiny. You can't just fix up a Count for me, not while you commit to only showing up to help me and never to hurt me. You need me to tell you how much Margin I need us to add. And you need me to tell you if my Allocations are 4Ki or 1Ki or 0.5Ki or whatever. Only then can you know how to round up our Counts well

And besides, it's 2026 now. We don't involve me personally in the careful allocation of Space anything like as often as we did in 1972. Let's wake up and meet our moment, why not


# Fixed for Ints

How I make 'ls -lh' say what it should mean in 2026 is

```sh
ls -l |pb eng replace columns
```

It's the '|pb eng' part that fixes up the counts

```sh
ls -l |pb eng
```

You can download & run our Code, or you can write your own. Below we show you our Code for this


## Ints of Python

You can call on Python to clip a count back to three digits. You don't have to let it whisper lies into your eyes

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

Correct Answers

```python
(0, "0"),
(99, "99"),
(999, "999"),

(9000, "9e3"),  # not '9.00e3'  # not '9e+03'
(9800, "9.8e3"),  # not '9.0e3'
(9870, "9.87e3"),  # not '9.870e3'
(9876, "9.87e3"),  # not rounded up to '9.88e3'
```

We're looking at correct answers here. Correct and nothing but correct. No "B" vs "8" visual confusions. Always unsigned metric exponents like "e3", never a scientific exponent like "e+2" or "e1" or "e-0". Powers of 10 as the Base of "e", not powers of the 10th power of 2 (1024). Three digits when you've got three digits, never chopped down so far as to show just two digits or one. And no empty busy ".00"s. Ink spent only when ink delivers value


## Ints of Google Sheets

Google Sheets can clip numbers as well as Python

As you know, their oldest convention is to code up every new idea as a Simd Formula

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

Next we contrast your results with their defaults. The g Sheets default is to speak these counts with a reckless excess of precision

```
0 9 999  9000 9800 9870 9876
```

Our code tells to it to speak with more consideration for your true needs and fading eyesight

```
'0 '9 '999  '9e3 '9.8e3 '9.87e3 '9.87e3
```

If you work so closely with g Sheets as to name this Formula, you can give the name 'int.clip' to this Formula and then call it far more directly and clearly

```excel
=int.clip(9876)  # '9.87e3
```

I don't understand why Google doesn't give out '=int.clip' as a standard part to build with

Do you know someone who knows someone who can get 'int.clip' added as a standard part out there?


## Ints of Microsoft Excel

Same deal in Microsoft Excel, as in Google Sheets

You can see our Excel Simd Formula above, presented as our Simd Formula for g Sheets

Indeed, I first wrote this kind of thing for Excel, before I wrote it for g Sheets. The =Let and =Lambda Simd Formula Functions first reached me in a Microsoft Excel

My Feb/2026 pitch for how best to introduce =Let and =Lambda Formulae to new people is
> https://social.vivaldi.net/@pelavarre/116066365378672153

But back in Jun/2021, I posted a similar welcome to work with =Let and =Lambda Formulae at
> https://github.com/pelavarre/like-py-xlsx/blob/main/README.md

I don't understand why Microsoft doesn't give out '=int.clip' as a standard part to build with

Do you know someone who knows someone who can get 'int.clip' added as a standard part out there? If Google & Microsoft insist on staying clueless, can we wake up Amazon & Apple?


# Fixed for Floats


## Floats of Python

Python counts many things as Ints, but some things as Floats

Like Python says the 'time.time()' difference between two moments is a float

```python
>>> print(type(time.time() - time.time()).__name__.title())
Float
>>>
```

When you count a thing as Floats, then I still want our only "0" to be the true actual positive and negative zeroes, not the other numbers near to them

For sure, we can tell Python to be this careful in how it speaks to us

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

    # could return .clip_int for floats equal to ints, but doesn't


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

    # math.trunc leaps too far, all the way down to the int ceil/ floor
```

## Floats of Google Sheets

We solve g Sheets for Floats like so

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

Here you're watching us spend 14 Lines of Simd Formula to solve Floats and Ints. Far above, we spent 14 Lines to solve only Ints. Maybe there's a simpler way to solve Ints

We did do some more homework here. We've shown ourselves that our two Formulae do agree across the Ints from -1000 to 1000, and across a few thousand Random Ints. As for Ints below -1000 and above 1000, we give ourselves inductive algebraic arguments as reasons to believe our Float and Int Formulae always do produce the same correct answers


## Floats of Microsoft Excel

Same deal in Microsoft Excel, as in Google Sheets

You can see our Excel Simd Formula above, presented as our Simd Formula for g Sheets


## Traps laid for you by Google Sheets & Microsoft Excel

Pitfalls, with spikes in them


### Near Infinities

g Sheets will corrupt very small input of '1e-999' or '-1e-999', silently substituting an actual zero. By contrast, it does at least poison very large input of '1e999' or '-1e999'

They say bounds checking vs small numbers is on you, not on them. They say it's on you to stay perfectly inside a range of like 1e-300 to 1e300 to keep answers reasonable


### Not-a-Number

When you can get your Number to be their =NA() form of not-a-number, then our Formulae produce =NA() as their Results, not the String '#N/A, which would be more like our design choice for Python



# Links

- [GitHub Repository](https://github.com/pelavarre/pylitfun)
- [Questions/ Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre+%23PyLitFun)


<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/clipped-numbers.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
