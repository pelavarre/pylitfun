# sh/.sed = Insert "-- " before, and " --" after, each Line of the Paste Buffer

set -xe
pbpaste |awk '{print $NF}' |sed 's,^,-- ,' |sed 's,$, --,' |pbcopy
