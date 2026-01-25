# Call Bash with the --noprofile --norc kind of lots less Local Reconfiguration

set -xe
env -i PS1='bash \$ ' bash --noprofile --norc "$@"
