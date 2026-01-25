# .exit = show the Process Exit Return Code of the Last Process

function .exit() { echo + exit $? >&2; }  # most classic Sh rejects .exit as 'not a valid id'
