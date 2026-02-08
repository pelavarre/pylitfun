# sh/.zsh = Call Zsh but without Profile

set -xe
env -i PS1='zsh %# ' TERM=$TERM zsh -f "$@"
