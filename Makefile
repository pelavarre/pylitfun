# pylitfun/Makefile


#
# Define 'make' and 'make help'
#


define __EPILOG__

make  # shows a few examples and exits zero

make help  # shows many help lines and exits zero
make bin  # updates your Shell Path ~/bin/ Folder from our bin/ and sh/
make pips  # installs/ updates Python add-on's from PyPi·Org
make sense  # calls for Code Review from Black, Flake8, and MyPy Strict
make tests  # updates:  git diff csp/cspbook-py-readme.md

endef


define __DOC__
usage: make TARGET

help download, run, and give back changes

positional arguments:
  TARGET  which work to do (one of help, bin, pips, sense, tests)

examples:
  make  # shows a few examples and exits zero
  make help  # shows many help lines and exits zero
  make bin  # updates your Shell Path ~/bin/ Folder from our bin/ and sh/
  make pips  # installs/ updates Python add-on's from PyPi·Org
  make sense  # calls for Code Review from Black, Flake8, and MyPy Strict
  make tests  # updates:  git diff csp/cspbook-py-readme.md
endef


default:
	@$(info $(__EPILOG__))
	@true


help:
	@$(info $(__DOC__))
	@true


#
# Install stale copies into your Shell Path ~/bin/ Folder
#


bin:
	(ls -A bin && ls -A bin/git-verbs && ls -A sh) \
		|(cd ~/ && xargs -I{} rm -fr bin/{})
	ls -d bin/* bin/git-verbs/* sh/* sh/.* \
		|grep -v -e /__pycache__$$ \
		|grep -v -e ^bin/git-verbs$$ -e ^bin/git-verbs/man$$ -e ^sh/[.]$$ -e ^sh/[.][.]$$ -e sh/pwnme$$ \
		|xargs -I{} cp -ip {} ~/bin/.
	cp -ipR bin/git-verbs/man ~/bin/.
	@# rm -fr ~/bin/Makefile
	@# cp -ip Makefile ~/bin/.  # wrong answer except for hosts who want ours

# beware: the classic 'sh' can add ./ and ../ into sh/.*
# beware: the classic bin/* or sh/* can include a bin/__init__.py or sh/__init__.py
# beware: working far from 'git clean -dffxq' can toss in __pycache__/ dirs to freak us out


#
# Installs/ replaces Python add-on's from PyPi·Org
#


.PHONY: bin pips requirements.txt

pips requirements.txt:
	: 'remake our ~/.pyvenvs/pips/ in less than 10s'
	:
	mkdir -p ~/.pyvenvs/  # or ~/.venvs/ or ~/.envs/
	:
	cd ~/.pyvenvs/ && rm -fr pips~
	cd ~/.pyvenvs/ && if [ -e pips ]; then mv -i pips pips~; fi
	:
	cd ~/.pyvenvs/ && python3 -m venv pips
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade pip
	:
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade black
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade flake8
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade flake8-import-order
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip install --upgrade mypy
	:
	source ~/.pyvenvs/pips/bin/activate && python3 -m pip freeze >requirements.txt
	git diff --color-moved requirements.txt
	:


#
# Calls for Python Code Review from Black, Flake8, and MyPy Strict
#


push:  # as in do push now, without rerunning any tests
	git push


smoke: sense
	:


sense: black flake8 mypy
	:

slow: black flake8 mypy
	:
	bin/litdatetime.py -- >/dev/null 2>/dev/null
	bin/litdecimal.py -- >/dev/null 2>/dev/null
	: bin/litgit.py -- >/dev/null 2>/dev/null
	: bin/litglass.py -- >/dev/null 2>/dev/null
	bin/litjson.py -- >/dev/null 2>/dev/null
	bin/litmath.py -- >/dev/null 2>/dev/null
	: bin/litpython.py -- >/dev/null 2>/dev/null
	: bin/litshell.py -- >/dev/null 2>/dev/null
	bin/litsys.py -- >/dev/null 2>/dev/null
	:


black:
	~/.pyvenvs/black/bin/black \
		--line-length=101 \
			$$PWD

# --line-length=101  # my 2024 Window Width, over PyPi·Org Black Default of 89 != 80 != 71


flake8:
	~/.pyvenvs/flake8/bin/flake8 \
		--max-line-length=999 --max-complexity 15 --extend-ignore=E203,E704,W503 \
			$$PWD

# --max-complexity 15  # limit how much McCabe Cyclomatic Complexity we accept

# --max-line-length=999  # Black max line lengths over Flake8 max line lengths
# --extend-ignore  # adds to the Defaults E121,E123,E126,E226,E24,E704,W503,W504 (--ignore replaces)
# --extend-ignore=E203  # Black '[ : ]' rules over E203 whitespace before ':'

# some setups do not need
# --extend-ignore=E704  # Black of typing.Protocol over E704 multiple statements on one line (def)
# --extend-ignore=W503  # 2017 Pep 8 and Black over W503 line break before bin op

# exits 0 despite finding some F401 '...' imported but unused


mypy:
	~/.pyvenvs/mypy/bin/mypy --strict "$$PWD"

# without PYTHONPATH="$$PWD/.."


#
# Calls for Shell Code Review from ShellCheck
#


shellcheck:
	if ! which shellcheck; then \
		ls /usr/bin/shellcheck || :; \
		echo 'ok by you? or do you want:  date && time  sudo apt install shellcheck'; \
		exit 1; \
	fi
	:
	shellcheck bin/pwnme


#
# Updates:  git diff csp/cspbook-py-readme.md
#

tests:
	csp/cspbook.py -c '' >/dev/null
	csp/cspbook.py --make-tests


# posted as:  https://github.com/pelavarre/pylitfun/blob/main/Makefile
# copied from:  git clone https://github.com/pelavarre/pylitfun.git
