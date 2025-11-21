#!/usr/bin/env python3

"""
usage: git.py [--shfile=SHFILE] [SHWORD ...]

abbreviate the subcommands to call Git, but do show them

positional arguments:
  SHWORD           option or positional argument of Git

options:
  --help           show this help message and exit (-h is for Git, not for Git·Py)
  --shfile SHFILE  which Git Alias to decode

examples:
  gcaa
  git.py --shfile=$HOME/bin/gcaa
  : gcaa && git commit --all --amend
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard

import os
import shlex
import signal
import subprocess
import sys

from pylitfun import litshell

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


# Define two dozen and more everyday Git Aliases

shline_by_shverb = {
    "g": "git checkout",
    "ga": "git add ...",
    "gb": "git branch --sort=committerdate",
    "gcaa": "git commit --all --amend",
    "gcam": "git commit --all -m wip",  # inverts : grh1 && git reset HEAD~1
    "gcl": "... && git clean -dffxq",
    "gcp": "git cherry-pick ...",
    "gd": "git diff --color-moved [...]",
    "gda": "git describe --always --dirty",
    "gdh": "git diff --color-moved HEAD~1",
    "gdno": "git diff --name-only [...]",
    "gg": "git grep ...",  # -ai -e ... -e ...
    "ggl": "git grep -l ...",  # -ai -e ... -e ...
    "gf": "git fetch --prune --prune-tags --force",
    "gl": "git log --pretty=fuller --no-decorate [...]",
    "glf": "git ls-files ...",  # |grep -ai -e ... -e ...
    "gls": "git log --pretty=fuller --no-decorate --numstat [...]",
    "glq": "git log --oneline --no-decorate [...]",
    "glv": "git log --oneline --decorate [...]",
    "gno": "git show --pretty= --name-only [...]",  # cuts back to truthy 'qdno' when available
    "gri": "git rebase -i [...]",
    "grias": "git rebase -i --autosquash [...]",
    "gspno": "git show --pretty= --name-only [...]",
    "grh": "git reset --hard ...",  # actual no args 'git reset hard' would mean to Head
    "grh1": "git reset HEAD~1",  # inverts : gcam && git commit --all -m wip
    "grhu": "... && git reset --hard @{upstream}",
    "grl": "git reflog --date=relative --numstat",
    "grv": r'''echo git clone "$(git remote -v |tr ' \t' '\n' |grep : |uniq)"''',
    "gs": "git show --color-moved [...]",
    "gsis": "git status --ignored --short",
}


# Expand the Shell Verb as a Git Alias

incoming_shargv = litshell.sys_argv_partition(default="g")
shverb = incoming_shargv[0]

git_shverbs = tuple(shline_by_shverb.keys())
if shverb not in git_shverbs:
    print(f"don't choose {shverb!r}, do choose from {list(git_shverbs)}", file=sys.stderr)
    sys.exit(2)  # exits 2 for bad args


# Require Args, or allow Args, or reject Args

shline = shline_by_shverb[shverb]

if shline.endswith(" ..."):
    required_args_usage = f"usage: {shverb} ..."

    arguable_shline = shline.removesuffix(" ...")
    shsuffix = " ..."

    if not incoming_shargv[1:]:
        print(required_args_usage, file=sys.stderr)
        sys.exit(2)  # exits 2 for bad args

elif shline.endswith(" [...]"):
    optional_args_usage = f"usage: {shverb} [...]"

    arguable_shline = shline.removesuffix(" [...]")
    shsuffix = " ..." if incoming_shargv[1:] else ""

else:
    no_args_usage = f"usage: {shverb}"

    arguable_shline = shline
    shsuffix = ""

    if incoming_shargv[1:]:
        print(no_args_usage, file=sys.stderr)
        sys.exit(2)  # exits 2 for bad args


# Fail fast when called outside of a Git Clone

gpwd_shline = "git rev-parse --show-toplevel"

run = subprocess.run(
    shlex.split(gpwd_shline),
    stdin=None,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,  # small 2 Lines vs like 129 Lines from "git diff"
)

if run.returncode:
    print(f": gpwd && {gpwd_shline}", file=sys.stderr)
    sys.stderr.write(run.stdout.decode())  # written to Stderr, and commonly empty
    sys.stderr.write(run.stderr.decode())
    print(f"+ exit {run.returncode}", file=sys.stderr)

    sys.exit(run.returncode)


# Sometimes mention it, when Git runs outside of the top-level of a Git Clone

gpwd = run.stdout.decode().rstrip()
relpath = os.path.relpath(gpwd)
if gpwd != os.getcwd():
    if shverb in ("ga", "gcl", "glf"):
        print(f"# {shverb!r} not at: cd {relpath}/", file=sys.stderr)


# Expand 'gno' differently while 'git diff --name-only' truthy

expanded_shverb = shverb
expanded_shline = arguable_shline

if shverb == "gno":
    expanded_shverb = "gspno"
    if not shsuffix:
        gdno_shline = "git diff --name-only"
        run = subprocess.run(
            shlex.split(gdno_shline),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if run.returncode or run.stderr:
            print(f": gdno && {gdno_shline} && ...", file=sys.stderr)
            sys.stderr.write(run.stdout.decode())  # written to Stderr, and commonly empty
            sys.stderr.write(run.stderr.decode())
            print(f"+ exit {run.returncode}", file=sys.stderr)

            sys.exit(run.returncode)

        if run.stdout:
            expanded_shverb = "gdno"
            expanded_shline = gdno_shline


# Pause for affirmation

assert int(0x80 + signal.SIGINT) == 130

taggable_shline = expanded_shline
if expanded_shline.startswith("... && "):
    expanded_shline = expanded_shline.removeprefix("... && ")
    taggable_shline = "echo Press ⌃D && cat - >/dev/null && " + expanded_shline

    print(f"Press ⌃D to run:  {expanded_shline}", file=sys.stderr)
    try:
        sys.stdin.readline()
    except KeyboardInterrupt:
        sys.exit(130)


# Decorate the the incoming Sh ArgV extensively, for 'gg', 'ggl', and 'glf'

shargv = tuple(incoming_shargv)  # because 'better copied than aliased'
if shverb in ("gg", "ggl", "glf"):
    shargv = (shargv[0],) + litshell.grep_expand_ae_i(incoming_shargv[1:])


# Show the expansion of the Git Alias, on screen before running it
# todo: Shrink back down such voluminous expanded ShArgV as *.py

shargv_join = " ".join(shlex.quote(_) for _ in shargv[1:])  # less quote marks than shlex.join
tagged_shline = f": {expanded_shverb}{shsuffix} && {taggable_shline} {shargv_join}".rstrip()
print(tagged_shline, file=sys.stderr)  # not ("+",  # not ("|" +


# Run the expansion of the Git Alias

if "(" in expanded_shline:
    assert "..." not in expanded_shline, (expanded_shline, shverb)
    litshell.exit_after_shell(expanded_shline)

alt_sys_argv = shlex.split(expanded_shline) + list(shargv[1:])
litshell.exit_after_run(alt_sys_argv)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/git.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
