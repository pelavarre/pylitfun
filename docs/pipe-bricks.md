# pipe-bricks.md

Contents

1. Welcome
2. Input
3. Terminal Console Transcript
4. Quick Install
5. Get It?
6. A Small Alphabet of Bricks

WELCOME

You build your Shell Pipes from Bricks, often spoken of (in four syllables) as Shell Pipe Filters

We make simple Bricks easy quick for you to deploy. You strike a single letter Key to run a copy of the Brick. Your radically abbreviated Shell Pipes look like this

INPUT

    echo Hello Shell Pipe Filter Brick World |pbcopy
    pbpaste

    0
    0 upper
    1
    1

TERMINAL CONSOLE TRANSCRIPT

    % echo Hello Shell Pipe Filter Brick World |pbcopy |pbcopy
    %
    % pbpaste
    Hello Shell Pipe Filter Brick World
    %

    % 0
    Hello Shell Pipe Filter Brick World
    % 0 upper
    HELLO SHELL PIPE FILTER BRICK WORLD
    % 1
    Hello Shell Pipe Filter Brick World
    % 1
    HELLO SHELL PIPE FILTER BRICK WORLD
    %

QUICK INSTALL

This is conventional, and it works

    git clone https://github.com/pelavarre/pylitfun.git
    cd pylitfun/
    export PATH="$PATH:$PWD/bin:$PWD"
    which 0

It's not the simplest lightest touch that works

GET IT?

Have you tried these out? These are easy to show and hard to explain

These run like a simple classic four-level Stack Machine

Each Cell of the Stack is a Revision of your Os Copy/Paste Clipboard Buffer

You strike the 0 Key and press Return to copy the Buffer into a File named ./0

You say 1 or 2 or 3 instead to copy an old Revision into ./0 and into the Os Buffer. Except first the Revisions all shuffle down deeper into the Stack. Whatever you had at ./0 becomes ./1, and ./1 becomes ./2, and ./2 becomes the ./3 File. Whatever was at ./3 is lost

You saying 0 and nothing more works like the DUP of an HP or Forth Stack Machine. You saying 0 and some more stuff says what Bricks to run for you and drop the result into the ./0 File, except first the Revisions all shuffle down deeper into the Stack. You saying 1 or 2 or 3 and some more stuff says what Bricks to run before replacing the ./0 File

When you want to peek at a Revision without disturbing the Stack, you say to pipe the Revision in the classic fiddly way

    1 |cat -

AN ALPHABET OF BRICKS

    _ is for >/dev/null

    0 ... is for mv 2 3 && mv 1 2 && mv 0 1 && touch 0 && (pbpaste |... |pbcopy) >0
    1 ... is for (cat 1 |pbcopy) && mv 2 3 && mv 1 2 && mv 0 1 && touch 0 && (pbpaste |... |pbcopy) >0
    2 ... is for (cat 2 |pbcopy) && mv 2 3 && mv 1 2 && mv 0 1 && touch 0 && (pbpaste |... |pbcopy) >0
    3 ... is for (cat 3 |pbcopy) && mv 2 3 && mv 1 2 && mv 0 1 && touch 0 && (pbpaste |... |pbcopy) >0

    a is for |awk 'NF{print $NF}'
    b
    c
    d
    e

    f
    g is for |grep -ai -e ... -e ...  # but we ship that outside of |pb g as our |g
    h is for |head -9
    i is for |tr ' ' '\n', as in split words
    j is for |jq .  # maybe

    k is for |less -FIRX  # todo
    l
    m
    n is for |nl -pba -v0 |expand, but accepts -v1
    o is for dropping a blank frame if present, as if rounding off ← ↑ → ↓ corners

    p
    q
    r is for |tac or |tail -r
    s is for |LC_ALL=C sort or for LC_ALL=C sort -n
    t is for |tail -9

    u is for |awk '!d[$0]++' or for |uniq -c |expand
    v
    w is for |wc -l
    x is for |xargs
    y
    z

    F is for |python str.casefold
    L is for |python str.lower
    O is for |python denting ← ↑ → ↓ with a blank frame
    T is for |python str.title
    U is for |python str.upper

    . is for to guess what to do

AN ALPHABET OF SHELL ALIASES

We put these into our bin/ Folder as Shell Scripts named by single letters

    _ is for cat - >/dev/null

    a
    b is for env -i PS1='bash \$ ' bash --noprofile --norc
    c
    d is for diff -brpu a b
    e is for emacs -nw --no-splash --eval '(menu-bar-mode -1)', or emacs ... -Q

    f is for find .
    g is for git.py, but |g is for grep.py
    h
    i
    j

    k
    l could be for ls -hlAF -rt, but much Linux tradition is alias l='ls -CF'
    m is for make
    n
    o

    p is for python.py -i -c ''  # but with automagic imports
    q
    r
    s
    t

    u
    v is for vim, or vim -u /dev/null
    w is often occupied by /usr/bin/w
    x
    y
    z is for env -i PS1='zsh %# ' TERM=$TERM zsh -f

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/docs/pipe-bricks.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
