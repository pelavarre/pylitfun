# sh/.make: Run the localhost:~/bin/Makefile as the next new ./Makefile = aka sh/m
# often set up by:  ln -s $PWD/Makefile ~/bin/Makefile

if [ ! -e Makefile ]; then
    (set -xe; cp -ip ~/bin/Makefile .) || exit $?
fi

set -xe
make "$@"
