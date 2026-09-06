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

Each of these Scripts says again who it is when it runs. It prints the command that it's about to run, and then it runs it. Often it does this by way of 'set -xe'.

Try '|.less' a few times and you'll have learned '|less -FIRX' without working hard to remember it. Try '.curl' much, and you'll have learned 'curl -k -LSs'. Each file is a flashcard for an option or a trick you'd otherwise look up again next month. Each Script works hard to make friends with you itself, and works hard to make the Shell Command inside into more of a friend for you too.

This is why the appendix below reads fine in any order. Skim the headings. Stop at one that names a thing you do often. Read its three lines: what it does, how to call it, and why to like it. If it lands with you, copy that one Script into your Shell Path. Come back for another whenever you like. Nobody's counting.

A few of these Scripts lean on the macOS ways of reaching a Homebrew Emacs or the Os Copy/Paste Clipboard Buffer (the pbuffer). To make those run at Linux, you can define the same underlying Shell Commands: pbcopy, pbpaste, and a /opt/homebrew/bin/emacs. Two of these Scripts, the 'm' and '.make', do you good only after you place your most loved Makefile at '~/bin/Makefile', and they say so up top. The rest run well anywhere a Shell runs well.


## Appendix

Here we present each Script, in the order 'ls -1A' shows them. We give you three lines per Script: what it does, one call with the trace it prints, and why to like it. The Screen-fitting Scripts below are shown at 80 Columns by 24 Rows. The Scripts that print who and where you are are shown for J Q Doe (JQD) < jqdoe @ example . com >.

### [sh/_](./_)

A 'cat' that says what it's doing with your Stdin when it sits in the middle or at the back of a Pipe, and quietly takes what you type when it stands alone or at the front.

    $ echo alfa |_
    + cat -
    alfa

Type '\_' alone and it shows what you paste next as input, but discards it, doesn't force you to forward it.

### [sh/.argv](./.argv)

Shows each Shell Arg as one Line of Python Repr, numbered from 1, after the Shell has done its splitting and unquoting.

    $ .argv 'Hello, ArgV World!' ''
    + python3 -c ''' ...
    1: 'Hello, ArgV World!'
    2: ''

The empty Arg and the doubled Space show up here, where 'echo' would have hidden them.

<!-- todo: think over if argv[0] should show up in sh/.argv and/or sh/.echo output -->

### [sh/.awk](./.awk)

Picks out the last Column of each Line, and skips the empty Lines.

    $ printf 'alfa bravo charlie\n\ndelta echo\n' |.awk
    + awk 'NF{print $NF}'
    charlie
    echo

The last Column is the one you wanted four times in five, and your own Awk Options still pass through in front, as in '.awk -F/'.

### [sh/.bash](./.bash)

Runs a Bash that reads none of your Profile or Rc Files, inside an empty Environment.

    $ .bash
    + env -i 'PS1=bash \$ ' bash --noprofile --norc
    bash $

When a thing works here and fails in your own Shell, the bug is in your own Rc Files, and you've just proved it.

### [sh/.cat](./.cat)

The same Script as '_', but as a longer verb that you can remember more easily.

    $ .cat t.txt
    + cat t.txt
    alfa bravo charlie

Stood alone, it says 'Press ⌃D to quit happy, or ⌃C to quit sad', which is the manual for 'cat' that 'cat' never gave you.

### [sh/.cd.sh](./.cd.sh)

Defines a '.cd' Shell Function that joins all its Args into one Pathname, goes there, and says where it landed.

    $ source .cd.sh
    $ .cd /usr /bin
    /usr/bin

A Pathname that wrapped across two Lines pastes as two Args, and this takes you there anyway.

### [sh/.clear](./.clear)

Clears the Scrollback too, not just the Screen.

    $ .clear |od -c
    0000000  033   [   H 033   [   2   J 033   [   3   J
    0000013

The macOS Terminal does this for ⌘K.

### [sh/.code](./.code)

Runs the VsCode that macOS keeps out of your Shell Path, and with no Args opens your VsCode Settings·Json.

    $ .code
    + '/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code' '/Users/jqdoe/Library/Application Support/Code/User//settings.json'

The one File you most often go edit in VsCode opens here with the shortest command.

### [sh/.cp](./.cp)

Makes a backup copy of a File or Folder, named with a date-time stamp.

    $ .cp t.txt
    + cp -ipR t.txt t.txt~0906jqd1301~

The stamp is the mtime of the original, not the time of the copying, so the name says when you last edited the thing. The 'jqd' between date and time are the initials of J Q Doe, the traditional name for nobody in particular, so the stamp is signed by no one and can't be mistaken for part of the name.

### [sh/.curl](./.curl)

Calls Curl, but shrugs off Tls Security, follows Redirects, and meters no progress.

    $ .curl https://example.com/ |head -3
    + curl -k -LSs https://example.com/
    <!doctype html>
    <html>
    <head>

Four Options you want for a quick look, and four you'd look up again next month without this flashcard.

### [sh/.cut](./.cut)

Cuts each Line to fit your Screen, leaving 4 Columns blank at the right, which is just room enough to add '... ' when needed.

    $ seq 100 |tr '\n' ' ' |.cut
    + cut -c1-76
    1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 2

Each long Line stays one Row, so a wide Log or Table reads in place, no wrapping.

### [sh/.date](./.date)

Prints the time three ways: your local time, a home time, and UTC.

    $ .date
    + date
    Sun Sep  6 14:01:30 MDT 2026
    + TZ=America/Los_Angeles
    + date
    Sun Sep  6 13:01:30 PDT 2026
    + date -u
    Sun Sep  6 20:01:30 UTC 2026

A Log stamps its Lines in one of these three, and you can read all three without arithmetic.

### [sh/.diff](./.diff)

Compares the latest backup made by '.cp' against the present File.

    $ .diff t.txt
    ++ ls -rt t.txt~0906jqd1301~
    + diff -brpu t.txt~0906jqd1301~ t.txt
    --- t.txt~0906jqd1301~	2026-09-06 13:01:30
    +++ t.txt	2026-09-06 13:01:32
    @@ -1,3 +1,4 @@ delta echo
     alfa bravo charlie

     delta echo
    +delta echo foxtrot

Back up with '.cp', edit, and then this '.diff' says what you did.

### [sh/.echo](./.echo)

Shows each Shell Arg as one Line of Python Repr, numbered from 1, after the Shell has done its splitting and unquoting.

    $ .echo 'a  b' c
    + python3 -c ''' ...
    1: 'a  b'
    2: 'c'

