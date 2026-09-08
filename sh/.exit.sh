# sh/.exit.sh = show the Process Exit Return Code of the Last Process

function .exit() { echo + exit $? >&2; }

# function .exit() { local rc=$?; echo + exit $rc >&2; return $rc; }  # reads without clearing

# many classic Sh reject .exit as 'not a valid id' or as 'Syntax error: "(" unexpected'
