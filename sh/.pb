# .pb = Edit your Os Copy/Paste Clipboard Buffer

if [ ! -t 0 ]; then
    pbcopy "$@"
else
    pbpaste "$@"
fi
