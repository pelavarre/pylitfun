# sh/.sh = Call Sh but without Profile, and don't wait for Posix to define 'sh -p'

set -xe
env -i PS1='bash \$ ' sh -p "$@"
