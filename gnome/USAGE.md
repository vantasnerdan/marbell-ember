# Desktop theme

Marbell Ember targets Ubuntu 26.04 with GNOME 50, GTK3, GTK4 and libadwaita. It changes user configuration and builds theme assets from the installed Yaru packages. It does not patch or rebuild Ubuntu software, install system packages, or need sudo.

The desktop installer is separate from the terminal installer at the repository root. Read the requirements below before running it.

## Requirements

Run from a terminal in your logged-in GNOME session. The scripts use system tools under `/usr/bin` so Python, GI libraries and GNOME settings schemas come from the same Ubuntu installation.

The desktop installer needs:

- Installed Yaru-dark GTK3, GTK4 and GNOME Shell themes, and Yaru/Yaru-dark icons under `/usr/share`.
- System Python 3 with PyGObject and Pillow; GTK3/GTK4, libadwaita, GJS, GNOME Shell's St library, dconf, GLib utilities and fontconfig.
- The settings schemas for GNOME Terminal, Ptyxis, GNOME Text Editor, Ubuntu Dock and Ubuntu's Tiling Assistant. These are required even if you do not regularly use those applications. Missing schemas or locked settings stop preflight.
- **Space Mono** and **MesloLGM Nerd Font Mono** already installed. The root terminal installer can download Space Mono; the desktop installer downloads neither font and checks that the Meslo fallback is available.
- An internet connection if the matching official **User Themes** extension is not already installed. The Shell component downloads it from extensions.gnome.org and checks its UUID and supported Shell version. An incompatible existing copy is left untouched and installation stops.

These scripts are designed for the Ubuntu 26.04/GNOME 50 theme and schema layout. They are not a portable theme installer for arbitrary desktop environments or GTK versions. Future Yaru builds may need a palette-map or icon-signature update.

## Apply and revert

From the repository checkout:

```sh
./gnome/apply.sh
```

This builds and installs the named theme, copies the user CSS and wallpaper, applies the desktop settings, and calls the executable Shell and icon component installers. Terminal profile lists are read again before writing, and the Ember profile is merged into each list. Existing profiles are retained; Ember becomes the default profile in GNOME Terminal and Ptyxis.

Every apply creates a timestamped snapshot under `${XDG_STATE_HOME:-$HOME/.local/state}/marbell-ember/gnome/backups/`. It saves the exact explicit or unset state of each changed key, previous files and symlinks, and the absence of files created by the installer. The Shell and icon components share that snapshot through `MARBELL_EMBER_BACKUP_DIR`. Repeated application keeps one Ember profile in each registry and preserves the original rollback state.

Restore the entire installation round:

```sh
./gnome/revert.sh
```

Default revert walks pending snapshots newest first to the original baseline, including saved Shell and icon component state. It preserves unrelated profile and extension-list additions made later. It also finds component snapshots saved independently inside the desktop snapshot directories.

Preview the full restore without changing settings, files or snapshots:

```sh
./gnome/revert.sh --dry-run
```

To restore one particular apply instead, pass its printed snapshot directory. Use `--through /path/to/snapshot` to restore that snapshot and all newer ones. `--settings-only` on either apply or revert skips the Shell/icon hooks; it still handles the GTK theme, user CSS and other desktop settings.

Rollback checks the complete file history before making changes. If a managed file was edited after installation, it stops; `--force` explicitly restores the saved version over that edit. Snapshots and empty directories remain on disk after rollback. If apply stops partway through, its saved snapshot can still be reverted.

## What changes

| Part | Configuration |
|---|---|
| Window bars and GTK | A named `Marbell-Ember` GTK3/GTK4/Metacity theme plus GTK3/GTK4 user CSS. Libadwaita uses the user CSS rather than `gtk-theme`. |
| GNOME Shell | Yaru-derived Shell CSS, selected through the official User Themes extension. |
| Icons | Yaru-derived folders and places, with lighter slate fronts, coral flaps and bright emblems. Other icons inherit Yaru. |
| Wallpaper | Silent Seam at 3440×1440, copied into the user's backgrounds directory and selected for both colour schemes. |
| Dock and tiling | An opaque navy Ubuntu Dock with coral running indicators, and the Tiling Assistant focus-hint colour. The hint itself is not enabled. |
| Fonts | Space Mono for interface, document, monospace and window-title text; a Meslo Nerd Font fallback for glyphs Space Mono lacks. |
| Terminals | New GNOME Terminal and Ptyxis profiles with the Ember palette, opaque backgrounds and matching chrome. Existing profiles and shell commands are unchanged. |
| Other settings | Dark colour preference, orange system accent fallback, Yaru cursor, and dark GNOME Text Editor styling. |
| Brave snap | A separate compatible GTK4 CSS override when an existing `~/snap/brave/current` directory is present. |

The GTK/Shell bases and folder icons are generated from the installed Yaru assets; their upstream copyright notices accompany the generated output. The repo contains builders and colour overrides, not derived copies of Ubuntu's themes.

