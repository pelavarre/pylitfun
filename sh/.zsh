# .zsh = Call Zsh with the -f kind of lots less Local Reconfiguration

set -xe
env -i PS1='zsh %# ' TERM=$TERM zsh -f "$@"
