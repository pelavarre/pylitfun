# sh/.make: Run the localhost:~/bin/Makefile as the next new ./Makefile
# often set up by:  ln -s $PWD/Makefile ~/bin/makefile

if [ ! -e Makefile ]; then
    (set -xe; cp -ip ~/bin/Makefile .) || exit $?
fi

set -xe
make "$@"