Coral marks focus, active controls, tab indicators, progress and suggested actions, with dark text on coral fills. Slate defines borders and large selections. Titles are bright, ordinary text pale and secondary text dim blue. Teal, amber, red and blue retain success, warning, error and information roles. In Files, teal navigation icons, amber headings and blue metadata also make those colours visible during ordinary browsing.

The [icon compatibility record](icons/nautilus-verified.json) is part of the installer, not an optional test log. The icon component selects Marbell-Ember only when generated pixels match its approved hash. An unfamiliar Yaru build keeps Yaru-dark selected until reviewed; see [icon maintenance](icons/README.md). The Shell builder likewise stops if it encounters unmapped colours that need review.

If user extensions are globally disabled, the Shell installer records that state, explicitly keeps the other installed user extensions suppressed, then clears the global switch so User Themes can run. Revert restores the previous switch and affected list membership. It does not add a background service.

## Installed files

Paths respect `XDG_CONFIG_HOME`, `XDG_DATA_HOME` and `XDG_STATE_HOME`, except for Brave's own snap configuration directory.

| Default path | Contents |
|---|---|
| `~/.config/gtk-3.0/gtk.css`, `~/.config/gtk-4.0/gtk.css` | User CSS; previous files are backed up, not merged. |
| `~/.config/fontconfig/conf.d/60-marbell-ember-space-mono.conf` | Space Mono → MesloLGM Nerd Font Mono fallback. |
| `~/.local/share/themes/Marbell-Ember/` | Generated GTK3, GTK4, Metacity and Shell theme assets. |
| `~/.local/share/icons/Marbell-Ember/` | Generated folder/places icons and icon cache. |
| `~/.local/share/gnome-shell/extensions/user-theme@gnome-shell-extensions.gcampax.github.com/` | Official User Themes extension, when missing. |
| `~/.local/share/backgrounds/marbell-ember/silent-seam-3440x1440.png` | Installed wallpaper copy. |
| `~/.local/share/org.gnome.Ptyxis/palettes/marbell-ember.palette` | Ptyxis palette. |
| `~/snap/brave/current/.config/gtk-4.0/gtk.css` | Optional Brave snap override. |
| `~/.local/state/marbell-ember/gnome/` | Snapshots, latest-snapshot pointer and installer lock. |

Installed wallpaper URIs point at the copied file, so moving the checkout does not break the background. Keep the checkout available for revert and component scripts.

Five 3440×1440 wallpapers are included in [wallpapers/](wallpapers/). They are cropped/upscaled from generated artwork; they are not native ultrawide renders. Only Silent Seam is installed automatically. The darker Silent Seam variant can be selected as a desktop background; GNOME's native lock screen follows the desktop wallpaper rather than using an independent image.

## Reloading and application limits

Reopen GTK applications after applying or reverting user CSS. The installer does not restart GNOME Shell, close applications or log you out. On first installation, the newly installed User Themes extension becomes available at the next login. GNOME 50's already-running XWayland title-bar helper also needs the next login to load the new libadwaita user CSS.

For Brave, select **Dark** and **Use GTK** in its Appearance settings, then restart the browser. The installer supplies the snap's CSS but does not edit browser Preferences or website content. A browser appearance choice made through its UI is outside the installer's rollback. Other confined applications may have separate configuration directories; custom-drawn application chrome may ignore GTK colours entirely.

Space Mono is wider than the default interface font. Some fixed-width labels, including quick-settings labels, can truncate. To use Ubuntu Sans for interface text while retaining the terminal and document fonts:

```sh
/usr/bin/gsettings set org.gnome.desktop.interface font-name 'Ubuntu Sans 11'
```

That changes interface typography only; explicit Shell theme and terminal-profile fonts are separate. Full revert restores every font setting changed by the desktop installer.

The fontconfig rule leaves ordinary text in Space Mono and prioritizes Meslo for missing symbols. This prevents unrelated symbol fonts from claiming the same private-use codepoints used by Nerd Font icons. Reopen terminals to clear cached font maps. Neither terminal profile sets a custom command, changes the login shell or `SHELL`, or edits shell startup files.

[oh-my-posh/ember.omp.json](oh-my-posh/ember.omp.json) is an optional prompt theme with Ember colours. Apply and revert never install it or touch an oh-my-posh configuration. To use it, copy it to a location of your choice and explicitly select it in your own oh-my-posh setup.

The desktop part does not theme GDM's login screen, the boot splash, Qt applications, editor interfaces, browser page content or sounds. It adds no blur, transparency or animation, and retains the base theme's existing motion behaviour. No unlock-dialog extension is installed.

## Component development

[Shell maintenance](shell/README.md) and [icon maintenance](icons/README.md) describe the builders and isolated preview tools. CSS parsing, snapshot round trips and a private HOME/XDG/dconf integration run exercise the installer without changing the logged-in desktop. Run records, machine audits and staging proposals are kept out of Git.
