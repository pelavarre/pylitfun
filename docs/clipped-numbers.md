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
    - [And still give me Ceils for Sums of Measure plus Margin](#and-still-give-me-ceils-for-sums-of-measure-plus-margin)
- [One main takeway](#one-main-takeway)
  - [What you can have now, for the asking](#what-you-can-have-now-for-the-asking)
  - [Why fear the bad keming tomorrow](#why-fear-the-bad-keming-tomorrow)
- [Fix known, and not yet well known](#fix-known-and-not-yet-well-known)
  - [Fix for Ints](#fix-for-ints)
    - [Ints of Python](#ints-of-python)
    - [Ints of Google Sheets](#ints-of-google-sheets)
    - [Ints of Microsoft Excel](#ints-of-microsoft-excel)
  - [Fix for Floats](#fix-for-floats)
    - [Floats of Python](#floats-of-python)
    - [Floats of Google Sheets](#floats-of-google-sheets)
    - [Floats of Microsoft Excel](#floats-of-microsoft-excel)
    - [Traps laid for you by Google Sheets \& Microsoft Excel](#traps-laid-for-you-by-google-sheets--microsoft-excel)
      - [Numbers too close to zero for them](#numbers-too-close-to-zero-for-them)
      - [Not-a-Number](#not-a-number)
- [Future Work](#future-work)


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

These numbers do naturally show us more structure, when made more meaningful. They split themselves apart, into two piles

Most simply, the small numbers

```sh
% ls -l |pb eng awk 5 split |grep -v e3 |pb join
818  716  288  282
%
```

But also separately, the big numbers

```sh
% ls -l |pb eng awk 5 split |grep e3 |pb join
1.41e3  1.37e3  1.56e3  3.65e3  10.7e3  1.63e3
%
```

Hold this difference in mind, between small numbers written with little ink, vs big numbers written with more ink. Watch what happens to your visual perception when we just correct the format of these numbers, while leaving them in place in their rows. You see that? They come and naturally split their rows across this same dividing line

The extra ink visually brings forward the rows of the big numbers

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

The careful lack of extra ink visually pushes back the rows of the small numbers

```sh
% ls -l |pb eng replace columns |grep -v e3
total        72
...     818  Feb  13  17:22  2
...     716  Feb  13  17:22  3
...     288  Feb  14  09:05  docs
...     282  Feb   1  12:32  requirements.txt
%
```

You don't have to make time to read through the meaningless detail. You can decline to struggle. You can make it a job for the Bots to clip away the meaningless detail for you


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

Yea well, they get these wrong too. I feel they stopped thinking. I'd say they got stuck in 1998, because it was 1999 when we solved this. We stood up then to spell out that Ki is 1024 and k is 1000

Like our particular example of 3652 is more than 3.65k and more than 3.56Ki. But they distort it. They go and count out what doesn't exist, by thinking of it as 3.56Ki rounded up to 3.6Ki, then intentionally misspeaking it as '3.6K'

They come out talking bizarrely far away from the actual 3.65k we're actually looking at. They're unthinkingly, arbitrarily and misleadingly, rounded up to wrongly speak of the 3.6 that is 0.05 less than 3.65. Rounding UP to speak of LESS than. Grr

4 ) How many digits do you need to see?

2 digits is not enough, and 4 digits is too many, I am saying. Here I stand. How about for your eyes?

Tools like last century's 'ls -h' do me wrong, by giving me 2 digits and stopping there. All the while the only 3652 known to me is the 3.65e3. I need its name spoken in that familiar way. Aye fair enough, in real life I autocorrect their wrongs on the fly, but I'm posting this rant because I do wish they'd stop shoving their wrongs at me. Take out their own trash, why can't they. Keep it away from me


## Say what fix solves the four bugs

Bug reports harm us while they talk only of what we got wrong

What we need from a bug report is a fresh new vision of what we can do better, because we care about how I receive the numbers you format. We voluntell you to work harder on tuning up what you send me, until I do receive your numbers well

Above I say only what we get wrong. Here I say what we can do better

I'm saying you have spoken **a well-clipped number** when you speak the name I know best of a number that counts things. It's on me to learn the best names, but it's on you to speak the best names, and only the best names. Specifically =>

1 ) **Zero means Zero =>** You say 0, but only to mean 0

2 ) **Zero doesn't mean Epsilon =>** You don't say 0 to mean 1, and you don't say 0 to mean a 1e-999 nonzero epsilon

3 ) **Empty details fade away =>** You don't waste ink on mentioning 'e+' or 'e0' or a trailing '.' or '.0' or '.00'. Instead, you show your proper respect for the time I'll be spending reading every character of what you wrote. You hold back from giving me the kinds of extra characters that I never need to read

4 ) **You give me my first three digits =>** You stop yourself from sending me wrong. You don't round up to some irrelevant ideal of a rounder number. You do give me three digits and done, but you do it by backing off from demanding I give you credit for the last few things you counted. You never give me the lie of you having counted things that you never actually saw

You make it easy for me to read what you say correctly, and you make it hard for me to read it wrong


### And still give me Ceils for Sums of Measure plus Margin

And doesn't rounding UP matter too, in the digital age? Yes it does. But here's how

To speak clearly, we'll start by borrowing two words from Maths. Digital Maths people talk of a "Floor" when you slam a Float down to the next smaller Int, and a "Ceil" when you slam the Float up to the next larger Int. They speak their word Ceil as shorthand for the word picture of a ceiling above you

Ceils matter, yes they matter. But they work differently. Ceils are for sums of measure plus margin

Like when I make a space for a Count of Things, then I have to add Margin to the Count. and then I round this Sum up to the next whole Allocation. Like there's practically never any real need for speaking of 9999 as 10000, because that Margin is tiny 

You can't just tweak around a Count for me, not while you commit fully to only showing up to help me and never to hurt me. You need me to tell you how much Margin I need us to add. And you need me to tell you if my Allocations are 4Ki or 1Ki or 0.5Ki or whatever. Only then can you know how to round up our Counts well, to a Ceil of a good choice of Sum

Can we wake up and meet our moment? We all know we actually don't involve you or me personally in the careful allocation of Space anything like as often as we did in 1972. Now that's commonly a job for the Bots, not the work of living People

Do you get it? You see how our first century of Software Traditions for clipping numbers lead us astray?


# One main takeway


## What you can have now, for the asking

You can have "correct at a glance" precision. Ask for it persistently, and they will eventually come and give it to you

| Format    | 3652   | 104999 | 288   | Precision  | Acuity |
|-----------|--------|--------|-------|----------- |--------|
| ls -l     | 3652   | 104999 | 288   | Too Much   | Weak   |
| ls -lh    | 3.6K   | 103K   | 288B  | Too Litle  | Weak   |
| pb eng    | 3.65e3 | 10.4e3 | 288   | Helpful    | Strong |


## Why fear the bad keming tomorrow

Beware

If you don't yet feel their bugs are bugs, please stop. Give yourself a moment to feel a fitting degree of fear

I can only teach you to start seeing, I can't teach you to stop. I can't even stop myself seeing. It'll be as if I were teaching you to notice bad [keming](https://en.wikipedia.org/wiki/Kerning) on street signs. Learning to see more wrong will poison your life. It's only worth it if you're building with numbers, or getting rewarded in some other way to work well with numbers. Only then do you need to learn to reject lying numbers quickly, simply, and accurately. As we do here


# Fix known, and not yet well known


To get your numbers well-clipped, you can download & run our Code, or you can write your own Code. To help you write your own, or to help you trust ours, we show our Code below

The run-time costs of adopting this Code are near zero. This Code runs in scratch time, and requires nearly zero memory


## Fix for Ints

The fixes for Floats work for Ints too, but less simply. So you might prefer to first learn to trust the fixes for Ints. Like you can push them faster through Code Review

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


### Ints of Google Sheets

Google Sheets can clip numbers as accurately as Python

As you know, their oldest convention is to code up every new idea as a Simd Formula. Here is our idea, so coded

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

Put that code into a g Sheet, and we can contrast your results with their defaults. Their default is to speak these counts with a reckless excess of precision

```
0 9 999  9000 9800 9870 9876
```

Our code tells the g Sheet to speak with more consideration for your true needs and fading eyesight

```
'0 '9 '999  '9e3 '9.8e3 '9.87e3 '9.87e3
```

And you can tell g Sheets to give the name 'int.clip' to this Formula so as to call your code far more directly and clearly

```excel
=int.clip(9876)  # '9.87e3
```

I don't understand why Google doesn't give out '=int.clip' as a standard part to build with

Do you know someone who knows someone who can get 'int.clip' added as a standard part out there?


### Ints of Microsoft Excel

Same deal on offer from Microsoft Excel, as with Google Sheets

You can see our Simd Formula for g Sheets above, this same Simd Formula works in Excel too

Myself, I first wrote this kind of thing for Excel, years before I tried it inside g Sheets. The =Let and =Lambda Simd Formula Functions first reached me in a Microsoft Excel

My Feb/2026 pitch for how best to introduce the =Let and =Lambda Simd Formulae to new people is
> https://social.vivaldi.net/@pelavarre/116066365378672153

But back in Jun/2021, I posted a similar welcome to work with =Let and =Lambda Formulae at
> https://github.com/pelavarre/like-py-xlsx/blob/main/README.md

I don't understand why Microsoft doesn't give out '=int.clip' as a standard part to build with

Do you know someone who knows someone who can get 'int.clip' added as a standard part out there? If Google & Microsoft resist, can we wake up Amazon & Apple?


## Fix for Floats


### Floats of Python

Python counts many things as Ints, but some things as Floats

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

When you count a thing as Float, then I still need our only "0" to be the true actual positive and negative zeroes, not the other numbers near to them. Happily, yes we can tell Python to be this careful in how it speaks to us

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

    # math.trunc leaps too far, all the way down to the int ceil/ fl∏oor
```

You could claim copyright on the arbitrary 0.000123 fudge factor in here. The answers come out the same for most choices of what to add. You very nearly only need to add something nonzero and smaller than one. Like you could add in a significant date-time, if you want. Like you could add Tank Man's 1989-06-05 12th Hour, spoke of as 0.1989060512

### Floats of Google Sheets

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


### Floats of Microsoft Excel

Same deal in Microsoft Excel, as in Google Sheets

You can see our Excel Simd Formula above, presented as our Simd Formula for g Sheets


### Traps laid for you by Google Sheets & Microsoft Excel

Pitfalls, with spikes in them


#### Numbers too close to zero for them

g Sheets will corrupt very small input of '1e-999' or '-1e-999', silently substituting an actual zero. By contrast, it does at least poison very large input of '1e999' or '-1e999'

They say bounds checking vs small numbers is on you, not on them. They say it's on you to stay perfectly inside a range of like 1e-300 to 1e300 to keep answers reasonable


#### Not-a-Number

When you can get your Number to be their =NA() form of not-a-number, then our Formulae produce a conventional =NA() as our Result

That's not the String '#N/A that would be more of a transliteration of the Python convention of looking always to narrow a Result Datatype to Str from Str | Float | None


# Future Work

Help people speak e3, e-3, e6, e-6, etc as metric prefixes of k, m, M, Greek μ, etc

Help people find the Ceil of a Measure plus Margin, rounding up to their Unit of Choice

Help people separate when to clip a number sharply, vs when to forward all the precision they've got. APIs for data interchange send out lots of precision for good reasons through standard file formats: .csv, .json, etc


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
