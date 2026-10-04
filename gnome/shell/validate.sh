#!/bin/sh
# Parse through the installed Shell's St, without attaching to the running Shell.
set -eu
css=$(realpath "${1:?usage: validate.sh /path/to/gnome-shell.css}")
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
typelib=/usr/lib/gnome-shell
libpath=/usr/lib/gnome-shell
for directory in /usr/lib/*/mutter-*; do
    [ -d "$directory" ] || continue
    typelib="$typelib:$directory"
    libpath="$libpath:$directory"
done
log=$(mktemp)
trap 'rm -f "$log"' EXIT HUP INT TERM
if ! GI_TYPELIB_PATH="$typelib${GI_TYPELIB_PATH:+:$GI_TYPELIB_PATH}" LD_LIBRARY_PATH="$libpath${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" /usr/bin/gjs "$script_dir/validate.js" "$css" >"$log" 2>&1; then
    cat "$log" >&2
    exit 1
fi
cat "$log"
if grep -Ei 'warning|critical|error|failed' "$log"; then exit 1; fi
