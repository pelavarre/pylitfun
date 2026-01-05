<!-- omit in toc -->
# terminal-lies

Two dozen lies that too many Terminal Programs tell themselves

- [1. About Input Bytes read from the Terminal Touch/ Tap/ Key-Strike](#1-about-input-bytes-read-from-the-terminal-touch-tap-key-strike)
  - [You can know which Key Chords will send each of the 128 US Ascii Bytes (Lie 1.1)](#you-can-know-which-key-chords-will-send-each-of-the-128-us-ascii-bytes-lie-11)
  - [Each different Key Chord sends different Bytes (Lie 1.2)](#each-different-key-chord-sends-different-bytes-lie-12)
  - [Key Chords send the same Bytes through your Terminal and mine (Lie 1.3)](#key-chords-send-the-same-bytes-through-your-terminal-and-mine-lie-13)
  - [You can know which Sets of Key Chords send the same Bytes (Lie 1.4)](#you-can-know-which-sets-of-key-chords-send-the-same-bytes-lie-14)
  - [You can know when the Bytes of one Key Chord end before the start of the next (Lie 1.5)](#you-can-know-when-the-bytes-of-one-key-chord-end-before-the-start-of-the-next-lie-15)
  - [You can't know when the Bytes of one Key Chord end before the start of the next (Lie 1.6)](#you-cant-know-when-the-bytes-of-one-key-chord-end-before-the-start-of-the-next-lie-16)
  - [Key Chords send the same Character through your App and mine (Lie 1.7)](#key-chords-send-the-same-character-through-your-app-and-mine-lie-17)
  - [You can know which Key Chords send any Bytes at all (Lie 1.8)](#you-can-know-which-key-chords-send-any-bytes-at-all-lie-18)
  - [Similar Key Chords work similarly at your Terminal App (Lie 1.9)](#similar-key-chords-work-similarly-at-your-terminal-app-lie-19)
  - [The Bytes sent by striking some Key Chords always come again only from striking Key Chords (Lie 1.10)](#the-bytes-sent-by-striking-some-key-chords-always-come-again-only-from-striking-key-chords-lie-110)
  - [That Key Chord that worked for you yesterday will work today too (Lie 1.11)](#that-key-chord-that-worked-for-you-yesterday-will-work-today-too-lie-111)
- [2. About Output Bytes written to the Terminal Screen](#2-about-output-bytes-written-to-the-terminal-screen)
  - [Every Character looks a little different when printed (Lie 2.1)](#every-character-looks-a-little-different-when-printed-lie-21)
  - [Every Character can be encoded as a UTF-8 SurrogateEscape Byte Sequence (Lie 2.2)](#every-character-can-be-encoded-as-a-utf-8-surrogateescape-byte-sequence-lie-22)
  - [Every well-loved Character has one distinct Python UnicodeData Name (Lie 2.3)](#every-well-loved-character-has-one-distinct-python-unicodedata-name-lie-23)
  - [Printing a double-wide Character moves the Terminal Cursor by two Columns (Lie 2.4)](#printing-a-double-wide-character-moves-the-terminal-cursor-by-two-columns-lie-24)
  - [Printing an Escape Sequence won't close all your Terminal Tabs (Lie 2.5)](#printing-an-escape-sequence-wont-close-all-your-terminal-tabs-lie-25)
- [3. About Terminal Feature Discovery \& Negotiation](#3-about-terminal-feature-discovery--negotiation)
  - [Every Terminal reports if it's a Darkmode Terminal or a Lightmode Terminal (Lie 3.1)](#every-terminal-reports-if-its-a-darkmode-terminal-or-a-lightmode-terminal-lie-31)
  - [Python "import pty" doesn't change the Colors negotiated by Vim (Lie 3.2)](#python-import-pty-doesnt-change-the-colors-negotiated-by-vim-lie-32)
  - [Escape Sequences can tell a Terminal Cursor to step towards the 8 Points of the Compass (Lie 3.3)](#escape-sequences-can-tell-a-terminal-cursor-to-step-towards-the-8-points-of-the-compass-lie-33)
  - [Preplanning put the related Characters together in Unicode (Lie 3.4)](#preplanning-put-the-related-characters-together-in-unicode-lie-34)
- [4. About copying and pasting Characters between the Terminal and Apps](#4-about-copying-and-pasting-characters-between-the-terminal-and-apps)
  - [You can copy in what you please (Lie 4.1)](#you-can-copy-in-what-you-please-lie-41)
  - [You can copy out what you please (Lie 4.2)](#you-can-copy-out-what-you-please-lie-42)
  - [The Emacs Key Chords you learn at the Terminal do or don't work elsewhere (Lie 4.3)](#the-emacs-key-chords-you-learn-at-the-terminal-do-or-dont-work-elsewhere-lie-43)
  - [You can print the Glyphs you printed in 1980 (Lie 4.4)](#you-can-print-the-glyphs-you-printed-in-1980-lie-44)
  - [Two people can agree on how to spell out a Keyboard Chord Sequence (Lie 4.5)](#two-people-can-agree-on-how-to-spell-out-a-keyboard-chord-sequence-lie-45)

As posted by Pat LaVarre & friends, Jan/2026


## 1. About Input Bytes read from the Terminal Touch/ Tap/ Key-Strike

### You can know which Key Chords will send each of the 128 US Ascii Bytes (Lie 1.1)

If you try enough variations, you do get there, but at every different Terminal App you need its variations

The 95 Printable US Ascii Bytes are no problem

    cat - >/dev/null
        # strike the Spacebar by itself
        # strike ⇧! ⇧" ⇧# ⇧$ ⇧% ⇧& ' ⇧( ⇧) ⇧* ⇧+ , - . /
        # strike 0 through 9 and ⇧: ; ⇧< = ⇧> ⇧?
        # strike ⇧@ and ⇧A through ⇧Z and [ \ ] ⇧^ ⇧_
        # strike ` and A through Z and ⇧{ ⇧| ⇧} ⇧~

It's the Control Bytes that trouble you. To find those, you can try a broad survey of possible solutions

        # strike ⌃ Spacebar and ⌃A and ⌃B through ⌃Z and ⌃[ ⌃] ⌃\ ⌃⇧^ ⌃⇧_
        # strike ⇥ as well as ⌃I, strike ⏎ as well as ⌃M
        # strike ⌫ as well as ⌃⇧?

macOS and Linux, same today as last century, will echo ^? to speak of \177 inside of `stty erase undef && cat - >/dev/null'. All the same, Terminal life is not so simple now as to say you can press ⌃⇧? to send \177

a ) The Apple macOS Terminal rejects the classic ⌃⇧? and ⌃/ for \177, so there instead you must strike its ⌫ Delete Key

b ) The macOS iTerm2 does accept the classic ⌃⇧? or the macOS ⌫ for \177 but its ⌃/ is something else

c ) The Ghostty sends something else for ⌃I and ⌃M, so there instead you must learn to strike its ⇥ Tab and ⏎ Return Keys. And its ⌃⇧? and ⌃/ both don't mean \177, so there instead you must strike its ⌫ Delete Key, same as an Apple macOS Terminal

d ) The Google Cloud Shell takes away ⌃B, you have to strike it twice. And its ⌃M never works, you must strike its ⏎ Return Key. And whether its ⇥ Tab Key works is what its ⌃M toggles on and off. So when it's toggled off, there you must strike its ⌃I instead. And its ⌃⇧? and ⌃/ send no Codes, and its ⌃/ beeps. Its ⌃[ does work as well as its Esc Key, but they're both weirdly slow, like always at least 500ms per Key Strike

### Each different Key Chord sends different Bytes (Lie 1.2)

    cat - >/dev/null
        # strike Esc
        # strike ⇧ Esc
            # see the same ^[ from both

### Key Chords send the same Bytes through your Terminal and mine (Lie 1.3)

    cat - >/dev/null
        # strike ⌥←
            # see ^[b at Apple macOS Terminal
            # see ^[[1;3D at macOS iTerm2
        # strike ⌥I P
            # see ˆp at Apple macOS Terminal and at macOS iTerm2
            # see ^[i p at macOS Ghostty
            # see ˆˆ at Google Cloud Shell in macOS Apple Safari
            # see ˆp at Google Cloud Shell in macOS Google Chrome

Google Cloud Shell eventually distributed consistency across Apple Safari and Google Chrome. But we know they couldn't do simultaneous consistent delivery back then. So maybe they still can't today. We can't know more without paying for more test

### You can know which Sets of Key Chords send the same Bytes (Lie 1.4)

    cat - >/dev/null
        # strike ↓
        # strike ⇧↓
            # see ^[B twice at Apple macOS Terminal, same same
            # see ^[B from ↓ and ^[[1;2B from ⇧↓ at macOS iTerm2
            # see no bytes sent by Google Cloud Shell

### You can know when the Bytes of one Key Chord end before the start of the next (Lie 1.5)

    cat - >/dev/null
        # strike Esc
        # strike ←
            # see ^[ said for Esc
            # see ^[[D said for ←, starts with same Byte

Similarly, striking ⌥⇧O to mean ⎋⇧O comes across as ^[O as a whole Key Chord struck when you test the Settings > Keyboard > Use Option As Meta Key mode of an Apple macOS Terminal. But Fn F1 is ^[OP. Were you done after the ^[O part? You cannot know, until after you learn how to ask

### You can't know when the Bytes of one Key Chord end before the start of the next (Lie 1.6)

    sleep 1 && printf '\033[5n' && cat - >/dev/null
        # strike Esc during the Sleep
        # see the ^[[0n from the ^[[5n arrives after the Esc, showing the end of its Bytes

Ta da, you can learn to ask if the Key Chord has ended. This technique works pretty well, but still gets wrong the astonishingly slow ⌥⎋ corner of Google Cloud Shell wrong, also known as ⎋⎋. And still gets wrong the Intercardinal Arrows, wrongly splitting ↖ ↗ ↘ ↙ into ↑← ↑→ ↓→ ↓←

### Key Chords send the same Character through your App and mine (Lie 1.7)

    cat - >/dev/null
        # strike ⌥ Y
            # See ¥ inside most macOS Apps
            # See \ inside the Terminal, in homage to Japanese Tech of the past century

Similarly, ⌃⌥⇧ B means ⌥⇧← inside a macOS Notepad, but beeps inside a macOS Terminal. Apps disagree

### You can know which Key Chords send any Bytes at all (Lie 1.8)

    cat - >/dev/null
        # strike ⇧F1
            # see ^[[1;2P at macOS Ghostty or iTerm2
            # see nothing at Apple macOS Terminal (but hear an audible Bel or see a visual Bel)

Apple macOS Terminal has many pages of Settings. You can intervene separately at each macBook and ask for ⇧F1 to work. But this Key Chord, like many Key Chords, don't work by default

### Similar Key Chords work similarly at your Terminal App (Lie 1.9)

After you test Z, you still must test A, B, C, F, I, and M, or you'll miss corners that I've found. These are corners found just in the puzzle of which Key Chords sends which Bytes, quite apart from what those Bytes do when they arrive, like how sharply your Shell distinguishes C, D, T, Z, and \

The ` and ⇧~ and marks in the upper left often work differently than the rest, ditto the ⇧@ and ⇧^ and ⇧_ across the top Row

F1, F3, F7, F8, and F11 have surprised me by working differently than the other Fn Keys, and often F2 and F4 go with F1

I'm curious to learn if Ghostty people mean for their ⌃⇧@ and the three ⌃⇧{ ⌃⇧} ⌃⇧| to work so differently, mixing Shifts Index 5 in with their usual choice of Shifts Index 6 for encoding ⌃⇧ Key Chords. Similarly, do they really mean for their ⎋⌃⇧{ ⎋⌃⇧} ⎋⌃⇧| to mix Shifts Index 7 in with their usual choice of Shifts Index 8 for encoding ⎋⌃⇧ Key Chords. How can we ever know? The Internet is so large

### The Bytes sent by striking some Key Chords always come again only from striking Key Chords (Lie 1.10)

Actually, the people choosing standards for Screen Bytes and Keyboard Bytes don't quite always avoid stepping on each other

macOS iTerm2 defines ⎋[1;2⇧R to mean ⇧F3 struck. To work well there, your Tui App inside your Terminal has to guess well when ⎋[1;2⇧R does mean a strike of ⇧F3 and when it means a Cursor-Position-Report (CPR) of Y=1 X=1. macOS Ghostty gives up on Tui App ahead of time, and sends ⎋[13;2⇧~ instead to mean a strike of ⇧F3

Also Paste can send one or more arbitrary Bytes to a Terminal. Except that some Terminals block some forms of Paste, like macOS iTerm2 blocks 010 ⌃H while allowing 177 ⌫

And the people choosing standards for Mouse Bytes and Keyboard Bytes don't quite always avoid stepping on each other

Similarly, ⎋[⇧M can come from a strike of the ⌥⇧M Key or from a Mouse Press/ Release. When it comes from the Mouse Press/ Release then it's not complete in itself, it sends another three Bytes

### That Key Chord that worked for you yesterday will work today too (Lie 1.11)

This can be true in places, but . . .

We got settings

At the Apple macOS Terminal, you can toggle its Settings > Keyboard > Use Option As Meta Key back and forth. And then you get more distinct Key Chords in this special mode. You get ⎋ ⎋ and ⎋⌫ and ⎋ ⏎ apart from ⏎ and ⌫ and ⎋. You get quick complete ⎋\` ⎋E ⎋I ⎋N ⎋U because you gave up the Key Chords coded as accented vowels at ⎋\` E and ⎋E E and ⎋I I and ⎋N N and ⎋U U and so on. But then when you toggle this Setting back, you lose all these new Key Chords

At the Google Cloud Shell, they churn their rules from time to time. Lately, their ⌃M is a toggle between having the ⇥ Tab Key mean ⌃I or some Browser Thing. Their ⌃M also toggle the ⇧⇥ Shift Tab Key Chord between meaning ⎋[Z and some Browser Thing. And they break the classic equivalence between ⌃M and ⏎ Return: you get different effects at each. And ditto they give you different effects at ⌃I and at ⇥ Tab. And I saw their encoding of ⌥I P changing by browser. And they do offer a ⛭ > Keyboard > Alt Is Meta toggle, but I can't see that it ever does much

At the Google Cloud Shell, you can't depend on ⌃C meaning anything. Sometimes, you can pound away on ⌃C to no response. With us, we'll likely take ⌃\ or ⌃Z to mean some kind of quit, even while they're blocking ⌃C

And don't go thinking that having ⎋⎋ ⎋` ⎋E ⎋I ⎋N ⎋U means you have ⎋← ⎋↑ ⎋→ ⎋↓. At the Apple macOS Terminal you still then have only ⎋← and ⎋→ and ⇧← and ⇧→ as distinct from ← ↑ → ↓ across all combinations of the ⌃ ⌥ ⇧ shifting Keys. That's why we'll often take ⎋← and ⎋→ to mean ⎋↑ and ⎋↓ in place of themselves

Google Cloud Shell often pops up complaints about this whole mess, in particular

> Is your browser intercepting key combinations? Install Cloud Shell as a PWA for a better experience

> The tab key is being redirected to the terminal. Press ctrl+m to enable page navigation with the tab key

## 2. About Output Bytes written to the Terminal Screen

### Every Character looks a little different when printed (Lie 2.1)

    printf '_\040_ U+0020 Space\n'
    printf '_\302\240_ U+00A0 No-Break Space\n'
    printf '_\343\200\200_ U+3000 Ideographic Space\n'

    cat - >/dev/null
        # strike Spacebar
        # strike ⌥ Spacebar

This demo runs happy across the Apple macOS Terminal, macOS iTerm2, and Google Cloud Shell. Ghostty sends Esc Spacebar in place of ⌥ Spacebar, so then the PrintF Demo still works but the Cat demo doesn't

A treacherously similar, rather than exactly identical, collection of glyphs is ^ ` ´ ˜ ¨ ' " ⌃. All but one of these show up on the Apple macOS Terminal Keyboards. But living people don't so very reliably distinguish them, the one from the next

### Every Character can be encoded as a UTF-8 SurrogateEscape Byte Sequence (Lie 2.2)

Yes you can decode and then encode any Byte Sequence

    >>> b"\xc0\x80".decode(errors="SurrogateEscape".lower())
    '\udcc0\udc80'
    >>>
    >>> "\udcc0\udc80".encode(errors="SurrogateEscape".lower())
    b'\xc0\x80'
    >>>

No you can't encode any Character Sequence

    >>> "\ud800".encode(errors="SurrogateEscape".lower())
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' in position 0: surrogates not allowed
    >>>

### Every well-loved Character has one distinct Python UnicodeData Name (Lie 2.3)

python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("EOM"))))'
python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("End Of Medium"))))'
    # they both say 0x19

python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("NBSP"))))'
python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("No-Break Space"))))'
    # they both say 0xA0

python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("Null"))))'
python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("Line Feed"))))'
python3 -c 'import unicodedata; print(unicodedata.name("\000").title())'
python3 -c 'import unicodedata; print(unicodedata.name("\012").title())'
    # they let you lookup 0x00 and 0x0A, but then they don't let you name those
    # they say ValueError for U+0000 Null
    # they say ValueError for U+000A Line Feed

Some well-loved Characters have two or more names. Some well-loved Characters have no name you can find

### Printing a double-wide Character moves the Terminal Cursor by two Columns (Lie 2.4)

This does work in some Terminals. But at a Google Cloud Shell you have to blank out the East Column yourself, and you have to move the Cursor across the East Column yourself

The need as shown by Shell PrintF

    printf '\xF0\x9F\x9F\xA1' && printf '\xF0\x9F\x9F\xA1' && printf '\033[6n' && printf '\x0A' && cat - >/dev/null

    printf 'AlfaBravo''\r''\xF0\x9F\x8F\x86''\033[C''\033[K''\n'

The need and some of the fix as shown by Python

    python3 -i -c '''

    import unicodedata

    o = unicodedata.lookup("Large Orange Circle")
    y = unicodedata.lookup("Large Yellow Circle")
    print(o + "\033[C" + y)  # orange and then yellow, separately

    print(o + y)  # yellow over east half of orange
    print(y + o)  # orange over east half of yellow

    print(" " + o + "\r" + y)  # yellow beneath west half of orange
    print(" " + y + "\r" + o)  # orange beneath west half of yellow

    '''

### Printing an Escape Sequence won't close all your Terminal Tabs (Lie 2.5)

Unlock your Google Cloud Shell. Visit https://shell.cloud.google.com/?show=terminal with your gMail Username & Password. Feel free to ignore their many many upsells: you can always choose Reject. Indeed, even if you slip and fail to choose Reject, then they still give you a second chance to choose Reject after all

Then try

    printf '\033]12;#''ff0000\007' && sleep 1 && printf '\033]112\007'

Watch it close all your Terminal Tabs out there. Oops


## 3. About Terminal Feature Discovery & Negotiation

### Every Terminal reports if it's a Darkmode Terminal or a Lightmode Terminal (Lie 3.1)

Apple macOS Terminal & macOS iTerm2 & macOS Ghostty, yes

Google Cloud Shell, no

Try the Osc 11 Query of a 16-bit R G B encoding of the default Backlight behind foreground Color

    % printf '\033[5n''\033]11;?\007' && cat - >/dev/null
    ^[[0n^[]11;rgb:2020/2020/2020^G

That's what it looks like when it works. When it doesn't work, it silently ignores the Osc 11

    % printf '\033[5n''\033]11;?\007' && cat - >/dev/null
    ^[[0n

### Python "import pty" doesn't change the Colors negotiated by Vim (Lie 3.2)

Last time I checked, the orange went missing, even when you worked to keep the $TERM setting intact

### Escape Sequences can tell a Terminal Cursor to step towards the 8 Points of the Compass (Lie 3.3)

Aye, North & South & East & West do work

    Write ⎋[⇧A to move ↑ North
    Write ⎋[⇧B to move ↓ South
    Write ⎋[⇧C to move → East
    Write ⎋[⇧D to move ← West

But the standards say Northwest, Northeast, Southeast, Southwest are unspeakable ideas. Whereas we say

    Write ⎋[↖ to move ↖ Northwest, as if ↑ ← ←
    Write ⎋[↗ to move ↗ Northeast, as if ↑ → →
    Write ⎋[↘ to move ↘ Southeast, as if ↓ → →
    Write ⎋[↙ to move ↙ Southwest, as if ↓ ← ←

### Preplanning put the related Characters together in Unicode (Lie 3.4)

Yes you will see clusters

You can find 0123456789 and ABCDEFGHIJKLMNOPQRSTUVWXYZ and abcdefghijklmnopqrstuvwxyz, because of how slowly and carefully the US Ascii standard came together in the 1960's. But even their cluster of !"#$%&'()*+,-./ isn't the !@#$%^&*() across the top of your macBook 0123456789 digits. And out beyond the 7-bits, the clusters don't even happen

But you will find the 9 Comic Colors of Unicode jumbled, ordered like this

    ⚪ ⚫
    ⬛ ⬜

    🔴 🔵 🟠 🟡 🟢 🟣 🟤
    🟥 🟦 🟧 🟨 🟩 🟪 🟫

And the names of the Circles and Squares that look alike come out jumbled. We show youv "Medium White Circle" and "Medium Black Circle" in here, together with all the rest named as "Large".

And Apple promotes having Keyboard Shortcut docs order the mentions of ⎋ ⌃ ⌥ ⇧ ⌘ as such, but those show up jumbled in Unicode, and not all together

    ← ↑ → ↓
    ↖ ↗ ↘ ↙
    ⇥ ⇧ ⋮ ⌃ ⌘ ⌥ ⌫ ⎋ ⏎ ☰

## 4. About copying and pasting Characters between the Terminal and Apps

### You can copy in what you please (Lie 4.1)

Try pasting in a U+0008 Backspace

    printf '\010' |pbcopy && cat - >/dev/null
    printf '\177' |pbcopy && cat - >/dev/null

At Apple macOS Terminal, this pops up a dialog to yell at you
> Paste control characters? <br>
> The text contains control characters which could allow the pasted content to perform arbitrary commands. <br>
> To confirm and Paste, you can use ⇧ ⌘ ⏎ <br>
> &lt;Paste&gt; &lt;Paste without Control Characters&gt; &lt;Cancel&gt;

At macOS iTerm2, the 010 just rings the Bell, and doesn't work, but the 177 works

At macOS Ghostty and at Google Cloud Shell, the 177 just works and the 010 pastes a visible echo of ^ H as if you had pressed ⌃H

### You can copy out what you please (Lie 4.2)

The world outside shoves in on your choice of what to paste out. Some parts of it works better than other parts, depending on where you go

Putting U+0009 Tab into the text can matter. Like you can get Slack to paste Tsv. You can also paste as Tsv into ⇧ ⌘ V at Google's sheets.new > Edit > Paste Special > Values Only

    printf 'Alfa\tBravo\tCharlie\n''A1\tB1\tC1\n''A2\tB2\tC2\n' |pbcopy

Putting Backlights and Colors into the text can matter. Like you can get a Google docs.new to show Colors and Bold and Indents

    % printf '    ''\033[31m''\033[103m''31 on 103\n'
        31 on 103
    %

Google sheets.new forces you to choose between Indents or Colors and Bold, so far as I can tell

Slack doesn't do Colors on Text generally, but Slack does understand monospacing the 9 Comic Colors of Unicode. Odds on your Markdown Viewer feels this figure is assymetric, not a regular square. If that's so, then your Markdown Viewer is wrong, and Slack Monospace will correctly show you how wrong your Markdown Viewer is, if you ask

          ⚪⚪⚪⚪⚪
          ⚪🔴🔴🔴⚪
      ⚪⚪⚪⚪⚪⚪⚪⚪⚪
      ⚪🔴⚪⚪⚪⚪⚪🔴⚪
      ⚪🔴⚪⚪⚪⚪⚪🔴⚪
      ⚪🔴⚪⚪⚪⚪⚪🔴⚪
      ⚪⚪⚪⚪⚪⚪⚪⚪⚪
          ⚪🔴🔴🔴⚪
          ⚪⚪⚪⚪⚪

### The Emacs Key Chords you learn at the Terminal do or don't work elsewhere (Lie 4.3)

In reality, they don't simply all work, and they don't simply all not work

Lots of macOS understands ⌃A ⌃B ⌃D ⌃E ⌃F ⌃K ⌃N ⌃O ⌃P ⌃T ⌃Y in the way of Emacs, though their ⌃H and ⌥⌫ depart from Emacs tradition. As for ⌃W and ⌃U and ⌃⇧@ should mean, well, Emacs & Shell never have agreed over what those should mean

The Apple macOS Terminal doesn't let you distinguish ⌥⌫ from ⌫, but does pretty natively understand ⎋B and ⎋F, which Emacs ⌃H K docs as M-b 'backward-word' and M-f 'forward-word'

You can get some variations of Emacs ⎋Z and ⎋⇧Z to work in places like macOS Zsh, which gives you a bit and not much of what Vim does with D T and D F. Emacs speaks of 'zap-to-char' and 'zap-up-to-char', with ⎋Z traditionally doing the work of Vim D F I, but Zsh ⎋Z can more easily be told to do D T

### You can print the Glyphs you printed in 1980 (Lie 4.4)

Wikipedia [ATASCII](https://en.wikipedia.org/wiki/ATASCII), meaning Atari® Ascii, has tried to find similar Glyphs inside Unicode, and they're not all plainly found.

Back in the days of the Atari 800, the Byte Codes 0x80 through 0xFF printed as the reverse video of Byte Codes 0x00 through 0x7F, and only 0x20 was blank. 0xA0 was a reversed blank

Reverse-video at my Terminal copies into Google http://docs.new no problem, aye, but it lands wrong in Google http://sheets.new/ and it lands wrong in Slack

I felt so very disappointed when first I saw the IBM PC choose to render 0x00 and 0x20 and 0xFF as all the very same blank glyph. Like, you know, "you had just the one job". You could have done it well

See also
+ a screenshot of [Atari®](https://en.wikipedia.org/wiki/ATASCII#/media/File:Atascii-character-set-00toFF-2x.gif)
+ a screenshot of [IBM PC](https://en.wikipedia.org/wiki/Code_page_437#/media/File:Codepage-437.png)

### Two people can agree on how to spell out a Keyboard Chord Sequence (Lie 4.5)

Eleven points of disagreement

a ) The real life Key Caps of a macBook speak of upper case US Ascii and then esc, delete, tab, · caps lock, return, shift, fn 🌐, control ⌃, option ⌥, command ⌘, and the four cardinal arrows ← ↑ → ↓, without mentioning the intercardinal arrows ↖ ↗ ↘ ↙. Its Spacebar is large and rectangular and blank. Its upper right Key is small and squarish and blank

b ) Apple's Keyboard Viewer inside macOS speaks of:  esc, ⌫, ⇥, ⇪, ⏎, ⇧, fn, ⌃, ⌥, ⌘, but otherwise matches a macBook, except the upper right Key of the Keyboard Viewer looks lots like the ☰ Trigram For Heaven. We follow most of that convention, except we say ⎋ U+238B Broken Circle With Northwest Arrow to mean the Esc Key Cap (or the 033 Meta Encoding of the Alt Option Key Cap), and we say Fn to mean the fn Key Cap

c ) The classic 'stty echoctl' convention speaks of the first 33 (0o41) Control Characters as ^A through ^Z, and of ^@ ^[ ^\ ^] ^^ ^_ ^?. We come near to that convention. We first let the nerds snipe us into distinguishing U+2303 ⌃ Up Arrowhead , and then we decide ⇧ matters, so we end up talking of ⌃A through ⌃Z and of ⌃⇧@ ⌃[ ⌃\ ⌃] ⌃^ ⌃_ ⌃⇧?

d ) macOS Menus speak of ⎋ ⌃ ⌥ ⇧ ⌘ Fn in pretty much that exact order. We copy this convention likewise, often making a point of mentioning ⌃ before ⌥ before ⇧. But your Fingers and the Keyboard don't themselves decide if you struck ⎋ Meta or ⌥ Option Alt, that distinction comes from context

e ) We take the Space as a Separator, to mean the end of one Key Chord and the start of the next. So for an ordinary strike of the Spacebar we talk of ␢, but we say ⌃␢ or ⌃⇧@ to talk of holding down Control ⌃ while striking the Spacebar to send the \0 Key Code to talk of the U+0000 NUL Character. And we say ⌥␢ to talk of holding down Option ⌥ while striking the Spacebar to send the \302 \240 Key Codes to talk of the U+00A0 No-Break Space Character

f ) We can speak unambiguously and precisely of ⇧T A B Key Chord Sequence to mean 3 Keys struck, first Shift with the Letter Key T, then the Letter Key A without a Shift, then the Letter Key B without a Shift. Other conventions more struggle to distinguiush the 3 Chords of ⇧T A B from the single strike of the ⇥ Tab Key. They have similar troubles with all their named keys: their ⎋ Esc, ⌫ Delete, ⇥ Tab, & Return ⏎

g ) We give up the struggle to assign meaning to the lowercase letters a .. z. We speak of the A ... Z Key Caps and the ⇧A .. ⇧Z Key Chords. In particular we speak of ⎋[M and ⎋[⇧M where PrintF speaks of '\033[m' and '\033[M'. We speak of ⇧⇥ and ⎋[⇧Z where PrintF speaks of '\033[Z'. And so on. When reading what we write, its encoding is mostly unambiguous. But you have to struggle to know we mean PrintF '\033b' when we say ⎋B like an Emacs M-b, distinct from our ⎋[⇧B that would be an Emacs M-B

h ) We require further separators when you want to speak of &lt;F12&gt; and &lt;F11&gt; and &lt;F2&gt; and &lt;F1&gt; all together. Without extra Separators such as &lt;> we can still confuse &lt; F1 &gt; with &lt; F12 &gt; and confuse &lt; F1 &gt; with &lt; F11 &gt; and &lt; ⌥1 &gt; with &lt; ⌥1 ⌥2 ⌥3 &gt; and so on and on

h ) The thin single-wide monospace Fonts struggle to make a clear-at-a-glance distinction between our ^ and ⌃, and between our ⇪ and ⇧. Ouch

i ) People often disagree over whether to say Ctrl or Control, Esc or Escape, Del or Delete, Ret or Return, Opt or Alt or Option. People often want "Shift" to mean only exactly "⇧" and none of the rest of them, and spend three syllables to say "Modifier" to mean all of them. We go mostly with the symbols ⌃ ⎋ ⌫ ⏎ ⌥ ⇧, and we speak of all of them as the Shift Keys

j ) People often want to shove "+" Plus-Sign's into mentions of Key Chords, such as speaking of ⌃⌥⌫ as Control+Alt+Delete. We find this unhelpful

k ) Practically no one stands up for the Intercardinal Arrows ↖ ↗ ↘ ↙. On a macBook, those only work reliably enough for games. Lag in the computer can often suddenly break them into two, the ↖ into ← ↑ or into ↑ ←, the ↘ into → and ↓ or ↓ and →, and so on

<!--

todo: show when same Bytes have different meanings from Keyboard or to Screen

todo: show when Screen Bytes can call for Keyboard Reply which calls for more Reply if echoed

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/terminal-lies.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
