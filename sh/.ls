# sh/.ls = show latest columns of datatype, metric byte size, exact date/time

if [ $# -le 1 ]; then
    set -xe
    ls -hlAF -rt "$@"
else
    set -xe
    ls -hlAF -rt -d "$@"
fi

# and Linux knows about:  ls -hlAF -rt --full-time
