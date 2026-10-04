#!/usr/bin/env bash
# Marbell Ember installer: copies configs into user directories, keeping numbered
# backups. No packages; see README "Requirements".
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"

put() {  # put <src> <dest>
  mkdir -p "$(dirname "$2")"
  cp --backup=numbered "$1" "$2"
  echo "  $2"
}

echo "configs:"
put "$here/ghostty/config.ghostty"        "$cfg/ghostty/config.ghostty"
put "$here/ghostty/themes/Marbell Ember"  "$cfg/ghostty/themes/Marbell Ember"
for f in "$here"/ghostty/shaders/*.glsl; do put "$f" "$cfg/ghostty/shaders/$(basename "$f")"; done
put "$here/ghostty/ember.css"             "$cfg/ghostty/ember.css"
# Set the driver environment on the packaged D-Bus/systemd activation path.
# This drop-in is harmless when the package does not provide the named unit.
put "$here/ghostty/app-com.mitchellh.ghostty.service.d/10-ember.conf" \
    "$cfg/systemd/user/app-com.mitchellh.ghostty.service.d/10-ember.conf"
if command -v systemctl >/dev/null 2>&1; then
  if ! systemctl --user daemon-reload; then
    echo "systemd: user manager unavailable; Ghostty drop-in saved for its next start."
  fi
fi
for f in ember.py make_plate.py logo.txt delta.gitconfig plate.png; do put "$here/ember/$f" "$cfg/ember/$f"; done
put "$here/xonsh/rc.xsh"                  "$cfg/xonsh/rc.xsh"
[ -f "$cfg/xonsh/local.xsh" ] || put "$here/xonsh/local.xsh.example" "$cfg/xonsh/local.xsh"
put "$here/starship.toml"                 "$cfg/starship.toml"
put "$here/herdr/config.toml"             "$cfg/herdr/config.toml"
put "$here/fastfetch/config.jsonc"        "$cfg/fastfetch/config.jsonc"
put "$here/bat/config"                    "$cfg/bat/config"
put "$here/btop/ember.theme"              "$cfg/btop/themes/ember.theme"
sed -i "s|__HOME__|$HOME|g" "$cfg/ghostty/config.ghostty" "$cfg/herdr/config.toml"

if [ ! -f "$cfg/btop/btop.conf" ]; then
  printf 'color_theme = "ember"\ntheme_background = False\ntruecolor = True\nrounded_corners = True\ngraph_symbol = "braille"\n' > "$cfg/btop/btop.conf"
else
  echo "btop: set color_theme = \"ember\" and theme_background = False in $cfg/btop/btop.conf"
fi

fonts="$HOME/.local/share/fonts/space-mono"
if ! fc-list 2>/dev/null | grep -qi "Space Mono"; then
  echo "font: downloading Space Mono (OFL) from google/fonts"
  mkdir -p "$fonts"
  for f in SpaceMono-Regular SpaceMono-Bold SpaceMono-Italic SpaceMono-BoldItalic; do
    curl -fsSL -o "$fonts/$f.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/spacemono/$f.ttf"
  done
  fc-cache -f "$fonts"
fi

echo
echo "optional: git diffs through delta"
echo "  git config --global --add include.path $cfg/ember/delta.gitconfig"
echo "missing tools:"
for b in ghostty xonsh starship fastfetch eza bat btop fzf zoxide delta rg herdr; do
  command -v "$b" >/dev/null 2>&1 || echo "  $b"
done
echo "done. Open Ghostty."
echo
echo "optional desktop theme (Ubuntu 26.04; see gnome/USAGE.md for requirements):"
echo "  ./gnome/apply.sh"
