# .cp = Make a backup copy of a File or Folder and put a date-time stamp on it

F=$(echo "$@") && echo + cp -ipR $F{,~$(date -r $F +%m%djqd%H%M)~} |tee /dev/stderr |sed 's,^+ ,,' |sh
