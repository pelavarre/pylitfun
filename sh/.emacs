# .emacs = Run Homebrew Emacs with the -Q kind of lots less Local Reconfiguration

# sh/.emacs is same Basename different Pathname vs the ~/.emacs that is the ~/.vimrc of Emacs

set -xe
/opt/homebrew/bin/emacs -Q --no-splash -q -nw --eval '(menu-bar-mode -1)' "$@"
