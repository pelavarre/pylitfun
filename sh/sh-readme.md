# Tiny independent Shell Tools, one file each

**Take one. Then another. Then more.**

Each file in [here/](.) is a few lines of a plain Shell Script. Each Script stands alone. Copy one into your own Shell Path, and it works. Copy none of the others, and the one you did copy still works.

    cp -ip sh/.ls ~/bin/.

That is the whole install. No framework, no config to source. If you stop liking one, delete it, and nobody cares.

## Who is this for?

You already have a dozen aliases in your Shell rc file. You know more is a bit wrong than you have made time to fix. A few of them you have forgotten altogether by now.

They die when you 'ssh' somewhere, because they didn't come with you. They die when you switch to Zsh from Bash. They fail when not found in the Shell Path by a new Script. They pile up as lines of 'alias' inside one file that you're slow to edit, because you've forgotten how half of them work.

A tool that is one small file has none of these problems. It runs from any Shell, or from no Shell. It travels by 'cp' and by 'scp'. Its whole story fits on one screen, it opens by saying what it's for, and it can be coded to say who it is again, when it runs.

Fifty of these small files are exactly this simple. And then there are two more. These other two end in '.sh' and come from 'chmod -x'. They code up Shell 'function's to source into your Shell, because they touch things that exist only inside your Shell: your $Pwd current directory and your $? last exit code. To install them, you copy them into your ~/.zprofile and ~/.bash_profile and so on. Or you can 'source' them on demand.

## Three kinds of new Shell Commands

You'll find three kinds of new Shell Commands here, doing three kinds of work.

### 1 Most of the familiar names wear a leading dot

Six telling examples of a few lines each are [.clear](./.clear), [.cp](./.cp), [.cut](./.cut), [.ls](./.ls), [.rm](./.rm), and [.seq](./.seq). Each dotfile calls the command you already know, but with the options you'd have chosen, if you'd stopped and chosen. The '.cp' duplicates like a mouse drag, and doesn't falsely say it also edited the duplicated file or folder. The '.clear' does clear the Scrollback, not only the Screen. The '.cut' cuts to fit on Screen. The '.ls' shows the dotfiles and sorts by when last edited. The '.rm' has an undo. The '.seq' scrolls the old Screen up into the Scrollback, so as to leave your Screen empty without losing its history.

Type the dot and you get the options you need. Skip the dot and you get the stock command, untouched. You get it? We've improved three dozen familiar Shell commands, but we've disrupted nothing. The improvements you need will be obvious to you, in the first moment when you stop and look now. All you needed to learn here you already know now: the leading dot opens up a new and conventionally empty namespace for you to define.

### 2 A handful of familiar names wear no dot at all

The 'emacs', 'md5sum', 'sha256sum', and 'tac' add back in a frequently needed Linux Shell Command that old or new macOS leaves out. 'emacs' finds the Homebrew Emacs. Adding these in at the back of your Shell Path only fills your gaps. They're harmless if you install some other solution ahead of them.

### 3 The few surprising names are extremely short, because you type them so often

The 'd' for a diff, 'v' or 'e' for an editor, 'f' for a find, 'm' for a make. And the 'pb' is your Os Copy/Paste Clipboard Buffer: at the front of a Pipe it pastes, at the back of a Pipe it copies, and in the middle it copies, waits for end-of-file, and then passes the bytes along, so you type 'pb' wherever you like, and never stop again to remember which of 'pbpaste' and 'pbcopy' you meant. Plus you get the classic idea of '|sponge|' more simply installed and running just as well, but as '|pb|'.

## Why you'll enjoy paging through

Each of these tools says again who it is when it runs. It echoes the command it's about to run, and then it runs it. Often it does this by way of 'set -xe'. Use '.less' a few times and you'll have learned 'less -FIRX' without meaning to. Use '.curl' and you'll learn 'curl -k -LSs'. Each file is a flashcard for one Flag or one trick you'd otherwise look up again next month. It works hard to make friends with you itself, and to make the Shell Command inside into more of a friend for you too.

So the appendix below reads fine in any order. Skim the headings. Stop at one that names a thing you do often. Read its three lines: what it does, how to call it, and why to like it. If it lands with you, copy that one file into your Shell Path. Come back for another whenever you like. Nobody's counting.

A few of these lean on macOS, such as anything that touches the Clipboard or the Homebrew Emacs. Two, 'm' and '.make', expect a Makefile of your own at '~/bin/Makefile', and say so up top. The rest run anywhere a Shell runs.
