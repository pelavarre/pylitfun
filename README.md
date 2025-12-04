# pylitfun

**A Python terminal engine that actually gets input decoding right**

In pure Python, working down at the level of raw terminal bytes, with zero dependencies

For the nine of us who notice when a ⇧← comes out wrong, as if it were a plain ←

<div align="center">
⚪ ⚫ 🔴 🔵 🟠 🟡 🟢 🟣 🟤 <br>
⬛ ⬜ 🟥 🟦 🟧 🟨 🟩 🟪 🟫 <br>
</div>


## The Problem

You're building a terminal app. You want ⌥-Click to move the cursor. Simple, right?

Wrong. Try it in vim or emacs, and click past the end of a wrapped line. The cursor jumps to the wrong place. Click again, it moves somewhere else, or beeps

Or try ⇧← in your favorite terminal app framework, and try ⌥↓, and try ⇧Fn→. Half the time they're decoded as plain ← ↓ → arrows with their modifier keys lost, or the engine gives up and tells you nothing was pressed at all

And can we roll our eyes over the large ⎋ Esc key delays? Press and release Esc: now you wait. The engine freezes in fear, as if you just might be slowly typing out the ⎋ [ ⇧A encoding of the ↑ Up Arrow key

**These aren't edge cases. These are Tuesday.**


## What we fix

We decode what your terminal sends: instantly, simply, & correctly

1. **Shifted arrow keys work** <br>
   ⇧←, ⌥↓, and ⇧Fn→ decode correctly, all the while terminals send ambiguous byte sequences. We don't invent key presses that didn't happen, and we don't lose the modifier keys that you did press

2. **⌥-Click goes where you clicked it** <br>
   ⌥-Click works even across wrapped lines and in a Google Cloud Shell. We accept ⎋[⇧C and ⎋[⇧D as meaning wrap-across-edge for ⌥-Click, not an error to beep over

3. **Zero ⎋ Esc key delay** <br>
   We frame your input instantly & simply & correctly by sending ⎋[5N DSR5 queries for ⎋[0N DSR0 replies. When you release the ⎋ Esc key, we know immediately. We don't wait and wonder

4. **Double-character keystrokes work** <br>
   Try ⌥E J on macOS. You get '**j́**' (j with combining accent). Many terminal engines, including Emacs ⌃H K, then lose track, wrongly saying you pressed J without the ⌥E before that adds the aigu accent afterwards. We frame the '**j́**' from ⌥E J and the '**J́**' from ⌥E ⇧J correctly

5. **Double-wide characters work too** <br>
   Characters like 😃 and **웃** and **襾** and **祝** and **￥** should take two columns, says Unicode. We make it so, at both odd and even columns. We don't chop double-wide characters in half. And we let your Terminal itself decide the width of characters like **¤**

6. **Double-key jams work when they exist** <br>
   Try press and release of both W and D at once. You & I know that's an an W D ↗ Northeast double-key jam. But many terminal engines insist those are two separate keys, chopped off to mean first W ↑ North and then A ← West, or to mean first A ← West and then  W ↑ North, distinctly and jankily. We don't push this problem on you. We frame all four of the W D ↗ Northeast, the A W ↖ Northwest, the A S ↙ Southeast, and the S D ↘ Southwest, no problem, every so often as your Terminal does send them

7. **Free-form layout, cell by cell** <br>
   We give widgets their choice of screen cells and scrollback cells to write. We don't force them to clear and fill rectangular panes. We don't lock them out of adding rows to the scrollback. We do help them move, grow, shrink, hide away, and return to the screen. We help them share the screen well with other widgets, and share it well with the terminal apps you ran before calling us


## Quick Start

```bash
rm -fr pylitfun/ && git clone https://github.com/pelavarre/pylitfun.git && cd pylitfun/

which -a python3  # such as 2025/Oct Python 3.10

python3 litglass.py --egg=yolo

git log --oneline --no-decorate -1
```

**Requirements**: Python and a Terminal <br>
**Tested in**: macOS Terminal, macOS iTerm2, and Google Cloud Shell <br>
**Tested on**: iPad, iPhone, MacBook, and a remote Linux <br>
**Tests needed**: WSL, Windows Command Prompt, more Linuxes <br>

**Launch one widget**: python3 bin/pylitfun.py Luff <br>
**Send keycaps by name**: python3 bin/pylitfun.py Fn F1 <br>


## Widgets you can build here

We put up 7 games nearby, as proofs of concept:

- **Tic-Tac-Tuh** - Tic-Tac-Toe plus flip, rotate, undo, extra turns, and try to lose
- **Chuckers** - Checkers with 0, 1, or 2 players, and you can save the game to come back and play more later
- **Luff** - Conway's Game of Life, but clearing & writing only the cells it needs
- **Chuss** - Chess, with the Checkers & Tic-Tac-Toe flexibilities
- **Pung** - Pong® homage, two players on one keyboard, and you can bump the scoreboard up and down
- **Puckmuhn** - Pac-Man® style, and you can fly through walls and come back from the dead
- **Snuck** - Snake®, but with double-wide characters, an undo, and a pause before dying

We include Easter eggs in every game to help you improve the rules. Because we can

We're working presently to port these 7 in here

Tell us what else you know will fit in here?
How about Galaga® 1981, Dig-Dug® 1982, Tetris®, Sorry!®, and LEGO®
from the commercial gaming world?
How about Go from China, and Pachisi from India?
Can we do something visually fun with a Text Adventure? Hunt the Wumpus?


## Status

We're porting 1 Engine and 7 Games in from the older repos we put up as proofs of concept

**Completed**
- This README
- Our "what we fix" list of six terminal bugs fixed

**Coming soon**
- 'from pylitfun.litglass import KeyLogger' - Print the keycaps you release and their byte encodings
- 'from pylitfun.litglass import Loopbacker' - Echo with vertical paste, loop the control sequences you type straight back into the screen and scrollback

**Coming next**
- Our 7 games, but rewritten now to run as widgets,
no longer running only as full-screen apps


## Controls

- **⌃C** to quit <br>
- **Fn F1** for help <br>
- **⌥-Click** to move the cursor <br>


## Setup by Platform

**macOS**: Finder → Go → Utilities → Terminal

**Windows**: Run in WSL or Windows Command Prompt

**Linux**: You know where your Terminal is

**Web Browser**: Yes you do have a Linux in your Web Browser, like so =>

Google Cloud Shell at [shell.cloud.google.com](https://shell.cloud.google.com/?show=terminal) comes free of charge, bundled with Gmail, except you do have to learn to ignore its silly prompts. It really does still work after you click "Reject" on its every ask to upsell you. It really does keep your saved games saved, when you close the Browser Tab and choose "Leave Page" in place of "Stay on Page". And you can accidentally click the wrong choice, no problem, for then they do give you your second chance to say No, No, please do stop asking me


## Why This Repo Exists

Because ⇧← shouldn't be decoded as ← <br>
Because Vim gets ⌥-Click wrong and Emacs gets ⌥E ⇧J wrong <br>
Because pressing ⎋ Esc shouldn't make you wait <br>
Because wide emoji shouldn't come out chopped in half <br>

Because we've wrongly been saying these bugs are impractically expensive to fix

Because I like turning "impossible" into "done"


## Links

- [GitHub Repository](https://github.com/pelavarre/pylitfun)
- [Questions/Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre+%23PyLitFun)


<!--

Written with help from Claude·Ai

This is a draft for a ReadMe·Md of a new public GitHub Repository built in public. We're scavenging bits from old repos, building out a new repo

What does its form and content tell you about what audience I should be building towards connecting with?

I've spoken with you before, this is like our third choice of audience and our sixth draft together

I fear you feel it's unconventional that it matters to me

+ we find some good way to show, up top, all nine of the comic colors and circular circles and square squares of Unicode

+ we keep with the old precise mark of ® on registered trademarks

+ we keep with the new precise ⎋[5N DSR5 and ⎋ [ ⇧A ways of speaking of byte encodings and keycaps

+ we keep with the new · Middle-Dot workaround for aggressively wrong bots insisting on hotlinking every mention of a word with a . Dot inside of it

+ we don't presume our audience keeps correctly memorized precisely which Python 3 revision takes the win in their 'which -a python3' results

+ we disclose we're developing our Code primarily on a macOS Terminal running the new-ish Oct/2025 Python 3.10, but we also show we sincerely want our tests to pass on other platforms, else explain briefly clearly how to fix our Code or replace an old platform

I want my unconventionalities to come across as thought-provoking,
only offputting for people who aren't real terminal geeks
because they don't enjoy having real terminals surprise them

Can we live within in these limits and still rewrite this text so well as to hope I can reach my audience?

-->

<!--

'The Comments are the first Issue Tracker'

know how

   revive --egg=keycaps

   accept U+F8FF  as Printable Enough from ⌥⇧K

   accept

   backport to Oct/2019 Python 3.8

   p should mean print inside ~/bin/p

   ~/bin/c sh script of litshell.py
      prompt before blocking till Tty Stdin Line complete

   ~/bin/o sh script of litshell.py - counting _.strip()'s
      |o| filter = |o|
      |o filter & dump = |o
      o| source & filter = pbpaste |o|
      o source & filter & sink = pbpaste |o |pbcopy

   ~/bin/-1 sh script of litshell.py
      |-1| capture & re/publish & dump = >-1 && -1 |pbcopy && pbpaste
      |-1 capture & publish & sink = >-1 && -1 |pbcopy
      -1| publish & dump = cat -1 |pbcopy && pbpaste
      -1 capture & publish = pbpaste >-1 && cat -1 |pbcopy

dunno how

   gcam should pick up new Added Files into the wip

   Zsh ⌃U wrongly does row-erase, I want the row-head-erase of ⎋[1⇧K

Game - **Smushup** - Arrow Pair to move 8 ways, and smush matching colors
Game - **Muhnswuhper** - Minesweeper® style, but ...
Single File Download & Run of the Python

-->

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/README.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