The empty Arg and the doubled Space show up here, where the stock 'echo' would have hidden them.

We'd never want this to be the only /bin/echo, so we also push it out as 'sh/.argv'.

### [sh/.emacs](./.emacs)

Runs the Homebrew Emacs in the Terminal, and reads none of your Emacs Init Files.

    $ .emacs t.txt
    + /opt/homebrew/bin/emacs -Q --no-splash -q -nw --eval '(menu-bar-mode -1)' t.txt

Same Basename as your ~/.emacs and a different Pathname: this runs Emacs as if you'd never customized it, which is how you check whether the bug is yours.

### [sh/.exit.sh](./.exit.sh)

Defines a '.exit' Shell Function that says the Exit Code of your last Command.

    $ false
    $ .exit
    + exit 1

The '$?' is gone the moment you type your next Command, and this says it first, in fewer careful keystrokes than 'echo $?'.

### [sh/.fmt](./.fmt)

Reflows Paragraphs to fit your Screen, leaving 4 Columns blank at the right, which is just room enough to add '... ' when needed.

    $ .fmt <t.txt
    + fmt -w 76

Where '.cut' throws away the far right of each Line, this keeps every word and wraps.

<!-- todo: stop sh/.fmt from silently hanging terminals, and screen for others in sh/ that do and stop them -->

### [sh/.gh](./.gh)

Asks GitHub who it thinks you are.

    $ .gh
    + ssh -T git@github.com
    Hi jqdoe! You've successfully authenticated, but GitHub does not provide shell access.

Run it before the 'git push' that would otherwise fail, when you carry more than one Ssh Key.

### [sh/.head](./.head)

Shows the top of the input, cut to fit your Screen.

    $ .head <t.txt
    + head -21

Fills the Screen and no more, so your Prompt stays in view and the first Line hasn't scrolled away.

### [sh/.less](./.less)

Calls Less, but quits when the input fits one Screen, ignores case in search, passes color through, and leaves the text in your Scrollback when you quit.

    $ .ls -l |.less
    + less -FIRX

Try it a few times and you've learned '|less -FIRX' without working to remember it.

### [sh/.ls](./.ls)

