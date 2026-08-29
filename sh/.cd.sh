# sh/.cd.sh = go to the join of a split pathname

function .cd() {
    cd $(printf '%s' "$@")
    dirs -p |head -1 >&2
}
