# pylitfun / ... / litgit-readme.md

**Abbreviated Git verbs that guess the rest, and then show you what they guessed**

Every verb here is 1 to 5 letters starting with 'g'. Typing one is an ask for a guess

We print the whole Shell Line before we run it, so you can read our guess and correct it


## What we guess

| Verbs | We Guess | When |
|---|---|---|
| gcaf gcf | HEAD | no Pos Args before "--" |
| gcam | more of a wip message | git diff is truthy |
| gco | a "-" | no Args at all |
| gf | --quiet | no Options and no "--" |
| gg | git status, not git grep | no Pos Args before "--" |
| gg ggi ggl | -ai -e ... -e ... | >= 1 Pos Arg before "--" |
| gl gla glq glqn gls glv | --color-moved | >= 1 Option |
| gl glq glqn glv | -1 for gl, -9 for glq glqn glv | no Options and no "--" |
| gl glq glqn gls glv | --author=<user.email> | a bare --author Arg |
| gla | --author=<user.email> | no Pos Args before "--" |
| gla | --author=<first Pos Arg> | >= 1 Pos Arg before "--" |
| glf | \|grep -ai -e ... -e ... | Pos Args and Pos Args only |
| gno | gdno over gspno | no Args at all, and git diff is truthy |
| gno | gspno over gdno | >= 1 Sh Arg |
| gri grias | HEAD~N | 1 Arg, a bare 1..9 |

Note: We guess -19 in place of -9 when the Terminal Size is Portrait


## Words we use

**Option** is an Arg that starts with a Dash and is not a run of Dashes. So -p and --author=x are
Options. A lone - is not, and neither is ---

**"--"** is the Separator. It is never an Option and never a Pos Arg

**Pos Arg** is every other Arg, before or after the "--"

A Pos Arg after the "--" is a **Pathspec**. It counts as a Pos Arg, and it never serves as the Rev,
the Author, or the Pattern we would otherwise guess

**Portrait** is Columns < 2 * Rows. A monospaced cell runs about twice as tall as it is wide, so
50 Columns x 25 Rows is the square. Ties go to Landscape, because Landscape is the commoner shape


## Why the counts are what they are

We guess a count only to fill about one screen

-1 is gl, because one --pretty=fuller commit fills a screen by itself

-9 is every --oneline verb, because nine of those lines fill a screen

-19 in place of -9 when the window is Portrait, because a tall window holds more lines

We ask whether Stdout is a Tty only for the --oneline verbs, because only their count turns on the
shape of the window. One commit is one commit at any size, so gl takes its -1 down a pipe too

The --numstat verbs take no count, ever. gla and gls are filters, not windows. The other verbs
answer what just happened, and a --numstat verb answers how much changed across a stretch you
choose for yourself


<!--

Written with help from Claude·Ai

-->

<!--

# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/litgit-readme.md
# copied from:  git clone https://github.com/pelavarre/pylitfun.git

-->
