#!/usr/bin/env python3

"""
usage: git.py [--help] [--make-bin] [--shfile SHFILE] [SHWORD ...]

abbreviate the subcommands to call Git, but do show them in full

positional arguments:
  SHWORD           option or positional argument of Git

options:
  --help           show this help message and exit (-h is for Git, not for Git·Py)
  --shfile SHFILE  a filename as the Git alias to decode (default: '/dev/null/g')
  --make-bin       rewrite bin/g* as Shell Scripts to call g.py to call git.py

examples:
  gg -w gg ggl
  git.py --shfile=~/gg -w gg ggl
  : gg ... && git grep -ai -w -e gg -e ggl
  gla
  : gla && git log --pretty=fuller --no-decorate --color-moved --author=jqdoe
"""

# code reviewed by people and by Black, Flake8, Mypy-Strict, & Pylance-Standard


import __main__
import datetime as dt
import difflib
import os
import pathlib
import shlex
import signal
import subprocess
import sys
import textwrap
import time
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
    "gdh": "git diff --color-moved HEAD~1 [...]",
    "gdno": "git diff --name-only [...]",
    "gf": "date && date -u && time git fetch --prune --prune-tags --force",
    "gg/0": "git status",  # "gg": but without Sh Args
    "gg/n": "git grep -ai -e ... -e ...",  # "gg": but with Sh Args
    # 15
    "ggl": "git grep -l -ai -e ... -e ...",
    "gl": "git log --pretty=fuller --no-decorate --color-moved [...]",
    "gla": "git log --pretty=fuller --no-decorate --color-moved --author=...",
    "glf": "git ls-files |grep -ai -e ... -e ...",
    "glq": "git log --oneline --no-decorate --color-moved [...]",
    "gls": "git log --pretty=fuller --no-decorate --color-moved --numstat [...]",
    # 20
    "glv": "git log --oneline --decorate --color-moved [...]",
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
    "gsis": "find . -type p && git status --ignored --short",
    "gspno": "git show --pretty= --name-only [...]",
    # 32
}

# often does say '--color-moved' with Hyphen-Minus, but never says '--color=moved' with Equals Sign


_a_ = list(ShlinePlusByShverb.keys())
_b_ = sorted(_a_)
_diffs_ = list(difflib.unified_diff(a=_a_, b=_b_, fromfile="a", tofile="b", lineterm=""))
if _diffs_:
    print("\n".join(_diffs_), file=sys.stderr)
assert not _diffs_, (_diffs_,)


def main() -> None:
    """Run from the Shell Command Line"""

    gg = GitGopher()
    gg.go_for_it()


