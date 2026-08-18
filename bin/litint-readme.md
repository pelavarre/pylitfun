<!-- omit in toc -->
# litint-readme.md

Contents

- [Every standard Int format goes wrong](#every-standard-int-format-goes-wrong)
- [Python has a name for this corner](#python-has-a-name-for-this-corner)
- [We have tests for this corner](#we-have-tests-for-this-corner)
- [The precedent of Math Pi](#the-precedent-of-math-pi)
- [The engineer's answer to 2 + 2](#the-engineers-answer-to-2--2)
- [Not all Python Int's are created equal](#not-all-python-ints-are-created-equal)
- [The wins, and the low cost](#the-wins-and-the-low-cost)

## Every standard Int format goes wrong

We can teach you to see what they get wrong, and how to fix it.

| Format             |     288 |       3\_652 |  104\_999 | Precision                                   | Clarity                               |
|--------------------|--------:|-------------:|----------:|---------------------------------------------|---------------------------------------|
| ---                |     --- |          --- |       --- | ---                                         | ---                                   |
| str(_)[:3]         |     288 |       365... |    104... | Impossible to compare large and small_      | Cut too short                         |
| ls -lh .           |    288B |         3.6K |      103K | Two digits in total can be not enough       | Too hard to pick B apart from 8       |
| ls -l .            | **288** |         3652 |    104999 | 999 is too much, after 104                  | Too hard to pick 4999 apart from 9999 |
| {_:.2f}            |  288.00 |      3652.00 | 104999.00 | Every .00 is too much                       | Much too much ink                     |
| round(_ / 1000, 2) |   0.29k |    **3.65k** |    105.0k | Two digits past the dot can be not enough   | And which of these is rounded?        |
| {_:.3g}            | **288** | **3.65e+03** |  1.05e+05 | Enough precision, but still lacking clarity | Which of these is rounded?            |
| ---                |     --- |          --- |       --- | ---                                         | ---                                   |
| eng(_)             | **288** |   **3.65e3** | **104e3** | **Just Enough**                             | **Clear**                             |
| ---                |     --- |          --- |       --- | ---                                         | ---                                   |

Have your eyes learned to see problems in typography? For example, bad Keming is a common problem when printing English. You thought you said to print r and then n but then you feel what you got is m because your rn characters are printing too close together, looking too much like a smudged m. Good "Kerning" is the technical term for spacing out letters well. Bad "Keming" is what you have when it's gone wrong.

The problem we solve here is similar, but for digits, not for letters.

Lots of practical work needs at least three digits, and nearly all practical work never needs more than three digits. But getting a standard format to give you three digits always in a struggle. They love to cut your short, or they go on too long.

And even when they do deliver the three digits, they often get the last digit wrong. They don't let you ask to truncate the details. They insist on rounding up the last digit, and only half the time. When you don't have a copy of the original, you can't know what it said. Oops.

You can fix all this, simply, after you learn to notice that it's been going wrong on you.

## Python has a name for this corner

Python shows you our solution if you know to look for it, in the corner posted as

+ decimal.Context,
+ prec=3,
+ rounding=decimal.ROUND\_DOWN,
+ to\_eng\_string,
+ lower

And also to finish up you have to replace their "e+" with "e".

As Python Code, this looks like

    def _(n: int) -> str:
        i = int(repr(n))
        ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)
        D = ctx.create_decimal
        clip = D(i).to_eng_string().lower().replace("e+", "e")
        return clip

This corner is possible to find online, but deeply deeply buried in the weeds, as you can see. Besides the precise Round Down, they offer Up, and Ceiling & Floor, & the fuzzier choices of Half Down, Half Up, Half Even, and 0 5 Up.

After glancing across this much code gives you the idea, you're set up to review the details in the code we ship. We add comments, docstrings, and asserts. And we code the idea twice. Once as shown here, and then once again by working directly with strings, bypassing the 'import decimal' trick of Python, so as to set us up for porting this code into Google Sheets & Microsoft Excel and so on.

## We have tests for this corner

We've collected some telling test cases.

Never an "e0" exponent. Never more than three digits. Always exactly three digits before any "e" exponent, even when ending in "00". Always an unsigned exponent, never marked by "+", nor by "+0". Always the first three digits, truncated. Never the last digit changed by rounding up.

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

## The precedent of Math Pi

Nearly all practical work never needs more than three digits. But all the standard formats shove excess precision at you. Most famously, they try to say you must distinguish 'math.pi' from 22/7. Meanwhile, back in real life, you don't care, not until you need the last 0.04% of accuracy

    >>> 100 * ((22/7 - math.pi) / math.pi)
    0.04024994347707008
    >>>

Most engineers know to feel hurt by inadequate precision. But we feel the full horror of excess precision too. You see us here working hard to duck it.

## The engineer's answer to 2 + 2

Different roles call for different conventions. A mathematician will tell you 2 + 2 is 4. A scientist more like says 4.00, calling out some exact idea of precision. An accountant will ask you what you want it to be. An engineer will tell you it's less than 5, and ask if you need to know more than that.

We're arguing here that less than 3 digits commonly misleads you with inadequacy, more than 3 digits is commonly floods you with excess. That's how exactly 3 digits comes out as exactly correct. But you won't find those same 3 digits in your original detail, unless you take care to always truncate and never round up.

## Not all Python Int's are created equal

Do you feel Python Int Math should be simple?

In reality, working with larger and larger Int's gives you more wrinkles to solve, one after another. For sure, you can think first of the simple internal reality. Each Python Int is a simple digital native: a binary count of arbitrary precision, always with sign, never with overflow. But as you gather more and more bits into a Python Int, you face more and more consequences downstream.

Nine boundaries force us to write more code, as our Decimal Int's grow larger:

| - | At or Above |      Exact Last Simple | Next Complexity                                       |
|---|------------:|-----------------------:|-------------------------------------------------------|
| 1 |         999 |                    999 | 1000 or 1\_000 or 1,000 or 10**3 or 1e+3               |
| 2 |        1023 |              2**10 - 1 | Binary Prefixes start at Ki, go up through Qi, & stop |
| 3 |     9.00e15 |                  2**53 | float(n) == float(n - 1) starts happening             |
| 4 |     9.99e15 |             10**16 - 2 | repr(float(n)) switches to e+ notation                |
| 5 |     9.22e18 |              2**63 - 1 | 64-bit ints start arguing about if they're unsigned   |
| 6 |      999e30 |             10**33 - 1 | Decimal Metric Prefixes cap out above 999 Q - 1       |
| 7 |     1.29e33 |  2\*\*110 - 2**100 - 1 | Binary Prefixes cap out above 1023 Qi - 1             |
| 8 |     179e306 | 2\*\*1024 - 2**970 - 1 | float(n) raises OverflowError                         |
| 9 |   9.99e4299 |           10**4300 - 1 | str(n) and int(digits) and f"{:d}" raise ValueError   |

Last century had it easier, but work for hire now commonly crosses the 1e18 Exa and 1.15e18 Exbi boundaries.

+ 999: Many people stop transcribing numbers accurately near here.
+ 9.00e15: That's counting out Petabytes, not even Exabytes.
+ 9.22e18: We did dream a 63-bit Int could count anything. Not so much now.

Two technical notes.

Note 1.

Reducing your scope to speak of Python Int's only as Binary, Octal, or Hexadecimal changes the shape and consequences of the 10\*\*4300 - 1 boundary. CPython gives you MemoryError after O(N) time for binary bases, in place of ValueError before O(N*N) time for a decimal base, when you test indefinitely large Int's.

Note 2.

Mixing Python Int's with Python Byte's surfaces more boundaries:

| At or Above |      Exact Last Simple | Next Complexity                                        |
|------------:|-----------------------:|--------------------------------------------------------|
|         127 |               2**7 - 1 | max signed 8-bit int                                   |
|         256 |                   2**8 | CPython guarantees (int(n) is n) only across -5 .. 256 |
|      32.7e3 |              2**15 - 1 | max signed 16-bit int                                  |
|      2.14e9 |              2**31 - 1 | max signed 32-bit int                                  |
|     9.22e18 |              2**63 - 1 | max signed 64-bit int                                  |

## The wins, and the low cost

To fix this problem, you pretty much just have to notice it exists and move to fix it. Not much permission required.

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litint-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
