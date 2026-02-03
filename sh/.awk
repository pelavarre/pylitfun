# .awk = Pick out the last Column when it's not empty

awk "$@" 'NF{print $NF}'
