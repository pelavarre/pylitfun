# sh/.exit.sh = show the Process Exit Status Return Code of the Last Process

function .exit() { local rc=$?; echo + exit $rc >&2; return $rc; }  # reads without clearing

# many classic Sh reject .exit as 'not a valid id' or as 'Syntax error: "(" unexpected'