Lists the dotfiles too, with metric byte sizes, sorted so the latest edited lands at the bottom, next to your Prompt.

    $ .ls
    + ls -hlAF -rt
    total 32
    -rw-r--r--  1 jqdoe  staff    31B Sep  6 13:01 t.txt~0906jqd1301~
    -rw-r--r--  1 jqdoe  staff    13B Sep  6 13:01 b
    -rw-r--r--  1 jqdoe  staff    50B Sep  6 13:01 t.txt

Given two or more Args it adds '-d', so a Folder lists as itself and not as its contents.

### [sh/.make](./.make)

Copies your ~/bin/Makefile into a Folder that has no Makefile, and then runs Make.

    $ .make
    + cp -ip /Users/jqdoe/bin/Makefile .
    + make

Your most loved Makefile follows you into every new Folder, and the same Script answers to the shorter name 'm'.

### [sh/.mv](./.mv)

Renames a File or Folder with a date-time stamp, so that it looks deleted.

    $ .mv a
    + mv -i a a~0906jqd1301~

After this '.mv', every tool that searches for the filename 'a' now misses it, 'ls' still shows it, and the undo is one 'mv' back.

### [sh/.od](./.od)

Dumps Bytes as Hex and as Chars, in the style of 'hexdump -C', on the Hosts where 'hexdump' isn't there.

    $ printf 'Hi\n' |.od
    + od -A x -t x1c -v
    0000000    48  69  0a
               H   i  \n
    0000003

The '-v' shows every Byte, where the stock 'od' folds repeats into a '*' you then have to reason about.

### [sh/.path](./.path)

Prints your Shell Path one Dir per Line, or given Args searches every Dir in it for Executables matching each Arg as a loose substring.

    $ .path md5
    + for P in ... $PATH ...; do ls -A $P |grep -ai -e ...  # shellcheck disable=SC2010
    /sbin/md5
    /sbin/md5sum
    ~/bin/md5sum

Whereas 'which -a' needs the exact name, this finds 'md5sum' when you typed 'md5', and it spells your Home as '~'.

### [sh/.ps](./.ps)

Calls Ps to say which Shell is running the Script.

    $ .ps
    + ps -p $$ -o comm=
    sh

Run it as '.ps', then 'bash .ps', then 'zsh .ps', and learn which Shell each of those hands a Script without a Shebang to.

### [sh/.pwd](./.pwd)

Prints your Pwd as an Scp Spec, with your Home spelled as '~'.

    $ .pwd
    + printf "%s\n" "$(id -un ... hostname ... dirs -p ...
    jqdoe@example.com:~/Public/pylitfun/

Paste it into an 'scp' at your other machine, and it's already correct.

### [sh/.python](./.python)

Launches the Python Repl.

    $ .python
    + python3 -i -c ''
    >>>

The '-i -c' skips the three-Line banner, so the '>>>' lands where your eyes already are.

### [sh/.rm](./.rm)

Moves a File or Folder into your Desktop, instead of deleting it.

    $ .rm t.txt
    + mv -i t.txt /Users/jqdoe/Desktop/.

The stock 'rm' has no undo. This one thanks the File for its service and sets it aside, and the undo is a drag out of your Desktop.

### [sh/.screen](./.screen)

Reconnects to your detached Screen, or given a label launches a new Screen that logs every byte at once to a File named by that label.

    $ .screen alfa bash
    + echo 'logfile alfa.screen'
    + echo 'logfile flush 0'
    + T=alfa
    + screen -S alfa -L -c alfa.cfg bash

The 'flush 0' means a dropped connection loses nothing, and '.screen' alone gets you back in.

### [sh/.sed](./.sed)

Rewrites your Os Copy/Paste Clipboard Buffer, wrapping the last Column of each Line as '-- word --'.

    $ .sed
    + pbpaste
    + awk '{print $NF}'
    + sed 's,^,-- ,'
    + sed 's,$, --,'
    + pbcopy

This can encourage you to add file-by-file commentary into a Git Commit Message. The default draft Message presents the 'Changes to be committed' as a table whose last Column is Pathnames. This Script grabs that Column and places it inside of '-- ... --'.

### [sh/.seq](./.seq)

Scrolls the whole Screen up into the Scrollback and leaves the Screen empty.

    $ .seq
    + seq 23
    + printf '\e[H''\e[J'

Unlike 'clear', nothing is lost: what was on your Screen is one scroll away.

### [sh/.sh](./.sh)

Runs an Sh that reads none of your Profile or Rc Files, inside an empty Environment.

    $ .sh
    + env -i 'PS1=sh \$ ' sh -p
    sh $

