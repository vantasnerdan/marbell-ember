#!/usr/bin/env bash
# Marbell Ember status line — mirrors the Starship prompt: coral callsign block, panel dir, teal branch.
input=$(cat)
model=$(jq -r '.model.display_name // empty' <<<"$input")
dir=$(jq -r '.workspace.current_dir // .cwd // empty' <<<"$input")
pct=$(jq -r '.context_window.used_percentage // empty' <<<"$input")

fg() { printf '\033[38;2;%s;%s;%sm' "$1" "$2" "$3"; }
bg() { printf '\033[48;2;%s;%s;%sm' "$1" "$2" "$3"; }
ink="7 11 22"; panel="30 42 68"; dim="104 122 157"; bright="244 247 251"
coral="244 120 83"; teal="79 209 197"; amber="242 184 102"
rst=$'\033[0m'; bold=$'\033[1m'; sep=$'\uE0B0'; git_glyph=$'\uE0A0'

short=${dir/#$HOME/\~}
IFS=/ read -ra parts <<<"$short"
n=${#parts[@]}
((n > 3)) && short="…/${parts[n-3]}/${parts[n-2]}/${parts[n-1]}"

out="$(bg $coral)$(fg $ink)${bold} ${EMBER_CALLSIGN:-MARBELL} ${rst}"
out+="$(bg $panel)$(fg $coral)${sep}$(fg $bright)${bold} ${short} ${rst}$(fg $panel)${sep}${rst}"

if branch=$(git -C "$dir" symbolic-ref --short -q HEAD 2>/dev/null); then
  out+=" $(fg $teal)${git_glyph} ${branch}${rst}"
  dirty=$(git -C "$dir" status --porcelain 2>/dev/null | wc -l)
  ((dirty > 0)) && out+=" $(fg $amber)~${dirty}${rst}"
fi

[ -n "$model" ] && out+=" $(fg $dim)· ${model}${rst}"
if [ -n "$pct" ]; then
  p=${pct%.*}
  c=$dim; ((p >= 70)) && c=$amber; ((p >= 90)) && c=$coral
  out+=" $(fg $dim)·${rst} $(fg $c)ctx ${p}%${rst}"
fi
printf '%s' "$out"
