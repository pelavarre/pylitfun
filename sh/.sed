set -xe
pbpaste |awk '{print $NF}' |sed 's,^,-- ,' |sed 's,$, --,' |pbcopy
