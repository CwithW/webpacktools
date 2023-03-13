#!/bin/bash

which js-beautify 2>/dev/null 1>/dev/null || echo "pip3 install js-beautify"
which js-beautify 2>/dev/null 1>/dev/null || exit 1

foldername="$1"

if [ -z "$foldername" ]; then
    echo "Usage: $0 foldername"
    exit 1
fi

if [ ! -d "$foldername" ]; then
    echo "Folder $foldername does not exist"
    exit 1
fi

find $foldername -type f -name "*.js" -exec js-beautify -r {} \;
