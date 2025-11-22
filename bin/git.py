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

import difflib
import os
import pathlib
import shlex
import signal
import subprocess
import sys

from pylitfun import litshell

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


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
    "gf": "git fetch --prune --prune-tags --force",
    "gg": "git grep ...",  # -ai -e ... -e ...
    "gg0": "git status",  # shown in the Shell as 'gg' without Sh Args
    "ggl": "git grep -l ...",  # -ai -e ... -e ...
    "gl": "git log --pretty=fuller --no-decorate [...]",
    "glf": "git ls-files |grep [...]",  # |grep -ai -e ... -e ...
    "glq": "git log --oneline --no-decorate [...]",
    "gls": "git log --pretty=fuller --no-decorate --numstat [...]",
    "glv": "git log --oneline --decorate [...]",
    "gno": "git show --pretty= --name-only [...]",  # cuts back to truthy 'qdno' when available
    "grh": "git reset --hard ...",  # actual no args 'git reset hard' would mean to Head
    "grh1": "git reset HEAD~1",  # inverts : gcam && git commit --all -m wip
    "grhu": "... && git reset --hard @{upstream}",
    "gri": "git rebase -i [...]",
    "grias": "git rebase -i --autosquash [...]",
    "grl": "git reflog --date=relative --numstat",
    "grv": r'''echo git clone "$(git remote -v |tr ' \t' '\n' |grep : |uniq)"''',
    "gs": "git show --color-moved [...]",
    "gsis": "git status --ignored --short",
    "gspno": "git show --pretty= --name-only [...]",
}


a = list(shline_by_shverb.keys())
b = sorted(a)
diffs = list(difflib.unified_diff(a=a, b=b, fromfile="a", tofile="b", lineterm=""))
assert not diffs, (diffs,)


# Expand the Shell Verb as a Git Alias

incoming_shargv = litshell.sys_argv_partition(default="g")

shverb = incoming_shargv[0]
if shverb == "gg":  # 'git status' without args, or 'git grep' with args
    if not incoming_shargv[1:]:
        shverb = "gg0"


git_shverbs = tuple(shline_by_shverb.keys())
if shverb not in git_shverbs:
    print(f"don't choose {shverb!r}, do choose from {list(git_shverbs)}", file=sys.stderr)
    sys.exit(2)  # exits 2 for bad args


# Require Args, or allow Args, or reject Args

shline = shline_by_shverb[shverb]

if shline.endswith(" ..."):  # ga, gcp, gg, ggl, grh
    required_args_usage = f"usage: {shverb} ..."

    arguable_shline_0 = shline.removesuffix(" ...")
    shsuffix = " ..."

    if not incoming_shargv[1:]:
        print(required_args_usage, file=sys.stderr)
        sys.exit(2)  # exits 2 for bad args

elif shline.endswith(" [...]"):  # gd, gdno, gl, glf, glq, gls, glv, gno, gri, grias, gs, gspno
    optional_args_usage = f"usage: {shverb} [...]"

    arguable_shline_0 = shline.removesuffix(" [...]")
    shsuffix = " ..." if incoming_shargv[1:] else ""

else:  # g, gb, gcaa, gcam, gda, gdh, gf, grh1, grl, grv, gsis
    no_args_usage = f"usage: {shverb}"

    arguable_shline_0 = shline
    shsuffix = ""

    if incoming_shargv[1:]:
        print(no_args_usage, file=sys.stderr)
        sys.exit(2)  # exits 2 for bad args


# Choose to call Git through Shell, else directly

arguable_shline_1 = arguable_shline_0
shell = False

if shverb == "grv":
    assert '"$(' in arguable_shline_0, (arguable_shline_0,)
    shell = True

elif shverb == "glf":
    assert arguable_shline_0 == "git ls-files |grep"
    if not incoming_shargv[1:]:
        arguable_shline_1 = "git ls-files"
    else:
        assert " |" in arguable_shline_0, (arguable_shline_0,)
        shell = True

    # todo: learn to operate 'glf' and 'grv' without 'shell=True'


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
        print(f"# {shverb!r} not at:  cd {relpath}/", file=sys.stderr)


# Expand 'gno' differently while 'git diff --name-only' truthy

expanded_shverb = shverb
expanded_shline_n1 = arguable_shline_1

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
            expanded_shline_n1 = gdno_shline


# Pause for affirmation

expanded_shline_0 = expanded_shline_n1
taggable_shline_0 = expanded_shline_n1

if expanded_shline_n1.startswith("... && "):
    expanded_shline_0 = expanded_shline_n1.removeprefix("... && ")
    taggable_shline_0 = "echo Press ⌃D && cat - >/dev/null && " + expanded_shline_0

    print(f"Press ⌃D to auth:  {expanded_shline_0}", file=sys.stderr)
    assert int(0x80 + signal.SIGINT) == 130
    try:
        sys.stdin.read()
    except KeyboardInterrupt:
        sys.exit(130)


# Decorate the the incoming Sh ArgV extensively, for 'gg', 'ggl', and 'glf'

expanded_shline_1 = expanded_shline_0
taggable_shline_1 = taggable_shline_0
shargv = tuple(incoming_shargv)  # because 'better copied than aliased'

if not incoming_shargv[1:]:
    assert shverb not in ("gg", "ggl"), (shverb, incoming_shargv)
elif shverb in ("gg", "ggl"):
    shargv = (shargv[0],) + litshell.grep_expand_ae_i(incoming_shargv[1:])
elif shverb == "glf":
    assert taggable_shline_0 == expanded_shline_n1, (taggable_shline_0, expanded_shline_n1)
    grep_shargv_1 = litshell.grep_expand_ae_i(incoming_shargv[1:])
    grep_shargv_1_join = " ".join(shlex.quote(_) for _ in grep_shargv_1[1:])

    expanded_shline_1 = expanded_shline_n1 + " " + grep_shargv_1_join
    taggable_shline_1 = taggable_shline_0 + " " + grep_shargv_1_join
    shargv = tuple()

# Show the expansion of the Git Alias, on screen before running it
# todo: Shrink back down such voluminous expanded ShArgV as *.py

shargv_join = " ".join(shlex.quote(_) for _ in shargv[1:])  # less quote marks than shlex.join
tagged_shline = f": {expanded_shverb}{shsuffix} && {taggable_shline_1} {shargv_join}".rstrip()
print(tagged_shline, file=sys.stderr)  # not ("+",  # not ("|" +


# Run the expansion of the Git Alias

shline = expanded_shline_1
argv = shlex.split(expanded_shline_1) + list(shargv[1:])

if shell:
    assert shverb != "gcaa", (shverb, shell, expanded_shline_1)

    run = subprocess.run(shline, shell=True)
    if run.returncode:
        print("+ exit", run.returncode, file=sys.stderr)

    sys.exit(run.returncode)

run = subprocess.run(argv)
if run.returncode:
    print("+ exit", run.returncode, file=sys.stderr)

    # Help recover when 'git commit' loses its input file

    if shverb == "gcaa":
        print("+ cat .git/COMMIT_EDITMSG", file=sys.stderr)

        path = pathlib.Path(".git/COMMIT_EDITMSG")
        text = path.read_text()

        sys.stderr.flush()
        print(text)
        sys.stdout.flush()
        print("+", file=sys.stderr)

        print("Press ⌃D", file=sys.stderr)
        assert int(0x80 + signal.SIGINT) == 130
        try:
            sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(130)

        print("+ exit", run.returncode, file=sys.stderr)  # repeat from above

sys.exit(run.returncode)


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/git.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
