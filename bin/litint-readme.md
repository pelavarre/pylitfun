<!-- omit in toc -->
# litint-readme.md

Here we talk over how our short simple [litint.py](https://github.com/pelavarre/pylitfun/blob/main/docs/litint.py) works.

Contents

- [The problem and our solution](#the-problem-and-our-solution)
  - [Every standard Int format often goes far wrong](#every-standard-int-format-often-goes-far-wrong)
  - [Python has a name for our solution](#python-has-a-name-for-our-solution)
  - [Small systems solved similarly](#small-systems-solved-similarly)
  - [4 Digits with no Dot for when 16 is larger than 10](#4-digits-with-no-dot-for-when-16-is-larger-than-10)
- [Fourteen Compelling Tests](#fourteen-compelling-tests)
- [Past work](#past-work)
  - [The Engineer's answer to 2 + 2](#the-engineers-answer-to-2--2)
  - [Pi in schools](#pi-in-schools)
  - [The Python Int's created inequal](#the-python-ints-created-inequal)
- [Conclusion](#conclusion)

## The problem and our solution

### Every standard Int format often goes far wrong

You can learn to see how each standard Int format often goes far wrong, and how to tell your computer to fix it.

In this table, only the **bold** is correct, and every plain text is a standard computer gone wrong in some different standard way.

| Format             | 1st Example |  2nd Example | 3rd Example | Precision                           | Clarity                             |
|--------------------|------------:|-------------:|------------:|-------------------------------------|-------------------------------------|
| {:_}               |     **288** |       3\_652 |    104\_999 | Too many exact digits               | Blurred because wide                |
| str(_)[:3]         |     **288** |       365... |      104... | Cannot compare large and small      | Cut too short                       |
| ls -lh .           |        288B |         3.6K |        103K | Two digits can be too few           | Hard to see "B" is not "8"          |
| ls -l .            |     **288** |         3652 |      104999 | "999" is too much after "104"       | Hard to see "4999" is not "9999"    |
| {_:.2f}            |      288.00 |      3652.00 |   104999.00 | Every .00 is too much               | Blurred because wide                |
| round(_ / 1000, 2) |       0.29k |    **3.65k** |      105.0k | Two digits past dot can be too few  | How many rounded digits?            |
| {_:.3g}            |     **288** | **3.65e+03** |    1.05e+05 | Good precision, but lacking clarity | Too exact exp & many rounded digits |
| eng(_)             |     **288** |   **3.65e3** |   **104e3** | **Precise enough**                  | **Wonderfully clear**               |

Have your eyes already learned to see tiny problems in typography?

For example, bad Keming is a common problem when printing English. You thought you said to print r and then n but then you feel what you got is m because your rn characters are printing too close together, looking too much like a smudged m. Good "Kerning" is the technical term for spacing out letters well. Bad "Keming" is what you have when it's gone wrong.

The problem we solve here is similar, but for digits, not for letters.

Tiny problems in typography matter because they shatter trust. Some random someone begins to trust and promote your work, but then stumbles and quits on you, just because you neglected some basic principle of typography. Too many someones too often, until you learn to do better. Before you learn to see tiny problems in typography, you can wrongly feel they don't matter, just because you can't see them. You're wrong about that, till you learn to see well.

You can fix all this, simply, after you learn to see it gone wrong.

### Python has a name for our solution

Python includes a solution, and gives it six names. You can find this solution in Python if you can remember its six names.

+ decimal.Context,
+ prec=3,
+ rounding=decimal.ROUND\_DOWN,
+ to\_eng\_string,
+ .lower()
+ .replace("e+", "e")

Python's Decimal-Round-Down means Truncate. For instance, when the original was "2.489", then Truncate gives you "2.48" or "2.4" or "2". Truncate always gives you an accurate copy of what the first few digits were in the original. Python's Decimal-Round-Up is the enemy: it gives you "2.49" or "2.5" or "2", depending on where it's applied and how often it's applied. It rounds away the last few digits of the original, only sometimes or always, and never tells you how many digits it corrupted.

As Python Code, this solution looks like

    i = int(repr(n))
    ctx = decimal.Context(prec=3, rounding=decimal.ROUND_DOWN)
    D = ctx.create_decimal
    clip = D(i).to_eng_string().lower().replace("e+", "e")

We ship this solution out as a 'def decimal_int_chop_to_eng' with docstring & comments & tests added. But this is the core of it.

Python does offer you more choices. Together with the faithful Round Down, Python lets you choose instead a Round Up, and a Ceiling & a Floor, & fuzzier choices of Half Down, Half Up, Half Even, and 0 5 Up. All of these choices have earned a place in one kind of numerical analysis or another. But Python's "round down" choice of words is misleading. It is word choice anchored in last century, from pre-computer people who thought of ideal infinite precision as normal and quantization as an enemy. It falsely suggests some complex hidden choices changing from one number to the next, like noticing when a digit is 0 or 5 or even or odd or between 5 and 9. We say "truncate" and "chop" to emphasize we give you accuracy in the leading digits, never any complex hidden choices. We take quantization as normal, and ideal infinite precision as expensive. We say "truncate", we let them say "round down", and we all move on.

### Small systems solved similarly

Systems that work like Python but lack 'import decimal' can solve this just as well, albeit not quite as briefly. They work more directly with the Digits of the Int.

We ship our copy of their alternative out as 'def repr_int_chop_to_eng'. Its core is

    precise = digits[:-eng] + "." + digits[-eng:]  # '120.789'
    nearby = precise[:4]  # '120.'  # significand, mantissa, multiplier  # with a dot included
    worthy = nearby.rstrip(".")  # '120' # drops a single trailing '.'
    clip = dash + worthy + "e" + str(eng)  # '-120e3' as a way of saying -120*10**3

Still reasonably simple and small.

### 4 Digits with no Dot for when 16 is larger than 10

Lots of practical work needs at least three digits, and nearly all practical work never needs more than a dot and three digits. But getting a standard format to give you three digits always is such a struggle. They love to cut your short, and they love to go on too long.

Even when they do deliver the three digits, they often get the last digit wrong. They don't let you ask to truncate the details. They insist on rounding up the last digit, and only half the time. When you don't have a copy of the original, you can't know what it said. Oops. They often go far wrong like that, and we don't.

The corner of dealing with decimal counts of binary metric prefixes is slightly less simple, because 0 .. 2**10 - 1 is 0 .. 1023, which is as many as four digits, albeit no dots. We deal with that separately. For that corner, we talk of 0, 0.00, 0.01, ... 0.99, 1.00, ... 9.99, 10.0, 10.1, ... 100, ... 999, 1000, 1001, ... 1023.

After glancing across this much of our doc and tests and code gives you the idea, you're all set up to review the details in the code we ship.

## Fourteen Compelling Tests

We've dug up more than a dozen telling test cases.

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

Never an "e0" exponent. Never more than three digits. Always exactly three digits before any "e" exponent, even when ending in "00". Always an unsigned exponent, never marked by "+", nor by "+0". Always the first three digits, truncated. Never the last few digits damaged by rounding up.

We do agree, our "104e3" and "120e3" and "987e3" can be misread as lowercase hex. We're sorry to see it, but eating this cost as part of our chosen compromises. Nearby, our "999" can be misread as "0x999", and we're not fixing that either.

## Past work

### The Engineer's answer to 2 + 2

Different roles call for different conventions. A mathematician will tell you 2 + 2 is 4. A scientist more like says 4.00, calling out some exact idea of precision. An accountant will ask you what you want it to be. An engineer will tell you it's less than 5, and ask if you need to know more than that.

We're saying that less than 3 digits commonly misleads you with inadequacy, and more than 3 digits is commonly floods you with excess.

That's how exactly 3 digits comes out as exactly correct. Goldilocks. But your search will fail, when you go looking for those same 3 digits in the original detail, unless you take care to always truncate and never round up.

### Pi in schools

Nearly all practical work never needs more than three digits. And all the standard formats shove excess precision at you. Why? Who can afford excess precision, in this economy? They do try to say you must distinguish 'math.pi' from 22/7. But back in real life, you just don't care, not until you need the last 0.04% of accuracy:

    >>> 100 * ((22/7 - math.pi) / math.pi)
    0.04024994347707008
    >>>

Most engineers know to feel hurt by inadequate precision. But you can learn to feel the full horror of excess precision too. You see us working hard here now to duck out of it entirely.

### The Python Int's created inequal

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

## Conclusion

To fix this problem, you pretty much just have to learn to feel it exists, and then move to fix it. Not much permission required.

Tiny wins that add up well, bought for near zero cost, for not much beyond awareness.

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litint-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
