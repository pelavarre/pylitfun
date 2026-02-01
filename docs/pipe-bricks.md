<!-- omit in toc -->
# pipe-bricks.md

- [1 Welcome](#1-welcome)
  - [1.1 Please help yourself](#11-please-help-yourself)
  - [1.2 Download \& run](#12-download--run)
  - [1.3 Edit your own Os Copy/Paste Clipboard Buffer](#13-edit-your-own-os-copypaste-clipboard-buffer)
  - [1.4 Write into a Shell Pipe without spelling out the fiddly | and ' parts](#14-write-into-a-shell-pipe-without-spelling-out-the-fiddly--and--parts)
  - [1.5 Run the Paste Buffer through a Shell Pipe](#15-run-the-paste-buffer-through-a-shell-pipe)
  - [1.6 How many Words are out there?](#16-how-many-words-are-out-there)
- [2 Steer well clear of Unicode Decode Error, even at Apple macOS](#2-steer-well-clear-of-unicode-decode-error-even-at-apple-macos)
  - [2.1 Dash](#21-dash)
  - [2.2 Decode](#22-decode)
  - [2.3 Take out the Trash](#23-take-out-the-trash)
- [3 Count out all the things](#3-count-out-all-the-things)
  - [3.1 Count Lines](#31-count-lines)
  - [3.2 Count Bytes or Characters or Words](#32-count-bytes-or-characters-or-words)
  - [3.3 Count out the Length of Each Line, when need be](#33-count-out-the-length-of-each-line-when-need-be)
- [4 Byte by Byte](#4-byte-by-byte)
    - [4.1 Md5 and Sha256](#41-md5-and-sha256)
    - [4.2 Strings](#42-strings)
- [5 Character by Character](#5-character-by-character)
    - [5.1 ExpandTabs](#51-expandtabs)
    - [5.2 Str](#52-str)
- [6 Line by Line](#6-line-by-line)
  - [6.1 Append](#61-append)
  - [6.2 Counter](#62-counter)
  - [6.3 Dent](#63-dent)
  - [6.4 Enumerate](#64-enumerate)
  - [6.5 Frame](#65-frame)
  - [6.6 Head](#66-head)
  - [6.7 If](#67-if)
  - [6.8 Insert](#68-insert)
  - [6.9 Join](#69-join)
  - [6.10 LStrip](#610-lstrip)
  - [6.11 Max](#611-max)
  - [6.12 Min](#612-min)
  - [6.13 Printable](#613-printable)
  - [6.14 RemovePrefix](#614-removeprefix)
  - [6.15 RemoveSuffix](#615-removesuffix)
  - [6.16 Reverse](#616-reverse)
  - [6.17 RStrip](#617-rstrip)
  - [6.18 Set](#618-set)
  - [6.19 Shuffle](#619-shuffle)
  - [6.20 Slice](#620-slice)
  - [6.21 Sort](#621-sort)
  - [6.22 Strip](#622-strip)
  - [6.23 Sum](#623-sum)
  - [6.24 Tail](#624-tail)
  - [6.25 Translate](#625-translate)
  - [6.26 Unframe](#626-unframe)
- [7 Shell Aliases for Pipe Bricks](#7-shell-aliases-for-pipe-bricks)
  - [7.1 Inside the Pipe](#71-inside-the-pipe)
  - [7.2 Outside the Pipe](#72-outside-the-pipe)
- [8 Single Letter Aliases for Pipe Bricks](#8-single-letter-aliases-for-pipe-bricks)

# 1 Welcome

## 1.1 Please help yourself

You say you build out Shell Pipes in your Terminal? With your own fingers on a Keyboard, like a caveman?

Ouch, you're working too hard

I'm sorry, you are. You're tripping yourself out, to no purpose

Believe me for just long enough to read on a bit, and you'll see what I mean

## 1.2 Download & run

Download & run

    git clone https://github.com/pelavarre/pylitfun.git
    cd pylitfun/
    export PATH=$PATH:$PWD/bin
    which pb

This is not an install into the Shell Path chosen by your ~/.profile Shell Script. This is just a test, just a way to try out this Code, before you surface your need for it

<!--

It's a quicker test if you skip the 'cd' and just say

    export PATH=pylitfun/bin

But that stops working as soon as you change your $PWD

-->

## 1.3 Edit your own Os Copy/Paste Clipboard Buffer

So you know you can say

    pbpaste |tr '[a-z]' '[A-Z]' |pbcopy

Yes that works. And it's a horribly fiddly input line

For starters, I'm pointing out you can instead just say

    pb |tr '[a-z]' '[A-Z]' |pb

That comes out looking as clean as this

    % echo Hello, World! |pb
    % pb
    Hello, World!
    %

    % pb |tr '[a-z]' '[A-Z]' |pb
    %

    % pb
    HELLO, WORLD!
    %

Get it?

You don't have to keep straight whether you mean 'pbpaste' or 'pbcopy'. You don't have to spell out '|pbcopy' and 'pbpaste' in full. The 'pb' and '|pb' are hints enough

This kind of 'pb' works by branching on sys.stdin.fileno().isatty()

    % cat pb
    if [ ! -t 0 ]; then
        pbcopy "$@A"
    else
        pbpaste "$@A"
    fi
    %

You can adopt this sh/.pb Shell Script into your Shell Path and workflow now. Read a bit more, and you'll immediately pick up your next small win

<!--

Linux folk have to work first to make pbpaste, pbpaste|, and |pbcopy go. Those two come built-in at Apple macOS.

-->

## 1.4 Write into a Shell Pipe without spelling out the fiddly | and ' parts

We can carry this same line of thinking a step farther

You can just say

    pb upper

That comes out looking as clean as this

    % echo Hello, World! |pb
    % pb
    Hello, World!
    %

    % pb upper
    HELLO, WORLD!
    %

Our sh/.pb alone isn't change enough to make all of this work. You have to adopt our bin/pb to make this work

Our word UPPER comes from the Python BuiltIns. One of their datatypes is STR. And one of its methods is UPPER. This way of choosing a Word makes this Shell Hack memorable for Shell & Python people. You can add dozens of conveniences and then still find them a month later, when next you need them

All of the Python words could work, and dozens already do. Like you can try 'pb lower' and 'pb title' and 'pb casefold' now, just as seeing 'pb upper' work teaches you to hope you can

## 1.5 Run the Paste Buffer through a Shell Pipe

However, in our rush to show you can say 'upper' in place of "|tr '[a-z]' '[A-Z]'", we did run past mentioning that you're not rewriting the Paste Buffer when you say it that way

    % echo Hello, World! |pbcopy
    % pbpaste
    Hello, World!
    %

    % pb upper
    HELLO, WORLD!
    %

    % pbpaste
    Hello, World!
    %

See that? No change to the Paste Buffer

Next, from our talk so far, you know already know you could fix this by adding the four characters ' |pb'

    pb upper |pb

But there is a better way. Try

    0 upper

This comes out as clean as

    % echo Hello, World! |pbcopy
    % 0
    Hello, World!
    %

    % 0 upper
    HELLO, WORLD!
    %

    % pbpaste
    HELLO, WORLD!
    %

Our 'pb' was a middling kind of explicit. You don't spell out if you meant 'pbpaste' or 'pbcopy', but you do still say when you do and don't want to write into the Paste Buffer

Our '0' and '1' and '2' and '3' always do write back into the Paste Buffer

When you pick '0', then you read from the Paste Buffer and write back. When you pick '1' then you read from the -1'th copy

Try

    echo Hello, World! |pbcopy
    0 upper

    pbpaste
    1
    pbpaste

By the end you're looking at

    % pbpaste
    HELLO, WORLD!
    %

    % 1
    Hello, World!
    %

    % pbpaste
    Hello, World!
    %

Get it?

We give you a Stack of Paste Buffers. 0 is your latest revision, 1 is your second to last, 2 is your third to last, 3 is your fourth to last

You choosing 1 works like you choosing the "Over" of a Forth Stack Machine, or the "Rcl Y" of an HP Calculator Stack Machine. You choosing 0 after 0 works like you choosing the "Dup" of a Forth Stack Machine, the "Enter" of an HP Calculator Stack Machine

## 1.6 How many Words are out there?

An awful lot

Try some word that you remember from Python or from Shell and tell us when you feel a word is missing or running wrong?

You can see like 75 Words suggested at

    pb --help

You can speak each of these Words as the Name of a Pipe Brick. Each of these Pipe Bricks works like a Shell Pipe Filter, but each Pipe Brick is easier to grab a hold of and stick to other Bricks, like a LEGO® Brick is

Their names come from tradition. Learn the stories the old people tell, and you'll find the names memorable

# 2 Steer well clear of Unicode Decode Error, even at Apple macOS

## 2.1 Dash

Show the Bytes Written

When you do pipe a text back into the Paste Buffer, you often need to review it immediately. We let you say '| pb -' to mean that

    echo Abc |cat -n |pb -

We learned to spell Dash as the U+002D Hyphen-Minus by analogy with '|cat -'

    printf '\033[1m''bold\n''\033[m''plain\n' |cat -

Linux folk dream that Apple macOS lets you say make-it-printable with '|cat -tv'. Until one day they try out enough of the 0x80..0xFF Bytes

    % printf 'Tab\tNac\xC0\x80Lf\n' |cat -tv |hexdump -C
    00000000  54 61 62 5e 49 4e 61 63  c0 4d 2d 5e 40 4c 66 0a  |Tab^INac.M-^@Lf.|
    00000010
    %

You see that?

The Apple macOS '|cat -tv' lets the 0xC0 Byte through, as if it were printable, while actually it's not printable enough to go farther

    % printf 'Tab\tNac\xC0\x80Lf\n' |cat -tv |tr '[A-Z]' '[a-z]' >t.txt
    tr: Illegal byte sequence
    %

Try that in Apple macOS and it tells you talk to the hand while it's making a Stop sign. Apple's '|cat -tv' makes this trouble a problem for you, but our '|pb -' doesn't

## 2.2 Decode

Decode all the Bytes

Apple macOS will flatly deny service when you stray far from US Ascii

    % printf '\xC0\x80\n''Not a character\n' |sed 's/N/Just bytes, n/'
    sed: RE error: illegal byte sequence
    %

Why? Because Apple macOS is still fighting the Character Encoding Wars of late last century

Linux folk dream that '|cat -tv' should fix this. They're correct to say it should work, but they're wrong to feel it does work

    % printf '\xC0\x80\n''Not a character\n' |cat -tv |sed 's/N/Just bytes, n/'
    sed: RE error: illegal byte sequence
    %

Our Python bytes.decode Pipe Brick does just work. We don't freak over rare bytes so much as to deny service

    % printf '\xC0\x80\n''Not a character\n' |pb decode |sed 's/N/Just bytes, n/'
    ¤¤
    Just bytes, not a character
    %

You might want to substitute macOS Homebrew Shell Pipes for your Apple macOS Shell Pipes. Until you do that, your macOS Shell Pipes will flame out at random times, because still fighting the Character Encoding Wars of late last century

## 2.3 Take out the Trash

We call our Pb Decode for you when you ask for '|pb -', but just for what you show at the Terminal

When you do want to change what you're writing, not just show approximately what you're writing, then you have to ask to change it

    % printf '\xC0\x80\n' |pb -
    ¤¤
    % pb |hexdump -C |sed 's,   *,  ,g'
    00000000  c2 bf c3 84 0a  |.....|
    00000005
    %

    % printf '\xC0\x80\n' |pb decode |pb
    % pb |hexdump -C |sed 's,   *,  ,g'
    00000000  c2 a4 c2 a4 0a  |.....|
    00000005
    % pb
    ¤¤
    %

# 3 Count out all the things

By default, we work with Lines, exactly as Python str.splitlines does, which is much like Shell '|awk'


## 3.1 Count Lines

Counting Lines looks like this

    % seq 99 |pb len
    99
    %


## 3.2 Count Bytes or Characters or Words

And you can count Bytes or Characters or Words instead

    % echo ¡Feliz cumpleaños!
    ¡Feliz cumpleaños!
    %

    % echo ¡Feliz cumpleaños! |pb bytes len
    21
    % echo ¡Feliz cumpleaños! |pb str len
    20
    % echo ¡Feliz cumpleaños! |pb split len
    2
    % echo ¡Feliz cumpleaños! |pb splitlines len
    1
    % echo ¡Feliz cumpleaños! |pb len
    1
    %

At Shell, these are |wc -c, |wc -m, |wc -w, and |wc -l. Or they would be, except that lots of Shells don't count Line-Break's as Characters 🙄, so |wc -m comes out at N below what it means to count across N Lines ended by single U+000A Line-Feed Bytes

You can keep fighting that war, or you can move on


## 3.3 Count out the Length of Each Line, when need be

When what you want is the length of each Line, in the style of the Shell '|wc -L' that is not Shell '|wc -l, then you can say

    % ls -l |pb .len int.max
    67
    %


# 4 Byte by Byte

Above, we've already spoken of 9 Pipe Bricks

    bytes casefold decode len lower split str title upper

For working with Bytes, we offer more


### 4.1 Md5 and Sha256

You can ask for the Shell 'md5sum', and you can ask to include the Byte Length

    % cat /dev/null |pb md5
    d41d8cd98f00b204e9800998ecf8427e  -
    %

    % cat /dev/null |pb .md5
    d41d8cd98f00b204e9800998ecf8427e  0  -
    %

The Shell 'md5sum' and 'sha256sum' tools often mislead people by neglecting to mention Zeroed Byte Lengths. People come out wrongly feeling the Hash of Zero Bytes is indecipherable, while it's actually very well known

    % cat /dev/null |pb sha256
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
    %

    % cat /dev/null |pb .sha256
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 0  -
    %


### 4.2 Strings

You've often heard that Apple macOS is still fighting the Character Encoding Wars of late last century

Yea. Well, both their '|cat -etv' and their '|strings' do wrongly forward some of the 0x80 .. 0xFF Bytes as if they were Printable Characters. In our particular example here, the Unprintable Byte 0xC0

    % printf 'abcd\xC0wxyz\n' |cat -etv
    abcd¤wxyz$
    %

    % printf 'abcd\xC0wxyz\n' |hexdump -C
    00000000  61 62 63 64 c0 77 78 79  7a 0a                    |abcd.wxyz.|
    0000000a
    %

    % printf 'abcd\xC0wxyz\n' |strings
    abcd¤wxyz
    %

    % printf '\xC0wxyz\n' |strings |tr . .
    tr: Illegal byte sequence
    %

Odds on your Terminal is showing you those unprintable ¤ Characters ambiguously, as visually identical to the U+003F 'Question Mark' Character. We regret their error, and we don't follow it

    % printf 'abcd\xC0wxyz\n' |pb -
    abcd¤wxyz
    %

    % printf 'abcd\xC0wxyz\n' |pb strings
    abcd
    wxyz
    %

You can call on us in place of Apple macOS, as often as you remember you dislike their error as much as I do

    % cat $(which cat) |pb strings |head -3
    __PAGEZERO
    __TEXT
    __text
    %


# 5 Character by Character

Above, we've already spoken of 12 Pipe Bricks

    bytes casefold decode md5 len lower sha256 split str strings title upper


### 5.1 ExpandTabs

For working with Characters, we also offer expandtabs

    % echo Abc |cat -n |pb -
         1¤Abc
    % echo Abc |cat -n |pb expandtabs
         1  Abc
    %


### 5.2 Str

You've not yet seen our work with Lines, but I want you to know up front we do make all our work with Lines available to you for work with Characters

For example, to show which Characters show up in a Source File in the order of their first occurrence, you can call on us

    % cat bin/litshell.py |pb decode str set |pb join --sep=''
    #!/usrbinev pytho3"ag:l.[-]VSEPTARBICKdwcf,mkx'?QM01q|F$O=+2LUj56DHWz8&_>9N()G%Y·Z*{}4^←↑→↓\;7¤~<@

And you might prefer to tell us to sort the Characters before deduplicating them

    % cat bin/litshell.py |pb decode str sort set |pb join --sep=''
     !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIKLMNOPQRSTUVWYZ[\]^_abcdefghijklmnopqrstuvwxyz{|}~¤·←↑→↓
    %


# 6 Line by Line

We've developed most of our Bricks to work with Lines, in particular these twenty-five

    append counter dent enumerate frame head if insert join max min
    printable removeprefix removesuffix reverse rstrip set shuffle slice
    sort strip strip sum tail unframe


## 6.1 Append

Python str.append

    % ls -l |tail -2 |column -t |pb append
    -rw-r--r--@  1   plavarre  staff  282   Feb  1  12:32  requirements.txt$
    drwxr-xr-x   41  plavarre  staff  1312  Feb  1  12:55  sh$
    %

    % ls -l |tail -2 |column -t |pb append /@/
    -rw-r--r--@  1   plavarre  staff  282   Feb  1  12:32  requirements.txt@
    drwxr-xr-x   41  plavarre  staff  1312  Feb  1  12:55  sh@
    %

    % ls -l |tail -2 |column -t |pb append '/ <-- Line-Break /'
    -rw-r--r--@  1   plavarre  staff  282   Feb  1  12:32  requirements.txt <-- Line-Break
    drwxr-xr-x   41  plavarre  staff  1312  Feb  1  12:55  sh <-- Line-Break
    %

Technically speaking, Python BuiltIns declare only a list[str].append and not a str.append, but you know what we mean

Adding '|pb append' to a Shell Pipe comes out looking a lot like '|sed 's,$,$,' and even more like '|cat -etv

Often we'll just say '|pb $' to mean '|pb append'

See also Pb Insert, and Pb RemoveSuffix to undo Append


## 6.2 Counter

Python collections.Counter(list[str])

    % echo Alfa Bravo Alfa Bravo Charlie |pb split counter
    2?Alfa
    2?Bravo
    1?Charlie
    %

Adding '|pb counter |expand' to a Shell Pipe comes out looking a lot like '|uniq -c', but without forcing you to sort the Lines before you can drop the duplicates, so more like "|awk '!d[$0]++'" really

See also Pb Set


## 6.3 Dent

"Dent" in the sense of inserting 4 Blank Columns at the Left of each Line, as Python textwrap.dedent will undo

    % seq 3
    1
    2
    3
    %

    % seq 3 |pb dent -
        1
        2
        3
    %

See also Pb Unframe and Pb RemovePrefix


## 6.4 Enumerate

Python list[str].enumerate

    % ls -l |pb enumerate |tail -3 |column -t
    4  -rw-r--r--@  1   plavarre  staff  10746  Feb  1  12:12  README.md
    5  -rw-r--r--@  1   plavarre  staff  282    Feb  1  12:32  requirements.txt
    6  drwxr-xr-x   41  plavarre  staff  1312   Feb  1  12:55  sh
    %

Often we'll just say '|pb n' or '|pb nl' to mean '|pb enumerate'

We define '|pb enumerate' and '|pb nl' to default to ' --start=0', while defining '|pb .enumerate' and '|pb .nl' and '|pb n' to default to ' --start=1', in homage to Shell tradition. We don't define a '|pb .n'


## 6.5 Frame

"Frame" in the sense of inserting 2 Blank Rows above and below, as well as 4 Blank Columns at left and at right

    % seq 3 |pb frame


        1
        2
        3


    %

    % seq 3 |pb frame append
    $
    $
        1    $
        2    $
        3    $
    $
    $
    %

We define '|pb .frame' to mean '|pb frame' but str.rstrip each Line out

Often we'll just say '|pb O' to mean Pb Frame in its four dimensions, and '|pb o' to mean Pb Unframe

See also Pb Dent and Pb Unframe


## 6.6 Head

Python list[str][slice(stop)]

    % echo a b c d e f g h i j k l m |pb split enumerate head -3
    0¤a
    1¤b
    2¤c
    %

We define '|pb .head' to mean fill your Terminal Screen with the many First Lines, not just the First 9 Lines

Often we'll just say '|pb h' to mean '|pb head -9'. This works very much like Shell '|head -9' and it's off-by-one from Shell '|head'

We also ship '|sh/.head' to fill your Terminal Screen with the many First Lines

    ROWS=$(stty size </dev/tty|cut -d' ' -f1)  # $LINES flakes out variously
    set -xe
    head -$((ROWS - 3))

See also Pb Tail


## 6.7 If

"If" in the sense of drop the Precisely Empty Lines, like you can say in Python

    list(_ for _ in sys.stdin.splitlines() if _)

For example, to add double-spacing from a text can be

    % seq 3 |pb append |tr '$' '\n'
    1

    2

    3

    %

which is then neatly undone by Pb If

    % seq 3 |pb append |tr '$' '\n' |pb if
    1
    2
    3
    %


## 6.8 Insert

Python str.insert

    % ls -l |head -2 |column -t |pb insert
        total       40
        drwxr-xr-x  47  plavarre  staff  1504  Jan  29  08:17  bin
    %

    % ls -l |head -2 |column -t |pb insert /+/
    +total       40
    +drwxr-xr-x  47  plavarre  staff  1504  Jan  29  08:17  bin
    %

    % ls -l |head -2 |column -t |pb insert '/  /'
    total       40
    drwxr-xr-x  47  plavarre  staff  1504  Jan  29  08:17  bin
    %

Technically speaking, Python BuiltIns declare only a list[str].insert and not a str.insert, but you know what we mean

Often we'll just say '|pb ^' to mean '|pb insert'

See also Pb Append, Pb Dent, and Pb RemovePrefix to undo Insert


## 6.9 Join

Python str.join(list[str])

    % (echo a b; echo c d; echo e f)
    a b
    c d
    e f
    %

    % (echo a b; echo c d; echo e f) |pb join
    a b  c d  e f
    %
    % (echo a b; echo c d; echo e f) |pb join --sep=' '
    a b c d e f
    %
    % (echo a b; echo c d; echo e f) |pb join --sep=' x '
    a b x c d x e f
    %


## 6.10 LStrip

Python str.lstrip

    % echo '  abc  ' |pb $
      abc  $
    % echo '  abc  ' |pb lstrip $
    abc  $
    % echo '  abc  ' |pb strip $
    abc$
    % echo '  abc  ' |pb rstrip $
      abc$
    %


## 6.11 Max

Python list[str].max, or Python list[float].max, or Python list[int].max

    % echo 3 14 15 9 |pb split
    3
    14
    15
    9
    %

    % echo 3 14 15 9 |pb split max
    9
    %

    % echo 3 14 15 9 |pb split float.max
    15
    %

You can also say '|pb .max' to mean '|pb float.max'

See also Pb Min, Pb Sort, and Pb Sum


## 6.12 Min

Python list[str].max, or Python list[float].max, or Python list[int].max

    % echo 3 14 15 9 |pb split min
    14
    %

    % echo 3 14 15 9 |pb split float.min
    3
    %

You can also say '|pb .min' to mean '|pb float.min'

See also Pb Max, Pb Sort, and Pb Sum


## 6.13 Printable

Python str.isprintable

    % echo Abc |cat -n |pb
    %
    % echo Abc |cat -n |pb -
         1¤Abc
    %
    % echo Abc |cat -n |pb printable
         1¤Abc
    %

Our '|pb -' inside of a Pipe faithfully stores a copy of Stdin and forwards those Bytes intact on into Stdout. We default to run the Bytes through '|pb printable' only when they're going into a Tty

Technically speaking, Python defines both a Python string.printable and also a similar but different Python str.isprintable. Fun fun name collision! We regret their error. We go with the Python str.printable


## 6.14 RemovePrefix

Python str.removeprefix

See also Pb Insert of prefix, and Pb RemoveSuffix

    % seq 3 |pb insert
        1
        2
        3
    %

    % seq 3 |pb insert |pb removeprefix '/  /'
      1
      2
      3
    %


## 6.15 RemoveSuffix

Python str.removesuffix

    % seq 3 |pb insert
        1
        2
        3
    %

    % seq 3 |pb insert |pb removeprefix '/  /'
      1
      2
      3
    %

See also Pb Append of suffix, and Pb RemoveSuffix


## 6.16 Reverse

Python list[str].reverse, or Python str.reverse

When you're working with Lines, our '|pb reverse' comes across like a macOS '|tail -r' or a Linux '|tac'

    % seq 3
    1
    2
    3
    %

    % seq 3 |pb reverse
    3
    2
    1
    %

For when you want a line-by-line reversal of the Characters in each Line, we define '|pb .reverse' to work like Shell '|rev'

    % printf 'Hello\n''Goodbye' |pb .reverse
    olleH
    eybdooG
    % 

    % printf 'Hello\n''Goodbye' |rev        
    olleH
    eybdooG
    % 

Often we'll just say '|pb r' to mean '|pb reverse'

In particular '|pb r set r' means wait till the last Line arrives, then show me the Lines in the order they arrived, but with the duplicates removed from the top

And we do let you say '|pb reversed' in place of 'pb reverse', in homage of 'list(reversed(list[str]))'

See also Pb Shuffle, and Pb Sort


## 6.17 RStrip

Python str.rstrip

    % echo '  abc  ' |pb $
      abc  $
    % echo '  abc  ' |pb lstrip $
    abc  $
    % echo '  abc  ' |pb strip $
    abc$
    % echo '  abc  ' |pb rstrip $
      abc$
    %


## 6.18 Set

Python set(list[str])

    % echo Alfa Bravo Alfa Bravo Charlie |pb split
    Alfa
    Bravo
    Alfa
    Bravo
    Charlie
    %

    % echo Alfa Bravo Alfa Bravo Charlie |pb split set
    Alfa
    Bravo
    Charlie
    %

Adding '|pb set' to a Shell Pipe comes out looking a lot like '|uniq', but without forcing you to sort the Lines before you can drop the duplicates, so more like "|awk '!d[$0]++'" really

See also Pb Counter


## 6.19 Shuffle

Python random.shuffle(list[str])

    seq 6 |pb shuffle head -1

Try it, you'll like it. It's the pseudo-random roll of one 6-face die

See also Pb Sort


## 6.20 Slice

Not yet Spec'd out and implemented

    % ls -l |pb a
    40
    bin
    docs
    Makefile
    README.md
    requirements.txt
    sh
    % 

Often we'll just say '|pb a' to mean '|pb .slice -1'


## 6.21 Sort

Python list[str].sort, or Python list[float].sort, or Python list[int].sort

    % echo 3 14 15 9 |pb split
    3
    14
    15
    9
    %

    % echo 3 14 15 9 |pb split sort
    14
    15
    3
    9
    %

    % echo 3 14 15 9 |pb split float.sort
    3
    9
    14
    15
    %

You can also say '|pb .sort' to mean '|pb float.sort'

And we do let you say '|pb sorted' in place of 'pb sort', in homage of 'list(sorted(list[str]))'

See also Pb Max, Pn Reverse, Pb Shuffle, and Pb Sum


## 6.22 Strip

Python str.strip

    % echo '  abc  ' |pb $
      abc  $
    % echo '  abc  ' |pb lstrip $
    abc  $
    % echo '  abc  ' |pb strip $
    abc$
    % echo '  abc  ' |pb rstrip $
      abc$
    %


## 6.23 Sum

list[float].sum or list[int].sum

    % (echo 1 2 3; echo 4 5 6)
    1 2 3
    4 5 6
    %
    % (echo 1 2 3; echo 4 5 6) |pb sum
    5 7 9
    %

See also Pb Max, Pb Min, and Pb Sort


## 6.24 Tail

Python list[str][slice(len(_) - stop, len(_))]

    % echo a b c d e f g h i j k l m |pb split enumerate tail -3
    10¤k
    11¤l
    12¤m
    %

We define '|pb .tail' to mean fill your Terminal Screen with the many Last Lines, not just the Last 9 Lines

Often we'll just say '|pb t' to mean '|pb tail -9'. This works very much like Shell '|tail -9' and it's off-by-one from Shell '|tail'

Often we'll just say '|pb t' to mean '|pb tail -9'

We also ship '|sh/.tail' to fill your Terminal Screen with the many Last Lines

    ROWS=$(stty size </dev/tty|cut -d' ' -f1)  # $LINES flakes out variously
    set -xe
    tail -$((ROWS - 3))

See also Pb Head


## 6.25 Translate

Not yet Spec'd out and implemented

Calls Python str.maketrans once and then Python str.translate on the Characters


## 6.26 Unframe

Let's say you do frame some Lines. Well, after you frame them and copy them out somewhere, often enough you'll want to unframe them again

We help you with that

You can frame a thing

    % seq 3 |pb frame |pb
    % pbpaste |cat -e
    $
    $
        1    $
        2    $
        3    $
    $
    $
    %

And you can unframe it again

    % pbpaste |pb unframe |cat -e
    1$
    2$
    3$
    %

Showing this persuasively can be difficult, because we so often unframe by default. You've got to choose some Brick in particular when you want to run without an implicit automagic '|pb frame' cleaning up whatever you've left in the Paste Buffer. Our '|pb -' is the shortest explicit way to say we don't unframe it for you

    % seq 3 |pb frame |pb
    % pbpaste |cat -e
    $
    $
        1    $
        2    $
        3    $
    $
    $
    %
    % pb
    1
    2
    3
    % pb -


        1
        2
        3


    %
    % pb unframe |pb
    % pbpaste |cat -e
    1$
    2$
    3$
    %

As easy as we make it to unframe by default, we also keep it easy quick to explicitly say do unframe it. We'll just say '|pb o' to mean Pb Unframe in its four dimensions, and '|pb O' to mean Pb Frame


# 7 Shell Aliases for Pipe Bricks

## 7.1 Inside the Pipe

We often let you type a familiar Shell Word in place of our Python Word

| Shell | PyLitFun |
| ----- | -------- |
| awk | .slice |
| chars | str |
| data | bytes |
| expand | expandtabs |
| head | head |
| lines | splitlines |
| md5sum | md5 |
| nl | .enumerate |
| rev | .reverse |
| shuf | shuffle |
| tac | r |
| text | str |
| words | split |

The '|uniq' and '|uniq -c' of Shell come with their bizarre small-machine limitation of needing sorted input. Because of this, we don't emulate them, even though we could. For now you have to find your way to calling for '|pb counter' or '|pb set', much more in the way of "|awk '!d[$0]++'"

## 7.2 Outside the Pipe

Adopt our 'bin/pb' and you get most of what we discuss in this doc, but if you tire of typing 'pb 0' to mean 0 then you can also adopt our bin/0, bin/1, bin/2, and bin/3 as we've shown

For ourselves we also post many more intensely cryptic abbreviations to become everyday things in like daily use

In our Sh Folder

| Shell Script | Meaning |
| ------------ | ------- |
| sh/.bash | Bash but without Profile |
| sh/.cat | Cat but as 'echo Press ⌃D to continue' && cat - >/dev/null |
| sh/.cut | Cut to Screen |
| sh/.echo | Print an unambiguous Python Repr of the Sys ArgV |
| sh/.emacs | Emacs but without Profile |
| sh/.exit.sh | Shell Source for .exit to mean show the Shell's $? Process Exit Status Return Code |
| sh/.head | Head but fill Screen |
| sh/.ls | ls -hlAF -rt --full-time -d except also at macOS and -d only for multiple Args |
| sh/.od | Come close to '|hexdump -C' when that's not available |
| sh/.pb | Pb but without Args and without its implicit Unframes |
| sh/.screen | Celebrate 'screen -rr' and probably do nothing else as helpful |
| sh/.sed | Convert a Git 'Changes to be committed' into Commit Message Lines |
| sh/.sort | Sort but inside LC_ALL=C |
| sh/.ssh | Ssh but without Profile |
| sh/.tail | Tail but fill Screen |
| sh/.uniq | Uniq but inside LC_ALL=C |
| sh/.vim | Vim but without Profile |
| sh/.zsh | Zsh but without Profile |

In our Bin Folder

| Shell Script | Meaning |
| ------------ | ------- |
| g | git ... |
| \|g | \|grep -ai -e ... -e ... |
| p | python3 -c 'import ...; ...' |

# 8 Single Letter Aliases for Pipe Bricks

We let you type just one Memorable Letter to stand for a whole Pipe Brick

For example, a search of Shell Input History can look like

    cat ~/.*.log |pb decode r set r |.cut |grep -ai -e CP -e MV |grep -ai F=

In there, each of the two ' r ' stand for a '|pb reverse' Pipe Brick

Memorable Lowercase Letters

| Letter | Brick |
| ------ | ----- |
| h | head |
| i | split |
| n | enumerate --start=1 |
| o | unframe |
| r | reverse |
| s | sort |
| t | tail |
| u | counter, in the way of Shell \|uniq -c |
| w | splitlines len, much in the way of Shell \|wc -l |
| x | join --sep='  ', much in the way of Shell \|xargs |

Memorable Uppercase Letters

| Letter | Brick |
| ------ | ----- |
| F | casefold |
| L | lower |
| O | frame |
| T | title |
| U | upper |

The pun with 'FLOTUS' amuses me, but I've not found a convincing case for defining '|pb S' to mean anything in particular. We do define '|pb .sort' to mean the Float Sort not the Str Sort


<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/pipe-bricks.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
