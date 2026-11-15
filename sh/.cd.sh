# sh/.cd.sh = go to the join of a split pathname

function .cd() {
    cd $(printf '%s' "$@")  # '%s' "$@" catenates the Sh Args, as if '%s%s' "$1" "$2" etc
    dirs -p |head -1 >&2
}