class GitGopher:
    """Init and run, once"""

    def go_for_it(self) -> None:

        # Fail if no Shell Args

        usage = "usage: git.py [--help] [--make-bin] [--shfile SHFILE] [SHWORD ...]"

        if not sys.argv[1:]:
            print(usage)
            sys.exit(2)  # exits 2 for bad args

        # Find the Shell Verb and the Shell Args after it

        self.exit_if_dash_dash_help()
        self.exit_if_dash_dash_make_bin()

        shfile_shargv = self.dash_dash_shfile_shargv(sys.argv, default="/dev/null/g")

        shverb = os.path.basename(shfile_shargv[0])
        assert shverb, (shfile_shargv, shverb)
        shverb_shargv = (shverb, *shfile_shargv[1:])

        chosen_shverb = self.form_shverb_for_shargv(shverb_shargv)
        chosen_shargv = (chosen_shverb, *shverb_shargv[1:])

        # Replace the Shell Verb with a Git Shell Line, and edit the Args

        (found_shline, given_shsuffix) = self.form_shverb_shline(chosen_shargv)
        tweaked_shargv = self.shargv_tweak_up(chosen_shverb, shargv=chosen_shargv)

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
            chosen_shverb, shline=shell_shline, tweaked_shargv=tweaked_shargv
        )

        diff_shargv = (diff_shverb, *tweaked_shargv[1:])

        # Explicitly auth the especially destructive ops

        (authed, taggable) = self.auth_git_shline(diff_shline)

        # Shove back on Python ShLex Quote fussily quoting mentions of HEAD~... to no purpose

        run_shline = authed + " " + " ".join(shlex_quote_calmly(_) for _ in diff_shargv[1:])
        run_shline = run_shline.rstrip()

        run_shargv = shlex.split(authed) + list(diff_shargv[1:])

        # Loudly promise to call the Shell now

        taggable_shline = taggable + " " + " ".join(shlex_quote_calmly(_) for _ in diff_shargv[1:])
        taggable_shline = taggable_shline.rstrip()

        tagged_shverb = "gg" if diff_shverb in ("gg/0", "gg/n") else diff_shverb
        tagged_shline = f": {tagged_shverb}{given_shsuffix} && {taggable_shline}"

        print(tagged_shline, file=sys.stderr)  # prints its ":", not after a "+" or "|"

        # Call the Shell now

        if shell:
            git_run = subprocess.run(run_shline, shell=True)
        elif " && " in run_shline:
            assert tagged_shverb in ("gf", "gsis"), (tagged_shverb, run_shline)
            git_run = self.subprocess_run_shlines_till_exit_nonzero(run_shline.split(" && "))
        else:
            git_run = subprocess.run(run_shargv)

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

        # todo: do we ever call Git so that it needs a .pass_fds= to fill out /dev/fd ?
        # todo: do we ever call Git so that it needs its Stdin cut off ?

    def exit_if_dash_dash_help(self) -> None:
        """Print the Doc and exit zero, if '--help' in the Shell Args"""

        if "--help" in sys.argv[1:]:
            print(__main__.__doc__, file=sys.stderr)
            sys.exit(0)  # exits 0 after printing Help

    def exit_if_dash_dash_make_bin(self) -> None:
        """Rewrite bin/g* as Shell Scripts to call g.py to call git.py"""

        if sys.argv[1:] != ["--make-bin"]:
            return

        shline_plus_by_shverb = ShlinePlusByShverb

        gg_framed_text = f"""

            #!/bin/sh
            # {shline_plus_by_shverb["gg/0"]}
            # {shline_plus_by_shverb["gg/n"]}
            g.py --shfile="$0" "$@"

        """

        for shverb, shline_plus in shline_plus_by_shverb.items():

            framed_text = f"""

                #!/bin/sh
                # {shline_plus}
                g.py --shfile="$0" "$@"

            """

            pathname = f"bin/{shverb}"
            if "/" in shverb:
                assert shverb in ("gg/0", "gg/n"), (shverb,)
                framed_text = gg_framed_text
                pathname = "bin/gg"  # written twice, to no purpose

            text = textwrap.dedent(framed_text).strip()

            path = pathlib.Path(pathname)
            _ = path.read_text()  # requires readable
            x_ok = os.access(pathname, mode=os.X_OK)
            assert x_ok, (pathname, x_ok)  # requires executable

            path.write_text(text + "\n")

        sys.exit()

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

    #
    # Choose the ShVerb
    #

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

    #
    # Form the ShLine
    #

    def form_shverb_shline(self, shargv: tuple[str, ...]) -> tuple[str, str]:
        """Expand the Shell Verb as a Git Alias, with or without Args"""

        shverb = shargv[0]

        shline_plus_by_shverb = ShlinePlusByShverb
        shverb_shline_plus = shline_plus_by_shverb[shverb]

        # Require >= 1 Shell Args
        # or else:  Accept >= 0 Shell Args, and sometimes add 1 Shell Arg
        # or else:  Accept no Shell Args, else require first Shell Arg not obviously a Positional Arg

        if shverb_shline_plus.endswith("..."):

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

        assert shverb_shline_plus.endswith("..."), (shverb_shline_plus,)
        required_args_usage = f"usage: {shverb} ..."

        # Discover the present main Author

        gwho = self.find_git_who()

        # Tweak away from Doc when supposedly required Args absent

        if shverb_shline_plus == "git ls-files |grep -ai -e ... -e ...":
            assert shverb == "glf", (shverb, shverb_shline_plus)

            if shargv[1:]:
                shline = "git ls-files |grep"  # without -ai -e ... -e ...
                shsuffix = " ..."  # shouts out Args
            else:
                shline = "git ls-files"
                shsuffix = ""  # shouts out (and forgives) No Pos Args (indeed No Args)

            assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
            return (shline, shsuffix)

        if shverb_shline_plus.endswith(" --author=..."):
            shline = shverb_shline_plus.removesuffix(" --author=...")
            shsuffix = " ..."  # shouts out Args
            if not shargv[1:]:
                shline += " " + shlex.quote(f"--author={gwho}")
                shsuffix = ""  # shouts out (and forgives) No Pos Args (indeed No Args)

            assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
            return (shline, shsuffix)

        # Tweak away from Doc while heavily editing required Args

        shline = shverb_shline_plus.removesuffix(" ...")
        if shverb_shline_plus.endswith(" -ai -e ... -e ..."):
            shline = shverb_shline_plus.removesuffix(" -ai -e ... -e ...")

        shsuffix = " ..."  # shouts out Args

        # Do require Args

        if not shargv[1:]:

            if shverb in ("ga", "ggl"):
                gtop = self.find_git_top(default="")
                if gtop:
                    if gtop != os.getcwd():
                        print(f"# {shverb!r} not at:  cd {gtop}/", file=sys.stderr)

            print(required_args_usage, file=sys.stderr)
            sys.exit(2)  # exits 2 for bad args

        # Succeed

        assert shsuffix in ("", " ..."), (shsuffix, shline, shverb, shargv)
        return (shline, shsuffix)

        # ga, gcp, gg/n, ggl, glf, grh

    def _form_shline_optional_args_(
        self, shverb: str, shverb_shline_plus: str, shargv: tuple[str, ...]
    ) -> tuple[str, str]:
        """Handle case where >= 0 Shell Args are accepted, and sometimes add 1 Shell Arg"""

        assert shverb_shline_plus.endswith(" [...]"), (shverb_shline_plus,)

        shline = shverb_shline_plus.removesuffix(" [...]")

        shsuffix = " ..."  # shouts out Args
        if not shargv[1:]:
            shsuffix = ""  # shouts out No Pos Args (indeed No Args)

            if shverb_shline_plus == "git commit --all --fixup [...]":
                assert shverb in ("gcaf",), (shverb, shline)
                shline += " HEAD"  # tilts into:  git commit --all --fixup HEAD

            elif shverb_shline_plus == "git commit --fixup [...]":
                assert shverb in ("gcf",), (shverb, shline)
                shline += " HEAD"  # tilts into:  git commit --fixup HEAD

            elif shverb_shline_plus == "git log --pretty=fuller --no-decorate --color-moved [...]":
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

        assert not shverb_shline_plus.endswith("..."), (shverb_shline_plus,)
        assert not shverb_shline_plus.endswith(" [...]"), (shverb_shline_plus,)

        # Fill out some default Options, when given no Shell Args

        shline = shverb_shline_plus
        shsuffix = ""  # shouts out No Pos Args

        if not shargv[1:]:
            o = (shverb, shline)
            if shverb == "gf":
                assert shverb_shline_plus.endswith("git fetch --prune --prune-tags --force"), o
                shline += " --quiet"  # tilts into:  gf --quiet

            elif shverb == "grl":
                assert shverb_shline_plus == "git reflog --date=relative --numstat", o
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

        assert shsuffix == "", (shsuffix, shline, shverb, shargv)
        return (shline, shsuffix)

        # gb, gcaa, gcam, gda, gdh, gf, gno, grh1, grhu, grl, grv, gsis

    def find_git_who(self) -> str:
        """Go fetch the 'git config user.email'"""

        gwho_shline = "git config user.email"

        gwho_run = subprocess.run(
            shlex.split(gwho_shline),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Exit nonzero and explain why, if need be

        if gwho_run.returncode:

            print(f": gwho && {gwho_run}", file=sys.stderr)
            sys.stderr.write(gwho_run.stdout.decode())  # written to Stderr, and commonly empty
            sys.stderr.write(gwho_run.stderr.decode())

            print(f"+ exit {gwho_run.returncode}", file=sys.stderr)

            sys.exit(gwho_run.returncode)

        # Succeed

        gwho = gwho_run.stdout.decode().rstrip()

        return gwho

        # todo: merge with nearly identical .find_git_top
        # todo: run .find_git_who at most once per Process

    #
    # Solve work in Shell or not, work at Git Top or not, work with Git Diff or not
    #

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
            stdin=subprocess.DEVNULL,
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

        # Succeed

        gtop = gtop_run.stdout.decode().rstrip()

        return gtop

        # todo: merge with nearly identical .find_git_who
        # todo: run .find_git_top at most once per Process

    def shline_at_git_diff(
        self, shverb: str, shline: str, tweaked_shargv: tuple[str, ...]
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
            if tweaked_shargv[1:]:
                return ("gspno", gspno_shline)  # this 'gno' is 'gspno'

        # Try Git Diff once, and complain & exit nonzero if it fails

        gdno_run = subprocess.run(
            shlex.split(gdno_shline),
            stdin=subprocess.DEVNULL,
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

        pathnames = gdno_run_stdout.decode().splitlines()
        message = "wip - " + " ".join(pathnames)

        gcam_shline_plus = "git commit --all -m " + repr(message)
        return ("gcam", gcam_shline_plus)  # this 'gcam' knows its 'gdno'

        # todo: run .gdno_shline at most once per Process

    #
    # Choose ShArgV
    #

    def shargv_tweak_up(self, shverb: str, shargv: tuple[str, ...]) -> tuple[str, ...]:
        """Tune Greps to presume text, ignore case, and match >= 1 patterns"""

        shline_plus_by_shverb = ShlinePlusByShverb
        shline_plus = shline_plus_by_shverb[shverb]

        # Tweak 'gla jqdoe' up into 'gl --author=jqdoe', etc

        if shverb in ("gla",):
            assert shline_plus.endswith(" --author=..."), (shline_plus, shverb)
            if shargv[1:]:
                alt_sharg1 = "--author=" + shargv[1]

                tweaked_shargv = shargv[:1] + (alt_sharg1,) + shargv[2:]
                return tweaked_shargv

            return shargv

        # Tweak 'grias 3' up into 'grias HEAD~3', etc

        if shverb in ("gri", "grias"):
            assert shline_plus.startswith("git rebase -i "), (shline_plus, shverb)

            if len(shargv) == (1 + 1):
                sharg = shargv[-1]
                if sharg in list("123456789"):
                    tweaked_shargv = shargv[:1] + ("HEAD~" + sharg,)
                    return tweaked_shargv

            return shargv

        assert not shline_plus.startswith("git rebase -i "), (shline_plus, shverb)

        # Convert to '|grep -ai -e ... -e ...' and fall through, else don't

        if shverb not in ("gg/n", "ggl", "glf"):
            return shargv

        if (shverb == "glf") and not shargv[1:]:
            return shargv

        assert shargv[1:], (shargv[1:], shverb)

        shargv = (shargv[0],) + self._shargs_grep_expand_ai_e_(shargv[1:])

        # Success

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

    #
    # Auth & recover from Panic
    #

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
    # Run through each Step till first Fault
    #

    def subprocess_run_shlines_till_exit_nonzero(
        self, shlines: typing.Iterable[str]
    ) -> subprocess.CompletedProcess[bytes]:
        """Call the Shell for each Line and return the last, but quit early at exit nonzero, if any"""

        shlines_list = list(shlines)

        run = subprocess.run(["true"], stdin=subprocess.DEVNULL)
        assert run.returncode == 0, (run.returncode,)

        for shline in shlines_list:
            print(f"+ {shline}", file=sys.stderr)

            removeprefix = shline.removeprefix("time ")
            shargv = shlex.split(removeprefix)

            t0 = time.time()
            run = subprocess.run(shargv)
            t1 = time.time()

            t1t0 = t1 - t0
            strftime = dt_timedelta_strftime(dt.timedelta(seconds=t1t0))
            if shline.startswith("time "):
                print(f"... {strftime} ...", file=sys.stderr)

            if run.returncode:
                return run  # trust caller to print f"+ exit {run.returncode}"

        print("+", file=sys.stderr)

        return run


#
# Amp up Import DateTime as DT
#


def dt_timedelta_strftime(td: dt.timedelta, depth: int = 2, str_zero: str = "0s") -> str:
    """Give 'w d h m s ms us ms' to mean 'weeks=', 'days=', etc"""

    # Pick Weeks out of Days, Minutes out of Seconds, and Millis out of Micros

    w = td.days // 7
    d = td.days % 7

    h = td.seconds // 3600
    h_s = td.seconds % 3600
    m = h_s // 60
    s = h_s % 60

    ms = td.microseconds // 1000
    us = td.microseconds % 1000

    # Catenate Value-Key Pairs in order, but strip leading and trailing Zeroes,
    # and choose one unit arbitrarily when speaking of any zeroed TimeDelta

    keys = "w d h m s ms us".split()
    values = (w, d, h, m, s, ms, us)
    pairs = list(zip(keys, values))

    chars = ""
    count = 0
    for index, (k, v) in enumerate(pairs):
        if (chars or v) and any(values[index:]):
            chars += "{}{}".format(v, k)
            count += 1

            if count >= depth:  # truncates, does Not round up
                break

    str_zeroes = list((str(0) + _) for _ in keys)
    if not chars:
        assert str_zero in str_zeroes, (str_zero, str_zeroes)
        chars = str_zero

    # Succeed

    return chars  # '9ms331us' to mean 9ms 331us <= t < 9ms 333us


#
# Amp up Import ShLex
#


assert shlex.quote("HEAD~1") == "'HEAD~1'", (shlex.quote("HEAD~1"),)


def shlex_quote_calmly(arg: str) -> str:
    """Quote like ShLex Quote, but not more carefully at ~ than at @, except for starts with ~"""

    quote = shlex.quote(arg)

    at_quotable = arg.replace("~", "@")
    at_quote = shlex.quote(at_quotable)

    if at_quote == at_quotable:
        if not arg.startswith("~"):
            return arg

    return quote


assert shlex_quote_calmly("HEAD~1") == "HEAD~1", (shlex_quote_calmly("HEAD~1"),)


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


_ = """  # todo's

# todo: help rediscover 'gf --' is our not '--quiet' form

# todo: measure latency added by calling these aliases in place of an explicit whole shline

# todo: gcam should pick up new Added Files into the wip

# todo: add:  git checkout -, git push, git rebase, local/remote mkdir/rmdir of git branches, ...
# todo: no 'git checkout' on purpose:  without args it cancels cherry-pick and hides rebase

"""


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/git.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
