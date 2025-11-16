# pylitfun

**A Python terminal engine that actually gets input decoding right**

In pure Python, working with raw terminal bytes, & zero dependencies

For real terminal geeks, by total terminal geeks, like for all nine of us on Earth

<div align="center">
⚪ ⚫ 🔴 🔵 🟠 🟡 🟢 🟣 🟤 <br>
⬛ ⬜ 🟥 🟦 🟧 🟨 🟩 🟪 🟫 <br>
</div>

## Many Problems

You're building a terminal app. You want ⌥-Click to move the cursor. Simple, right?

Wrong. Try it in vim or emacs, and click past the end of a wrapped line. The cursor jumps to the wrong place. Click again, it moves somewhere else, or beeps

Or try ⇧← in your favorite terminal app framework, and ⌥↓, and ⇧Fn→. Half the time they're decoded as plain ← ↓ → arrows with their shifting keys lost, or the engine gives up and tells you nothing was pressed at all

And can we roll our eyes over the large ⎋ Esc key delays? Press and release Esc: now you wait. The engine freezes in fear, for you just might be slowly typing out the ⎋ [ ⇧A encoding of an ↑ Up Arrow key

**These aren't edge cases. These are everyday keystrokes that terminal engines commonly get wrong.**

## One Solution

We decode what your terminal *actually* sends, instantly and simply and correctly

### What we fix:

1. **Shifted arrow keys just work**  
   ⇧←, ⌥↓, ⇧Fn→ are decoded correctly, even when terminals send ambiguous byte sequences. We don't invent key presses that didn't happen, and we don't lose the modifier keys you actually pressed

2. **⌥-Click goes where you clicked**  
   Even past line ends. Even across wrapped lines. Even in Google Cloud Shell. We learned to accept ⎋[⇧C and ⎋[⇧D as wrap-to-edge, not an error to beep over

3. **No Esc key delay**  
   We frame your input instantly % simply & correctly by sending ⎋[5N DSR5 queries for ⎋[0N DSR0 replies. When you release Esc, we know immediately: no waiting, no ambiguity

4. **Multi-character keystrokes work**  
   Try ⌥E J on macOS. You get 'j́' (j with combining accent). Most terminal engines, including Emacs ⌃H K, then lose track, wrongly saying you pressed J without ⌥E. We frame the 'j́' from ⌥E J correctly, and the 'J́' from ⌥E ⇧J too

5. **Wide characters fill the correct number of columns**  
   Unicode gives us comically colored, circular circles and square squares: the orange 🟠 🟧 and the yellow 🟨 🟡 and so on and on. We lay each these Unicode Emoji down across two columns. We don't chop them in half

6. **Free-form layout, cell by cell**  
   We let your widgets write to any screen cell or scrollback cell. No forced rectangular panes. No getting locked out of scrollback. We help your widgets move, grow, shrink, hide away, and return. We share the screen well between multiple widgets and the terminal apps you ran before calling us

## Quick Start

```bash
git clone https://github.com/pelavarre/pylitfun.git && cd pylitfun/

which -a python3  # such as 2025/Oct Python 3.10

python3 bin/pylitfun.py --egg=yolo
```

**Requirements**: Python and a terminal <br>
**Tested on**: iPad, iPhone, MacBook, a remote Linux <br>
**Tested in**: macOS Terminal, iTerm2, Google Cloud Shell <br>
**Tests needed**: WSL, Windows Command Prompt, more Linux terminals <br>

**Run a specific demo**: python3 bin/pylitfun.py Pung <br>
**Send keycaps by name**: python3 bin/pylitfun.py Fn F1 <br>

## What you can build here

We've built 7 classic games as proofs of concept:

- **Tic-Tac-Tuh** - Tic-Tac-Toe with flip, rotate, undo, extra turns, and try to lose
- **Chuckers** - Checkers with 0, 1, or 2 players
- **Conway Luff** - Conway's Game of Life, but clearing & writing only the cells it needs
- **Chuss** - Chess, with the Checkers & Tic-Tac-Toe flexibilities
- **Pung** - Pong® homage, two players on one keyboard
- **Puckmuhn** - Pac-Man® style, but fly through walls and come back from the dead
- **Snuck** - Snake®, but with double-wide characters on odd or even columns, undo, and a pause to save before dying

In every game, we include Easter eggs to help you improve the rules. Because we can

Tell us what else you've notice will fit well here?
Like Galaga® 1981, Dig-Dug® 1982, Tetris®, Sorry!®, and LEGO®
from the commercial gaming world.
Like Go from China, and Pachisi from India


## Status: Building in Public

We're porting code from other repos, assembling the pieces here

**Completed**
- This README
- Fixes for the bugs

**Coming soon**
- from pylitfun.litglass import KeyLogger - Print the keycaps you release and their byte encodings
- from pylitfun.litglass import Loopbacker - Echo with vertical paste, loop back the control sequences you type straight into the screen and scrollback

**Coming next**
- Our seven games, but rewritten to run as widgets,
no longer running only as full-screen apps

## Controls

- **⌃C** to quit
- **Fn F1** for help  
- **⌥-Click** to move the cursor correctly with Option/Alt ⌥

## Setup by Platform

**macOS**: Finder → Go → Utilities → Terminal

**Web Browser**: Google Cloud Shell at [shell.cloud.google.com](https://shell.cloud.google.com/?show=terminal)  
(Free, bundled with Gmail. Ignore the access prompts—you can "Reject" everything and "Leave Page" without losing your work)

**Windows**: Run in WSL or Windows Command Prompt

**Linux**: You know where your Terminal is

## Why This Repo Exists

Because vim gets ⌥-Click wrong and emacs gets ⌥E ⇧J wrong <br>
Because pressing Esc shouldn't make you wait <br>
Because ⇧← shouldn't be decoded as ← <br>
Because wide emoji shouldn't be chopped in half <br>

Because
these bugs have been "acceptable" for decades,
AND they're really not necessary, nor acceptable neither

## Links

- [GitHub Repository](https://github.com/pelavarre/pylitfun)
- [Questions/Feedback](https://twitter.com/intent/tweet?text=/@PELaVarre+%23PyLitFun)