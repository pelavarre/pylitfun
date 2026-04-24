# sh/.ls = show latest columns of datatype, metric byte size, exact date/time

if ls --full-time /usr/bin/ls >/dev/null 2>&1; then  # as if linux

    if [ $# -le 1 ]; then
        set -xe
        ls -hlAF --full-time -rt "$@"
    else
        set -xe
        ls -hlAF --full-time -rt -d "$@"
    fi

else  # as if macosx

    if [ $# -le 1 ]; then
        set -xe
        ls -hlAF -rt "$@"
    else
        set -xe
        ls -hlAF -rt -d "$@"
    fi

fi