When a thing works here and fails in your own Shell, the bug is in your own Rc Files, and you've just proved it.

### [sh/.sort](./.sort)

Calls Sort, but in the C Locale.

    $ printf 'b\nA\na\n' |.sort
    + LC_ALL=C
    + sort
    A
    a
    b

Sorted this way, macOS and Linux agree, and 'uniq' and 'comm' and 'join' agree with 'sort'.

<!-- todo: add sh/.comm and sh/.join, if we want -->

### [sh/.ssh](./.ssh)

Calls Ssh, but reading no Config and no Known Hosts, and forwarding your Ssh Agent.

    $ .ssh example.com
    + ssh -A -t -F /dev/null -o 'UserKnownHostsFile /dev/null' -o 'StrictHostKeyChecking no' -o 'LogLevel QUIET' jqdoe@example.com

When a thing works here and fails when you just call Ssh itself, then the bug is in some configuration file, odds on your own ~/.ssh/config file, and you've just proved it.

### [sh/.tail](./.tail)

Shows the bottom of the input, cut to fit your Screen.

    $ .tail <t.txt
    + tail -21

Fills the Screen and no more, so the top Line of the output hasn't scrolled away before you read it.

### [sh/.uniq](./.uniq)

Calls Uniq, but in the C Locale.

    $ printf 'a\na\nb\n' |.uniq
    + LC_ALL=C
    + uniq
    a
    b

Paired with '.sort', so the two agree on what is equal.

### [sh/.valid](./.valid)

Says when your Ssh Certs expire.

    $ .valid
    + ssh-add -l
    256 SHA256:AbCdEf... jqdoe@example.com (ED25519-CERT)
    + ssh-add -L
    + grep -- -jqdoe
    + ssh-keygen -L -f -
    + date
    Sun Sep  6 13:01:30 PDT 2026
    + grep Valid
            Valid: from 2026-09-06T06:00:00 to 2026-09-07T06:00:00

Prints today's date beside the expiry, so you learn the Cert is dying before the next 'ssh' tells you.

### [sh/.vim](./.vim)

Runs Vim, but reads none of your Vimrc.

    $ .vim t.txt
    + vim -u /dev/null t.txt

Vim as if you'd never customized it, which is how you check whether the bug is yours.

### [sh/.which](./.which)

Calls Which with '-a', and spells your Home as '~'.

    $ .which python3
    + which -a python3 |awk -v HOME=... '(index ...){ "~" substr ...; next} 1'
    /usr/local/bin/python3
    /usr/bin/python3

Shows every copy in your Shell Path, not just the first, so you can see the one hiding the others.

### [sh/.zsh](./.zsh)

Runs a Zsh that reads none of your Rc Files, inside an empty Environment.

    $ .zsh
    + env -i 'PS1=zsh %# ' TERM=xterm-256color zsh -f
    zsh %

The third clean room, beside '.bash' and '.sh', for when Zsh is the Shell in question.

### [sh/@](./@)

Runs a Command inside some other Folder, without moving your own Pwd.

    $ @ /usr pwd
    + cd /usr
    + pwd
    /usr

No 'cd' there, no 'cd -' back, and no chance of forgetting the second half.

### [sh/cv](./cv)

