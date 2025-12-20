<!-- omit in toc -->
# terminal-lies

Lies that too many Terminal Programs tell themselves

- [1. Input Key Chords read from the Terminal Touch/ Tap/ Key Press/ Release](#1-input-key-chords-read-from-the-terminal-touch-tap-key-press-release)
  - [Lie 1.1 Each different Key Chord sends different Bytes](#lie-11-each-different-key-chord-sends-different-bytes)
  - [Lie 1.2 Key Chords send the same Bytes through your Terminal and mine](#lie-12-key-chords-send-the-same-bytes-through-your-terminal-and-mine)
  - [Lie 1.3 You can know which sets of Key Chords send the same Bytes](#lie-13-you-can-know-which-sets-of-key-chords-send-the-same-bytes)
  - [Lie 1.4 Key Chords that send Bytes through your Terminal also send Bytes through mine](#lie-14-key-chords-that-send-bytes-through-your-terminal-also-send-bytes-through-mine)
  - [Lie 1.5 You can know when the Bytes of one Key Chord end before the start of the next](#lie-15-you-can-know-when-the-bytes-of-one-key-chord-end-before-the-start-of-the-next)
  - [Lie 1.6 You can't know when the Bytes of one Key Chord end before the start of the next](#lie-16-you-cant-know-when-the-bytes-of-one-key-chord-end-before-the-start-of-the-next)
  - [Lie 1.7 Key Chords send the same Character through your App and mine](#lie-17-key-chords-send-the-same-character-through-your-app-and-mine)
  - [Lie 1.8 That Key Chord that worked yesterday will work today too](#lie-18-that-key-chord-that-worked-yesterday-will-work-today-too)
- [2. Output Characters written to the Terminal Screen](#2-output-characters-written-to-the-terminal-screen)
  - [Lie 2.1 Every Character looks a little different when printed](#lie-21-every-character-looks-a-little-different-when-printed)
  - [Lie 2.2 Every Character can be encoded as a UTF-8 SurrogateEscape Byte Sequence](#lie-22-every-character-can-be-encoded-as-a-utf-8-surrogateescape-byte-sequence)
  - [Lie 2.3 Every well-loved Character has one distinct Python UnicodeData Name](#lie-23-every-well-loved-character-has-one-distinct-python-unicodedata-name)
  - [Lie 2.4 Every Python Character found by UnicodeData Lookup has a Python UnicodeData Name](#lie-24-every-python-character-found-by-unicodedata-lookup-has-a-python-unicodedata-name)
  - [Lie 2.5 Printing a double-wide Character moves the Terminal Cursor by two Columns](#lie-25-printing-a-double-wide-character-moves-the-terminal-cursor-by-two-columns)
  - [Lie 2.6 Printing an Escape Sequence won't close all your Terminal Tabs](#lie-26-printing-an-escape-sequence-wont-close-all-your-terminal-tabs)
- [3. Terminal Capability Discovery \& Negotiation](#3-terminal-capability-discovery--negotiation)
  - [Lie 3.1 Every Terminal reports if it's a Darkmode Terminal or a Lightmode Terminal](#lie-31-every-terminal-reports-if-its-a-darkmode-terminal-or-a-lightmode-terminal)
  - [Lie 3.2 Python "import pty" doesn't change the Colors negotiated by Vim](#lie-32-python-import-pty-doesnt-change-the-colors-negotiated-by-vim)
  - [Lie 3.3 Escape Sequences can tell a Terminal Cursor to step towards the 8 Points of the Compass](#lie-33-escape-sequences-can-tell-a-terminal-cursor-to-step-towards-the-8-points-of-the-compass)
  - [Lie 3.4 Preplanning put the related Characters together in Unicode](#lie-34-preplanning-put-the-related-characters-together-in-unicode)
- [4. Copying Characters out from the Terminal and pasting Characters back into the Terminal](#4-copying-characters-out-from-the-terminal-and-pasting-characters-back-into-the-terminal)
  - [Lie 4.1 You can copy in what you please](#lie-41-you-can-copy-in-what-you-please)
  - [Lie 4.2 You can copy out what you please](#lie-42-you-can-copy-out-what-you-please)
  - [Lie 4.3 The Emacs Key Chords you learn at the Terminal do or don't work elsewhere](#lie-43-the-emacs-key-chords-you-learn-at-the-terminal-do-or-dont-work-elsewhere)
  - [Lie 4.4 You can print the Glyphs you printed in 1980](#lie-44-you-can-print-the-glyphs-you-printed-in-1980)

As posted by Pat LaVarre & friends, Dec/2025


## 1. Input Key Chords read from the Terminal Touch/ Tap/ Key Press/ Release

### Lie 1.1 Each different Key Chord sends different Bytes

    cat - >/dev/null
        # press Esc
        # press ⇧ Esc
            # see the same ^[ from both

### Lie 1.2 Key Chords send the same Bytes through your Terminal and mine

    cat - >/dev/null
        # press ⌥←
            # see ^[b at Apple macOS Terminal
            # see ^[[1;3D at Open-Source macOS iTerm2

### Lie 1.3 You can know which sets of Key Chords send the same Bytes

    cat - >/dev/null
        # press ↓
        # press ⇧↓
            # see ^[B twice at Apple macOS Terminal, same same
            # see ^[B from ↓ and ^[[1;2B from ⇧↓ at Open-Source macOS iTerm2

### Lie 1.4 Key Chords that send Bytes through your Terminal also send Bytes through mine

    cat - >/dev/null
        # press ⇧ Fn F1
            # ring the bell to say don't do that, at Apple macOS Terminal, till after you reconfigure it
            # see ^[[1;2P at Open-Source macOS iTerm2

### Lie 1.5 You can know when the Bytes of one Key Chord end before the start of the next

    cat - >/dev/null
        # press Esc
        # press ←
            # see ^[ said for Esc
            # see ^[[D said for ←, starts with same Byte

### Lie 1.6 You can't know when the Bytes of one Key Chord end before the start of the next

    sleep 1 && printf '\033[5n' && cat - >/dev/null
        # press Esc during the Sleep
        # see the ^[[0n from the ^[[5n arrives after the Esc, showing the end of its Bytes

### Lie 1.7 Key Chords send the same Character through your App and mine

    cat - >/dev/null
        # press ⌥ Y
            # See ¥ inside most macOS Apps
            # See \ inside the Terminal, in homage to Japanese Tech of the past century

Understand here we mean the 2 Key Chord of hold down the ⌥ Option/Alt Key while you press and release the Y Key, there is no ⌥⇧Y 3 Key Chord here

### Lie 1.8 That Key Chord that worked yesterday will work today too

This can be true in places, but . . .

At the Apple macOS Terminal, you can toggle its Settings > Keyboard > Use Option As Meta Key back and forth. And then you get more distinct Key Chords in this special mode. You get ⎋ ⎋ and ⎋⌫ and ⎋ ⏎ apart from ⏎ and ⌫ and ⎋. You get quick complete ⎋\` ⎋E ⎋I ⎋N ⎋U because you gave up the Key Chords coded as accented vowels at ⎋\` E and ⎋E E and  ⎋I I and ⎋N N and  ⎋U U and so on. But then when you toggle this Setting back, you lose all these new Key Chords

At the Google Cloud Shell, they churn their rules from time to time. Lately, their ⌃M is a toggle between having the ⇥ Tab Key mean ⌃I or some Browser Thing. Their ⌃M also toggle the ⇧⇥  Shift Tab Key Chord between meaning ⎋[Z and some Browser Thing. And they break the classic equivalence between ⌃M and ⏎ Return: you get different effects at each. And ditto they give you different effects at ⌃I and at ⇥ Tab. Plus they have a ⛭ > Keyboard > Alt Is Meta toggle that works lots like Apple's Keyboard > Use Option As Meta Key

At the Google Cloud Shell, you can't depend on ⌃C meaning anything. Sometimes, you can pound away on ⌃C to no response. With us, we'll likely take ⌃\ or ⌃Z to mean some kind of quit, even while they're blocking ⌃C

And don't go thinking that having ⎋⎋ ⎋` ⎋E ⎋I ⎋N ⎋U means you have ⎋← ⎋↑ ⎋→ ⎋↓. At the Apple macOS Terminal you still then have only ⎋← and ⎋→ and ⇧← and ⇧→ as distinct from ← ↑ → ↓ across all combinations of the ⌃ ⌥ ⇧ shifting Keys. That's why we'll often take ⎋← and ⎋→ to mean ⎋↑ and ⎋↓ in place of themselves

Google Cloud Shell often pops up complaints about this whole mess, in particular

> Is your browser intercepting key combinations? Install Cloud Shell as a PWA for a better experience

> The tab key is being redirected to the terminal. Press ctrl+m to enable page navigation with the tab key

## 2. Output Characters written to the Terminal Screen

### Lie 2.1 Every Character looks a little different when printed

    printf '_\040_ U+0020 Space\n'
    printf '_\302\240_ U+00A0 No-Break Space\n'

    cat - >/dev/null
        # press Spacebar
        # press ⌥ Spacebar

### Lie 2.2 Every Character can be encoded as a UTF-8 SurrogateEscape Byte Sequence

Often it works

    >>> b"\xc0\x80".decode(errors="surrogate""escape")
    '\udcc0\udc80'
    >>>
    >>> "\udcc0\udc80".encode(errors="surrogate""escape")
    b'\xc0\x80'
    >>>

Sometimes it doesn't

    >>> "\ud800".encode(errors="surrogate""escape")
    Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    UnicodeEncodeError: 'utf-8' codec can't encode character '\ud800' in position 0: surrogates not allowed
    >>>

### Lie 2.3 Every well-loved Character has one distinct Python UnicodeData Name

    python3 -c 'import unicodedata; print(unicodedata.name(b"\302\240".decode()).title())'
        # see they say No-Break Space, hurrah, but next look below

    python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("EOM"))))'
    python3 -c 'import unicodedata; print(hex(ord(unicodedata.lookup("End Of Medium"))))'
        # see they both say 0x19

    python3 -c 'import unicodedata; print(unicodedata.name("\000").title())'
    python3 -c 'import unicodedata; print(unicodedata.name("\012").title())'
        # see they say ValueError for U+0000 Null
        # see they again say ValueError, now for U+000A Line Feed

### Lie 2.4 Every Python Character found by UnicodeData Lookup has a Python UnicodeData Name

    python3 -c 'import unicodedata; print(unicodedata.name("\x19").title())'
        # see they again say ValueError

### Lie 2.5 Printing a double-wide Character moves the Terminal Cursor by two Columns

This does work in some Terminals. But at a Google Cloud Shell you have to blank out the East Column yourself, and you have to move the Cursor across the East Column yourself

As shown by Shell PrintF

    printf '\xF0\x9F\x9F\xA1' && printf '\xF0\x9F\x9F\xA1' && printf '\033[6n' && printf '\x0A' && cat - >/dev/null

    printf 'AlfaBravo''\r''\xF0\x9F\x8F\x86''\033[C''\033[K''\n'

As shown by Python

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

### Lie 2.6 Printing an Escape Sequence won't close all your Terminal Tabs

Unlock https://shell.cloud.google.com/?show=terminal with your gMail Username & Password. You can ignore the many upsells, you can always choose Reject. If you slip and fail to choose Reject, it still gives you a second chance to choose Reject

Then try

    printf '\033]12;#''ff0000\007' && sleep 1 && printf '\033]112\007'

Watch it close all your Terminal Tabs. Oops


## 3. Terminal Capability Discovery & Negotiation

### Lie 3.1 Every Terminal reports if it's a Darkmode Terminal or a Lightmode Terminal

Apple macOS Terminal & Open-Source macOS iTerm2, yes

Google Cloud Shell, no

Try the Osc 11 Query of a 16-bit R G B encoding of the default Backlight behind foreground Color

    % printf '\033[5n''\033]11;?\007' && cat - >/dev/null
    ^[[0n^[]11;rgb:2020/2020/2020^G

That's what it looks like when it works. When it doesn't work, it silently ignores the Osc 11

    % printf '\033[5n''\033]11;?\007' && cat - >/dev/null
    ^[[0n

### Lie 3.2 Python "import pty" doesn't change the Colors negotiated by Vim

Last time I checked, the orange went missing

### Lie 3.3 Escape Sequences can tell a Terminal Cursor to step towards the 8 Points of the Compass

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

### Lie 3.4 Preplanning put the related Characters together in Unicode

Yes you will see clusters

You can find 0123456789 and ABCDEFGHIJKLMNOPQRSTUVWXYZ and abcdefghijklmnopqrstuvwxyz, because of how slowly and carefully the US ASCII standard came together in the 1960's

But you will find the 9 Comic Colors of Unicode jumbled

    ⚪ ⚫
    ⬛ ⬜

    🔴 🔵 🟠 🟡 🟢 🟣 🟤
    🟥 🟦 🟧 🟨 🟩 🟪 🟫

And Apple promotes ordering mentions of ⎋ ⌃ ⌥ ⇧ ⌘ as such, but those show up jumbled in Unicode, and not all together

    ← ↑ → ↓
    ↖ ↗ ↘ ↙
    ⇥ ⇧ ⋮ ⌃ ⌘ ⌥ ⌫ ⎋ ⏎ ☰

## 4. Copying Characters out from the Terminal and pasting Characters back into the Terminal

### Lie 4.1 You can copy in what you please

Try pasting in a U+0008 Backspace

    printf '\010' |pbcopy && cat - >/dev/null

At Open-Source macOS iTerm2, it just doesn't work

At Apple macOS Terminal, it pops up a dialog to yell at you
> Paste control characters? <br>
> The text contains control characters which could allow the pasted content to perform arbitrary commands. <br>
> To confirm and Paste, you can use ⇧ ⌘ ⏎  <br>
> &lt;Paste&gt; &lt;Paste without Control Characters&gt; &lt;Cancel&gt;

### Lie 4.2 You can copy out what you please

Putting U+0009 Tab into the text can matter. Like you can get Slack to paste Tsv. You can also paste as Tsv into ⇧ ⌘ V at Google's sheets.new > Edit > Paste Special > Values Only

    printf 'Alfa\tBravo\tCharlie\n''A1\tB1\tC1\n''A2\tB2\tC2\n' |pbcopy

Putting Backlights and Colors into the text can matter. Like you can get a Google docs.new to show the Colors

    % printf '\033[31m''\033[103m''31 on 103\n'
    31 on 103
    %

Slack doesn't do Colors generally, but Slack does understand monospacing the 9 Comic Colors of Unicode. Odds on your Markdown Viewer feels this figure is assymetric, not a regular square. If that's so, then your Markdown Viewer is wrong

          ⚪⚪⚪⚪⚪
          ⚪🔴🔴🔴⚪
      ⚪⚪⚪⚪⚪⚪⚪⚪⚪
      ⚪🔴⚪⚪⚪⚪⚪🔴⚪
      ⚪🔴⚪⚪⚪⚪⚪🔴⚪
      ⚪🔴⚪⚪⚪⚪⚪🔴⚪
      ⚪⚪⚪⚪⚪⚪⚪⚪⚪
          ⚪🔴🔴🔴⚪
          ⚪⚪⚪⚪⚪

### Lie 4.3 The Emacs Key Chords you learn at the Terminal do or don't work elsewhere

In reality, they don't simply all work, and they don't simply all not work

Lots of macOS understands ⌃A ⌃B ⌃D ⌃E ⌃F ⌃K ⌃N ⌃O ⌃P ⌃T ⌃Y in the way of Emacs, though their ⌃H and ⌥⌫ depart from Emacs tradition. As for ⌃W and ⌃U and ⌃⇧@ should mean, well, Emacs & Shell never have agreed over what those should mean

The Apple macOS Terminal doesn't let you distinguish ⌥⌫ from ⌫, but does pretty natively understand ⎋B and ⎋F, which Emacs ⌃H K docs as M-b 'backward-word' and M-f 'forward-word'

You can get some variations of Emacs ⎋Z and ⎋⇧Z to work in places like macOS Zsh, which gives you a bit and not much of what Vim does with D T and D F. Emacs speaks of 'zap-to-char' and 'zap-up-to-char', with ⎋Z traditionally doing the work of Vim D F I, but Zsh ⎋Z can more easily be told to do D T

### Lie 4.4 You can print the Glyphs you printed in 1980

Wikipedia [ATASCII](https://en.wikipedia.org/wiki/ATASCII), meaning Atari® Ascii, has tried to find similar Glyphs inside Unicode, and they're not all plainly found.

Back in the days of the Atari 800, the Byte Codes 0x80 through 0xFF printed as the reverse video of Byte Codes 0x00 through 0x7F, and only 0x20 was blank. 0xA0 was a reversed blank

Reverse-video at my Terminal copies into Google http://docs.new no problem, aye, but it lands wrong in Google http://sheets.new/ and it lands wrong in Slack

I felt so very disappointed when first I saw the IBM PC choose to render 0x00 and 0x20 and 0xFF as all the very same blank glyph. Like, you know, "you had just the one job". You could have done it well

See also
+ a screenshot of [Atari®](https://en.wikipedia.org/wiki/ATASCII#/media/File:Atascii-character-set-00toFF-2x.gif)
+ a screenshot of [IBM PC](https://en.wikipedia.org/wiki/Code_page_437#/media/File:Codepage-437.png)

<!--

todo: show when same Bytes have different meanings from Keyboard or to Screen

todo: show when Screen Bytes can call for Keyboard Reply which calls for more Reply if echoed

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/terminal-lies.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
