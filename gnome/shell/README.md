# Marbell Ember Shell

`./gnome/shell/install.sh` builds the installed Yaru-dark stylesheet, parses it with the installed Shell's St library, installs only `$XDG_DATA_HOME/themes/Marbell-Ember/gnome-shell/` (default `~/.local/share`), downloads the official User Themes build matching the installed Shell, and merges its UUID into the extension settings. Newly installed extensions load at the next login. It does not restart the live Shell. Sibling GTK/Metacity theme directories are preserved.

Use `MARBELL_EMBER_BACKUP_DIR=/path/to/snapshot ./gnome/shell/install.sh` with the desktop installer. Revert with the same variable and `./gnome/shell/revert.sh`. Without the variable, both scripts use the component's latest snapshot below `${XDG_STATE_HOME:-$HOME/.local/state}/marbell-ember/shell/`. Repeated install/revert calls are idempotent; a reverted shared snapshot requires a new snapshot before installing again. Revert restores this extension's list membership and preserves unrelated later list edits.

If user extensions are globally muted, installation preserves that baseline, explicitly disables other installed user extensions currently suppressed by the mute, and clears the global mute. This lets User Themes work without activating Blur My Shell or Tiling Shell. Revert restores the global switch before restoring those extensions' membership.

To turn the Shell theme off immediately, including after login:

```sh
/usr/bin/dconf write /org/gnome/shell/extensions/user-theme/name "''"
```

All GNOME commands use `/usr/bin`, and Python uses the system GI bindings so tools and schemas come from the same Ubuntu installation. Dependencies are the already installed Yaru packages, Shell, GJS, Python GI, dconf and GLib utilities; the installer does not install packages.

`build.py --output /tmp/ember/gnome-shell` reads the installed Yaru CSS at build time. It preserves every selector and non-colour declaration, replaces accent tokens, neutral colour values and semantic colours, copies/recolours relative and resource SVGs, and creates a separate dark calendar-event dot for coral days. Only colour/face refinements are appended; geometry, animation timing and existing alpha are retained. Major surfaces are opaque. No blur, glow or new animation is added. Warnings, danger and success retain their meaning using Ember amber, red and teal. Looking Glass diagnostic colours remain. Unexpected non-neutral colours in a future Yaru release stop the build for review. Upstream copyright notices and licences accompany generated assets, which are not checked into this repository.

`validate.sh /path/to/gnome-shell.css` uses `St.Theme.load_stylesheet`, rejects parser warnings/errors, and never contacts the running Shell. The builder's `build-report.json` records exact selector coverage, colour edits, asset paths and hashes.

After installation, `/usr/bin/python3 gnome/shell/preview.py --output /tmp/ember-preview` runs a finite headless Wayland smoke test on an independent D-Bus connection, runtime directory and settings backend. It loads only the official User Themes extension, captures actual Shell surfaces and Nautilus, and stops its temporary processes. This is an optional development check, not part of normal installation or a background service. Its screenshots use a plain isolated background. It requires GNOME 50's headless compositor and RemoteDesktop virtual input API. It never uses the live session's Eval interface.

`roles.css` keeps the palette's roles explicit after the generated base: coral for active controls, focus rings, slider/progress fill, today and suggested actions (dark text on coral); `#26365A` for selections and checked quick-tile surfaces; `#1E2A44` for edges, separators and tracks; `#5B6B8C` for secondary/placeholder text and inactive icons; bright titles; blue links/info; teal/amber/red for status. Large surfaces, ordinary buttons and app brand icons remain neutral or inherited. No decorative success/warning colours are added to ordinary controls.

`role-probes.js` checks computed St colours on real actors, including focused/checked/disabled states, entry hints, panel icons and calendar headings. These development checks do not certify every extension interaction, display scale or hardware renderer. GDM is a separate privileged theme and is not changed. Space Mono can ellipsize quick-settings labels within Yaru's fixed layout widths.
