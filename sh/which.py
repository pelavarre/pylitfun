#!/usr/bin/env python3

"""
usage: which.py [-h] [-a] [PATTERN ...]

search out and sum up what's found in the Shell $PATH now

positional arguments:
  PATTERN     a Python Regular Expression to say which Verbs to show

options:
  -h, --help  show this help message and exit
  -a, --all   explicitly ask to show more than one match, in the tradition of 'which -a'

examples:
  which.py --  # show the 'which -a' of every Shell Verb
  which.py python  # show the 'which -a' of every form of a Python Shell Verb
"""


import collections
import os
import pathlib


import litnotes


#
# Run from the Shell Command Line
#


def main() -> None:
    """Run from the Shell Command Line"""

    litnotes.print_doc_and_exit_zero_if("examples:")

    default_eq_str = str()
    env_path = os.getenv("PATH", default_eq_str)

    splits = env_path.split(":")

    shpa = ShellPath(pathnames=splits)
    shpa.pathnames_sample_each()
    shpa.print_folders()
    shpa.print_files()


class ShellPath:

    pathnames: list[str] = list()

    realname_by_pathname: dict[str, str] = dict()
    realpath_by_realname: dict[str, pathlib.Path] = dict()

    is_dir_by_realname: dict[str, bool] = dict()
    realpaths_by_verb: dict[str, list[pathlib.Path]] = collections.defaultdict(list)
    verbs_by_realname: dict[str, list[str]] = collections.defaultdict(list)

    def __init__(self, pathnames: list[str]) -> None:
        self.pathnames.extend(pathnames)  # almost collides with kwarg .pathnames

    def pathnames_sample_each(self) -> None:
        """Sample each Pathname once, in order, skipping duplicates"""

        pathnames = self.pathnames
        realname_by_pathname = self.realname_by_pathname
        realpath_by_realname = self.realpath_by_realname

        is_dir_by_realname = self.is_dir_by_realname
        realpaths_by_verb = self.realpaths_by_verb
        verbs_by_realname = self.verbs_by_realname

        assert not realname_by_pathname, (realname_by_pathname.keys(),)
        assert not realpath_by_realname, (realpath_by_realname.keys(),)

        assert not is_dir_by_realname, (is_dir_by_realname.keys(),)
        assert not realpaths_by_verb, (realpaths_by_verb.keys(),)
        assert not verbs_by_realname, (verbs_by_realname.keys(),)

        for pathname in pathnames:
            if pathname in realname_by_pathname.keys():
                continue

            realname = os.path.realpath(pathname)
            realpath = pathlib.Path(realname)

            realname_by_pathname[pathname] = realname
            realpath_by_realname[realname] = realpath

        for realname, path in realpath_by_realname.items():
            if realname in is_dir_by_realname:
                continue

            is_dir = path.is_dir()
            is_dir_by_realname[realname] = is_dir

            if is_dir:
                for child in path.iterdir():  # unordered
                    verb = child.name
                    if child.is_file() and os.access(child, os.X_OK):

                        realpaths_by_verb[verb].append(child)
                        verbs_by_realname[realname].append(verb)

    def print_folders(self) -> None:
        """Say which Paths contribute Dirs and Verbs"""

        pathnames = self.pathnames
        realname_by_pathname = self.realname_by_pathname

        is_dir_by_realname = self.is_dir_by_realname
        verbs_by_realname = self.verbs_by_realname

        for index, pathname in enumerate(pathnames):

            realname = realname_by_pathname[pathname]
            is_dir = is_dir_by_realname[realname]
            verbs = verbs_by_realname[realname]

            sorted_verbs = sorted(verbs)
            assert sorted_verbs == sorted(set(sorted_verbs))

            cells: list[str | int] = list()
            cells.append(index)

            if not is_dir:
                assert sorted_verbs == list(), (sorted_verbs,)
                cells.append("-")
            else:
                cells.append(len(sorted_verbs))

            cells.append(pathname)
            if realname != pathname:
                cells.append(realname)

            if index != pathnames.index(pathname):
                cells.append("# duplicate")
            elif not is_dir:
                cells.append("# isn't dir")
            elif not sorted_verbs:
                pass
            else:
                if len(sorted_verbs) == 1:
                    cells.append(sorted_verbs[0])
                elif len(sorted_verbs) == 2:
                    cells.append(sorted_verbs[0])
                    cells.append(sorted_verbs[1])
                else:
                    cells.append(sorted_verbs[0])
                    cells.append("...")
                    cells.append(sorted_verbs[-1])

            join = "\t".join(str(_) for _ in cells)
            print(join)  # todo0: join with " \t" when "\t" means " "?

            # todo: show the ~/... folders as such

            # todo: show groups of verbs - initial Upper, initial Lower, other

            # todo: show common suffix at left as '/...'

    def print_files(self) -> None: ...


#
# Run from the Shell Command Line, if not imported
#


if __name__ == "__main__":
    main()


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/bin/which.py
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
