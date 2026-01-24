# .emacs = Run Homebrew Emacs, like on an Empty Buffer, and with less Spam

# sh/.emacs is same Basename different Pathname vs the ~/.emacs that is the ~/.vimrc of Emacs

set -xe
/opt/homebrew/bin/emacs -Q --no-splash -q -nw --eval '(menu-bar-mode -1)' "$@"
