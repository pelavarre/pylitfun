# .exit = show the Process Exit Return Code of the Last Process

function .exit() {  # a most classic Sh would say:  sh: `.exit': not a valid identifier
    echo + exit $? >&2
}