The same Script as 'pb', under a name for hands that reach for ⌃C and ⌃V.

    $ echo alfa |cv
    + if [ -t 0 ... -t 1 ... then pbpaste ...; else pbcopy ...
    $ cv
    + if [ -t 0 ... -t 1 ... then pbpaste ...; else pbcopy ...
    alfa

At the front of a Pipe it pastes, at the back it copies, and in the middle it does both.

### [sh/d](./d)

Compares ./a against ./b, or ./a against one File, or any Files and Folders against any others.

    $ d
    + diff -brpu a b
    --- a	2026-09-06 13:01:31
    +++ b	2026-09-06 13:01:31
    @@ -1,2 +1,2 @@ alfa
     alfa
    -bravo
    +charlie

Name two scratch Files 'a' and 'b' and the diff is one keystroke, and the '-brpu' ignores whitespace, recurses, names the Function, and speaks unified.

### [sh/e](./e)

Runs the Homebrew Emacs in the Terminal with less noise, and with no Args edits your Os Copy/Paste Clipboard Buffer.

    $ e
    + pbpaste
    + /opt/homebrew/bin/emacs --no-splash -nw --eval '(menu-bar-mode -1)' ./pb
    + pbcopy

Copy some text, type 'e', edit, quit, paste: the Clipboard was the File all along.

### [sh/emacs](./emacs)

Finds the Homebrew Emacs and runs it.

    $ emacs t.txt
    + /opt/homebrew/bin/emacs t.txt

macOS stopped shipping Emacs, since Oct/2019 macOS Catalina, leaving you with only 'mg'. This Script puts the name back, at the back of your Shell Path where it fills the gap and disturbs nothing.

### [sh/f](./f)

Calls Find, but with no Args searches the Pwd.

    $ f
    + find .
    .
    ./t.txt

Called with no Args, the stock 'find' on macOS prints its usage and quits, where 'f' prints the tree.

### [sh/m](./m)

The same Script as '.make', under a name one letter long.

    $ m
    + make

You type it more often than you type anything else, so it's the shortest name here.

### [sh/md5sum](./md5sum)

Calls OpenSsl to speak like the Linux 'md5sum'.

    $ echo hi |md5sum
    + openssl dgst -md5 -r
    + sed 's,[*]stdin$,*-,'
    + sed 's,[*], ,'
    764efa883dda1e11db47671c4a3bbd9e  -

The output matches Linux byte for byte, two Spaces and the '-' for Stdin included, so a checksum you paste between Hosts compares equal.

### [sh/pb](./pb)

Edits your Os Copy/Paste Clipboard Buffer: pastes at the front of a Pipe, copies at the back, and in the middle copies, waits for end-of-file, and passes the bytes along.

    $ .ls |pb
    + if [ -t 0 ... -t 1 ... then pbpaste ...; else pbcopy ...
    $ pb |wc -l
    + if [ -t 0 ... -t 1 ... then pbpaste ...; else pbcopy ...
           4

You type 'pb' wherever you like and never again stop to remember which of 'pbpaste' and 'pbcopy' you meant, and '|pb|' is '|sponge|' with nothing to install.

### [sh/pwnme](./pwnme)

Brings this Git Clone up to date, from wherever you call it, and shows the last three Commits before and after.

    $ sh/pwnme

    + cd /Users/jqdoe/Public/pylitfun/
    + :
    + git log --oneline --no-decorate -3
    2cb7c4d sh/.sh: Revive its correct prompt of 'sh $ '.
    70671dc sh/_: Revive what it always was, before collab with Claude, and fixup sh/.cat too
    fbffccb sh/.fmt = Call '|fmt' but wrap Lines to fit Screen width, where sh/.cut would truncate them
    + :
    + git fetch --prune --prune-tags --force
    + git rebase
    Current branch main is up to date.
    + :
    + git log --oneline --no-decorate -3
    2cb7c4d sh/.sh: Revive its correct prompt of 'sh $ '.
    70671dc sh/_: Revive what it always was, before collab with Claude, and fixup sh/.cat too
    fbffccb sh/.fmt = Call '|fmt' but wrap Lines to fit Screen width, where sh/.cut would truncate them

The two 'git log' Lines say what the 'git rebase' did to you, and 'make bin' keeps this one out of your Shell Path by name, because each of its sibling Repos carries a 'pwnme' of its own.

### [sh/sha256sum](./sha256sum)

Calls OpenSsl to speak like the Linux 'sha256sum'.

    $ sha256sum t.txt
    + openssl dgst -sha256 -r t.txt
    + sed 's,[*]stdin$,*-,'
    + sed 's,[*], ,'
    154d5d238d27461c33398f3766ca2da78969f6ca0415f05392dfa6aebfda47d7  t.txt

The same Script as 'md5sum' with one word changed, and the same byte-for-byte match with Linux.

### [sh/tac](./tac)

Calls 'tail -r' to speak like the Linux 'tac'.

    $ tac t.txt
    + tail -r t.txt
    delta echo

    alfa bravo charlie

macOS has 'tail -r' and no 'tac', Linux has 'tac' and no 'tail -r', and this makes the one name work at both.

### [sh/v](./v)

Runs Vim, and with no Args edits your Os Copy/Paste Clipboard Buffer.

    $ v
    + pbpaste
    + vim ./pb
    + pbcopy

Copy some text, type 'v', edit, quit, paste: the same trick as 'e', for the other editor.


<!--

# all read by me, at least once
# written, especially the Appendix, with help from:  Claude·Ai Fable 5.1

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/sh/sh-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
