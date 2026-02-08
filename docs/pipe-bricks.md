<!-- omit in toc -->
# pipe-bricks.md

- [1 Welcome](#1-welcome)
  - [1.1 Please help yourself](#11-please-help-yourself)
  - [1.2 Download \& run](#12-download--run)
  - [1.3 Edit your own Os Copy/Paste Clipboard Buffer](#13-edit-your-own-os-copypaste-clipboard-buffer)
  - [1.4 Write into a Shell Pipe without spelling out the fiddly | and ' parts](#14-write-into-a-shell-pipe-without-spelling-out-the-fiddly--and--parts)
  - [1.5 Familiar vocabulary](#15-familiar-vocabulary)
  - [1.6 Run your Paste Buffer through a Shell Pipe](#16-run-your-paste-buffer-through-a-shell-pipe)
  - [1.7 How many Words are out there?](#17-how-many-words-are-out-there)
- [2 Steer well clear of Unicode Decode Error, even at Apple macOS](#2-steer-well-clear-of-unicode-decode-error-even-at-apple-macos)
  - [2.1 Dash, to show the Bytes Written](#21-dash-to-show-the-bytes-written)
  - [2.1.1 More particular than macOS '|cat -tv'](#211-more-particular-than-macos-cat--tv)
  - [2.1.2 Less deceptive than macOS '|cat -tv'](#212-less-deceptive-than-macos-cat--tv)
  - [2.2 Decode, to forward all the Bytes in some form](#22-decode-to-forward-all-the-bytes-in-some-form)
  - [2.3 Take out the Trash](#23-take-out-the-trash)
- [3 Count out all the things](#3-count-out-all-the-things)
  - [3.1 Count Lines](#31-count-lines)
  - [3.2 Count Bytes or Characters or Words](#32-count-bytes-or-characters-or-words)
  - [3.3 Count out the Length of Each Line, when need be](#33-count-out-the-length-of-each-line-when-need-be)
- [4 Byte by Byte](#4-byte-by-byte)
    - [4.1 Md5 and Sha256](#41-md5-and-sha256)
    - [4.2 Strings](#42-strings)
- [5 Character by Character](#5-character-by-character)
    - [5.1 Columns](#51-columns)
    - [5.2 Eng](#52-eng)
    - [5.3 ExpandTabs](#53-expandtabs)
    - [5.4 Ord](#54-ord)
    - [5.5 Str](#55-str)
- [6 Line by Line](#6-line-by-line)
  - [6.1 Append](#61-append)
  - [6.2 Counter](#62-counter)
  - [6.3 Cut](#63-cut)
  - [6.4 Dent](#64-dent)
  - [6.5 Enumerate](#65-enumerate)
  - [6.6 Frame](#66-frame)
  - [6.7 Head](#67-head)
  - [6.8 If](#68-if)
  - [6.9 Insert](#69-insert)
  - [6.10 Join](#610-join)
  - [6.11 LStrip](#611-lstrip)
  - [6.12 Max](#612-max)
  - [6.13 Min](#613-min)
  - [6.14 Printable](#614-printable)
  - [6.15 RemovePrefix](#615-removeprefix)
  - [6.16 RemoveSuffix](#616-removesuffix)
  - [6.17 Reverse](#617-reverse)
  - [6.18 RStrip](#618-rstrip)
  - [6.19 Set](#619-set)
  - [6.20 Shuffle](#620-shuffle)
  - [6.21 Slice](#621-slice)
  - [6.22 Sort](#622-sort)
  - [6.23 Strip](#623-strip)
  - [6.24 Sum](#624-sum)
  - [6.25 Tail](#625-tail)
  - [6.26 Translate](#626-translate)
  - [6.27 Unframe](#627-unframe)
- [7 File by File](#7-file-by-file)
- [7.1 Json Files](#71-json-files)
- [8 Shell Aliases for Pipe Bricks](#8-shell-aliases-for-pipe-bricks)
  - [8.1 Inside the Pipe](#81-inside-the-pipe)
  - [8.2 Outside the Pipe](#82-outside-the-pipe)
  - [8.3 Built most quickly](#83-built-most-quickly)
- [9 Future work](#9-future-work)
  - [9.1 Please tell your friends](#91-please-tell-your-friends)
  - [9.2 Their Testimonials](#92-their-testimonials)
  - [9.3 Your Input Errors](#93-your-input-errors)
  - [9.4 Parallel Processing](#94-parallel-processing)
- [10 Links](#10-links)


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

Like to rework your Paste Buffer, you think you can say

    pbpaste |tr '[a-z]' '[A-Z]' |pbcopy

I admit that works. But it's a horribly fiddly input line. You can instead just say

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

You don't have to keep straight whether you mean 'pbpaste' or 'pbcopy'. You don't have to spell out '|pbcopy' and 'pbpaste' in full. Your 'pb' and '|pb' are hints enough

A unified 'pb' works by branching on sys.stdin.isatty() and sys.stdout.isatty(). Inside of Shell, you speak of these as a '-t' test of sys.stdin.fileno() == 0, and as a '-t' test of sys.stdout.fileno() == 1

    % cat sh/.pb
    # .pb = Edit your Os Copy/Paste Clipboard Buffer

    if [ -t 0 ]; then
        pbpaste "$@"
    else
        pbcopy "$@"
        if [ ! -t 1 ]; then
            pbpaste
        fi
    fi
    %

You can see that '|pb ' ends up meaning '| (pbcopy; pbpaste)', which works much like '|sponge' but leaves a copy in '|tee >(pbcopy) |' as it runs oruns on

You can adopt this sh/.pb Shell Script into your Shell Path and workflow now

Read a bit more, and you'll immediately pick up your next small Shell Integration win

<!--

Linux folk have to work first to make pbpaste, pbpaste|, and |pbcopy go. Those two come built-in at Apple macOS.

-->


## 1.4 Write into a Shell Pipe without spelling out the fiddly | and ' parts

This same line of thinking can go a step farther. You can just say

    pb upper

That comes out looking as clean as this

    % echo Hello, World! |pb
    % pb
    Hello, World!
    %

    % pb upper
    HELLO, WORLD!
    %

You do have to adopt our bin/pb to make this work. You make it into an Shell Alias

    alias cv=~/Public/pelavarre/pylitfun/bin/pb

Or you add it into your Path

    ln -s ~/Public/pelavarre/pylitfun/bin/pb ~/bin/pb

You name it what you like. Some of us like 'pb', short for Paste Buffer. Some of us like 'cv', short for ⌘C Edit Copy and ⌘V Edit Paste


## 1.5 Familiar vocabulary

Our word UPPER comes from the Python BuiltIns. One of their datatypes is STR. And one of its methods is UPPER. This way of choosing a Word makes this '|pb upper' Shell Hack memorable for Shell & Python people. You can add dozens of shortcuts and then still find these shortcuts a month later, when next you need them

All of the Python and Shell words could work, and six dozen already do. Like you can try '|pb lower' and '|pb title' and '|pb casefold' now, just as seeing '|pb upper' work teaches you to hope you can, working from your memorization of Python's 'dir(str)'


## 1.6 Run your Paste Buffer through a Shell Pipe

We did leave out a key detail, as we rushed to show you can say 'upper' in place of "|tr '[a-z]' '[A-Z]'"

We owe you mention that you're not rewriting the Paste Buffer when you say it that way

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

But it gets better. Like you know you can fix this by adding the four characters ' |pb'

    pb upper |pb

And we're here to tell you, there is a better way. Try

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

Our 'pb' was a middling kind of explicit. You didn't spell out if you meant 'pbpaste' or 'pbcopy', but you did still say when you did and didn't want to write into the Paste Buffer

Our '0' and '1' and '2' and '3' do more work for you, but more implicitly, more automagically. These four always do write back into the Paste Buffer. When you pick '0', then you read from the Paste Buffer and write back into it. When you pick '1' then you read from your -1'th revision of the Paste Buffer, but you write into the present Paste Buffer

Try

    echo Hello, World! |pbcopy
    0 upper

    pbpaste
    1
    pbpaste

By the end of all that, you're looking at

    % pbpaste
    HELLO, WORLD!
    %

    % 1
    Hello, World!
    %

    % pbpaste
    Hello, World!
    %

You see what you made happen?

We give you a Stack of Paste Buffers. 0 is your latest revision, 1 is your second to last, 2 is your third to last, 3 is your fourth to last

You choosing 1 works like you choosing the "Over" of a Forth Stack Machine, or the "Rcl Y" of an HP Calculator Stack Machine. You choosing 0 after 0 works like you choosing the "Dup" of a Forth Stack Machine, the "Enter" of an HP Calculator Stack Machine

We store these revisions of your Paste Buffer in a very local and destructive way. Without your permission and without backup, we replace one or more of the four Files at

    ./0
    ./1
    ./2
    ./3


## 1.7 How many Words are out there?

Lots and lots

Please try some word that you remember from Python or from Shell. Tell us if you feel a word is missing or running wrong

You can see like 75 Words suggested at

    pb --help

You can speak each of these Python and Shell Words as the Name of a Pipe Brick. Each of these Pipe Bricks runs like a Shell Pipe Filter, but each Pipe Brick is easier to grab a hold of and stick to other Bricks, like a LEGO® Brick is

The names of our Pipe Bricks come from Python and Shell traditions. Learn the stories the old people tell, and you'll find these names memorable


# 2 Steer well clear of Unicode Decode Error, even at Apple macOS


## 2.1 Dash, to show the Bytes Written

When you do pipe a text back into the Paste Buffer, you often need to review it immediately. We let you say '|pb -' in place of '|pb' to mean that you want to see what you wrote

    echo Abc |cat -n |pb -

We chose to spell this out as '|pb -' by analogy with '|cat -', which does much the same thing

    printf '\033[1m''bold\n''\033[m''plain\n' |cat -


## 2.1.1 More particular than macOS '|cat -tv'

Linux folk dream that Apple macOS lets you say make-it-printable with '|cat -tv'. Until one day they try out enough of the 0x80..0xFF Bytes

    % printf 'Tab\tNac\xC0\x80Lf\n' |cat -tv |hexdump -C
    00000000  54 61 62 5e 49 4e 61 63  c0 4d 2d 5e 40 4c 66 0a  |Tab^INac.M-^@Lf.|
    00000010
    %
    % # .............................. ^^
    %

You see that?

The Apple macOS '|cat -tv' lets the 0xC0 Byte through, as if it were printable, while actually it's not printable enough to go farther

    % printf 'Tab\tNac\xC0\x80Lf\n' |cat -tv |tr '[A-Z]' '[a-z]' >t.txt
    tr: Illegal byte sequence
    %

Try this in Apple macOS and it tells you talk to the hand while it's making a Stop Sign. Apple's '|cat -tv' makes this Byte Trouble a problem for you, but our '|pb -' doesn't. We substitute the Bytes b"\xC2\xA4" 'Currency Sign' that are printable as ¤, much like a 💥 'Collision' Boom, as often as you send us Unprintable Bytes to print for you

    % printf 'Tab\tNac\xC0\x80Lf\n' |pb -
    Tab¤Nac¤¤Lf
    %


## 2.1.2 Less deceptive than macOS '|cat -tv'

Linux folk dream that Apple macOS lets you pick apart U+0020 Space from other kinds of blanks with '|cat -tv'. Until one day they try out enough of the U+0080..U+00FF Characters

The Character Trouble that most often trips macOS folk out is the U+00A0 No-Break Space (Nbsp), encoded as the Bytes b"\xC2\xA0", struck on the Macbook Keyboard as ⌥ Spacebar

    % printf 'abc\xC2\xA0def\n' |cat -tv |hexdump -C |column -t
    00000000  61  62  63  c2  a0  64  65  66  0a  |abc..def.|
    00000009
    %
    % # ................. ^^^^^^
    %

You see that?

The Apple macOS '|cat -tv' lets the Bytes b"\xC2\xA0 through, as if they were as printable as a U+0020 Space. But the Python str.isprintable test knows to reject these. We let it tell us to substitute the ¤ 'Currency Sign'

    % printf 'abc\xC2\xA0def\n' |pb -
    abc¤def
    %


## 2.2 Decode, to forward all the Bytes in some form

We define '|pb decode |' inside the Shell Pipe to work a lot like '|pb -' at the far end of the Pipe

Our '|pb -' scrubs the unprintables out of your life, but only when you try to write them to a Tty

Let's look back at how Apple macOS will flatly deny service when you stray far from US Ascii

    % printf 'Just \xC0\x80 Bytes\n' |sed 's/$/, not a Character/'
    sed: RE error: illegal byte sequence
    %

And you'll remember, linux folk dream that '|cat -tv' should fix this. They're correct to say it should work, and they're wrong to feel it does work

    $ printf 'Just \xC0\x80 Bytes\n' |cat -tv |sed 's/$/, not a Character/'
    sed: RE error: illegal byte sequence
    %

Apple macOS is still fighting the Character Encoding Wars of late last century. Their C*pyright fight with Gnu stalled out by freezing their Bash in the Oct/2006 Release Line at the Nov/2014 Bash 3.2.57. The bug fixes for this don't ship into macOS from Linux

Our Python bytes.decode Pipe Brick does just work. We don't freak over rare bytes so much as to deny service. We substitute ¤ 'Currency Symbol'

    % printf 'Just \xC0\x80 Bytes\n' |pb decode |sed 's/$/, not a Character/'
    Just ¤¤ Bytes, not a Character
    %

As you learn these corners, you may wish to go so far as to substitute macOS Homebrew Shell Pipes for your Apple macOS Shell Pipes. Until you do that, your macOS Shell Pipes will flame out at random times, because still fighting the Character Encoding Wars of late last century. We help with this, but we only solve it for you reliably if you put us into your every Shell Pipe


## 2.3 Take out the Trash

We call our Pb Decode for you when you ask for '|pb -', but just for what you show at the Terminal

When you do want to change what you're writing, and not only show what you're writing, then you do have to ask to change what you're writing

    % printf '\xC0\x80\n' |hexdump -C |column -t
    00000000  c0  80  0a  |...|
    00000003
    %

    % printf '\xC0\x80\n' |pb decode |hexdump -C |column -t
    00000000  c2  a4  c2  a4  0a  |.....|
    00000005
    %

    % printf '\xC0\x80\n' |pb decode
    ¤¤
    %


# 3 Count out all the things

We default to work with the Lines found between Line-Break's and the Line found at End-of-File, exactly as Python str.splitlines and Shell '|awk' do


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

    % ls -l |pb .len .max
    67
    %


# 4 Byte by Byte

Above, we've already spoken of ten Pipe Bricks (and their .max and .len variations)

    bytes casefold decode max len  lower split str title upper

For working with Bytes, we offer more Pipe Bricks


### 4.1 Md5 and Sha256

You can ask for the Shell 'md5sum', and you can ask it to include the Byte Length

    % cat /dev/null |pb md5
    d41d8cd98f00b204e9800998ecf8427e  -
    %

    % cat /dev/null |pb .md5
    d41d8cd98f00b204e9800998ecf8427e  0  -
    %

The merely classic Shell 'md5sum' and 'sha256sum' tools do too often mislead people by neglecting to mention Zeroed Byte Lengths. People come out wrongly feeling the Hash of Zero Bytes is indecipherable, while it's actually very well known. If you always ask for the Byte Length, then you don't have that problem

    % cat /dev/null |pb sha256
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
    %

    % cat /dev/null |pb .sha256
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 0  -
    %


### 4.2 Strings

You'll remember that Apple macOS still fighting the Character Encoding Wars of last century means they forward the Byte b"\xC0" as if it were printable

Ayup. This is a problem not only for their '|cat -tv' but also for their '|strings'. Oops

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

You can call on us in place of Apple macOS, any time you regret their error as much as I do

    % cat $(which cat) |pb strings |head -3
    __PAGEZERO
    __TEXT
    __text
    %


# 5 Character by Character

Above, we've already spoken of thirteen Pipe Bricks (and their .max, .md5, .len, and .sha256 variations)

    bytes casefold decode max md5  len lower sha256 split str
    strings title upper

For working with Characters, we offer more Pipe Bricks


### 5.1 Columns

Right-align the Numeric Columns, and left-align the Text Columns, after splitting Columns by two or more Spaces, except also taking Numeric Columns ended by single Spaces

Try these

    ls -lAF -rt |pb eng columns

    du -s ~/Public/* |expand |pb eng columns

And try them again but without asking for 'columns'

    ls -lAF -rt |pb eng

    du -s ~/Public/* |expand |pb eng

You'll see. You get vertically aligned Columns when you ask for them, and you don't when you don't

We don't require you to remember if it is "columns" or "column". We let you say singular '|pb column' in place of plural 'pb columns', in homage of Shell '|column -t', which does split Columns but doesn't volunteer to right-align any of them

We don't engage with the unrelated Shell legacies of 'col' and 'colrm'


### 5.2 Eng

Replace numeric Int or Float Literals, much as if rewritten by Python f"{:.3g}

But truncate, never round up. Like don't talk of the next millisecond till after it arrives. And do conserve ink. Don't say 'e+0' to mean 'e'. Don't end with 'e0' nor '.0' nor '.' either, except in the obscure corner of saying '-0e0' to mean '-0e0'

**10.7e3 not 10747**

    % ls -lAF -rt |head -3
    total 152
    -rw-r--r--@  1 plavarre  staff    282 Feb  1 12:32 requirements.txt
    -rw-r--r--@  1 plavarre  staff  10747 Feb  3 09:40 README.md
    %
    % ls -lAF -rt |head -3 |pb eng
    total 152
    -rw-r--r--@  1 plavarre  staff    282 Feb  1 12:32 requirements.txt
    -rw-r--r--@  1 plavarre  staff  10.7e3 Feb  3 09:40 README.md
    %

**99e3 not 99088**

    % du -s ~/Public/* |expand |head -3
    99088   /Users/plavarre/Public/__pycache__
    8       /Users/plavarre/Public/0
    200     /Users/plavarre/Public/100k
    %
    % du -s ~/Public/* |expand |head -3 |pb eng
    99e3   /Users/plavarre/Public/__pycache__
    8       /Users/plavarre/Public/0
    200     /Users/plavarre/Public/100k
    %

    % echo -- 2.718 3.14159 6.283 42. -inf -0e0 0e0 +inf nan |pb eng split join
    --  2.71  3.14  6.28  42  -Inf  -0e0  0  Inf  NaN
    %


### 5.3 ExpandTabs

Python str.expandtabs

For working with Characters, we offer '|pb expandtabs'

    % echo Abc |cat -n |pb -
         1¤Abc
    % echo Abc |cat -n |pb expandtabs
         1  Abc
    %


### 5.4 Ord

Python str.ord

For working with Character Codes spoken as Decimal Int Literals, we offer '|pb ord'

    % echo Abc |cat -n |pb ord
    32
    32
    32
    32
    32
    49
    9
    65
    98
    99
    10
    %


### 5.5 Str

Python str

I want you to know up front to hold in mind as you learn, yes we do make all our work with Lines available to you for work with Characters

For example, after you learn how we help you work with Lines, then you can come back and tell us to show which Characters show up in a Source File in the order of their first occurrence

    % cat bin/litshell.py |pb decode str set |pb join --sep=''
    #!/usrbinev pytho3"ag:l.[-]VSEPTARBICKdwcf,mkx'?QM01q|F$O=+2LUj56DHWz8&_>9N()G%Y·Z*{}4^←↑→↓\;7¤~<@

And you can tell us to sort the Characters before deduplicating them

    % cat bin/litshell.py |pb decode str sort set |pb join --sep=''
     !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIKLMNOPQRSTUVWYZ[\]^_abcdefghijklmnopqrstuvwxyz{|}~¤·←↑→↓
    %


# 6 Line by Line

We've developed the most Bricks to work with Lines, in the way of Shell '|awk'

Here are twenty-six of them

    append counter dent enumerate frame  head if insert join lstrip
    max min printable removeprefix removesuffix  reverse rstrip set shuffle slice
    sort strip sum tail translate  unframe

And they come in variations

    .enumerate .frame .head .max .min  .reverse .sort .tail

The .enumerate variation defaults to --start=1. The .frame variation implicitly adds a '|pb rstrip' after itself. The .head and .tail variations fill the Screen Rows, not just taking 9 Rows. The .max and .min and .sort variations take the Lines as Float, not as Str. The .reverse variation reverses the Characters in each Line, not the Lines of the File


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


## 6.3 Cut

End each Line with " ..." or "..." before it wraps.

    % seq 99 |pb join cut
    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  ...
    %

You can spell out the Line Width in Screen Columns if you like

    % seq 99 |pb join cut -72
    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  ...
    % seq 99 |pb join cut -71
    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19 ...
    % seq 99 |pb join cut -70
    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  1...
    % 

We define '|pb .cut' to mean fill your Terminal Screen with as much of each Line as fits, don't chop it exactly just past the classic 72 Columns

Like to fit into 101-Column Terminal

    % seq 99 |bin/pb join .cut
    1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16  17  18  19  20  21  22  23  24  25  26  ...
    %

    % stty size
    40 101
    % 

Our Counting of Columns comes out far more accurately than classic Shell '|cut -c' when you've got Ansi Color in your Output, or Ansi Bold, and some such

    git log --oneline --decorate --color-moved -1 --color=always |cut -c1-72

    git log --oneline --decorate --color-moved -1 --color=always |pb .cut |cat -

    git log --oneline --decorate --color-moved --color=always |pb .head .cut | cat -


## 6.4 Dent

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


## 6.5 Enumerate

Python list[str].enumerate

    % ls -l |pb enumerate |tail -3 |column -t
    4  -rw-r--r--@  1   plavarre  staff  10746  Feb  1  12:12  README.md
    5  -rw-r--r--@  1   plavarre  staff  282    Feb  1  12:32  requirements.txt
    6  drwxr-xr-x   41  plavarre  staff  1312   Feb  1  12:55  sh
    %

Often we'll just say '|pb n' or '|pb nl' to mean '|pb enumerate'

We define '|pb enumerate' and '|pb nl' to default to ' --start=0'. We define '|pb .enumerate' and '|pb .nl' and '|pb n' to default to ' --start=1'. We don't define a '|pb .n'


## 6.6 Frame

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

We define '|pb .frame' to mean '|pb frame' but also str.rstrip each Line out

Often we'll just say '|pb O' to mean Pb Frame in its four dimensions, and '|pb o' to mean Pb Unframe

See also Pb Dent and Pb Unframe


## 6.7 Head

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


## 6.8 If

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


## 6.9 Insert

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


## 6.10 Join

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


## 6.11 LStrip

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


## 6.12 Max

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

We give you list[str].max by default, but you can say '|pb .max' to mean '|pb float.max'

See also Pb Min, Pb Sort, and Pb Sum


## 6.13 Min

Python list[str].max, or Python list[float].max, or Python list[int].max

    % echo 3 14 15 9 |pb split min
    14
    %

    % echo 3 14 15 9 |pb split float.min
    3
    %

We give you list[str].min by default, but you can say '|pb .min' to mean '|pb float.min'

See also Pb Max, Pb Sort, and Pb Sum


## 6.14 Printable

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


## 6.15 RemovePrefix

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


## 6.16 RemoveSuffix

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


## 6.17 Reverse

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

We define '|pb .reverse' to work like Shell '|rev', for when you want the Characters in each Line reversed, rather than the Lines of the File

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

And we do let you say past-tense '|pb reversed' in place of imperative-tense 'pb reverse', in homage of 'list(reversed(list[str]))'. And we do let you say '|pb rev' to mean '|pb .reverse', in the Shell tradition

See also Pb Shuffle, and Pb Sort


## 6.18 RStrip

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


## 6.19 Set

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


## 6.20 Shuffle

Python random.shuffle(list[str])

    seq 6 |pb shuffle head -1

Try it, you'll like it. It's the pseudo-random roll of one 6-face die

See also Pb Sort


## 6.21 Slice

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

    % ls -l |pb awk -1
    40
    bin
    docs
    Makefile
    README.md
    requirements.txt
    sh
    %

    % ls -l |pb awk 6 7 8
    Feb  2  11:56
    Feb  1  17:12
    Jan  25  18:51
    Feb  1  12:12
    Feb  1  12:32
    Feb  2  11:57
    %

Often we'll just say '|pb a' to mean '|pb .slice -1'

Comparable to the most basic deployments of Shell '|awk'


## 6.22 Sort

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

We give you list[str].sort by default, but you can say '|pb .sort' to mean '|pb float.sort'

And we do let you say past-tense '|pb sorted' in place of imperative-tense 'pb sort', in homage of 'list(sorted(list[str]))'

See also Pb Max, Pn Reverse, Pb Shuffle, and Pb Sum


## 6.23 Strip

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


## 6.24 Sum

list[float].sum or list[int].sum

    % (echo 1 2 3; echo 4 5 6)
    1 2 3
    4 5 6
    %
    % (echo 1 2 3; echo 4 5 6) |pb sum
    5 7 9
    %

See also Pb Max, Pb Min, and Pb Sort


## 6.25 Tail

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


## 6.26 Translate

Not yet Spec'd out and implemented

Calls Python str.maketrans once and then Python str.translate on the Characters

Comparable to the most basic deployments of Shell '|tr' and '|tr -c' and '|tr -d'


## 6.27 Unframe

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

Technically speaking, the work of Pb Frame can be done Line by Line, but the work of Pb Unframe has to wait for the whole File to arrive, so it can know how many Columns are Blank on the Left. Because this is a detail of the Undo, and not part of the Do, I figure our Doc comes across most clear if we gloss over this point, as we have


# 7 File by File


# 7.1 Json Files

Many macOS and Linux understand between one and three of

    echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |python3 -m json.tool

    echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |python3 -m json

    echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |jq .

We give you the uncolored experience like that, via Python json.loads/ json.dumps, at

    echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |pb jq .

But we also offer

    echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |pb j

Call us like that and you see the nests go flat

    import json

    j = dict()
    j["alfa"] = 11
    j["bravo"] = dict()
    j["bravo"]["charlie"] = 33
    j["bravo"]["delta"] = 44

    print(json.dumps(j))  # from |pb .jq

You can say '|pb .jq' or 'pb j' to get this to come out

You can run this output as Python to get back to where you started

    % echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |pb j |python3
    {"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}
    %

You can grep this output to see what you've got, surfacing the exact path of keys that picks out the values you care about

    % echo '{"alfa": 11, "bravo": {"charlie": 33, "delta": 44}}' |pb j |grep -ai -e BRAVO
    j["bravo"] = dict()
    j["bravo"]["charlie"] = 33
    j["bravo"]["delta"] = 44
    %


# 8 Shell Aliases for Pipe Bricks


## 8.1 Inside the Pipe

We often let you type a familiar Shell Word in place of our Python Word

| Shell | PyLitFun |
| ----- | -------- |
| awk | .slice |
| chars | str |
| data | bytes |
| expand | expandtabs |
| head | head |
| jq | jq |
| lines | splitlines |
| md5sum | md5 |
| nl | enumerate |
| rev | .reverse |
| sha256sum | sha256 |
| shuf | shuffle |
| tac | reverse |
| tail | tail |
| text | str |
| words | split |

Our jq, head, md5sum, nl, sha256sum, & tail come in also as dot variations: .jq, .head, .md5sum, .nl, .sha256sum, & .tail

Our jq and .jq are minimal, nothing like as ambitious as the real '|jq' that is more than its '|jq .'

We could emulate the '|uniq' and '|uniq -c' of Shell, and we don't. Those two come with their bizarre small-machine limitation of needing sorted input. For now, with us, you have to find your way to calling for '|pb counter' or '|pb set', much more in the way of "|awk '!d[$0]++'"


## 8.2 Outside the Pipe

Adopt our 'bin/pb' and you get most of what we discuss in this doc, but if you tire of typing 'pb 0' to mean 0 then you can also adopt our bin/0, bin/1, bin/2, and bin/3 as we've shown

For ourselves we also post many more intensely cryptic abbreviations to become everyday things in like daily use

In our Sh Folder

| Shell Script | Meaning |
| ------------ | ------- |
| sh/.awk | Pick out the last Column when it's not empty |
| sh/.bash | Bash but without Profile |
| sh/.cat | Cat but as 'echo Press ⌃D to continue' && cat - >/dev/null |
| sh/.cp | Copy with 1 Pos Arg = Make a backup copy of a File or Folder and put a date-time stamp on it |
| sh/.cut | Cut to Screen |
| sh/.cv | Same as sh/.pb, but collides with other people's 'cv' rather than their 'pb' |
| sh/.echo | Print an unambiguous Python Repr of the Sys ArgV |
| sh/.emacs | Emacs but without Profile |
| sh/.exit.sh | Shell Source for .exit to mean show the Shell's $? Process Exit Status Return Code |
| sh/.head | Head but fill Screen |
| sh/.ls | ls -hlAF -rt --full-time -d except also at macOS and -d only for multiple Args |
| sh/.mv | Rename with 1 Pos Arg = Put a date-time stamp on an original File or Folder so that it looks deleted |
| sh/.od | Come close to '|hexdump -C' when that's not available |
| sh/.pb | Pb but without Args and without its implicit Unframes |
| sh/.ps | Call Ps to disclose which Shell is calling Ps |
| sh/.screen | Celebrate 'screen -rr' and probably do nothing else as helpful |
| sh/.sed | Convert a Git 'Changes to be committed' into Commit Message Lines |
| sh/.sh | Sh but without Profile |
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


## 8.3 Built most quickly

When you like, we do let you type just one Memorable Letter to stand for a whole Pipe Brick

For example, a search of Shell Input History can look like

    cat ~/.*.log |pb decode r set r |.cut |grep -ai -e CP -e MV |grep -ai F=

In there, each of the two ' r ' stand for a '|pb reverse' Pipe Brick

Memorable Lowercase Letters

| Letter | Brick |
| ------ | ----- |
| a | awk |
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

The pun with 'First Lady of the United States (FLOTUS)' does amuse me, but I've not found a convincing case for defining '|pb S' to mean anything in particular. We do define '|pb .sort' to mean the Float Sort not the Str Sort, in contrast with '|pb s' to mean the Str Sort of the default Locale


# 9 Future work


## 9.1 Please tell your friends

The bots feel this is written for you if ...


**You are an intermediate to advanced Terminal Shell command-line user**

+ You already use shell pipes regularly (assumes knowledge of tr, sed, awk, grep, etc.)
+ You know Python basics (methods like str.upper, list.append, and more of the ~150 Python builtins)
+ You work primarily like on a macOS Macbook (pbpaste/pbcopy to reach the Paste Buffer, and dealing with BSD-specific issues)
+ You appreciate Unix philosophy but want modern conveniences

Does this sound like a friend of yours? Please tell them about us

Does this sound like you? Please stick around, and make time to come say hi


## 9.2 Their Testimonials

"Love an artist/programmer/person's website where they matter-of-factly share some process/subject exploration in great detail, written from scratch" ~ Feb/2026 <!-- https://twitter.com/nbhdlady/status/2018683247157260551 -->


## 9.3 Your Input Errors

We've focused first on bringing up what should work

Presently you can toss extra input into your Shell Command Lines near us, and receive no pushback to tell you that you placed it wrong

    % echo hello |sh/.pb 1 2 3
    %

    % bin/pb 4 5 6
    hello
    %

That's not nice. We can do better


## 9.4 Parallel Processing

A classic Shell Pipe Filter can write output before and while it receives input

By contrast, most of our Pipe Bricks wait for end-of-file. They wait to copy the whole Input into Process Memory before working on it, like a Shell '| sponge' Pipe Filter

A few of our Pipe Bricks must wait for end-of-file:  counter, join, len, max, md5, min, reverse, set, sha256, sort, sum

The rest could learn to run in parallel with one another, so as to give you your first output sooner, and occupy less Process Memory


# 10 Links

- [GitHub Repository](https://github.com/pelavarre/pylitfun)
- [Questions/ Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre+%23PyLitFun)


<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/pipe-bricks.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
