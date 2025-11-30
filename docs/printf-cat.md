# printf-cat

You can just try things. Inside an actual Terminal, they do go more or less well


## Terminal Things that go well


### The classic four Arrows in order

Try

    cat - >/dev/null

Press and release the ↑ ↓ → ← Arrow Keys in this order: Up, Down, Right, Left. Press the Spacebar in between each two Arrow Keys. You'll see the 'stty echoctl' encoding of which Keys you released

    ^[[A ^[[B ^[[C ^[[D


## Terminal Things that don't thing well


### The Shifted Arrow Key Chords

Try

    cat - >/dev/null

Hold down ⇧ Shift and press and release the → Right and ← Left Arrow Keys. At macOS Terminal, or at macOS iTerm2, this does just work. They tell you that ⇧← and ⇧← say

    ^[[1;2C ^[[1;2D

But try your Google Cloud Shell inside macOS Safari, and it will tell you that you've pressed no keys at all. The different Terminals disagree over which Key Chords to say you have and haven't pressed

Look closer next, and you'll see they also disagree over which Byte Encodings to send in, even when they do agree to say you have pressed a Key Chord. To see a broad sparkling variety of opinions, try a broad variety of Arrow Key Chords, such as these eight kinds

> ↑ ↓ → ← <br>
> ⌃↑ ⌃↓ ⌃→ ⌃← <br>
> ⌥↑ ⌥↓ ⌥→ ⌥← <br>
> ⇧↑ ⇧↓ ⇧→ ⇧← <br>
> ⌃⌥↑ ⌃⌥↓ ⌃⌥→ ⌃⌥← <br>
> ⌃⇧↑ ⌃⇧↓ ⌃⇧→ ⌃⇧← <br>
> ⌥⇧↑ ⌥⇧↓ ⌥⇧→ ⌥⇧← <br>
> ⌃⌥⇧↑ ⌃⌥⇧↓ ⌃⌥⇧→ ⌃⌥⇧← <br>

And try all of these with Fn too. You'll see one set of encodings at macOS Terminal, another at macOS iTerm2, and another at Google Cloud Shell


### The Fn Arrow Key Chords

In particular, hold down ⇧ Shift and Fn, and press and release the ↑ ↓ → ← Arrow Keys

At macOS Terminal, this works. It tells you that ⇧Fn↑, then ⇧Fn↓, ⇧Fn→, then ⇧Fn← says

    ^[[5~ ^[[6~ ^[[F ^[[H

But next try macOS iTerm2 or Google Cloud Shell. As for ⇧Fn↑ Up and ⇧Fn↓ Down, all the while you have no scrollback, macOS iTerm2 will tell you that you've pressed no keys at all. Once you make some scrollback (like with Shell 'seq 999'), then iTerm2 will take your ⇧Fn↑ and ⇧Fn↓ as commands to scroll your screen up and down a page

As for ⇧Fn→ Right and ⇧Fn← Left, iTerm2 will tell you that these are Key Chords for you to press and release, but it changes their EchoCtl encoding away from ^[[F ^[[H over to

    ^[[1;2F ^[[1;2H

And Google Cloud Shell is up contradicting them both. It will say that you've pressed no keys at all, when you have pressed ⇧Fn and an Arrow Key 


### The ⌥-Click across Lines of Vim or Emacs

Try Vim at Google Cloud Shell

Your ⌥-Click moves the Cursor back and forth inside a Screen Row, yes no problem, aye. And even when you make the Vim Line long enough to wrap, then you can still ⌥-Click anywhere in the Line to move the Cursor well

But next try ⌥-Click to move into another Line. The Cursor leaps to the start or end of the Current Line, and the Terminal beeps. Oops

What's happening inside is that Vim rejects ⎋[⇧C and ⎋[⇧D Byte Encodings of the → and ← arrows when they arrive at the start or end of a Vim Line.

And next try Emacs in place of Vim. Now the Cursor overshoots wildly. Sure it goes towards where you asked, but it keeps on going farther on its own, it doesn't stop

What's happening inside is that Emacs does accept ⎋[⇧C and ⎋[⇧D Byte Encodings of the → and ← arrows but gives them no credit for moving across the Spaces it shows past the end of each Emacs Line. Oops


### The ⌥-Click far across the Screen

Try a different couple of places to look at EchoCtl encodings of Key Chords

First inside the default ⎋[ ?1049L Main Screen

    cat - >/dev/null

But then also inside the ⎋[ ?1049H Alt Screen

    printf '\033[''?1049h' && sleep 3.456 && printf '\033[''?1049l'

These two will both look & feel much the same

However, at macOS iTerm2, when you try ⌥-Click, then you get the EchoCtl encodings of all 4 of the Arrows (^[[A ^[[B ^[[C ^[[D) only inside the ⎋[ ?1049H Alt Screen. Back out in the default ⎋[ ?1049L Main Screen, you only get the EchoCtl encodings of ^[[C → Right Arrow and ^[[D ← Left Arrow. Oops

It's not like avoiding half the encodings doesn't work. But it can be way slow: huge lag in gameplay. However many Columns wide your screen is, multiply that by 3 and that's how many Bytes you're sending slowly to say move Up or Down by one Row

Google Cloud Shell has this same problem, but out there our ⎋[ ?1049H workaround doesn't fix it. macOS Terminal doesn't have this problem. It has other problems


### Four common Terminal bugs, and counting

How about you?

Got another Terminal bug you know?

How about we celebrate them here, soon after we first meet them?


<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/printf-cat.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
