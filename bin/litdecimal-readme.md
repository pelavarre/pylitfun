<!-- omit in toc -->
# litdecimal-readme.md


# Why we care

**1 ) The problem:** We need your eyes to grasp instantly which numbers matter, when you glance across a list of file sizes, network traffic, or search results. But today's formatting tools fail you. They show much detail, or too little. They make small and large numbers hard to compare, or they round away information you need. They cost you time and accuracy.

**2 ) Why care:** We work now with numbers that span enormous ranges, more enormous now than in years past. Like lately we'll put 74 bytes next to 2 billion bytes in the same table. When your formatter says "0" for something that's actually 74, you've been lied to. When it rounds 3652 to "3.6K" to mean 3.65e3, you've been misled. These aren't edge cases. These corners come at you more like daily. Even our 64-bit Ints for counting things have now begun overflowing, for everyone working out beyond 9.22e18 E (exa).

**3 ) Why now:** We wrote the first generation of number formatters for analog engineers. We kept the ranges narrow and limited the precision. Today, we count digital things that run from single bytes to terabytes, from nanoseconds to years. We need formatting that does format well across all of our actual data and its indefinitely large and growing precision. We need formatting that doesn't trip us up.

**4 ) What dream:** A quick & simple way to format numbers that makes it immediately clear which numbers are big and which are small, that doesn't round away information you need, that doesn't says you crossed a critical boundary when you didn't. A kind of formatting that speaks only the truth of Ints. This short paper sketches up a simple way that works.


# Show not tell

6 Bad Examples and then 1 Good Example:

| Format             |     288 |         3652 |    104999 | Precision                                 | Clarity                              |
|--------------------|--------:|-------------:|----------:|-------------------------------------------|--------------------------------------|
| ---                |     --- |          --- |       --- | ---                                       | ---                                  |
| str(_)[:3]         |     288 |       365... |    104... | Impossible to compare large and small     | Cut too short                        |
| ls -lh .           |    288B |         3.6K |      103K | Two digits are often not enough           | Too hard to pick B apart from 8      |
| ls -l .            | **288** |         3652 |    104999 | 999 is too much                           | To hard to pick 4999 apart from 9999 |
| {_:.2f}            |  288.00 |      3652.00 | 104999.00 | Every .00 is too much                     | Much too much ink                    |
| round(_ / 1000, 2) |   0.29k |    **3.65k** |    105.0k | Two digits past the dot can be not enough | Which did come out rounded           |
| {_:.3g}            | **288** | **3.65e+03** |  1.05e+05 | Delivered as asked                        | But which did come out rounded       |
| ---                |     --- |          --- |       --- | ---                                       | ---                                  |
| eng(_)             | **288** |   **3.65e3** | **104e3** | **Just Enough**                           | **Clear**                            |
| ---                |     --- |          --- |       --- | ---                                       | ---                                  |

Do you feel you get most of this? Are you only thinking real numbers or also the text of the digits of a digital numeric literal?


# Round down to floor, up to ceiling, or either way half the time

Do you feel I've gone too far, when I chose the simple constant truncation of always rounding down to the floor, and not the conventional variable round up to the ceiling half the time?

I agree more conventional is an option. Indeed, I agree round to ceiling half the time is the most familiar, and therefore most clear, option when we do have so much control that we're giving the audience only one revision of the data. But as for this century now, not last century, well, things have changed. In my present work for hire, we commonly send the data down multiple routes to reach our audiences. They get one revision from one pipe and another revision from another pipe.

When we tell our audiences to look for 1 0 4 9 in one place and 1 0 5 in another, we're not helping. Near me, the least awful compromise is to radically reduce the precision, give over only three digits, and have those three digits be the same three digits that they'll find coming at them through the other pipelines that do not radically reduce precision. Soon enough to round things up after we can get all the pipes to agree over how much precision to send out.

Aye for certain when I give you just 1 0 4 then half the time you'll have to search for 1 0 5 too before you find everybody out there who is rounding up. But this is better than asking you to remember to search also for 1 0 3 when they give you 1 0 4 because maybe it was 1 0 3 9. Because for most of the people in our audiences, it's better to ask you to remember to look up than to ask you to look down. Because they hold a bias for forward, over backward.

Choices. Second standards, and third standards, after the first standard.

We're working here to put out the word on **the wins found in always presenting three digits and always rounding down to floor**. To catch what every one means by 1 0 4 you have to search up 1 0 3 and 1 0 5 too. Yes you do, and no we're not making this worse. Truncate to floor already did have adopters you had to go find, especially the people who just copy the leftmost digits of the number to you, and then cut it short.

**The wins, and the low cost.** To fix this problem, you pretty much just have to notice it exists and move to fix it. Not much permission required.

<!--

zero
single digit positive ints
two and three digit ints

0
1 .. 9
10 .. 999
1000 .. 9999
10_000 ... 2**53 - 1 (aka 8 Pi - 1)
2**53 .. (10**308 + x)
(10**309 - y) ..


-->