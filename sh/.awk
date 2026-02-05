# .awk = Pick out the last Column when it's not empty

awk "$@" 'NF{print $NF}'

# And some Shell Comments on things this sh/.awk could say, but doesn't =>
#
# # .awk = Pair up each Two Lines into a Tsv, but reverse each Pair
# awk '!(NR%2){print $0"\t"o} {o=$0}'
#
