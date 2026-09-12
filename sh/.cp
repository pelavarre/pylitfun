# sh/.cp = Make a backup copy of a File or Folder and put a date-time stamp on it

if [ $# = 0 ]; then
    P=$(find . -maxdepth 1 -not -type d -print0 |xargs -0 -r ls -rt |tail -1)
    if [ "$P" ]; then
       set "$P"
    fi
fi

F=$(echo "$@") && echo + cp -ipR $F{,~$(date -r $F +%m%djqd%H%M)~} |tee /dev/tty |sed 's,^+ ,,' |sh
