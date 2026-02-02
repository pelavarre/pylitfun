# .bash = Call Bash but without Profile

set -xe
env -i PS1='bash \$ ' bash --noprofile --norc "$@"
