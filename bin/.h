# bin/.h = Compose bin/.history |pylitgit/g ...

if [ $# = 0 ]; then
    echo "+ cat ~/.*.log |pf decode reverse set reverse cut" >&2
    cat ~/.*.log |pf decode reverse set reverse cut
else
    echo "+ cat ~/.*.log |pf decode reverse set reverse cut |g.py g $*" >&2
    cat ~/.*.log |pf decode reverse set reverse cut |g.py g "$@"
fi
