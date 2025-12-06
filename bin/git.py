#!/usr/bin/env python3

"""
usage: git.py [--help] [--shfile SHFILE] [SHWORD ...]

abbreviate the subcommands to call Git, but do show them in full

positional arguments:
  SHWORD           option or positional argument of Git

options:
  --help           show this help message and exit (-h is for Git, not for Git·Py)
  --shfile SHFILE  a filename as the Git alias to decode (default: '/dev/null/g')

examples:
  gg -w gg ggl
  git.py --shfile=~/gg -w gg ggl
  : gg ... && git grep -ai -w -e gg -e ggl
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import __main__
import difflib
import os
import pathlib
import shlex
import signal
import subprocess
import sys
import typing

if not __debug__:
    raise NotImplementedError([__debug__])  # because 'python3 better than python3 -O'


assert int(0x80 + signal.SIGINT) == 130


# Disclose nearly three dozen everyday Git Idioms

ShlinePlusByShverb = {  # sorted by key
    # 0
    "g": "git status --short [...]",
    "ga": "git add ...",
    "gb": "git branch --sort=committerdate",
    "gcaa": "git commit --all --amend",
    "gcaf": "git commit --all --fixup [...]",
    # 5
    "gcam": "git commit --all -m wip",  # inverts : grh1 && git reset HEAD~1
    "gcf": "git commit --fixup [...]",
    "gcl": "... && git clean -dffxq",
    "gcp": "git cherry-pick ...",
    "gd": "git diff --color-moved [...]",
    "gda": "git describe --always --dirty",
    # 10
    "gdh": "git diff --color-moved HEAD~1",
    "gdno": "git diff --name-only [...]",
    "gf": "git fetch --prune --prune-tags --force",
    "gg/0": "git status",  # in Shell as 'gg' without Sh Args
    "gg/n": "git grep ...",  # -ai -e ... -e ...  # in Shell as 'gg' with Sh Args
    # 15
    "ggl": "git grep -l ...",  # -ai -e ... -e ...
    "gl": "git log --pretty=fuller --no-decorate [...]",
    "glf": "git ls-files |grep ...",  # |grep -ai -e ... -e ...
    "glq": "git log --oneline --no-decorate [...]",
    "gls": "git log --pretty=fuller --no-decorate --numstat [...]",
    # 20
    "glv": "git log --oneline --decorate [...]",
    "gno": "git diff/show --pretty= --name-only [...]",  # 'qdno' when truthy, else 'qspno'
    "grh": "git reset --hard ...",  # actual no args 'git reset hard' would mean to Head
    "grh1": "git reset HEAD~1",  # inverts : gcam && git commit --all -m wip
    "grhu": "... && git reset --hard @{upstream}",
    # 25
    "gri": "git rebase -i [...]",
    "grias": "git rebase -i --autosquash [...]",
    "grl": "git reflog --date=relative --numstat",
    "grv": r"git remote -v |tr ' \t' '\n' |grep : |uniq |sed 's,^,git clone ,'",
    "gs": "git show --color-moved [...]",
    # 30
    "gsis": "git status --ignored --short",
    "gspno": "git show --pretty= --name-only [...]",
    # 32
}

# no 'git checkout' on purpose:  without args it cancels cherry-pick and hides rebase

# todo: add:  git checkout -, git push, git rebase, local/remote mkdir/rmdir of git branches, ...
# todo: something less ugly than "gg/0": and "gg/n"?


_a_ = list(ShlinePlusByShverb.keys())
_b_ = sorted(_a_)
_diffs_ = list(difflib.unified_diff(a=_a_, b=_b_, fromfile="a", tofile="b", lineterm=""))
if _diffs_:
    print("\n".join(_diffs_), file=sys.stderr)
assert not _diffs_, (_diffs_,)


def main() -> None:

    gg = GitGopher()
    gg.go_for_it()


class GitGopher:

    def go_for_it(self) -> None:

        # Fail if no Shell Args

        if not sys.argv[1:]:
            print("usage: git.py [--help] [--shfile SHFILE] [SHWORD ...]", file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        # Find the Shell Verb and the Shell Args after it

        self.exit_if_dash_dash_help()

        shfile_shargv = self.dash_dash_shfile_shargv(sys.argv, default="/dev/null/g")

        shverb = os.path.basename(shfile_shargv[0])
        assert shverb, (shfile_shargv, shverb)
        shverb_shargv = (shverb, *shfile_shargv[1:])

        chosen_shverb = self.form_shverb_for_shargv(shverb_shargv)
        chosen_shargv = (chosen_shverb, *shverb_shargv[1:])

        # Replace the Shell Verb with a Git Shell Line, and edit the Args

        (found_shline, given_shsuffix) = self.form_shverb_shline(chosen_shargv)
        grep_shargv = self.shargv_at_grep(chosen_shverb, shargv=chosen_shargv)

        # Choose to call Git through Shell or not

        (shell, shell_shline) = self.form_shell_shline(
            chosen_shverb, shline=found_shline, given_shsuffix=given_shsuffix
        )

        # Take the Shell Pwd & Git Diff into account

        gtop = self.find_git_top(default=None)

        relpath = os.path.relpath(gtop)
        if gtop != os.getcwd():
            if chosen_shverb in ("ga", "gcl", "glf"):
                print(f"# {chosen_shverb!r} not at:  cd {relpath}/", file=sys.stderr)

        (diff_shverb, diff_shline) = self.shline_at_git_diff(
            chosen_shverb, shline=shell_shline, grep_shargv=grep_shargv
        )

        diff_shargv = (diff_shverb, *grep_shargv[1:])

        # Explicitly auth the especially destructive ops

        (authed, taggable) = self.auth_git_shline(diff_shline)
        run_shargv = shlex.split(authed) + list(diff_shargv[1:])

        # Shove back on Python ShLex Quote fussily quoting mentions of HEAD~1 to no purpose

        assert shlex.quote("HEAD~1") == "'HEAD~1'", (shlex.quote("HEAD~1"),)

        def like_shlex_join(argv: typing.Iterable[str]) -> str:
            return " ".join(("HEAD~1" if (_ == "HEAD~1") else shlex.quote(_)) for _ in argv)

        # Loudly promise to call the Shell now

        taggable_shargv = shlex.split(taggable) + list(diff_shargv[1:])
        taggable_shline = like_shlex_join(taggable_shargv)

        tagged_shverb = "gg" if diff_shverb in ("gg/0", "gg/n") else diff_shverb
        tagged_shline = f": {tagged_shverb}{given_shsuffix} && {taggable_shline}"

        print(tagged_shline, file=sys.stderr)  # prints its ":", not after a "+" or "|"

        # Call the Shell now

        run_shline_suffix = like_shlex_join(diff_shargv[1:])
        run_shline = authed + " " + run_shline_suffix

        if not shell:
            git_run = subprocess.run(run_shargv)
        else:
            git_run = subprocess.run(run_shline, shell=True)

        if git_run.returncode:
            print("+ exit", git_run.returncode, file=sys.stderr)

            if diff_shverb == "gcaa":
                self.rescue_git_commit_message(git_run.returncode)

        if not git_run.returncode:
            if diff_shverb == "gf":
                print("# next:  git rebase", file=sys.stderr)

        # Exit happy or sad, same as the Shell

        sys.exit(git_run.returncode)

        # todo: shrink back down such voluminous expanded ShArgV as *.py
        # todo: run without without shlex.quote

    def exit_if_dash_dash_help(self) -> None:
        """Print the Doc and exit zero, if '--help' in the Shell Args"""

        if "--help" in sys.argv[1:]:
            print(__main__.__doc__, file=sys.stderr)
            sys.exit(0)  # exits 0 after printing Help

    def dash_dash_shfile_shargv(
        self, sys_argv: typing.Iterable[str], default: str
    ) -> tuple[str, ...]:
        """Move the '--shfile FILE' into ArgV 0 when given as 1 or 2 Shell Args"""

        tuple_sys_argv = tuple(sys_argv)
        assert tuple_sys_argv, (tuple_sys_argv,)

        # Fail if no Shell Args

        default_shargv = (default, *tuple_sys_argv[1:])
        if not tuple_sys_argv[1:]:
            return default_shargv

        # Fail if the '--shfile' option isn't the leading Shell Arg

        sys_argv_1 = tuple_sys_argv[1]
        (head, sep, tail) = sys_argv_1.partition("--shfile=")
        if head or (not sep):
            return default_shargv

        # Fail if the '--shfile' option carries no Pathname

        pathname = tail  # like from --shfile=/dev/null/g
        shargv = (pathname, *tuple_sys_argv[2:])

        if not tail:
            if not tuple_sys_argv[2:]:
                return default_shargv

            sys_argv_2 = tuple_sys_argv[1]

            pathname = sys_argv_2  # like from --shfile /dev/null/g
            shargv = (pathname, *sys.argv[3:])

        # Fail if the --shfile=Pathname carries no Basename

        shverb = os.path.basename(pathname)
        if not shverb:
            return default_shargv

        # Else succeed

        return shargv

    def form_shverb_for_shargv(self, shargv: tuple[str, ...]) -> str:
        """Take the head of the Shell ArgV as the Shell Verb"""

        shverb = shargv[0]

        shline_plus_by_shverb = ShlinePlusByShverb
        git_shverbs = tuple(shline_plus_by_shverb.keys())

        # Take 'gg' as 'gg/n', except as 'gg/0' when no obvious Positional Arguments

        alt_shverb = shverb
        if shverb == "gg":  # 'git status' without args, or 'git grep' with args
            alt_shverb = "gg/n"
            obvious_posargs = list(_ for _ in shargv[1:] if not _.startswith("-"))
            if not obvious_posargs:
                alt_shverb = "gg/0"

                # takes 'gg --ignored --short' is a kind of 'git status', not a 'git grep -ai -e'

        # Reject the Shell Verb if it has no Git Alias Expansion here

        if alt_shverb not in git_shverbs:
            print(
                f"don't choose {alt_shverb!r}, do choose from {list(git_shverbs)}", file=sys.stderr
            )
            sys.exit(2)  # exits 2 for bad args

        # Succeed

        return alt_shverb

    def form_shverb_shline(self, shargv: tuple[str, ...]) -> tuple[str, str]:
        """Expand the Shell Verb as a Git Alias, with or without Args"""

        shverb = shargv[0]

        shline_plus_by_shverb = ShlinePlusByShverb
        shverb_shline_plus = shline_plus_by_shverb[shverb]

        # Require >= 1 Shell Args
        # or else:  Accept >= 0 Shell Args, and sometimes add 1 Shell Arg
        # or else:  Accept no Shell Args, else require first Shell Arg not obviously a Positional Arg

        if shverb_shline_plus.endswith(" ..."):

            (shline, shsuffix) = self._form_shline_required_args_(shverb, shverb_shline_plus, shargv)

        elif shverb_shline_plus.endswith(" [...]"):

            (shline, shsuffix) = self._form_shline_optional_args_(shverb, shverb_shline_plus, shargv)

        else:

            (shline, shsuffix) = self._form_shline_no_leading_pos_arg_(
                shverb, shverb_shline_plus, shargv
            )

        assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
        return (shline, shsuffix)

    def _form_shline_required_args_(
        self, shverb: str, shverb_shline_plus: str, shargv: tuple[str, ...]
    ) -> tuple[str, str]:
        """Handle case where >= 1 Shell Args are required"""

        assert not shverb_shline_plus.startswith("... && "), (shverb, shverb_shline_plus)

        required_args_usage = f"usage: {shverb} ..."

        shline = shverb_shline_plus.removesuffix(" ...")
        shsuffix = " ..."

        if shverb_shline_plus == "git ls-files |grep ...":
            assert shverb == "glf", (shverb, shline)

            if not shargv[1:]:
                shline = "git ls-files"
                shsuffix = ""

                assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
                return (shline, shsuffix)

        if not shargv[1:]:

            if shverb in ("ga", "ggl"):
                gtop = self.find_git_top(default="")
                if gtop:
                    if gtop != os.getcwd():
                        print(f"# {shverb!r} not at:  cd {gtop}/", file=sys.stderr)

            print(required_args_usage, file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
        return (shline, shsuffix)

        # ga, gcp, gg/n, ggl, glf, grh

    def _form_shline_optional_args_(
        self, shverb: str, shverb_shline_plus: str, shargv: tuple[str, ...]
    ) -> tuple[str, str]:
        """Handle case where >= 0 Shell Args are accepted, and sometimes add 1 Shell Arg"""

        assert not shverb_shline_plus.startswith("... && "), (shverb, shverb_shline_plus)

        shline = shverb_shline_plus.removesuffix(" [...]")

        shsuffix = " ..."
        if not shargv[1:]:
            shsuffix = ""

            if shverb_shline_plus == "git commit --all --fixup [...]":
                assert shverb in ("gcaf",), (shverb, shline)
                shline += " HEAD"  # tilts into:  git commit --all --fixup HEAD

            elif shverb_shline_plus == "git commit --fixup [...]":
                assert shverb in ("gcf",), (shverb, shline)
                shline += " HEAD"  # tilts into:  git commit --fixup HEAD

            elif shverb_shline_plus == "git log --pretty=fuller --no-decorate [...]":
                assert shverb == "gl", (shverb, shline)
                shline += " -1"  # tilts into:  gl -1

            elif shverb_shline_plus.startswith("git log "):
                assert shverb in ("glq", "gls", "glv"), (shverb, shline)
                if shverb not in ("gls",):  # tilts into:  gls --
                    shline += " -9"  # tilts into:  glq -9, glv -9

        assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
        return (shline, shsuffix)

        # g, gcaf, gcf, gd, gdno, gg/0, gl, glf, glq, gls, glv, gno, gri, grias, gs, gspno

    def _form_shline_no_leading_pos_arg_(
        self, shverb: str, shverb_shline_plus: str, shargv: tuple[str, ...]
    ) -> tuple[str, str]:
        """Handle case where no Shell Args are accepted, or first Shell Arg must not be a Positional Arg"""

        no_arg_usage = f"usage: {shverb}"

        shsuffix = ""

        shline = shverb_shline_plus

        # Fill out some default Options, when given no Shell Args

        if not shargv[1:]:

            if shverb_shline_plus == "git fetch --prune --prune-tags --force":
                assert shverb == "gf", (shverb, shline)
                shline += " --quiet"  # tilts into:  gf --quiet

            elif shverb_shline_plus == "git reflog --date=relative --numstat":
                assert shverb == "grl", (shverb, shline)
                shline += " -9"

        # Accept no Shell Args
        # But if Shell Args, then require the first to be Not obviously Positional

        if shargv[1:]:
            shargv1 = shargv[1]

            leading_pos_arg = (shargv1 == "-") or (not shargv1.startswith("-"))

            too_many_args = leading_pos_arg
            if shverb in ("grhu", "grv"):
                too_many_args = True

            if too_many_args:
                print(no_arg_usage, file=sys.stderr)
                sys.exit(2)  # exits 2 for bad args

            # accepts: gdh -w, gf --, grl --

        return (shline, shsuffix)

        # gb, gcaa, gcam, gda, gdh, gf, gno, grh1, grhu, grl, grv, gsis

    def form_shell_shline(self, shverb: str, shline: str, given_shsuffix: str) -> tuple[bool, str]:
        """Choose to call Git by way of .shell=False or .shell=True"""

        if shverb == "glf":
            if not given_shsuffix:
                assert shline == "git ls-files", (shline, shverb)

                shell = False
                return (shell, "git ls-files")

            assert shline == "git ls-files |grep", (shline, shverb)
            assert " |" in shline, (shline, shverb)

            shell = True
            return (shell, shline)

        if shverb == "grv":
            assert " |" in shline, (shline, shverb)

            shell = True
            return (True, shline)

        assert " |" not in shline, (shline, shverb)

        shell = False
        return (shell, shline)

        # todo: operate 'glf ...' and 'grv' without 'shell=True'

    def find_git_top(self, default: str | None) -> str:
        """Find RealPath of the enclosing Git Clone, else complain & exit nonzero"""

        gtop_shline = "git rev-parse --show-toplevel"

        gtop_run = subprocess.run(
            shlex.split(gtop_shline),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # small 2 Lines here, vs like 129 Lines from "git diff"
        )

        # Exit nonzero and explain why, if Pwd not inside a Git Clone

        if gtop_run.returncode:
            if default is not None:
                return default

            print(f": gtop && {gtop_shline}", file=sys.stderr)
            sys.stderr.write(gtop_run.stdout.decode())  # written to Stderr, and commonly empty
            sys.stderr.write(gtop_run.stderr.decode())

            print(f"+ exit {gtop_run.returncode}", file=sys.stderr)

            sys.exit(gtop_run.returncode)

        # Exit nonzero and explain why, if Pwd not inside a Git Clone

        gtop = gtop_run.stdout.decode().rstrip()

        return gtop

    def shline_at_git_diff(
        self, shverb: str, shline: str, grep_shargv: tuple[str, ...]
    ) -> tuple[str, str]:
        """Change up 'gcam' and 'gno' when truthy 'git diff --name-only'"""

        shline_plus_by_shverb = ShlinePlusByShverb

        # Require 'gno' to expand to precisely accurate copies of 'gdno' and 'gspno'

        gdno_shline = shline_plus_by_shverb["gdno"].removesuffix(" [...]")
        gspno_shline = shline_plus_by_shverb["gspno"].removesuffix(" [...]")

        assert gdno_shline == "git diff --name-only"
        assert gspno_shline == "git show --pretty= --name-only"

        # Change nothing but 'gcam' or 'gno'

        if shverb not in ("gcam", "gno"):
            return (shverb, shline)  # no change

        # Collapse a "gno" with Shell Options or Pos Args
        # Collapse to one "gspno" with no "gdno" pre-check

        if shverb == "gno":
            assert shline == "git diff/show --pretty= --name-only", (shline,)
            if grep_shargv[1:]:
                return ("gspno", gspno_shline)  # this 'gno' is 'gspno'

        # Try Git Diff once, and complain & exit nonzero if it fails

        gdno_run = subprocess.run(
            shlex.split(gdno_shline),
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        if gdno_run.returncode or gdno_run.stderr:
            print(f": gdno && {gdno_shline} && : ...", file=sys.stderr)
            sys.stderr.write(gdno_run.stdout.decode())  # written to Stderr, and commonly empty
            sys.stderr.write(gdno_run.stderr.decode())
            print(f"+ exit {gdno_run.returncode}", file=sys.stderr)

            sys.exit(gdno_run.returncode)

        gdno_run_stdout = gdno_run.stdout

        # Plan for 'gno' to sum up the Git Diff if truthy, else to sum up the Git Show

        if shverb == "gno":
            assert shline == "git diff/show --pretty= --name-only", (shline,)

            if gdno_run_stdout:

                gdiff_shverb = "gdno"
                gdiff_shline = gdno_shline

                return (gdiff_shverb, gdiff_shline)

            return ("gspno", gspno_shline)  # this 'gno' is 'gspno'

        # Add each Git Diff Pathname into the Commit Message, for 'gcam'

        assert shverb == "gcam", (shverb,)
        assert shline == "git commit --all -m wip", (shline,)

        if not gdno_run_stdout:
            return (shverb, shline)  # no change

        message = shlex.quote("wip -")
        for line in gdno_run_stdout.decode().splitlines():
            message += shlex.quote(" " + line)

        gcam_shline_plus = "git commit --all -m " + message
        return ("gcam", gcam_shline_plus)  # this 'gcam' knows its 'gdno'

    def shargv_at_grep(self, shverb: str, shargv: tuple[str, ...]) -> tuple[str, ...]:
        """Tune Greps to presume text, ignore case, and match >= 1 patterns"""

        if shverb not in ("gg/n", "ggl", "glf"):
            return shargv

        if (shverb == "glf") and not shargv[1:]:
            return shargv

        assert shargv[1:], (shargv[1:], shverb)

        shargv = (shargv[0],) + self._shargs_grep_expand_ai_e_(shargv[1:])

        return shargv

    def _shargs_grep_expand_ai_e_(self, shargs: tuple[str, ...]) -> tuple[str, ...]:
        """Tune to presume text, ignore case, and match >= 1 patterns"""

        strs = list()
        strs.append("-ai")  # -a = --text  # -i = --ignore-case
        for i, arg in enumerate(shargs):
            if arg == "--":
                strs.extend(shargs[i:])
                break
            elif arg.startswith("-"):
                strs.append(arg)
            else:
                strs.append("-e")
                strs.append(arg)

        argv = tuple(strs)
        return argv

    def auth_git_shline(self, shline: str) -> tuple[str, str]:
        """Let Auth fail, else say which Shell Line to run and which Shell Line to trace"""

        if not shline.startswith("... && "):
            return (shline, shline)

        authable = shline.removeprefix("... && ")
        taggable = "echo Press ⌃D && cat - >/dev/null && " + authable

        print(f"Press ⌃D to auth:  {authable}", file=sys.stderr)
        assert int(0x80 + signal.SIGINT) == 130
        try:
            sys.stdin.read()
        except KeyboardInterrupt:
            sys.exit(130)

        authed = authable
        return (authed, taggable)

    def rescue_git_commit_message(self, returncode: int) -> None:
        """Help recover when 'git commit' loses its input file"""

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

        print("+ exit", returncode, file=sys.stderr)  # repeat after caller

        sys.exit(returncode)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/git.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
