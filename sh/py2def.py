#!/usr/bin/env python3

"""
usage: py2def.py [-h] DEFNAME

extract a Py Def from every Py File that has Py Def's of that name

positional arguments:
  DEFNAME     the Name of a Py Def

options:
  -h, --help  show this help message and exit

quirks:
  does the 'find . |grep [.]py$' part for you

examples:
  rm -fr ./def*.py
  ./sh/py2def.py exc.pthook
  ls ./def*.py
"""

import argparse
import collections.abc
import dataclasses
import difflib
import os
import pathlib
import re
import shlex
import sys
import textwrap

#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    parser = arg_doc_to_parser(__doc__ or "")
    ns = parser.parse_args_if(sys.argv[1:])  # often prints help & exits zero

    defname = ns.defname
    run_for_defname(defname)

    print()
    print("Bye from sh/py2def.py")
    print()


def arg_doc_to_parser(doc: str) -> "ArgDocParser":
    """Declare the Options & Positional Arguments"""

    parser = ArgDocParser(doc, add_help=True)

    defname_help = "the Name of a Py Def"
    parser.add_argument("defname", metavar="DEFNAME", help=defname_help)

    return parser


#
# Save Lines of each Revisio of Def
#


def run_for_defname(defname: str) -> None:

    pattern = re.escape("def " + defname)

    pypathnames = os_walk_ext(".py")

    text_by_path: dict[pathlib.Path, str] = dict()
    for pathname in pypathnames:
        path = pathlib.Path(pathname)
        text = path.read_text()
        if re.search(pattern, string=text):
            assert path not in text_by_path.keys(), (text_by_path,)
            text_by_path[path] = text

    n = 0
    for path, text in text_by_path.items():
        lines = text.splitlines()

        print()
        print("Fetched", len(lines), "lines from", path)

        i = 0
        while i < len(lines):
            i_of_line = i
            line = lines[i]
            i += 1

            rstrip = line.rstrip()
            if re.search(pattern, string=rstrip):
                opathname = f"./def{n}.py"
                skip = write_one_file(opathname, path=path, lines=lines, i=i_of_line)
                i += skip - 1

                line1 = lines[0]
                if not line1.endswith("found by sh/py2def.py"):
                    n += 1

                # breakpoint()
                # pass


def write_one_file(opathname: str, path: pathlib.Path, lines: list[str], i: int) -> int:
    """Save Lines of one Revisio of Def"""

    #

    lineno = 1 + i
    oline = f"# {path}:{lineno} found by sh/py2def.py"

    pass  # todo: add the obvious imports

    #

    line = lines[i]
    rstrip = line.rstrip()

    lstrip = rstrip.lstrip()
    ldent = (len(rstrip) - len(lstrip)) * " "
    assert rstrip.startswith(ldent), (opathname, rstrip, i)

    j = i + 1
    while j < len(lines):
        line = lines[j]
        rstrip = line.rstrip()
        if (not rstrip) or rstrip.startswith(ldent):
            if rstrip[len(ldent) :][:1] in (" ", "#", ")", ""):
                j += 1
                continue

        # print(repr(rstrip))
        # breakpoint()
        # pass

        break

    #

    deflines = lines[i:j]
    assert deflines, (deflines,)
    len_deflines = len(deflines)

    for k in range(len(deflines) - 1, 0, -1):
        line = deflines[k]
        strip = line.strip()
        if (not strip) or strip.startswith("#"):
            len_deflines -= 1
            continue

        break

    deflines[::] = deflines[:len_deflines]

    result = len(deflines)

    #

    lineno = 1 + i
    olines = [oline] + deflines
    otext = "\n".join(olines) + "\n"

    line1 = lines[0]
    if line1.endswith("found by sh/py2def.py"):  # todo: merge the 'found by's
        pname = shlex.quote(path.name)
        print(f"Skipping {pname} found by sh/py2def.py")
        return result

    opname = shlex.quote(opathname)
    print(f"Writing {len(olines)} lines into {opname} as found by sh/py2def.py")
    pathlib.Path(opathname).write_text(otext)

    #

    return result


