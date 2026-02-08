# sh/.pb = Edit your Os Copy/Paste Clipboard Buffer

if [ -t 0 ]; then
    pbpaste "$@"
else
    pbcopy "$@"
    if [ ! -t 1 ]; then
        pbpaste
    fi
fi
