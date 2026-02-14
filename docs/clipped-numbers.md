<!-- omit in toc -->
# clipped-numbers.md

Contents

- [Show \& tell](#show--tell)
  - [Show](#show)
  - [First Tell](#first-tell)
  - [Second Tell](#second-tell)
  - [What is a Well Clipped Number?](#what-is-a-well-clipped-number)
  - [How much Space do I need?](#how-much-space-do-i-need)
- [Fixed for Int's](#fixed-for-ints)
  - [Int's of Python](#ints-of-python)
  - [Int's of Google Sheets](#ints-of-google-sheets)
  - [Int's of Microsoft Excel](#ints-of-microsoft-excel)
- [Fixed for Float's](#fixed-for-floats)
  - [Float's of Python](#floats-of-python)
  - [Float's of Google Sheets](#floats-of-google-sheets)
  - [Float's of Microsoft Excel](#floats-of-microsoft-excel)
- [Links](#links)


# Show & tell


## Show


A familiar Terminal Shell Experience is

    || Permissions || Hardlinks || Owner || Group || Bytes || Date/ Time || Pathname ||

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

But have your eyes learned to prefer

    || Permissions || Hardlinks || Owner || Group || Bytes || Date/ Time || Pathname ||

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

?

## First Tell

The big difference here is in the Byte Counts, spoken as precise decimal int literals. Like so long as you do keep the Byte Counts detailed out to the last digit, then they are

    % ls -l |pb && pb awk 5 |pb join --sep=' '
    1415 1378 818 716 1568 288 3652 10747 282 1632
    %

But who has time for that? When made more meaningful, these Numbers catch up some structure. They naturally split into two piles

First the Small Numbers

    % ls -l |pb
    %

    % pb eng awk 5 split |grep -v e3 |pb join
    818  716  288  282
    %

And also, separately, the Big Numbers

    % pb eng awk 5 split |grep e3 |pb join
    1.41e3  1.37e3  1.56e3  3.65e3  10.7e3  1.63e3
    %

Keep these Numbers inside their Rows, and then they easily split the Rows exactly across this same boundary

First the Rows of the Small Numbers

    % ls -l |pb eng replace columns |grep e3
    -rw-r--r--@   1  jqdoe  staff  1.41e3  Feb  14  09:11  0
    -rw-r--r--@   1  jqdoe  staff  1.37e3  Feb  14  09:10  1
    drwxr-xr-x   49  jqdoe  staff  1.56e3  Feb  13  16:24  bin
    -rw-r--r--    1  jqdoe  staff  3.65e3  Feb   7  18:46  Makefile
    -rw-r--r--@   1  jqdoe  staff  10.7e3  Feb   3  09:40  README.md
    drwxr-xr-x   51  jqdoe  staff  1.63e3  Feb  13  16:24  sh
    %

And then also the Rows of the Big Numbers

    % ls -l |pb eng replace columns |grep -v e3
    total        72
    -rw-r--r--@   1  jqdoe  staff     818  Feb  13  17:22  2
    -rw-r--r--@   1  jqdoe  staff     716  Feb  13  17:22  3
    drwxr-xr-x    9  jqdoe  staff     288  Feb  14  09:05  docs
    -rw-r--r--@   1  jqdoe  staff     282  Feb   1  12:32  requirements.txt
    %


## Second Tell

Senior people will tell you that Linux & macOS do work to help you in just this way

That's true, but they get it significantly wrong. It looks like they stopped thinking, got stuck in the past, since 1998

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

Egregiously wrong in four ways

1 ) How old are your eyes? Do your eyes reliably pick out "888" from "88B"? Mine don't. Oh how I do dislike this waste of ink. I don't need a "B" on screen to tell me zero more digits are there. And half the time it comes into my brain as a lie, saying "2888" where it meant "288". Please make it stop

2 ) I do appreciate the metric units:  k, M, G, etc to mean e3, e6, e8, etc. But I feel annoyed as often as I notice they put an unconventional 'K' in place of the standard 'k'

3 ) I wish they would calculate standard units. Late last century we did spell out that Ki is 1025 and k is 1000. So our example of 3652 is more than 3.65k and more than 3.56Ki. But they distort this, they fabricate imaginary Bytes, they claim '3.6K'. They mislead me, which I dislike

4 ) Their abbreviation is 50% excessive, besides being slightly wrong. I practically always need to see three digits to feel I know the size of the thing. Two digits is not enough, and four digits is too many, but they give me two and stop. I know 3652 as 3.65e3, so I need its name spoken that way

If you don't yet feel these wrongs are egregious, beware. I can only teach you to start seeing, I can't teach you to stop. It'll be like me teaching you to notice bad keming. Learning to see will poison your life. It's only worth it if you're building with numbers, or getting paid in some other way to work with numbers. Then you do need to learn to reject lying numbers quickly, simply, and accurately. As we do here


## What is a Well Clipped Number?

When you speak the name I know best of a number that works as a count of things, then you have spoken a well-clipped number

You say 0 only to mean 0

You don't say 0 to mean 1

You don't waste ink on mentioning 'e+' or 'e0' or a trailing '.' or '.0' or '.00'. Instead, you show your respect for the time I spend reading every character of what you wrote

You don't round up to some fabricated ideal of a rounder number. Sure, you still do give me three digits and done, but you do it by backing off from demanding I give you credit for the last few things you counted. You don't round up and send me wrong by giving me the lie of you having counted things that you actually never saw


## How much Space do I need?

In maths, they talk of a "Floor" when you slam a Float down to the next smaller Int, and a "Ceil" when you slam the Float up to the next larger Int. Aye, sure, I do know and I do agree, there is a place in Engineering and Science for Ceil's, not only for Floors

But in the Engineering place for Ceil, there I also need Margin

When I'm involving myself in the careful allocation of space, then I have to add margin

I must round counts plus margin to whole allocations. But there's practically no need for speaking of 9999 as 10000, because that margin is tiny. You can't just fix it for me, not while you commit to only showing up to help me and never to hurt me. You need me to tell you how much margin I need. And you need me to tell you if my allocations are 4Ki or 1Ki or 0.5Ki or whatever. Only then can you know how to round up well

And besides, it's already 2026 now. We don't involve me personally in the careful allocation of space anything like as often as we did in 1972. Let's wake up and meet our moment, why not


# Fixed for Int's

To make `ls -lh` say what it should mean in 2026

    ls -l |pb eng replace columns

It's the '|pb eng' part that fixes up the counts

    ls -l |pb eng

You can download & run our Code, or you can write your own


## Int's of Python

Yes you can call on Python to clip a count back to three digits. You don't have to let it whisper lies into your eyes

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

Correct Answers

    (0, "0"),
    (99, "99"),
    (999, "999"),

    (9000, "9e3"),  # not '9.00e3'  # not '9e+03'
    (9800, "9.8e3"),  # not '9.0e3'
    (9870, "9.87e3"),  # not '9.870e3'
    (9876, "9.87e3"),  # not rounded up to '9.88e3'

We're looking at correct answers here. Correct and nothing but correct. No "B" vs "8" visual confusions. Always unsigned metric exponents like "e3", never a scientific exponent like "e+2" or "e1" or "e-0". Powers of 10 as the Base of "e", not powers of the 10th power of 2 (1024). Three digits when you've got three digits, never chopped down so far as to show just two digits or one. And no empty busy ".00"s. Ink spent only when ink delivers value


## Int's of Google Sheets

Google Sheets can clip numbers as well as Python. Their convention is to code up this idea as a Simd Formula

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

Again we can run the contrast with defaults. The g Sheets default is to speak these counts with a reckless excess of precision

    0 9 999  9000 9800 9870 9876

Our code tells to it to speak with more consideration for your true needs and fading eyesight

    '0 '9 '999  '9e3 '9.8e3 '9.87e3 '9.87e3

If you work so closely with g Sheets as to name this Formula, you can give it the name 'int.clip' and then call it far more simply

    =int.clip(9876)  # '9.87e3

I don't understand why Google doesn't give out '=int.clip' as a standard part to build with. Do you know someone who knows someone who can get 'int.clip' added as a standard part out there?


## Int's of Microsoft Excel

Same deal as in Google Sheets

The =Let and =Lambda Simd Formula Functions first reached me by way of a Microsoft Excel

My Feb/2026 pitch for how best to introduce =Let and =Lambda Formulae to new people is
> https://social.vivaldi.net/@pelavarre/116066365378672153

Back in Jun/2021, I posted a similar welcome to work with =Let and =Lambda Formulae at
> https://github.com/pelavarre/like-py-xlsx/blob/main/README.md

I don't understand why Microsoft doesn't give out '=int.clip' as a standard part to build with. Do you know someone who knows someone who can get 'int.clip' added as a standard part out there? If Google & Microsoft insist on staying so clueless, can we wake up Amazon & Apple?


# Fixed for Float's


## Float's of Python


## Float's of Google Sheets


## Float's of Microsoft Excel


# Links

- [GitHub Repository](https://github.com/pelavarre/pylitfun)
- [Questions/ Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre+%23PyLitFun)


<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/clipped-numbers.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