#
# Amp up Import ArgParse
#


_ARGPARSE_3_10_ = (3, 10)  # Oct/2021 Python 3.10, like from Ubuntu 2022


@dataclasses.dataclass(order=True)  # , frozen=True)
class ArgDocParser:
    """Scrape Prog & Description & Epilog from Doc to form an ArgParse Argument Parser"""

    doc: str  # a copy of parser.format_help()
    add_help: bool  # truthy to define '-h, --help', else not

    parser: argparse.ArgumentParser  # the inner standard ArgumentParser
    text: str  # something like the __main__.__doc__, but dedented and stripped
    closing: str  # the last Graf of the Epilog, minus its Top Line

    add_argument: collections.abc.Callable[..., object]
    print_help: collections.abc.Callable[[], None]
    print_usage: collections.abc.Callable[[], None]

    def __init__(self, doc: str, add_help: bool) -> None:

        self.doc = doc
        self.add_help = add_help

        text = textwrap.dedent(doc).strip()

        prog = self._scrape_prog_(text)
        description = self._scrape_description_(text)
        epilog = self._scrape_epilog_(text, description=description)
        closing = self._scrape_closing_(epilog)

        parser = argparse.ArgumentParser(  # doesn't distinguish Closing from Epilog
            prog=prog,
            description=description,
            add_help=add_help,
            formatter_class=argparse.RawTextHelpFormatter,  # lets Lines be wide
            epilog=epilog,
        )

        self.parser = parser
        self.text = text
        self.closing = closing

        self.add_argument = parser.add_argument
        self.print_help = parser.print_help
        self.print_usage = parser.print_usage

        # 'add_help=False' for needs like 'cal -h', 'df -h', 'du -h', 'ls -h', etc

        # callers who need Options & Positional Arguments have to add them

    #
    # Take in the Shell Args, else print Help and exit zero or nonzero
    #

    def parse_args_if(self, args: list[str]) -> argparse.Namespace:
        """Take in the Shell Args, else print Help and exit zero or nonzero"""

        parser = self.parser
        closing = self.closing

        # Print Diffs & exit nonzero, when Arg Doc wrong

        diffs = self._diff_doc_vs_format_help_()
        if diffs:
            if sys.version_info >= _ARGPARSE_3_10_:
                print("\n".join(diffs))

                sys.exit(2)  # exits 2 for Help Doc and/or Parser gone wrong

            # takes 'usage: ... [HINT ...]', rejects 'usage: ... HINT [HINT ...]'
            # takes 'options:', rejects 'optional arguments:'
            # takes '-F, --isep ISEP', rejects '-F ISEP, --isep ISEP'

        # Print Closing & exit zero, if no Shell Args

        if not args:
            print()
            print(closing)
            print()

            sys.exit(0)  # exits 0 after printing Closing

        # Drop the "--" Shell Args Separator, if present,
        # because 'ArgumentParser.parse_args()' without Pos Args wrongly rejects it

        shargs = list(args)
        if len(args) == 1:  # because ArgParse chokes if '--' Sep present without Pos Args
            if args[0] == "--":
                shargs.clear()

        # Print help lines & exit zero, else return Parsed Args

        ns = parser.parse_args(shargs)

        return ns

        # often prints help & exits zero

    #
    # Scrape out Parser, Prog, Description, Epilog, & Closing from Doc Text
    #

    def _scrape_prog_(self, text: str) -> str:
        """Pick the Prog out of the Usage Graf that starts the Doc"""

        lines = text.splitlines()
        prog = lines[0].split()[1]  # second Word of first Line  # 'prog' from 'usage: prog'

        return prog

    def _scrape_description_(self, text: str) -> str:
        """Take the first Line of the Graf after the Usage Graf as the Description"""

        lines = text.splitlines()

        firstlines = list(_ for _ in lines if _ and (_ == _.lstrip()))
        docline = firstlines[1]  # first Line of second Graf

        description = docline
        if self._docline_is_skippable_(docline):
            description = "just do it"

        return description

    def _scrape_epilog_(self, text: str, description: str) -> str:
        """Take up the Lines past Usage, Positional Arguments, & Options, as the Epilog"""

        lines = text.splitlines()

        epilog = ""
        for index, line in enumerate(lines):
            if self._docline_is_skippable_(line) or (line == description):
                continue

            epilog = "\n".join(lines[index:])
            break

        return epilog  # maybe empty

    def _docline_is_skippable_(self, docline: str) -> bool:
        """Guess when a Doc Line can't be the first Line of the Epilog"""

        strip = docline.rstrip()

        skippable = not strip
        skippable = skippable or strip.startswith(" ")  # includes .startswith("  ")
        skippable = skippable or strip.startswith("usage")
        skippable = skippable or strip.startswith("positional arguments")
        skippable = skippable or strip.startswith("options")  # ignores "optional arguments"

        return skippable

    def _scrape_closing_(self, epilog: str) -> str:
        """Pick out the last Graf of the Epilog, minus its Top Line"""

        lines = epilog.splitlines()

        indices = list(_ for _ in range(len(lines)) if lines[_])  # drops empty Lines
        indices = list(_ for _ in indices if not lines[_].startswith(" "))  # finds top Lines

        closing = ""
        if indices:
            index = indices[-1] + 1

            join = "\n".join(lines[index:])  # last Graf, minus its Top Line
            dedent = textwrap.dedent(join)
            closing = dedent.strip()

        return closing  # maybe empty

    #
    # Form Diffs from Help Doc to Parser Format_Help
    #

    def _diff_doc_vs_format_help_(self) -> list[str]:
        """Form Diffs from Help Doc to Parser Format_Help"""

        text = self.text
        parser = self.parser

        # Say where the Help Doc came from

        a = text.splitlines()

        basename = os.path.split(__file__)[-1]
        fromfile = "{} --help".format(basename)

        # Fetch the Parser Doc from a fitting virtual Terminal
        # Fetch from a Black Terminal of 89 columns, not from the current Terminal Width
        # Fetch from later Python of "options:", not earlier Python of "optional arguments:"

        default_eq_none = None
        with_columns_else = os.environ.get("COLUMNS", default_eq_none)  # checkpoints
        with_no_color_else = os.environ.get("NO_COLOR", default_eq_none)  # checkpoints

        os.environ["COLUMNS"] = str(89)  # adds or replaces
        os.environ["NO_COLOR"] = "True"  # adds or replaces

        try:

            b_text = parser.format_help()

        finally:

            if with_no_color_else is None:
                del os.environ["NO_COLOR"]  # removes
            else:
                os.environ["NO_COLOR"] = with_no_color_else  # reverts

            if with_columns_else is None:
                del os.environ["COLUMNS"]  # removes
            else:
                os.environ["COLUMNS"] = with_columns_else  # reverts

        b = b_text.splitlines()

        tofile = "ArgumentParser(...)"

        # Form >= 0 Diffs from Help Doc to Parser Format_Help,
        # but ask for lineterm="", for else the '---' '+++' '@@' Diff Control Lines end with '\n'

        diffs = list(difflib.unified_diff(a=a, b=b, fromfile=fromfile, tofile=tofile, lineterm=""))

        # Succeed

        return diffs

        # .parser.format_help defaults to color its texts, since Oct/2025 Python 3.14


#
# Amp up Import Os
#


def os_walk_ext(ext: str) -> list[str]:
    """Walk the Cwd, finding Pathnames of the given Ext"""

    relpaths = list()

    for root, dirs, files in os.walk("."):
        dirs.sort()  # todo: show we need this sort
        files.sort()

        for file in files:
            if file.endswith(ext):
                dotpath = os.path.join(root, file)  # './sh/py2def.py'

                relpath = os.path.relpath(dotpath)  # 'sh/py2def.py'
                relpaths.append(relpath)

    return relpaths


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# git grep posted.as |cut -d: -f1 |awk -F/ '{print $NF}' >a
# git grep posted.as |awk -F/ '{print $NF}' >b
# diff -brpu a b


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/py2def.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
